"""Behavioral checks on a fictional trial derived from the remote-work toy topic."""
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location("feedback_test_core", SCRIPTS / "feedback.py")
feedback = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(feedback)
NOW = datetime(2026, 10, 21, 15, tzinfo=timezone.utc)


def toy():
    contribution = [{"by": "alice", "attribution": "explicit", "mode": "text"}]
    nodes = [{"id": ident, "text": text, "kind": kind, "status": "proposed", "contributions": deepcopy(contribution)}
             for ident, kind, text in (
                 ("trial", "injection", "Alice tries remote work on a comparable call-handling shift."),
                 ("gain", "predicted_effect", "Alice completes more comparable calls during that shift."),
                 ("isolation", "undesirable_effect", "Alice may have more difficulty obtaining help during that shift."))]
    state = {"schema_version": 1, "project": "Fictional remote-work trial", "driver": "alice",
             "participants": {"alice": "Alice", "bob": "Bob"}, "active_tree": "future_reality",
             "trees": {"future_reality": {"nodes": nodes, "links": [], "backlog": []}}}
    request = feedback.new_request(state, "remote-trial", "trial", ["gain"], ["isolation"], ["alice", "bob"], "alice",
                                   recorded_at="2026-10-20T10:00:00Z", ready_when="After experiencing one comparable shift.")
    state["feedback_requests"] = [request]
    return state


def report(ident="report-1", by="alice", **overrides):
    return {"id": ident, "by": by, "recorded_at": NOW.isoformat(), "readiness": "experienced",
            "text": "More comparable calls; I have not assessed access to help.", "evidence_type": "self_report",
            "outcomes": [{"ref": "gain", "verdict": "observed", "note": "My shift record shows more comparable calls."}], **overrides}


class FeedbackTests(unittest.TestCase):
    def test_named_providers_required_but_timing_optional(self):
        state = toy()
        self.assertEqual(len(feedback.queue(state, "alice", NOW)), 1)
        state["feedback_requests"][0]["feedback_from"] = []
        with self.assertRaisesRegex(ValueError, "named human"):
            feedback.validate(state)

    def test_recipient_filter_and_unknown_identity(self):
        state = toy()
        state["participants"]["carol"] = "Carol"
        self.assertEqual(feedback.queue(state, "carol", NOW), [])
        with self.assertRaises(ValueError):
            feedback.queue(state, "unknown", NOW)

    def test_restart_and_topic_change_preserve_unanswered_requests(self):
        state = yaml.safe_load(yaml.safe_dump(toy()))
        state["driver"] = "bob"
        row = feedback.queue(state, "bob", NOW)[0]
        self.assertEqual(row["pending"], ["gain", "isolation"])

    def test_positive_feedback_does_not_answer_harm_or_other_provider(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report())
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["isolation"])
        self.assertEqual(feedback.queue(state, "bob", NOW)[0]["pending"], ["gain", "isolation"])
        self.assertTrue(all(n["status"] == "proposed" for n in state["trees"]["future_reality"]["nodes"]))

    def test_not_assessed_and_silence_never_resolve_outcome(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report(outcomes=[
            {"ref": "gain", "verdict": "not_assessed", "note": "I have not checked."}]))
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["gain", "isolation"])

    def unclear_gain(self):
        return feedback.add_report(toy(), "remote-trial", 1, report(outcomes=[
            {"ref": "gain", "verdict": "unclear", "note": "Only part of the shift record survived."}]))

    def test_unclear_keeps_outcome_open_and_shows_earlier_note(self):
        state = self.unclear_gain()
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["gain", "isolation"])
        text = feedback.render_request(state, state["feedback_requests"][0], "alice")
        self.assertIn("Earlier you found gain unclear: Only part of the shift record survived.", text)

    def test_later_assessment_settles_or_reopens_unclear(self):
        state = feedback.add_report(self.unclear_gain(), "remote-trial", 1, report("report-2", recorded_at="2026-10-21T16:00:00+00:00"))
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["isolation"])
        state = feedback.add_report(state, "remote-trial", 1, report("report-3", recorded_at="2026-10-21T17:00:00+00:00", outcomes=[
            {"ref": "gain", "verdict": "unclear", "note": "The second record contradicts the first."}]))
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["gain", "isolation"])

    def test_report_order_in_file_does_not_override_chronology(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report("later", recorded_at="2026-10-21T17:00:00+00:00"))
        state = feedback.add_report(state, "remote-trial", 1, report("earlier", recorded_at="2026-10-21T16:00:00+00:00", outcomes=[
            {"ref": "gain", "verdict": "unclear", "note": "Not sure yet."}]))
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["isolation"])

    def test_unavailable_after_unclear_closes_outcome(self):
        state = feedback.add_report(self.unclear_gain(), "remote-trial", 1, report("report-2", recorded_at="2026-10-21T16:00:00+00:00", outcomes=[
            {"ref": "gain", "verdict": "unavailable", "note": "The rest of the record is gone."}]))
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["isolation"])

    def test_unclear_outcome_respects_deferral(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report(defer_until="2026-10-24T12:00:00Z", outcomes=[
            {"ref": "gain", "verdict": "unclear", "note": "Ask me after the next shift."}]))
        self.assertEqual(feedback.queue(state, "alice", NOW), [])
        self.assertEqual(feedback.queue(state, "alice", datetime(2026, 10, 25, tzinfo=timezone.utc))[0]["pending"], ["gain", "isolation"])

    def test_lost_evidence_is_explicit_and_does_not_imply_safety(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report(readiness="cannot_assess", outcomes=[
            {"ref": "gain", "verdict": "unavailable", "note": "The shift record was lost."}]))
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["pending"], ["isolation"])
        self.assertEqual(state["feedback_requests"][0]["reports"][0]["outcomes"][0]["verdict"], "unavailable")

    def test_not_yet_experienced_can_defer_without_assessment(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report(readiness="not_yet", outcomes=[], defer_until="2026-10-24T12:00:00Z"))
        self.assertEqual(feedback.queue(state, "alice", NOW), [])
        self.assertEqual(feedback.queue(state, "alice", NOW, include_waiting=True)[0]["state"], "waiting")
        self.assertEqual(len(feedback.queue(state, "alice", datetime(2026, 10, 25, tzinfo=timezone.utc))), 1)

    def test_future_window_does_not_require_making_up_a_report(self):
        state = toy()
        state["feedback_requests"][0]["ask_after"] = "2026-10-24T12:00:00Z"
        self.assertEqual(feedback.queue(state, "alice", NOW), [])
        self.assertEqual(state["feedback_requests"][0]["reports"], [])

    def test_unexperienced_cannot_assert_no_harm(self):
        with self.assertRaisesRegex(ValueError, "Unexperienced"):
            feedback.add_report(toy(), "remote-trial", 1, report(readiness="not_yet", outcomes=[
                {"ref": "isolation", "verdict": "not_observed", "note": "No report exists."}]))

    def test_report_idempotency_and_conflicting_duplicate(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report())
        self.assertEqual(feedback.add_report(state, "remote-trial", 1, report()), state)
        with self.assertRaisesRegex(ValueError, "reused"):
            feedback.add_report(state, "remote-trial", 1, report(text="Different feedback"))

    def test_immutable_predictions_and_append_only_reports(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report())
        for mutate in (lambda s: s["feedback_requests"][0]["benefits"][0].update(text="An easier prediction"),
                       lambda s: s["feedback_requests"][0]["reports"].clear(),
                       lambda s: s["feedback_requests"].clear()):
            altered = deepcopy(state)
            mutate(altered)
            with self.assertRaises(ValueError):
                feedback.guard_transition(state, altered)

    def test_revised_prediction_keeps_old_wording_and_old_reports(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report())
        original = deepcopy(state["feedback_requests"][0])
        state["trees"]["future_reality"]["nodes"][1]["text"] = "Alice completes more comparable calls across two shifts."
        revised = feedback.new_request(state, "remote-trial", "trial", ["gain"], ["isolation"], ["alice"], "alice", recorded_at=NOW.isoformat())
        state["feedback_requests"].append(revised)
        self.assertEqual(revised["revision"], 2)
        self.assertEqual(state["feedback_requests"][0], original)
        self.assertEqual(feedback.queue(state, "alice", NOW)[1]["pending"], ["gain", "isolation"])
        # A later report may still describe the version the participant actually experienced.
        state = feedback.add_report(state, "remote-trial", 1, report("old-harm", outcomes=[
            {"ref": "isolation", "verdict": "observed", "note": "I had trouble obtaining help."}]))
        self.assertEqual(feedback.queue(state, "alice", NOW)[0]["revision"], 2)

    def test_unauthenticated_feedback_rejected(self):
        state = toy()
        altered = feedback.add_report(state, "remote-trial", 1, report(by="bob"))
        with self.assertRaisesRegex(ValueError, "impersonate"):
            feedback.guard_transition(state, altered, {"alice"})

    def test_reconciliation_can_reorder_existing_reports_but_not_impersonate(self):
        state = feedback.add_report(toy(), "remote-trial", 1, report("alice-1"))
        state = feedback.add_report(state, "remote-trial", 1, report("bob-1", by="bob"))
        reordered = deepcopy(state)
        reordered["feedback_requests"][0]["reports"].reverse()
        feedback.guard_transition(state, reordered, {"alice"})
        reordered["feedback_requests"][0]["reports"][0]["text"] = "Rewritten history"
        with self.assertRaises(ValueError):
            feedback.guard_transition(state, reordered, {"alice"})

    def test_new_snapshots_must_match_reasoning(self):
        state = toy()
        before = deepcopy(state)
        before.pop("feedback_requests")
        state["feedback_requests"][0]["benefits"][0]["text"] = "Invented easier outcome"
        with self.assertRaisesRegex(ValueError, "match actual"):
            feedback.guard_transition(before, state)

    def test_response_shows_both_sides_and_original_scope(self):
        state = toy()
        text = feedback.render_request(state, state["feedback_requests"][0], "alice")
        self.assertIn("Alice completes more comparable calls during that shift.", text)
        self.assertIn("Alice may have more difficulty obtaining help during that shift.", text)
        self.assertIn("After experiencing one comparable shift.", text)

    def test_cli_uses_saved_file_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.yaml"
            path.write_text(yaml.safe_dump(toy()))
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPTS / "feedback.py"), str(path), "--participant", "alice", "--format", "json"],
                                    check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(result.stdout)[0]["pending"], ["gain", "isolation"])
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
