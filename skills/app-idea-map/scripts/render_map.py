#!/usr/bin/env python3
"""Render a versioned app-requirements state as a self-contained radial mind map."""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple


TEXT_FIELDS = (
    "title",
    "mode",
    "idea",
    "audience",
    "problem",
    "outcome",
    "current_behavior",
)
LIST_FIELDS = (
    "flows",
    "screens",
    "constraints",
    "scope_in",
    "scope_out",
    "unknowns",
)

# Canvas the SVG connector layer is drawn in. Node positions below are in these
# same coordinates so the curves land on the nodes instead of merely decorating.
class Branch(NamedTuple):
    """One card in a side column."""

    key: str
    label: str
    hue: int
    side: str  # "left" or "right" of the core


# Declaration order is top-to-bottom within each column. The "why" of the idea
# sits on the left, the "what to build" on the right.
BRANCHES = (
    Branch("audience", "利用者", 210, "left"),
    Branch("problem", "解決したい問題", 350, "left"),
    Branch("current", "現在の挙動", 15, "left"),
    Branch("outcome", "望む結果", 40, "left"),
    Branch("flows", "主要な体験", 155, "right"),
    Branch("screens", "画面・情報", 190, "right"),
    Branch("scope", "範囲", 265, "right"),
    Branch("constraints", "制約", 300, "right"),
)


def load_state(path: Path) -> dict[str, object]:
    """Load and validate a JSON object from *path*."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object")
    return data


def write_new_file(path: Path, content: str) -> None:
    """Write a new UTF-8 file without replacing an existing version."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def write_live_file(path: Path, content: str) -> None:
    """Write the always-current map, replacing any earlier render in place.

    The versioned history keeps every render recoverable, so this single live
    path is safe to overwrite and lets the user keep one browser tab open.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _normalize_state(state: Mapping[str, object]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key in TEXT_FIELDS:
        value = state.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{key} must be a string or null")
        normalized[key] = value.strip() if isinstance(value, str) else None

    for key in LIST_FIELDS:
        value = state.get(key, [])
        if value is None:
            value = []
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError(f"{key} must be a list of strings")
        normalized[key] = [item.strip() for item in value if item.strip()]

    question_count = state.get("question_count", 0)
    if isinstance(question_count, bool) or not isinstance(question_count, int) or question_count < 0:
        raise ValueError("question_count must be a non-negative integer")
    normalized["question_count"] = question_count

    version = state.get("version")
    if version is not None and (isinstance(version, bool) or not isinstance(version, int) or version < 0):
        raise ValueError("version must be a non-negative integer or null")
    normalized["version"] = version
    return normalized


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _body(value: str | None) -> tuple[str, bool]:
    if value:
        return f'<p class="node-text">{_escape(value)}</p>', True
    return '<p class="node-text is-pending">まだ未確定</p>', False


def _list_body(values: list[str]) -> tuple[str, bool]:
    if values:
        items = "".join(f"<li>{_escape(value)}</li>" for value in values)
        return f'<ul class="node-list">{items}</ul>', True
    return '<p class="node-text is-pending">まだ未確定</p>', False


def _flow_body(values: list[str]) -> tuple[str, bool]:
    """Render a journey as an ordered lane rather than a plain bullet list."""
    if values:
        steps = "".join(
            f'<li style="--step:{index}"><span class="flow-number">{index}</span>'
            f'<span class="flow-copy">{_escape(value)}</span></li>'
            for index, value in enumerate(values, start=1)
        )
        return f'<ol class="flow-list">{steps}</ol>', True
    return '<p class="node-text is-pending">まだ未確定</p>', False


def _node_html(*, key: str, label: str, body: str, known: bool, hue: int) -> str:
    """One card. Its position comes from the column flow, not from inline CSS."""
    state_class = "known" if known else "pending"
    role_class = " flow-node" if key == "flows" else ""
    return (
        f'<article class="node {state_class}{role_class}" data-key="{key}" style="--hue:{hue}">'
        f'<h2 class="node-label">{_escape(label)}</h2>'
        f'<div class="node-body">{body}</div></article>'
    )


def _branch_bodies(data: Mapping[str, Any]) -> dict[str, tuple[str, bool]]:
    """Map every node key to its rendered body and whether it is settled."""
    bodies: dict[str, tuple[str, bool]] = {}
    for key in ("audience", "problem", "outcome"):
        bodies[key] = _body(data[key])
    bodies["flows"] = _flow_body(data["flows"])
    bodies["screens"] = _list_body(data["screens"])

    scope_values = [
        *(f"含む: {item}" for item in data["scope_in"]),
        *(f"含まない: {item}" for item in data["scope_out"]),
    ]
    bodies["scope"] = _list_body(scope_values)
    bodies["constraints"] = _list_body(data["constraints"])

    # 現在の挙動 only exists for feature work; a permanent "not applicable" box
    # would waste prime canvas space on a new app, so the caller omits it.
    if data["mode"] == "feature":
        bodies["current"] = _body(data["current_behavior"])
    return bodies


def render_html(state: Mapping[str, object]) -> str:
    """Return a responsive, self-contained radial mind map document."""
    if not isinstance(state, Mapping):
        raise ValueError("State must be a mapping")
    data = _normalize_state(state)

    mode_label = "機能追加" if data["mode"] == "feature" else "新規アプリ"
    title = data["title"] or "要件マップ"
    idea_body, idea_known = _body(data["idea"])
    bodies = _branch_bodies(data)

    columns: dict[str, list[str]] = {"left": [], "right": []}
    settled = 0
    visible = [branch for branch in BRANCHES if branch.key in bodies]
    shown = len(visible)

    for branch in visible:
        body, known = bodies[branch.key]
        settled += int(known)
        columns[branch.side].append(
            _node_html(
                key=branch.key,
                label=branch.label,
                body=body,
                known=known,
                hue=branch.hue,
            )
        )

    total = shown
    progress = round(100 * settled / total) if total else 0
    unknowns = data["unknowns"]
    if unknowns:
        items = "".join(f"<li>{_escape(item)}</li>" for item in unknowns)
        unknowns_block = f'<ul class="open-list">{items}</ul>'
    else:
        unknowns_block = '<p class="open-empty">大きな未決事項はありません</p>'

    version_label = f"v{data['version']:02d} · " if data["version"] is not None else ""

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)} — 要件マップ</title>
  <style>
    :root {{
      color-scheme: light dark;
      --ink: light-dark(#1b2230, #e8eef7);
      --ink-soft: light-dark(#5d6a7e, #9fadc0);
      --ink-faint: light-dark(#93a0b2, #6d7b8e);
      --surface: light-dark(#ffffff, #161d29);
      --canvas: light-dark(#f4f7fb, #0d1219);
      --hairline: light-dark(#dbe3ed, #2b3646);
      --node-tint: light-dark(hsl(var(--hue) 82% 97%), hsl(var(--hue) 34% 15%));
      --node-edge: light-dark(hsl(var(--hue) 52% 78%), hsl(var(--hue) 38% 38%));
      --node-accent: light-dark(hsl(var(--hue) 62% 38%), hsl(var(--hue) 68% 74%));
      font-family: "Hiragino Kaku Gothic ProN", "Noto Sans JP", Inter, system-ui, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(1200px 700px at 50% 42%, light-dark(#ffffff, #18212e) 0%, transparent 70%),
        var(--canvas);
      min-height: 100vh;
    }}
    .sheet {{ width: min(1360px, 100%); margin: 0 auto; padding: clamp(20px, 3.5vw, 44px); }}

    .sheet-head {{
      display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between;
      gap: 14px 24px; margin-bottom: clamp(18px, 3vw, 34px);
    }}
    h1 {{ margin: 0; font-size: clamp(22px, 2.6vw, 34px); font-weight: 600; letter-spacing: .01em; }}
    .head-meta {{ display: flex; align-items: center; gap: 14px; color: var(--ink-soft); font-size: 13px; }}
    .badge {{
      padding: 4px 11px; border: 1px solid var(--hairline); border-radius: 999px;
      background: var(--surface); font-weight: 500; white-space: nowrap;
    }}
    .gauge {{ display: flex; align-items: center; gap: 8px; }}
    .gauge-track {{
      width: 90px; height: 5px; border-radius: 999px; overflow: hidden;
      background: light-dark(#e3e9f2, #263141);
    }}
    .gauge-fill {{
      display: block; height: 100%; border-radius: 999px;
      background: light-dark(#4f7bd6, #7aa6f0);
      transition: width .5s ease;
    }}

    /* --- Map ------------------------------------------------------------- */
    .map {{
      position: relative;
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: clamp(24px, 4cqi, 56px);
      container-type: inline-size;
    }}
    /* Two stacks flanking the core. The browser distributes the vertical space,
       so a tall card pushes its own column instead of colliding with a
       neighbour the way absolute ring positions used to allow. */
    .column {{
      display: flex; flex-direction: column;
      justify-content: center; gap: clamp(12px, 1.8cqi, 22px);
    }}
    .column-left {{ align-items: flex-end; }}
    .column-right {{ align-items: flex-start; }}
    .links {{ position: absolute; inset: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }}
    .link {{
      fill: none;
      stroke: light-dark(hsl(var(--hue) 48% 62%), hsl(var(--hue) 44% 52%));
      stroke-width: 2.4; stroke-linecap: round;
    }}
    .link.pending {{ stroke: var(--ink-faint); stroke-dasharray: 3 7; opacity: .55; }}

    .node, .core {{
      position: relative;
      width: clamp(160px, 17cqi, 250px);
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--node-edge);
      background: var(--node-tint);
      box-shadow: 0 10px 26px light-dark(rgba(26,38,58,.09), rgba(0,0,0,.34));
      transition: transform .18s ease, box-shadow .18s ease;
      z-index: 1;
    }}
    .node:hover {{
      transform: scale(1.035);
      box-shadow: 0 16px 34px light-dark(rgba(26,38,58,.16), rgba(0,0,0,.46));
      z-index: 5;
    }}
    .node.pending {{
      border-style: dashed;
      border-color: light-dark(#c8d1de, #38455a);
      background: light-dark(#fbfcfe, #131a24);
      box-shadow: none;
    }}
    .node-label {{
      margin: 0 0 6px;
      font-size: clamp(10px, 1.05cqi, 12px);
      font-weight: 600; letter-spacing: .07em;
      color: var(--node-accent);
    }}
    .node.pending .node-label {{ color: var(--ink-faint); }}
    .node-text {{ margin: 0; font-size: clamp(12px, 1.25cqi, 14px); line-height: 1.55; }}
    .node-list {{ margin: 0; padding-left: 15px; font-size: clamp(12px, 1.2cqi, 13.5px); line-height: 1.5; }}
    .node-list li + li {{ margin-top: 4px; }}
    .is-pending, .is-na {{ color: var(--ink-faint); }}

    /* The main journey reads as a moving lane: numbered stops remain clear in
       a static export, while the highlight suggests direction on screen. */
    .flow-node {{ overflow: hidden; }}
    .flow-node.known::after {{
      content: ""; position: absolute; inset: 0 auto 0 -45%; width: 38%;
      background: linear-gradient(100deg, transparent, light-dark(rgba(255,255,255,.72), rgba(255,255,255,.10)), transparent);
      transform: skewX(-12deg); pointer-events: none;
      animation: flow-sheen 4.8s ease-in-out infinite;
    }}
    .flow-list {{ list-style: none; margin: 0; padding: 0; }}
    .flow-list li {{
      position: relative; display: grid; grid-template-columns: 24px 1fr;
      align-items: start; gap: 8px; min-height: 34px;
      opacity: 0; transform: translateX(-7px);
      animation: flow-arrive .42s ease-out forwards;
      animation-delay: calc(var(--step) * 90ms);
    }}
    .flow-list li:not(:last-child)::after {{
      content: ""; position: absolute; left: 11px; top: 23px; bottom: 1px;
      width: 2px; border-radius: 2px;
      background: linear-gradient(to bottom, var(--node-accent), transparent);
    }}
    .flow-number {{
      position: relative; z-index: 1; display: grid; place-items: center;
      width: 24px; height: 24px; border-radius: 50%;
      color: light-dark(#fff, #102018); background: var(--node-accent);
      font-size: 11px; font-weight: 700;
      box-shadow: 0 0 0 4px var(--node-tint);
    }}
    .flow-copy {{ padding: 2px 0 9px; font-size: clamp(12px, 1.2cqi, 13.5px); line-height: 1.45; }}
    @keyframes flow-arrive {{ to {{ opacity: 1; transform: translateX(0); }} }}
    @keyframes flow-sheen {{
      0%, 58% {{ left: -45%; opacity: 0; }}
      68% {{ opacity: 1; }}
      88%, 100% {{ left: 120%; opacity: 0; }}
    }}

    .core {{
      position: relative;
      z-index: 2;
      width: clamp(190px, 19cqi, 290px);
      padding: 18px 20px;
      border: 0; border-radius: 20px;
      color: #f7fafe;
      background: linear-gradient(150deg, #35507e 0%, #253c62 55%, #1d2f4d 100%);
      box-shadow: 0 18px 46px light-dark(rgba(24,44,80,.30), rgba(0,0,0,.55));
    }}
    .core .node-label {{ color: #a8c4ee; }}
    .core .node-text {{ font-size: clamp(13px, 1.5cqi, 17px); font-weight: 500; line-height: 1.5; }}
    .core .is-pending {{ color: #9fb2cf; }}

    /* --- Open questions --------------------------------------------------- */
    .open {{
      margin-top: clamp(16px, 2.5vw, 30px);
      padding: 16px 20px;
      border: 1px solid var(--hairline); border-radius: 14px;
      background: var(--surface);
    }}
    .open h2 {{
      margin: 0 0 8px; font-size: 12px; font-weight: 600;
      letter-spacing: .07em; color: var(--ink-soft);
    }}
    .open-list {{ margin: 0; padding-left: 18px; font-size: 14px; line-height: 1.6; }}
    .open-empty {{ margin: 0; font-size: 14px; color: light-dark(#3d7a5f, #86d2b2); }}
    .legend {{
      display: flex; flex-wrap: wrap; gap: 8px 20px;
      margin: 16px 0 0; color: var(--ink-faint); font-size: 12px;
    }}
    .legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
    .swatch {{ width: 18px; height: 0; border-top: 2px solid currentColor; }}
    .swatch.dashed {{ border-top-style: dashed; }}

    /* --- Narrow screens: fall back to a readable stack -------------------- */
    @media (max-width: 900px) {{
      /* One column reads better than a squeezed map; the core leads. */
      .map {{ display: flex; flex-direction: column; gap: 12px; }}
      .links {{ display: none; }}
      .column {{ width: 100%; align-items: stretch; }}
      .node, .core {{ width: 100%; }}
      .node:hover {{ transform: none; }}
      .core {{ order: -1; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ transition: none !important; }}
    }}
  </style>
</head>
<body>
  <main class="sheet">
    <header class="sheet-head">
      <h1>{_escape(title)}</h1>
      <div class="head-meta">
        <span class="badge">{mode_label}</span>
        <span class="badge">{version_label}質問 {data['question_count']} 件</span>
        <span class="gauge" title="主要な{total}項目のうち {settled} 件が確定">
          <span class="gauge-track"><span class="gauge-fill" style="width:{progress}%"></span></span>
          <span>{settled}/{total} 確定</span>
        </span>
      </div>
    </header>

    <div class="map" aria-label="{_escape(title)} の要件マインドマップ">
      <svg class="links" aria-hidden="true"></svg>
      <div class="column column-left">{''.join(columns['left'])}</div>
      <article class="core {'known' if idea_known else 'pending'}">
        <h2 class="node-label">作りたいもの</h2>
        <div class="node-body">{idea_body}</div>
      </article>
      <div class="column column-right">{''.join(columns['right'])}</div>
    </div>

    <section class="open">
      <h2>残っている確認</h2>
      {unknowns_block}
      <p class="legend">
        <span><span class="swatch"></span>確定した内容</span>
        <span><span class="swatch dashed"></span>これから確認すること</span>
      </p>
    </section>
  </main>
{CONNECTOR_SCRIPT}</body>
</html>
"""


CONNECTOR_SCRIPT = """
<script>
// Connectors are drawn from measured geometry rather than precomputed
// coordinates: the columns decide where cards land, so only the browser knows
// the real positions. Redrawn whenever the layout can change.
(function () {
  function draw() {
    var map = document.querySelector('.map');
    var svg = map && map.querySelector('svg.links');
    var core = map && map.querySelector('.core');
    if (!map || !svg || !core) { return; }

    var box = map.getBoundingClientRect();
    var coreBox = core.getBoundingClientRect();
    svg.setAttribute('viewBox', '0 0 ' + box.width + ' ' + box.height);
    while (svg.firstChild) { svg.removeChild(svg.firstChild); }

    var coreMidY = coreBox.top + coreBox.height / 2 - box.top;
    document.querySelectorAll('.node').forEach(function (node) {
      var r = node.getBoundingClientRect();
      var onLeft = r.left + r.width / 2 < coreBox.left + coreBox.width / 2;
      // Start at the core edge facing the card, end at the card's near edge.
      var x1 = (onLeft ? coreBox.left : coreBox.right) - box.left;
      var y1 = coreMidY;
      var x2 = (onLeft ? r.right : r.left) - box.left;
      var y2 = r.top + r.height / 2 - box.top;
      var midX = (x1 + x2) / 2;

      var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute(
        'd',
        'M ' + x1 + ' ' + y1 +
        ' C ' + midX + ' ' + y1 + ' ' + midX + ' ' + y2 + ' ' + x2 + ' ' + y2
      );
      path.setAttribute(
        'class',
        'link ' + (node.classList.contains('pending') ? 'pending' : 'known')
      );
      path.style.setProperty('--hue', getComputedStyle(node).getPropertyValue('--hue'));
      svg.appendChild(path);
    });
  }

  window.__drawLinks = draw;
  addEventListener('resize', draw);
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(draw); }
  if (document.readyState === 'loading') {
    addEventListener('DOMContentLoaded', draw);
  } else {
    draw();
  }
})();
</script>
"""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_html", type=Path, help="versioned snapshot path; never overwritten")
    parser.add_argument(
        "--live",
        type=Path,
        default=None,
        help="stable path overwritten each run so one open browser tab stays current",
    )
    args = parser.parse_args(argv)
    try:
        state = load_state(args.input_json)
        write_new_file(args.output_html, render_html(state))
        if args.live is not None:
            write_live_file(args.live, render_html(state))
    except (OSError, ValueError) as error:
        print(f"render_map: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
