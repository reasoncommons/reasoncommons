"""Toy-case checks; no real project data or working-tree outputs are changed."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/update_views.py"
SPEC = importlib.util.spec_from_file_location("views", SCRIPT)
views = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(views)


def toy():
    # Observations from claim-tree-annotation.md, not invented CRT symptoms.
    contribution = [{"by": "alice", "attribution": "explicit", "mode": "text"}]
    texts = ["13% productivity gain for remote workers", "Study covers call centre workers only", "Gain was on solo call-handling tasks specifically"]
    nodes = [{"id": f"n{i}", "kind": "observation", "text": text, "status": "accepted", "accepted_by": ["alice"], "contributions": deepcopy(contribution)} for i, text in enumerate(texts, 1)]
    link = {"id": "l1", "from": ["n2"], "to": "n1", "relation": "limits_scope", "status": "accepted", "accepted_by": ["alice"], "contributions": deepcopy(contribution)}
    return {"schema_version": 1, "project": "Remote-work toy fixture", "driver": "alice", "participants": {"alice": "Alice", "bob": "Bob"}, "active_tree": "current_reality", "trees": {"current_reality": {"nodes": nodes, "links": [link], "backlog": [{"ref": "l1", "work": "examine_assumption"}]}}}


def receipt():
    return {"proposal_ref": "change-remote-work-scope", "proposal_revision": 1, "by": "alice",
            "recorded_at": "2026-10-14T12:00:00Z", "timezone": "Europe/Berlin", "mode": "text",
            "source": "conversation", "source_text": "yes, I accept this proposal",
            "scope": "Clarify the README's study scope and test the generalisation at l1.",
            "node_ids": [], "link_ids": ["l1"]}


class ChangeAcceptanceTests(unittest.TestCase):
    def test_feedback_validation_is_part_of_standard_validation(self):
        state = toy()
        state["feedback_requests"] = [{"id": "broken"}]
        with self.assertRaises(ValueError):
            views.validate(state)

    def setUp(self):
        self.state = toy()
        self.state["change_acceptances"] = [receipt()]

    def test_complete_record_and_legacy_state_are_valid(self):
        views.validate(self.state)
        views.validate(toy())
        self.state["change_acceptances"][0]["accepted_at"] = "2026-10-14T13:59:00+02:00"
        views.validate(self.state)

    def test_missing_required_metadata_is_rejected(self):
        for field in receipt():
            with self.subTest(field=field):
                state = deepcopy(self.state)
                del state["change_acceptances"][0][field]
                with self.assertRaises(ValueError):
                    views.validate(state)

    def test_invalid_values_are_rejected(self):
        invalid = {
            "proposal_ref": ["", " "], "proposal_revision": [0, -1, True, "1"],
            "by": ["assistant", "unknown", ""], "source_text": ["", " "], "scope": ["", " "],
            "recorded_at": ["not a time", "2026-10-14T12:00:00", "2026-10-14T14:00:00+02:00"],
            "timezone": ["", "Unknown/Place"], "mode": ["voice", "unknown"], "source": ["tool", "document"],
            "node_ids": [None, "n1", [""], ["n1", "n1"], [12]],
            "link_ids": [None, "l1", [""], ["l1", "l1"], [12]],
            "accepted_at": ["not a time", "2026-10-14T12:00:00"],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    state = deepcopy(self.state)
                    state["change_acceptances"][0][field] = value
                    with self.assertRaises(ValueError):
                        views.validate(state)
        for value in ({}, [None]):
            with self.subTest(receipts=value):
                state = deepcopy(self.state)
                state["change_acceptances"] = value
                with self.assertRaises(ValueError):
                    views.validate(state)

    def test_same_version_and_person_cannot_be_recorded_twice(self):
        self.state["change_acceptances"].append(receipt())
        with self.assertRaisesRegex(ValueError, "Duplicate change acceptance"):
            views.validate(self.state)
        self.state["change_acceptances"][1]["proposal_revision"] = 2
        views.validate(self.state)
        self.state["change_acceptances"][1].update(proposal_revision=1, by="bob")
        views.validate(self.state)

    def test_historical_references_survive_removal(self):
        self.state["change_acceptances"][0]["node_ids"] = ["removed-node"]
        self.state["trees"]["current_reality"] = {"nodes": [], "links": [], "backlog": []}
        views.validate(self.state)

    def test_an_id_cannot_refer_to_both_a_node_and_link(self):
        self.state["change_acceptances"][0]["node_ids"] = ["l1"]
        with self.assertRaisesRegex(ValueError, "both node and link"):
            views.validate(self.state)

    def test_approved_paths_are_optional_but_must_be_exact_relative_paths(self):
        for paths in ([], ["README.md", "skills/ltp/SKILL.md"]):
            self.state["change_acceptances"][0]["approved_paths"] = paths
            views.validate(self.state)
        for paths in (None, "README.md", [""], ["/tmp/file"], ["../file"], ["a/../file"], ["a//file"], ["./file"], ["."], ["a\\file"], ["README.md", "README.md"], [42]):
            with self.subTest(paths=paths):
                self.state["change_acceptances"][0]["approved_paths"] = paths
                with self.assertRaises(ValueError):
                    views.validate(self.state)


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "reason-commons.yaml"
        self.out = self.root / ".reason-commons"
        self.state = toy()

    def save(self):
        self.path.write_text(yaml.safe_dump(self.state, sort_keys=False))
        return views.update(self.path)

    def diagram(self, view="changes", name="current_reality"):
        return self.out / "diagrams" / view / f"{name}.svg"

    def test_proposals_are_saved_without_history_or_diagrams(self):
        tree = self.state["trees"]["current_reality"]
        for item in tree["nodes"] + tree["links"]:
            item["status"] = "proposed"
        result = self.save()
        self.assertEqual(result["revision"], 0)
        self.assertFalse(self.out.exists())

    def test_first_acceptance_keeps_backlogged_and_isolated_nodes(self):
        result = self.save()
        self.assertEqual(result["revision"], 1)
        self.assertIn("Gain was on solo call-handling", self.diagram("current").read_text())
        self.assertIn("limits scope", self.diagram("current").read_text())
        snapshot = yaml.safe_load((self.out / "history/000001.yaml").read_text())
        self.assertIsNone(snapshot["previous_revision"])
        self.assertEqual(snapshot["trees"], self.state["trees"])
        self.assertNotIn("revision", yaml.safe_load(self.path.read_text()))

    def test_labels_are_short_single_lines_and_views_draw_them(self):
        node = self.state["trees"]["current_reality"]["nodes"][0]
        for bad in ("", "x" * (views.LABEL_MAX + 1), "two\nlines", 7):
            node["label"] = bad
            with self.subTest(label=bad), self.assertRaises(ValueError):
                views.validate(self.state)
        self.state["trees"]["current_reality"]["backlog"][0]["label"] = "y" * (views.LABEL_MAX + 1)
        node["label"] = "Remote workers gained 13%."
        with self.assertRaises(ValueError):
            views.validate(self.state)
        self.state["trees"]["current_reality"]["backlog"][0]["label"] = "Test the limit."
        self.save()
        current = self.diagram("current").read_text()
        self.assertIn("Remote workers gained 13%.", current)
        self.assertNotIn("13% productivity gain for remote workers", current)

    def test_traces_are_described_by_tree_and_count_not_ids(self):
        goal = {"id": "goal-node-xyz", "kind": "goal", "text": "Understand where remote work helps.", "status": "accepted",
                "accepted_by": ["alice"], "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}]}
        self.state["trees"]["goal"] = {"nodes": [goal], "links": [], "backlog": []}
        self.state["trees"]["current_reality"]["nodes"][0]["addresses"] = ["goal-node-xyz"]
        self.save()
        current = self.diagram("current").read_text()
        self.assertIn("Addresses 1 Goal statement", current)
        self.assertNotIn("goal-node-xyz", "".join(ET.fromstring(current).itertext()))

    def test_wip_attribution_and_reordering_do_not_clear_delta(self):
        self.save()
        original = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.out.rglob("*") if p.is_file()}
        tree = self.state["trees"]["current_reality"]
        tree["nodes"].reverse()
        tree["nodes"][0]["contributions"][0]["by"] = "bob"
        tree["nodes"][0]["accepted_by"].append("bob")
        proposal = deepcopy(tree["nodes"][0])
        proposal.update(id="n4", status="proposed", text="A new question for later")
        tree["nodes"].append(proposal)
        tree["backlog"].append({"ref": "n4", "work": "clarify"})
        self.assertEqual(self.save()["revision"], 1)
        self.assertEqual(original, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in original})

    def test_change_receipt_does_not_endorse_proposals_or_create_revision(self):
        self.save()
        original = {p: p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        self.state["change_acceptances"] = [receipt()]
        proposal = deepcopy(self.state["trees"]["current_reality"]["nodes"][0])
        proposal.update(id="n4", status="proposed", text="Check whether the study generalises.")
        proposal.pop("accepted_by")
        self.state["trees"]["current_reality"]["nodes"].append(proposal)
        self.state["change_acceptances"][0]["node_ids"] = ["n4"]
        result = self.save()
        self.assertEqual(result["revision"], 1)
        self.assertEqual(result["changed_trees"], [])
        self.assertEqual(original, {p: p.read_bytes() for p in original})
        self.assertNotIn("n4", views.accepted(self.state)["current_reality"]["nodes"])
        self.assertEqual(yaml.safe_load(self.path.read_text())["change_acceptances"], [dict(receipt(), node_ids=["n4"])])

    def test_invalid_change_receipt_cannot_create_a_snapshot(self):
        self.state["change_acceptances"] = [dict(receipt(), by="assistant")]
        with self.assertRaisesRegex(ValueError, "configured human"):
            self.save()
        self.assertFalse(self.out.exists())

    def test_rewording_shows_old_and_new_with_minimal_context(self):
        self.save()
        history = (self.out / "history/000001.yaml").read_bytes()
        self.state["trees"]["current_reality"]["nodes"][0]["text"] = "The study reports a 13% productivity gain."
        self.save()
        dot = self.diagram().read_text()
        self.assertIn("PREVIOUSLY:", dot)
        self.assertIn("13% productivity gain for remote", dot)
        self.assertIn(">workers<", dot)
        self.assertIn("The study reports", dot)
        self.assertIn("Study covers call centre workers", dot)
        self.assertNotIn("solo call-handling", dot)
        self.assertEqual(history, (self.out / "history/000001.yaml").read_bytes())

    def test_loss_of_acceptance_uses_last_accepted_text(self):
        self.save()
        tree = self.state["trees"]["current_reality"]
        tree["nodes"][0].update(status="disputed", text="UNACCEPTED REPLACEMENT")
        tree["links"][0]["status"] = "proposed"
        self.save()
        self.assertNotIn('"n1"', self.diagram("current").read_text())
        delta = self.diagram().read_text()
        self.assertIn("REMOVED", delta)
        self.assertIn("13% productivity gain", delta)
        self.assertNotIn("UNACCEPTED REPLACEMENT", delta)

    def test_changed_joint_link_preserves_both_structures(self):
        self.save()
        self.state["trees"]["current_reality"]["links"][0]["from"].append("n3")
        self.save()
        dot = self.diagram().read_text()
        self.assertIn(">AND<", dot)
        self.assertIn("Study covers call centre workers", dot)
        self.assertIn("REMOVED: limits scope", dot)
        self.assertIn("CHANGED: limits scope", dot)

    def test_another_tree_keeps_previous_tree_delta(self):
        self.save()
        previous = self.diagram().read_bytes()
        objective = deepcopy(self.state["trees"]["current_reality"]["nodes"][0])
        objective.update(id="g1", kind="goal", text="Understand the conditions for productive remote work.")
        self.state["trees"]["goal"] = {"nodes": [objective], "links": [], "backlog": []}
        self.state["active_tree"] = "goal"
        result = self.save()
        self.assertEqual(result["changed_trees"], ["goal"])
        self.assertEqual(previous, self.diagram().read_bytes())
        self.assertTrue(self.diagram(name="goal").exists())

    def test_render_failure_retry_does_not_duplicate_history(self):
        self.save()
        self.state["trees"]["current_reality"]["nodes"][0]["text"] = "A clarified observation"
        original_write = views.write_atomic
        def fail_svg(path, content, exclusive=False):
            if path.suffix == ".svg":
                raise RuntimeError("SVG write unavailable")
            return original_write(path, content, exclusive=exclusive)
        with patch.object(views, "write_atomic", side_effect=fail_svg):
            with self.assertRaises(RuntimeError):
                self.save()
        self.assertTrue((self.out / "history/000002.yaml").exists())
        self.assertTrue(self.diagram().exists())
        self.assertTrue(self.diagram().exists())
        self.assertNotIn("A clarified observation", self.diagram().read_text())
        result = self.save()
        self.assertEqual(result["revision"], 2)
        self.assertEqual(result["changed_trees"], [])
        self.assertTrue(self.diagram().exists())
        self.assertIn("A clarified observation", self.diagram().read_text())

    def test_invalid_state_cannot_create_a_snapshot(self):
        self.state["trees"]["current_reality"]["nodes"][0]["status"] = "proposed"
        with self.assertRaisesRegex(ValueError, "accepted endpoints"):
            self.save()
        self.assertFalse(self.out.exists())
        self.state = toy()
        self.state["trees"]["current_reality"]["nodes"][0]["addresses"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "Unresolved"):
            self.save()

    def test_duplicate_yaml_keys_are_not_silently_discarded(self):
        self.path.write_text(yaml.safe_dump(self.state) + "trees: {}\n")
        with self.assertRaisesRegex(ValueError, "Duplicate YAML key: trees"):
            views.update(self.path)
        self.assertFalse(self.out.exists())

    def test_removing_everything_leaves_removal_diagram(self):
        self.save()
        self.state["trees"]["current_reality"] = {"nodes": [], "links": [], "backlog": []}
        self.save()
        self.assertIn("No accepted reasoning", self.diagram("current").read_text())
        self.assertIn("REMOVED", self.diagram().read_text())
        self.assertEqual(self.save()["revision"], 2)

    def test_missing_artifact_is_rebuilt_without_new_revision(self):
        self.save()
        previous = self.diagram().read_bytes()
        self.diagram().unlink()
        self.assertEqual(self.save()["revision"], 1)
        self.assertEqual(previous, self.diagram().read_bytes())

    def test_real_svg_rendering_handles_joint_causes_and_special_text(self):
        tree = self.state["trees"]["current_reality"]
        tree["nodes"][0]["text"] += ' — "quoted" & <scoped> \\ text'
        tree["links"][0]["from"].append("n3")
        self.path.write_text(yaml.safe_dump(self.state))
        views.update(self.path)
        for view in ("current", "changes"):
            svg = ET.fromstring(self.diagram(view).read_text())
            labels = " ".join(svg.itertext())
            self.assertIn("AND", labels)
            self.assertIn('<scoped>', labels)


if __name__ == "__main__":
    unittest.main()
