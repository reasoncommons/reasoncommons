"""Real Git round trips with fictional feedback, independent checkouts and failures."""
from copy import deepcopy
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import feedback_sync as sharing
from test_feedback import toy, report


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL).strip()


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.remote = root / "shared.git"
        git(root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.a, self.b = root / "alice", root / "bob"
        git(root, "clone", str(self.remote), str(self.a))
        self.identity(self.a)
        (self.a / "state.yaml").write_text(yaml.safe_dump(toy(), sort_keys=False, width=100000))
        (self.a / "code.txt").write_text("original code\n")
        git(self.a, "add", "state.yaml", "code.txt")
        git(self.a, "commit", "-m", "Shared fictional expectation")
        git(self.a, "push", "origin", "main")
        git(root, "clone", str(self.remote), str(self.b))
        self.identity(self.b)
        for repo in (self.a, self.b):
            sharing.configure(repo / "state.yaml", "origin", "main", "alice", "Share feedback automatically with this origin/main.")

    def identity(self, repo):
        git(repo, "config", "user.name", "Fixture participant")
        git(repo, "config", "user.email", "fixture@example.invalid")

    def load(self, repo):
        return sharing.load_text((repo / "state.yaml").read_text())

    def save(self, repo, state):
        (repo / "state.yaml").write_text(yaml.safe_dump(state, sort_keys=False, width=100000))

    def add(self, repo, ident="alice-report", by="alice", **extra):
        self.save(repo, sharing.feedback.add_report(self.load(repo), "remote-trial", 1, report(ident, by, **extra)))

    def shared(self):
        return sharing.load_text(git(self.remote, "show", "main:state.yaml"))

    def run_sync(self, repo):
        return sharing.sync(repo / "state.yaml")

    def test_round_trip_keeps_harm_open_and_creates_review_work(self):
        self.add(self.a)
        original_head = git(self.a, "rev-parse", "HEAD")
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertEqual(self.run_sync(self.b)["state"], "shared")
        state = self.load(self.b)
        self.assertEqual(sharing.feedback.queue(state, "alice")[0]["pending"], ["isolation"])
        self.assertEqual(len(state["feedback_requests"][0]["reports"]), 1)
        self.assertTrue(any(task.get("feedback_report") == "alice-report" for task in state["trees"]["future_reality"]["backlog"]))
        self.assertTrue(all(node["status"] == "proposed" for node in state["trees"]["future_reality"]["nodes"]))

    def test_checkouts_fast_forward_so_pull_keeps_working(self):
        self.add(self.a)
        original_head = git(self.a, "rev-parse", "HEAD")
        result = self.run_sync(self.a)
        self.assertEqual(result["checkout"], "advanced")
        tip = git(self.remote, "rev-parse", "main")
        self.assertNotEqual(tip, original_head)
        for repo in (self.a, self.b):
            if repo == self.b:
                self.assertEqual(self.run_sync(self.b)["checkout"], "advanced")
            self.assertEqual(git(repo, "rev-parse", "HEAD"), tip)
            self.assertEqual(git(repo, "status", "--porcelain", "--", "state.yaml"), "")
            git(repo, "pull", "--ff-only")
        self.assertEqual(self.run_sync(self.a)["checkout"], "current")

    def test_checkout_on_another_branch_is_left_alone(self):
        git(self.a, "checkout", "-q", "-b", "experiment")
        head = git(self.a, "rev-parse", "HEAD")
        self.add(self.a)
        result = self.run_sync(self.a)
        self.assertEqual((result["state"], result["checkout"]), ("shared", "unchanged"))
        self.assertEqual(git(self.a, "rev-parse", "HEAD"), head)

    def test_upstream_code_changes_are_never_pulled_in_automatically(self):
        (self.b / "code.txt").write_text("merged elsewhere\n")
        git(self.b, "commit", "-qam", "Code merged elsewhere")
        git(self.b, "push", "-q", "origin", "main")
        head = git(self.a, "rev-parse", "HEAD")
        self.add(self.a)
        result = self.run_sync(self.a)
        self.assertEqual((result["state"], result["checkout"]), ("shared", "behind"))
        self.assertEqual(git(self.a, "rev-parse", "HEAD"), head)
        self.assertEqual((self.a / "code.txt").read_text(), "original code\n")
        command = result["checkout_message"].split("Update with: ")[1]
        self.assertIn("checkout -- state.yaml", command)
        subprocess.run(command, shell=True, check=True, capture_output=True)
        self.assertEqual(git(self.a, "rev-parse", "HEAD"), git(self.remote, "rev-parse", "main"))
        self.assertEqual(len(self.load(self.a)["feedback_requests"][0]["reports"]), 1)

    def test_staged_reasoning_file_is_left_staged(self):
        self.add(self.a)
        git(self.a, "add", "state.yaml")
        staged = git(self.a, "diff", "--cached")
        head = git(self.a, "rev-parse", "HEAD")
        result = self.run_sync(self.a)
        self.assertEqual((result["state"], result["checkout"]), ("shared", "behind"))
        self.assertEqual(git(self.a, "rev-parse", "HEAD"), head)
        self.assertNotEqual(git(self.a, "diff", "--cached"), "")
        self.assertIsNotNone(staged)

    def test_independent_checkouts_merge_reports_and_retry_without_duplicates(self):
        self.add(self.a)
        self.add(self.b, "bob-report", "bob")
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertEqual(self.run_sync(self.b)["state"], "shared")
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        reports = self.load(self.a)["feedback_requests"][0]["reports"]
        self.assertEqual({r["id"] for r in reports}, {"alice-report", "bob-report"})
        tip = git(self.remote, "rev-parse", "main")
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertEqual(git(self.remote, "rev-parse", "main"), tip)

    def test_conflicting_report_identity_preserves_local_and_remote(self):
        self.add(self.a, "same-id", text="First observation")
        self.add(self.b, "same-id", text="Different observation")
        self.run_sync(self.a)
        before = (self.b / "state.yaml").read_bytes()
        result = self.run_sync(self.b)
        self.assertEqual(result["state"], "local")
        self.assertIn("Conflicting feedback report", result["message"])
        self.assertEqual((self.b / "state.yaml").read_bytes(), before)
        self.assertEqual(self.shared()["feedback_requests"][0]["reports"][0]["text"], "First observation")

    def test_offline_preserves_report_and_can_later_share(self):
        self.add(self.a)
        hidden = self.remote.with_name("offline.git")
        self.remote.rename(hidden)
        before = (self.a / "state.yaml").read_bytes()
        self.assertEqual(self.run_sync(self.a)["state"], "local")
        self.assertEqual((self.a / "state.yaml").read_bytes(), before)
        hidden.rename(self.remote)
        self.assertEqual(self.run_sync(self.a)["state"], "shared")

    def test_lost_push_response_is_verified_without_duplicate_report(self):
        self.add(self.a)
        original = sharing.git
        lost = False

        def uncertain(repo, *args, **kwargs):
            nonlocal lost
            result = original(repo, *args, **kwargs)
            if args[0] == "push" and not lost:
                lost = True
                raise sharing.SyncError("Response lost after accepted push")
            return result

        with patch.object(sharing, "git", side_effect=uncertain):
            self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertEqual(len(self.shared()["feedback_requests"][0]["reports"]), 1)
        self.assertEqual(git(self.remote, "rev-list", "--count", "main"), "2")

    def test_push_race_reconciles_both_records(self):
        self.add(self.a)
        self.add(self.b, "bob-report", "bob")
        original = sharing.git
        raced = False

        def concurrent(repo, *args, **kwargs):
            nonlocal raced
            if Path(repo).resolve() == self.a.resolve() and args[0] == "push" and not raced:
                raced = True
                self.assertEqual(self.run_sync(self.b)["state"], "shared")
            self.assertNotIn("--force", args)
            return original(repo, *args, **kwargs)

        with patch.object(sharing, "git", side_effect=concurrent):
            self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertTrue(raced)
        self.assertEqual({r["id"] for r in self.shared()["feedback_requests"][0]["reports"]}, {"alice-report", "bob-report"})

    def test_unrelated_index_code_and_local_reasoning_are_not_published(self):
        (self.a / "code.txt").write_text("unfinished implementation\n")
        git(self.a, "add", "code.txt")
        index_before = git(self.a, "diff", "--cached")
        local = self.load(self.a)
        local["trees"]["future_reality"]["nodes"][0]["label"] = "A local unshared wording choice."
        self.save(self.a, local)
        self.add(self.a)
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertEqual(git(self.a, "diff", "--cached"), index_before)
        self.assertEqual(self.run_sync(self.a)["checkout"], "behind")
        self.assertEqual(git(self.remote, "show", "main:code.txt"), "original code")
        self.assertNotIn("label", self.shared()["trees"]["future_reality"]["nodes"][0])
        self.assertIn("label", self.load(self.a)["trees"]["future_reality"]["nodes"][0])

    def test_changed_prediction_is_not_silently_shared(self):
        state = self.load(self.a)
        state["feedback_requests"][0]["benefits"][0]["text"] = "An easier prediction"
        self.save(self.a, state)
        self.assertEqual(self.run_sync(self.a)["state"], "local")
        self.assertEqual(self.shared(), toy())

    def test_remote_identity_change_requires_new_authorisation(self):
        self.add(self.a)
        git(self.a, "remote", "set-url", "origin", str(self.remote) + ".changed")
        result = self.run_sync(self.a)
        self.assertEqual(result["state"], "local")
        self.assertIn("remote changed", result["message"])

    def test_no_policy_does_not_push_or_claim_shared(self):
        (sharing.local_dir(self.a / "state.yaml") / "feedback-sync.json").unlink()
        self.add(self.a)
        self.assertEqual(self.run_sync(self.a)["state"], "local")
        self.assertEqual(self.shared(), toy())

    def test_stale_checkout_can_configure_then_receive_new_shared_reports(self):
        (sharing.local_dir(self.b / "state.yaml") / "feedback-sync.json").unlink()
        self.add(self.a)
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        sharing.configure(self.b / "state.yaml", "origin", "main", "bob", "Share feedback with this origin/main.")
        self.assertEqual(self.run_sync(self.b)["state"], "shared")
        self.assertEqual(len(self.load(self.b)["feedback_requests"][0]["reports"]), 1)

    def worktree(self):
        tree = Path(self.temporary.name) / "session"
        git(self.a, "worktree", "add", "-q", "-b", "session", str(tree))
        return tree

    def test_linked_worktree_shares_through_the_main_checkouts_authorisation(self):
        tree = self.worktree()
        self.add(tree)
        result = self.run_sync(tree)
        self.assertEqual(result["state"], "shared")
        self.assertEqual(result["inherited_from"], str(self.a.resolve()))
        self.assertEqual(len(self.shared()["feedback_requests"][0]["reports"]), 1)
        policy = json.loads((sharing.local_dir(tree / "state.yaml") / "feedback-sync.json").read_text())
        self.assertEqual((policy["by"], policy["branch"], policy["repo"]), ("alice", "main", str(tree.resolve())))
        self.assertEqual(git(tree, "rev-parse", "--abbrev-ref", "HEAD"), "session")

    def test_worktree_without_a_main_authorisation_stays_local(self):
        (sharing.local_dir(self.a / "state.yaml") / "feedback-sync.json").unlink()
        tree = self.worktree()
        self.add(tree)
        self.assertEqual(self.run_sync(tree)["state"], "local")
        self.assertEqual(self.shared(), toy())

    def test_worktree_refuses_an_authorisation_for_another_remote_url(self):
        granted = sharing.local_dir(self.a / "state.yaml") / "feedback-sync.json"
        granted.write_text(json.dumps({**json.loads(granted.read_text()), "url": str(self.remote) + ".other"}))
        tree = self.worktree()
        self.add(tree)
        self.assertEqual(self.run_sync(tree)["state"], "local")
        self.assertEqual(self.shared(), toy())

    def test_worktree_with_unshared_expectation_says_why_it_waits(self):
        tree = self.worktree()
        current = self.load(tree)
        current["trees"]["future_reality"]["nodes"].append({"id": "new-action", "kind": "injection", "text": "Another local action.", "status": "proposed", "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}]})
        current["feedback_requests"].append(sharing.feedback.new_request(current, "new-action-feedback", "new-action", ["gain"], [], ["alice"], "alice"))
        self.save(tree, current)
        result = self.run_sync(tree)
        self.assertEqual(result["state"], "local")
        self.assertIn("cannot be shared yet: Unknown prediction statement: new-action", result["message"])
        self.assertEqual(self.shared(), toy())

    def test_worktree_stops_when_the_main_checkout_withdraws(self):
        tree = self.worktree()
        self.assertEqual(self.run_sync(tree)["state"], "shared")
        subprocess.run([sys.executable, str(Path(sharing.__file__)), str(self.a / "state.yaml"), "disable"], check=True, capture_output=True)
        self.add(tree)
        result = self.run_sync(tree)
        self.assertEqual(result["state"], "local")
        self.assertIn("no longer authorises", result["message"])
        self.assertEqual(self.shared(), toy())

    def test_disabling_in_a_worktree_is_not_undone_by_inheritance(self):
        tree = self.worktree()
        self.assertEqual(self.run_sync(tree)["state"], "shared")
        subprocess.run([sys.executable, str(Path(sharing.__file__)), str(tree / "state.yaml"), "disable"], check=True, capture_output=True)
        self.add(tree)
        self.assertEqual(self.run_sync(tree)["state"], "local")
        self.assertEqual(self.shared(), toy())
        sharing.configure(tree / "state.yaml", "origin", "main", "alice", "Share this worktree's feedback with origin/main.")
        self.assertEqual(self.run_sync(tree)["state"], "shared")

    def test_cli_recovers_configuration_and_reports_delivery_state(self):
        self.add(self.a)
        result = subprocess.run([sys.executable, str(Path(sharing.__file__)), str(self.a / "state.yaml"), "sync"], text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["state"], "shared")

    def test_later_deferral_survives_opposite_report_arrival_order(self):
        self.add(self.a, "later", readiness="not_yet", outcomes=[],
                 recorded_at="2026-10-23T12:00:00Z", defer_until="2099-10-24T12:00:00Z")
        self.add(self.b, "earlier", readiness="not_yet", outcomes=[], recorded_at="2026-10-22T12:00:00Z")
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertEqual(self.run_sync(self.b)["state"], "shared")
        self.assertEqual(sharing.feedback.queue(self.load(self.b), "alice"), [])

    def test_new_prediction_versions_can_be_shared_together(self):
        original = self.load(self.a)
        original.pop("feedback_requests")
        # This independent expectation uses definitions that already exist remotely.
        current = self.load(self.a)
        current["feedback_requests"].append(sharing.feedback.new_request(current, "another-trial", "trial", ["gain"], ["isolation"], ["alice"], "alice"))
        current["feedback_requests"].append(sharing.feedback.new_request(current, "another-trial", "trial", ["gain"], ["isolation"], ["alice"], "alice"))
        self.save(self.a, current)
        self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertEqual([r["revision"] for r in self.shared()["feedback_requests"] if r["id"] == "another-trial"], [1, 2])

    def test_unshared_reasoning_for_new_expectation_stays_local(self):
        current = self.load(self.a)
        current["trees"]["future_reality"]["nodes"].append({"id": "new-action", "kind": "injection", "text": "Another local action.", "status": "proposed", "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}]})
        current["feedback_requests"].append(sharing.feedback.new_request(current, "new-action-feedback", "new-action", ["gain"], [], ["alice"], "alice"))
        self.save(self.a, current)
        before = (self.a / "state.yaml").read_bytes()
        self.assertEqual(self.run_sync(self.a)["state"], "local")
        self.assertEqual((self.a / "state.yaml").read_bytes(), before)
        self.assertEqual(self.shared(), toy())

    def test_new_remote_report_during_verification_is_saved_before_baseline_advances(self):
        self.add(self.a)
        self.add(self.b, "bob-report", "bob")
        original = sharing.git
        pushed = False

        def after_push(repo, *args, **kwargs):
            nonlocal pushed
            result = original(repo, *args, **kwargs)
            if Path(repo).resolve() == self.a.resolve() and args[0] == "push" and not pushed:
                pushed = True
                self.assertEqual(self.run_sync(self.b)["state"], "shared")
            return result

        with patch.object(sharing, "git", side_effect=after_push):
            self.assertEqual(self.run_sync(self.a)["state"], "shared")
        self.assertTrue(pushed)
        self.assertEqual(len(self.load(self.a)["feedback_requests"][0]["reports"]), 2)
        self.assertEqual(self.run_sync(self.a)["state"], "shared")

    def test_render_preserves_unrelated_source_text(self):
        text = "# Preserve this project comment\n" + (self.a / "state.yaml").read_text()
        state = sharing.feedback.add_report(sharing.load_text(text), "remote-trial", 1, report())
        rendered = sharing.render(text, state)
        self.assertTrue(rendered.startswith("# Preserve this project comment\n"))
        self.assertEqual(sharing.load_text(rendered), state)

    def test_render_adds_entries_without_rewriting_existing_formatting(self):
        flow = "    - {ref: gain, work: check_record, note: 'A hand-written, quoted note', beads: [fixture-1]}\n"
        text = (self.a / "state.yaml").read_text().replace("    backlog: []\n", "    backlog:\n" + flow)
        before = sharing.load_text(text)
        state = sharing.feedback.add_report(before, "remote-trial", 1, report())
        rendered = sharing.render(text, state)
        self.assertEqual(sharing.load_text(rendered), state)
        self.assertIn(flow, rendered)
        removed = [line for line in difflib.ndiff(text.splitlines(), rendered.splitlines()) if line.startswith("- ")]
        # Only the empty flow list of reports is rewritten; every other existing line survives.
        self.assertEqual([line[2:].strip() for line in removed], ["reports: []"])

    def test_reordered_reports_rewrite_only_their_own_list(self):
        later = report("later", recorded_at="2026-10-22T12:00:00Z")
        text = sharing.render((self.a / "state.yaml").read_text(), sharing.feedback.add_report(self.load(self.a), "remote-trial", 1, later))
        target = sharing.load_text(text)
        target["feedback_requests"][0]["reports"].insert(0, report("earlier", recorded_at="2026-10-21T12:00:00Z"))
        rendered = sharing.render(text, target)
        self.assertEqual(sharing.load_text(rendered), target)
        kept = [line for line in text.splitlines() if "reports" not in line and not line.startswith("  - ") and not line.startswith("    ")]
        self.assertTrue(all(line in rendered.splitlines() for line in kept))


if __name__ == "__main__":
    unittest.main()
