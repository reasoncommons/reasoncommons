"""First-session introduction with fictional participants; no network or shared-file writes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import onboarding
from test_feedback import toy


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state = self.root / "reason-commons.yaml"
        self.state.write_text(yaml.safe_dump(toy(), sort_keys=False, width=100000))

    def test_shown_once_per_participant_then_on_request(self):
        first = onboarding.show(self.state, "alice")
        self.assertIn("**Type: Introduction**", first)
        self.assertIn("Welcome, Alice. This is Reason Commons for **Fictional remote-work trial**", first)
        self.assertIn("You share it with Bob.", first)
        self.assertIsNone(onboarding.show(self.state, "alice"))
        self.assertIsNotNone(onboarding.show(self.state, "bob"))
        self.assertIsNotNone(onboarding.show(self.state, "alice", again=True))
        self.assertEqual(set(json.loads(onboarding.seen_file(self.state.resolve()).read_text())), {"alice", "bob"})

    def test_every_message_type_says_what_it_asks(self):
        text = onboarding.show(self.state, "alice")
        for kind in ("Feedback request", "Change proposal", "Next step", "Change result", "Answer", "Tree view", "Capture result"):
            self.assertIn(f"**{kind}**", text)
        self.assertIn('"not yet"', text)
        self.assertIn("Silence is never taken as an answer", text)

    def test_waiting_count_matches_the_feedback_queue(self):
        self.assertIn("**Waiting for you:** 1 feedback request. It comes next.", onboarding.show(self.state, "alice"))
        state = toy()
        state["participants"]["carol"] = "Carol"
        self.state.write_text(yaml.safe_dump(state, sort_keys=False, width=100000))
        self.assertIn("**Waiting for you:** nothing right now.", onboarding.show(self.state, "carol"))

    def test_sharing_line_reflects_this_checkout_without_configuring_it(self):
        self.assertIn("not available", onboarding.show(self.state, "alice"))
        git(self.root, "init", "-q", "-b", "main")
        text = onboarding.show(self.state, "alice", again=True)
        self.assertIn("**Sharing:** off in this checkout", text)
        self.assertIn(f"{self.state.resolve()} configure --remote origin --branch main --by alice", text)
        policy = onboarding.feedback_sync.local_dir(self.state.resolve()) / "feedback-sync.json"
        self.assertFalse(policy.exists())
        policy.write_text(json.dumps({"remote": "origin", "branch": "main"}))
        self.assertIn("**Sharing:** on.", onboarding.show(self.state, "alice", again=True))

    def test_setup_command_names_the_shared_default_branch_not_a_session_branch(self):
        remote = self.root / "shared.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "trunk", str(remote)], check=True)
        git(self.root, "init", "-q", "-b", "trunk")
        git(self.root, "remote", "add", "origin", str(remote))
        git(self.root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        git(self.root, "checkout", "-q", "-b", "claude/session")
        self.assertIn("configure --remote origin --branch trunk --by alice", onboarding.show(self.state, "alice"))

    def test_worktree_reports_the_main_checkouts_authorisation(self):
        main, tree = self.root / "main", self.root / "session"
        main.mkdir()
        state = main / "reason-commons.yaml"
        state.write_text(self.state.read_text())
        git(main, "init", "-q", "-b", "main")
        git(main, "remote", "add", "origin", "https://example.invalid/shared.git")
        git(main, "add", "reason-commons.yaml")
        git(main, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", "State")
        git(main, "worktree", "add", "-q", "-b", "session", str(tree))
        granted = onboarding.feedback_sync.local_dir(state.resolve()) / "feedback-sync.json"
        granted.parent.mkdir()
        granted.write_text(json.dumps({"repo": str(main.resolve()), "path": "reason-commons.yaml", "remote": "origin",
                                       "url": "https://example.invalid/shared.git", "branch": "main"}))
        text = onboarding.show(tree / "reason-commons.yaml", "alice")
        self.assertIn("**Sharing:** on. Your answers reach the other participants automatically through `origin/main`", text)
        self.assertIn(f"using the authorisation you gave in your main checkout, `{main.resolve()}`", text)
        self.assertFalse((onboarding.feedback_sync.local_dir((tree / "reason-commons.yaml").resolve()) / "feedback-sync.json").exists())

    def repository(self, *worktrees):
        """A main checkout holding the state file, with linked worktrees."""
        main = self.root / "main"
        main.mkdir()
        (main / "reason-commons.yaml").write_text(self.state.read_text())
        git(main, "init", "-q", "-b", "main")
        git(main, "remote", "add", "origin", "https://example.invalid/shared.git")
        git(main, "add", "reason-commons.yaml")
        git(main, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", "State")
        for name in worktrees:
            git(main, "worktree", "add", "-q", "-b", name, str(self.root / name))
        return main

    def test_one_showing_per_person_across_worktrees(self):
        main = self.repository("first", "second")
        self.assertIsNotNone(onboarding.show(self.root / "first" / "reason-commons.yaml", "alice"))
        self.assertIsNone(onboarding.show(self.root / "second" / "reason-commons.yaml", "alice"))
        self.assertIsNone(onboarding.show(main / "reason-commons.yaml", "alice"))
        record = onboarding.feedback_sync.local_dir((main / "reason-commons.yaml").resolve()) / "onboarding.json"
        self.assertEqual(set(json.loads(record.read_text())), {"alice"})
        git(main, "worktree", "remove", "--force", str(self.root / "first"))
        git(main, "worktree", "add", "-q", "-b", "third", str(self.root / "third"))
        self.assertIsNone(onboarding.show(self.root / "third" / "reason-commons.yaml", "alice"))
        self.assertIsNotNone(onboarding.show(self.root / "third" / "reason-commons.yaml", "bob"))

    def test_records_left_in_a_worktree_still_count(self):
        self.repository("earlier", "later")
        old = onboarding.feedback_sync.local_dir((self.root / "earlier" / "reason-commons.yaml").resolve()) / "onboarding.json"
        old.parent.mkdir()
        old.write_text(json.dumps({"alice": "2026-10-20T15:35:13+00:00"}))
        self.assertIsNone(onboarding.show(self.root / "later" / "reason-commons.yaml", "alice"))

    def test_file_only_in_a_worktree_creates_nothing_in_the_main_checkout(self):
        main = self.repository("session")
        only = self.root / "session" / "notes" / "new.yaml"
        only.parent.mkdir()
        only.write_text(self.state.read_text())
        self.assertIsNotNone(onboarding.show(only, "alice"))
        self.assertFalse((main / "notes").exists())
        self.assertTrue((onboarding.feedback_sync.local_dir(only.resolve()) / "onboarding.json").exists())
        self.assertIsNone(onboarding.show(only, "alice"))

    def test_worktree_setup_command_configures_the_main_checkout(self):
        main = self.repository("session")
        text = onboarding.show(self.root / "session" / "reason-commons.yaml", "alice")
        self.assertIn(f"{(main / 'reason-commons.yaml').resolve()} configure --remote origin", text)
        self.assertIn("It sets up your main checkout, so sessions in other worktrees share too.", text)
        # What that command records is what a worktree inherits.
        granted = onboarding.feedback_sync.local_dir((main / "reason-commons.yaml").resolve()) / "feedback-sync.json"
        granted.write_text(json.dumps({"repo": str(main.resolve()), "path": "reason-commons.yaml", "remote": "origin",
                                       "url": "https://example.invalid/shared.git", "branch": "main"}))
        self.assertIn("**Sharing:** on.", onboarding.show(self.root / "session" / "reason-commons.yaml", "alice", again=True))

    def test_shared_reasoning_is_only_read(self):
        before = self.state.read_bytes()
        onboarding.show(self.state, "alice")
        onboarding.show(self.state, "bob", again=True)
        self.assertEqual(self.state.read_bytes(), before)

    def test_unknown_participant_is_refused_and_not_recorded(self):
        with self.assertRaisesRegex(ValueError, "Unknown participant"):
            onboarding.show(self.state, "mallory")
        self.assertFalse(onboarding.seen_file(self.state.resolve()).exists())

    def test_cli_prints_once(self):
        command = [sys.executable, str(Path(onboarding.__file__)), str(self.state), "--participant", "alice"]
        self.assertIn("**Type: Introduction**", subprocess.run(command, capture_output=True, text=True, check=True).stdout)
        self.assertEqual(subprocess.run(command, capture_output=True, text=True, check=True).stdout, "")


if __name__ == "__main__":
    unittest.main()
