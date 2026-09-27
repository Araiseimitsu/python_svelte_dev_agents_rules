#!/usr/bin/env python3
"""Open a real browser through Kimi WebBridge and collect visual UI edits."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


BRIDGE_URL = "http://127.0.0.1:10086/command"
SKILL_DIR = Path(__file__).resolve().parent.parent
OVERLAY_PATH = SKILL_DIR / "assets" / "visual-ui-overlay.js"
BRIDGE_BIN = Path.home() / ".kimi-webbridge" / "bin" / "kimi-webbridge"
if sys.platform == "win32":
    BRIDGE_BIN = BRIDGE_BIN.with_suffix(".exe")


class BridgeError(RuntimeError):
    pass


def _parse_status(output: str) -> dict[str, Any]:
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise BridgeError("Kimi WebBridge status did not return JSON")


def bridge_status() -> dict[str, Any]:
    if not BRIDGE_BIN.exists():
        raise BridgeError(
            f"Kimi WebBridge is not installed at {BRIDGE_BIN}. "
            "Install it only after user approval."
        )
    result = subprocess.run(
        [str(BRIDGE_BIN), "status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise BridgeError(result.stderr.strip() or result.stdout.strip())
    return _parse_status(result.stdout)


def ensure_bridge() -> dict[str, Any]:
    status = bridge_status()
    if not status.get("running"):
        result = subprocess.run(
            [str(BRIDGE_BIN), "start"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise BridgeError(result.stderr.strip() or result.stdout.strip())

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        status = bridge_status()
        if status.get("running") and status.get("extension_connected"):
            return status
        time.sleep(0.25)

    if not status.get("running"):
        raise BridgeError("Kimi WebBridge daemon could not be started")
    raise BridgeError(
        "Kimi WebBridge daemon is running, but the browser extension is not connected. "
        "Open the browser or enable the existing extension, then retry."
    )


def command(action: str, args: dict[str, Any], session: str) -> Any:
    payload = json.dumps(
        {"action": action, "args": args, "session": session},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        BRIDGE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BridgeError(f"Kimi WebBridge request failed: {exc}") from exc
    if not result.get("ok"):
        raise BridgeError(json.dumps(result, ensure_ascii=False))
    return result.get("data")


def inject_overlay(session: str) -> Any:
    source = OVERLAY_PATH.read_text(encoding="utf-8")
    code = f"{source}\n;window.__visualUiFix.install();"
    return command("evaluate", {"code": code}, session)


def open_page(url: str, session: str) -> dict[str, Any]:
    status = ensure_bridge()
    navigation = command(
        "navigate",
        {"url": url, "newTab": True, "group_title": "Visual UI Fix"},
        session,
    )
    if not isinstance(navigation, dict):
        raise BridgeError("Kimi WebBridge navigate returned an unexpected response")
    try:
        command("snapshot", {}, session)
        injection = inject_overlay(session)
    except Exception:
        try:
            command("close_tab", {}, session)
        except (BridgeError, OSError):
            pass
        raise
    return {
        "status": "ready",
        "session": session,
        "url": navigation.get("url", url),
        "tabId": navigation.get("tabId"),
        "bridgeVersion": status.get("version"),
        "overlay": injection,
    }


def collect(session: str) -> Any:
    data = command(
        "evaluate",
        {"code": "(() => JSON.stringify(window.__visualUiFix ? window.__visualUiFix.exportChanges() : null))()"},
        session,
    )
    value = data.get("value") if isinstance(data, dict) else None
    if value is None:
        raise BridgeError("Visual UI overlay is not active in the current page")
    parsed = json.loads(value)
    if parsed is None:
        raise BridgeError("Visual UI overlay is not active in the current page")
    invalid_viewports = [
        change.get("id", "unknown")
        for change in parsed.get("changes", [])
        if change.get("context", {}).get("viewport", {}).get("width", 0) <= 0
        or change.get("context", {}).get("viewport", {}).get("height", 0) <= 0
    ]
    if invalid_viewports:
        ids = ", ".join(invalid_viewports)
        raise BridgeError(
            f"Browser viewport was unavailable while capturing {ids}. "
            "Bring the browser tab to the foreground, discard those changes, and capture them again."
        )
    return parsed


def close_session(session: str) -> Any:
    status = bridge_status()
    if not status.get("running"):
        return {"success": True, "closed": 0, "daemon": "not-running"}
    if not status.get("extension_connected"):
        raise BridgeError(
            "Kimi WebBridge daemon is running, but the browser extension is not connected. "
            "The session could not be closed through the bridge."
        )
    return command("close_session", {}, session)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="visual-ui-fix")
    subparsers = parser.add_subparsers(dest="action", required=True)
    open_parser = subparsers.add_parser("open")
    open_parser.add_argument("url")
    subparsers.add_parser("collect")
    subparsers.add_parser("snapshot")
    subparsers.add_parser("inject")
    subparsers.add_parser("status")
    subparsers.add_parser("close")
    args = parser.parse_args()

    try:
        if args.action == "open":
            result = open_page(args.url, args.session)
        elif args.action == "collect":
            result = collect(args.session)
        elif args.action == "snapshot":
            ensure_bridge()
            result = command("snapshot", {}, args.session)
        elif args.action == "inject":
            ensure_bridge()
            result = inject_overlay(args.session)
        elif args.action == "status":
            result = bridge_status()
        else:
            result = close_session(args.session)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (BridgeError, subprocess.SubprocessError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
