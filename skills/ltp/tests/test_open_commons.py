"""Checks for the private browser view of a whole commons on a small fixture."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import yaml

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/open_commons.py"
SPEC = importlib.util.spec_from_file_location("open_commons", SCRIPT)
viewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(viewer)
REPO = SKILL.parents[1]
EXAMPLE = REPO / "apps/reasoning-demo/examples/willow-lane/reason-commons.yaml"
EXPORT = REPO / "scripts/export-skill-viewer.py"


def said(by, attribution="explicit"):
    return [{"by": by, "attribution": attribution, "mode": "text"}]


STATE = {
    "schema_version": 1, "project": "Quote turnaround", "driver": "alice",
    "participants": {"alice": "Alice", "bob": "Bob"}, "active_tree": "current_reality",
    "trees": {
        "goal": {"nodes": [
            {"id": "g1", "kind": "goal", "text": "Customers get quotes within a day.", "status": "accepted", "accepted_by": ["alice", "bob"], "contributions": said("alice")},
            {"id": "g2", "kind": "necessary_condition", "text": "Pricing approval takes hours, not days.", "status": "proposed", "contributions": said("assistant", "assistant")}],
            "links": [{"id": "gl1", "from": ["g2"], "to": "g1", "relation": "necessary_for", "status": "proposed", "contributions": said("assistant", "assistant")}],
            "backlog": []},
        "current_reality": {"nodes": [
            {"id": "n1", "kind": "undesirable_effect", "text": "Customers often wait more than three days for quotes.", "label": "Quotes take three days.", "status": "accepted", "accepted_by": ["alice"], "contributions": said("bob")},
            {"id": "n2", "kind": "cause", "text": "Sales often waits for pricing approval.", "status": "proposed", "contributions": said("alice", "driver_default"),
             "assumptions": [{"text": "Approval is the only queue.", "by": "bob"}]},
            {"id": "n3", "kind": "cause", "text": "Quotes are drafted from scratch each time.", "status": "disputed", "accepted_by": ["alice"], "contributions": said("bob"),
             "challenges": [{"text": "Most quotes reuse a template already.", "by": "alice"}]}],
            "links": [{"id": "l1", "from": ["n2", "n3"], "to": "n1", "relation": "contributes_to", "status": "proposed", "contributions": said("bob")}],
            "backlog": [{"ref": "l1", "work": "test_causality", "label": "Check whether approval alone explains the wait."},
                        {"ref": "n3", "work": "resolve_challenge"}]},
    },
}


def fixture(directory, state=STATE):
    path = Path(directory) / "reason-commons.yaml"
    path.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True))
    return path


class PrivateViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = fixture(self.tmp.name)
        self.data, self.outputs = viewer.build(self.state_path, made_at="2026-10-29T10:00:00+00:00")
        self.html = {name: value for name, value in self.outputs.items() if name.endswith(".html")}

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_tree_page_and_the_start_page_are_built(self):
        for name in ("index.html", "commons/index.html", "commons/map.html", "commons/goal.html", "commons/in-the-way.html",
                     "commons/items.html", "commons/questions.html", "commons/about.html", "commons/reasoning.json", "styles.css", "app.js"):
            self.assertIn(name, self.outputs)
        self.assertNotIn("commons/changes.html", self.outputs)  # The view is the file as it is now; the skill keeps the history.
        self.assertTrue(any(name.startswith("fonts/") for name in self.outputs))

    def test_every_page_says_it_is_private_and_points_nowhere_public(self):
        for name, page in self.html.items():
            self.assertIn("Private view on this computer.", page, name)
            self.assertIn("Nothing here is published or sent anywhere.", page, name)
            self.assertNotIn("issues/new", page, name)
            self.assertNotIn("Review a public GitHub draft", page, name)
            self.assertNotIn("Changes <span>", page, name)
            self.assertIsNone(re.search(r'href="/(?!/)', page), f"{name} links to a path that only exists on the live site")
            self.assertNotIn(self.tmp.name, page, "Local folders stay out of the pages")

    def test_every_local_link_and_asset_is_there(self):
        out = Path(self.tmp.name) / "site"
        viewer.write(self.outputs, out)
        for page in out.rglob("*.html"):
            for target in re.findall(r'(?:href|src)="([^"#?]+)', page.read_text()):
                if not target.startswith(("https://", "http://")):
                    self.assertTrue((page.parent / target).exists(), f"{page.relative_to(out)} links to missing {target}")

    def test_every_standing_is_shown_as_recorded_with_names(self):
        items = self.html["commons/items.html"]
        self.assertIn("Accepted for now by Alice and Bob", items)
        self.assertIn("Proposed by AI assistant", items)
        self.assertIn("Disputed; earlier accepted by Alice", items)
        self.assertIn("Most quotes reuse a template already.", items)
        self.assertIn("Raised by Alice", items)
        self.assertIn("Approval is the only queue.", items)
        self.assertIn("Proposed by Alice", items)  # A contribution credited to the driver by default keeps the driver's name.
        self.assertIn("Check whether approval alone explains the wait.", self.html["commons/questions.html"])
        about = self.html["commons/about.html"]
        for standing in ("Accepted for now", "Proposed", "Disputed"):
            self.assertIn(standing, about)

    def test_nothing_is_left_out(self):
        record = json.loads(self.outputs["commons/reasoning.json"])
        shown = {i["id"] for tree in record["trees"].values() for i in tree["nodes"] + tree["links"]}
        recorded = {i["id"] for tree in STATE["trees"].values() for i in tree["nodes"] + tree["links"]}
        self.assertEqual(shown, recorded)
        self.assertEqual(record["view"], "private")
        self.assertEqual(record["source_file"], "reason-commons.yaml")
        items = self.html["commons/items.html"]
        for ident in recorded:
            self.assertIn(f'id="{ident}"', items)

    def test_briefs_resume_from_the_working_file(self):
        items = self.html["commons/items.html"]
        self.assertIn("This is from my own Reason Commons working file, reason-commons.yaml.", items)
        self.assertNotIn("Public page:", items)

    def test_a_loop_of_connections_is_drawn_round_the_side_with_its_relation(self):
        looped = deepcopy(STATE)
        looped["trees"]["current_reality"]["links"].append(
            {"id": "l2", "from": ["n1"], "to": "n2", "relation": "contributes_to", "status": "proposed", "contributions": said("bob")})
        data, outputs = viewer.build(fixture(self.tmp.name, looped))
        record = json.loads(outputs["commons/reasoning.json"])
        closing = {l["id"]: l for l in record["trees"]["current_reality"]["links"] if l.get("loop")}
        self.assertEqual(set(closing), {"l2"})
        self.assertEqual(closing["l2"]["relation"], "contributes_to")
        self.assertIn("loops back", outputs["commons/in-the-way.html"])
        self.assertIn("Loops back", outputs["commons/in-the-way.html"])  # The legend explains the drawing.
        self.assertNotIn("feeds back", outputs["commons/items.html"])

    def test_an_empty_file_has_nothing_to_show(self):
        empty = {**STATE, "trees": {"current_reality": {"nodes": [], "links": [], "backlog": []}}}
        with self.assertRaisesRegex(ValueError, "No reasoning has been recorded yet"):
            viewer.build(fixture(self.tmp.name, empty))

    def test_a_commons_without_a_goal_still_opens(self):
        no_goal = {**STATE, "trees": {"current_reality": STATE["trees"]["current_reality"]}}
        _, outputs = viewer.build(fixture(self.tmp.name, no_goal))
        self.assertIn("No goal is recorded yet.", outputs["commons/index.html"])
        self.assertIn("<h1>1 question</h1>", outputs["commons/map.html"])

    def test_a_rebuild_removes_only_its_own_stale_pages(self):
        out = Path(self.tmp.name) / "site"
        viewer.write(self.outputs, out)
        (out / "commons/learning.html").write_text("stale")
        manifest = out / viewer.MANIFEST
        manifest.write_text(manifest.read_text() + "commons/learning.html\n")
        viewer.write(self.outputs, out)
        self.assertFalse((out / "commons/learning.html").exists())
        self.assertTrue((out / "commons/items.html").exists())

    def test_it_will_not_write_into_a_folder_it_did_not_make(self):
        out = Path(self.tmp.name) / "notes"
        out.mkdir()
        (out / "mine.txt").write_text("keep")
        with self.assertRaisesRegex(ValueError, "did not write"):
            viewer.write(self.outputs, out)
        self.assertEqual((out / "mine.txt").read_text(), "keep")

    def test_the_command_writes_beside_the_file_and_reports_what_to_open(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.state_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        out = self.state_path.parent / ".reason-commons" / "site"
        self.assertEqual(report["output"], str(out.resolve()))
        self.assertEqual(report["open"], (out.resolve() / "commons/index.html").as_uri())
        self.assertEqual(report["standings"], {"accepted": 2, "proposed": 4, "disputed": 1})
        self.assertTrue((out / "commons/index.html").is_file())

    @unittest.skipUnless(EXAMPLE.is_file(), "The fictional example lives in the Reason Commons repository")
    def test_outcome_reports_get_a_learning_page(self):
        _, outputs = viewer.build(EXAMPLE)
        self.assertIn("commons/learning.html", outputs)
        self.assertIn("What happened when they tried it", outputs["commons/learning.html"])

    @unittest.skipUnless(EXPORT.is_file(), "The renderer's originals live in the Reason Commons repository")
    def test_the_viewer_copy_matches_the_demo_renderer(self):
        result = subprocess.run([sys.executable, str(EXPORT), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
