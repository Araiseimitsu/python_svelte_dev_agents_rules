import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPT = SCRIPTS / "render_map.py"
sys.path.insert(0, str(SCRIPTS))

from render_map import (  # noqa: E402
    load_state,
    render_html,
    write_live_file,
    write_new_file,
)


class RenderMapTests(unittest.TestCase):
    def test_incomplete_state_renders_known_and_pending_nodes(self):
        html = render_html(
            {
                "title": "予約アプリ",
                "mode": "new_app",
                "idea": "小さな店舗向け予約アプリ",
                "audience": "個人経営の店舗",
                "problem": None,
                "outcome": None,
                "current_behavior": None,
                "flows": [],
                "screens": [],
                "constraints": [],
                "scope_in": [],
                "scope_out": [],
                "unknowns": ["解決したい問題"],
                "question_count": 1,
            }
        )

        self.assertIn("個人経営の店舗", html)
        self.assertIn("まだ未確定", html)
        self.assertIn('class="node pending"', html)

    def test_user_text_is_html_escaped(self):
        html = render_html({"idea": "<script>alert(1)</script>"})

        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

    def test_load_state_rejects_non_object_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "JSON object"):
                load_state(path)

    def test_write_new_file_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map-v01.html"
            path.write_text("old", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                write_new_file(path, "new")

            self.assertEqual("old", path.read_text(encoding="utf-8"))

    def test_cli_renders_new_app_and_feature_fixtures(self):
        cases = (
            ("new-app.json", "店舗予約アプリ", "個人経営の店舗"),
            ("feature.json", "お気に入り検索", "保存済み商品だけを絞り込む"),
        )
        for fixture_name, expected_title, expected_detail in cases:
            with self.subTest(fixture=fixture_name), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "map-v01.html"

                result = subprocess.run(
                    [sys.executable, "-X", "utf8", str(SCRIPT), str(FIXTURES / fixture_name), str(output)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )

                self.assertEqual(0, result.returncode, result.stderr)
                rendered = output.read_text(encoding="utf-8")
                self.assertIn(expected_title, rendered)
                self.assertIn(expected_detail, rendered)

    def test_new_app_omits_current_behavior_node(self):
        html = render_html({"mode": "new_app", "idea": "予約アプリ"})

        self.assertNotIn("現在の挙動", html)

    def test_feature_renders_current_behavior_node(self):
        html = render_html(
            {"mode": "feature", "idea": "絞り込み追加", "current_behavior": "全件表示のみ"}
        )

        self.assertIn("現在の挙動", html)
        self.assertIn("全件表示のみ", html)

    def test_every_card_is_placed_in_a_column(self):
        html = render_html({"mode": "new_app", "idea": "予約アプリ"})

        # Seven cards for a new app; 現在の挙動 belongs to feature work only.
        self.assertEqual(7, html.count('<article class="node '))
        self.assertIn('class="column column-left"', html)
        self.assertIn('class="column column-right"', html)

    def test_connectors_are_drawn_from_measured_positions(self):
        html = render_html({"mode": "new_app", "idea": "予約アプリ"})

        # The columns decide where cards land, so the curves are measured in
        # the browser rather than baked into the markup.
        self.assertIn('<svg class="links"', html)
        self.assertIn("__drawLinks", html)

    def test_flow_is_rendered_as_an_ordered_animated_lane(self):
        html = render_html({"mode": "new_app", "idea": "予約アプリ", "flows": ["日時を選ぶ", "予約する"]})

        self.assertIn('class="node known flow-node"', html)
        self.assertIn('class="flow-list"', html)
        self.assertIn('class="flow-number">1</span>', html)
        self.assertIn("@keyframes flow-sheen", html)

    def test_render_has_no_live_reload_script(self):
        html = render_html({"mode": "new_app", "idea": "予約アプリ"})

        self.assertNotIn("setInterval", html)
        self.assertNotIn("fetch(location.href", html)

    def test_progress_title_uses_actual_visible_item_count(self):
        new_app = render_html({"mode": "new_app", "idea": "予約アプリ"})
        feature = render_html({"mode": "feature", "idea": "絞り込み"})

        self.assertIn('title="主要な7項目のうち', new_app)
        self.assertIn('title="主要な8項目のうち', feature)

    def test_write_live_file_overwrites_in_place(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.html"
            write_live_file(path, "first")

            write_live_file(path, "second")

            self.assertEqual("second", path.read_text(encoding="utf-8"))

    def test_cli_live_flag_writes_both_snapshot_and_live_file(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "history" / "map-v01.html"
            live = Path(directory) / "map.html"

            result = subprocess.run(
                [
                    sys.executable, "-X", "utf8", str(SCRIPT),
                    str(FIXTURES / "new-app.json"), str(snapshot), "--live", str(live),
                ],
                capture_output=True, text=True, encoding="utf-8", check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("店舗予約アプリ", snapshot.read_text(encoding="utf-8"))
            self.assertIn("店舗予約アプリ", live.read_text(encoding="utf-8"))
            self.assertNotIn("setInterval", live.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
