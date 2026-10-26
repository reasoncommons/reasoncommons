"""Toy-case checks in a throwaway Git repository; no real project data is read or changed."""

from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_pr_trees.py"
SPEC = importlib.util.spec_from_file_location("check_pr_trees", SCRIPT)
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

STATE = "reason-commons.yaml"


def receipt(ref="fixture-change", paths=None):
    return {"proposal_ref": ref, "proposal_revision": 1, "by": "alice",
            "recorded_at": "2026-10-14T12:00:00Z", "timezone": "UTC", "mode": "text",
            "source": "conversation", "source_text": "yes, I accept the fixture proposal",
            "scope": "Update the fixture README and remote-work scope reasoning.",
            "node_ids": ["n1", "n2"], "link_ids": ["l1"],
            "approved_paths": [STATE, "README.md"] if paths is None else paths}


def toy():
    # Observations from claim-tree-annotation.md, not invented CRT symptoms.
    contribution = [{"by": "alice", "attribution": "explicit", "mode": "text"}]
    texts = ["13% productivity gain for remote workers", "Study covers call centre workers only"]
    nodes = [{"id": f"n{i}", "kind": "observation", "text": text, "status": "proposed", "contributions": deepcopy(contribution)} for i, text in enumerate(texts, 1)]
    return {"schema_version": 1, "project": "Remote-work toy fixture", "driver": "alice", "participants": {"alice": "Alice"}, "active_tree": "current_reality", "trees": {"current_reality": {"nodes": nodes, "links": [], "backlog": []}}, "change_acceptances": [receipt()]}


def with_link(state):
    state["trees"]["current_reality"]["links"].append({"id": "l1", "from": ["n2"], "to": "n1", "relation": "limits_scope", "status": "proposed", "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}]})
    return state


def body(serves="", updates="None", acceptances="- `fixture-change` revision 1 by `alice`", diagrams="__FIXTURE_DIAGRAMS__", collapsed=True):
    if collapsed:
        updates = f"<details>\n<summary>Complete checked change list</summary>\n\n{updates}\n\n</details>"
    return f"## What this changes\n\nSomething.\n\n{diagrams}\n\n## Reasoning this serves\n\n{serves}\n\n## Tree updates\n\n{updates}\n\n## Accepted change proposals\n\n{acceptances}\n"


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "toy@example.com")
        self.git("config", "user.name", "Toy")
        self.write(toy())
        (self.repo / "README.md").write_text("The study reports a productivity gain.\n")
        self.git("add", STATE, "README.md")
        self.git("commit", "-q", "-m", "base")
        self.git("checkout", "-q", "-b", "change")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

    def write(self, state):
        (self.repo / STATE).write_text(yaml.safe_dump(state, sort_keys=False))

    def run_check(self, *args, text=None):
        if text is not None:
            if "__FIXTURE_DIAGRAMS__" in text:
                try:
                    _, before, after = check.load_documents([STATE], "main", self.repo)
                    generated = check.diagrams.markdown(before, after)
                except (ValueError, KeyError, TypeError, yaml.YAMLError):
                    generated = "## Reasoning changes\n"
                text = text.replace("__FIXTURE_DIAGRAMS__", generated)
            (self.repo / "pr.md").write_text(text)
            args = ("--body-file", str(self.repo / "pr.md"), *args)
        out = io.StringIO()
        with redirect_stdout(out):
            code = check.main(["--base", "main", *args, STATE], cwd=self.repo)
        return code, out.getvalue()

    def test_stated_updates_matching_the_yaml_pass(self):
        self.write(with_link(toy()))
        code, out = self.run_check(text=body(updates="- added `l1` — `n2` limits the scope of `n1`"))
        self.assertEqual(code, 0, out)
        self.assertIn("1 tree update(s) match", out)

    def test_suggested_list_passes_as_written(self):
        state = with_link(toy())
        state["trees"]["current_reality"]["nodes"][0]["status"] = "accepted"
        state["trees"]["current_reality"]["nodes"][0]["accepted_by"] = ["alice"]
        self.write(state)
        code, suggestion = self.run_check("--suggest")
        self.assertEqual(code, 0)
        self.assertIn("- changed `n1`", suggestion)
        self.assertIn("- added `l1`", suggestion)
        code, out = self.run_check(text=body(updates=suggestion))
        self.assertEqual(code, 0, out)

    def test_unstated_yaml_change_fails(self):
        self.write(with_link(toy()))
        code, out = self.run_check(text=body(serves="- `n1`"))
        self.assertEqual(code, 1)
        self.assertIn("The YAML added `l1`", out)

    def test_stated_update_without_yaml_change_fails(self):
        code, out = self.run_check(text=body(updates="- changed `n2`"))
        self.assertEqual(code, 1)
        self.assertIn("does not change it", out)

    def test_wrong_verb_fails(self):
        self.write(with_link(toy()))
        code, out = self.run_check(text=body(updates="- changed `l1`"))
        self.assertEqual(code, 1)
        self.assertIn("shows it added", out)

    def test_removed_item_must_be_stated(self):
        state = toy()
        del state["trees"]["current_reality"]["nodes"][1]
        self.write(state)
        self.assertEqual(self.run_check(text=body(updates="- removed `n2`"))[0], 0)
        self.assertEqual(self.run_check(text=body(serves="- `n1`"))[0], 1)

    def test_serving_existing_reasoning_without_updates_passes(self):
        code, out = self.run_check(text=body(serves="- `n1` — the claim this fix supports"))
        self.assertEqual(code, 0, out)

    def test_serving_unknown_id_fails(self):
        code, out = self.run_check(text=body(serves="- `n9`"))
        self.assertEqual(code, 1)
        self.assertIn("Serves `n9`", out)

    def test_no_reasoning_at_all_fails(self):
        code, out = self.run_check(text=body())
        self.assertEqual(code, 1)
        self.assertIn("names no reasoning", out)

    def test_missing_tree_updates_section_fails(self):
        code, out = self.run_check(text="## Reasoning this serves\n\n- `n1`\n")
        self.assertEqual(code, 1)
        self.assertIn('no "Tree updates" section', out)

    def test_template_comments_are_ignored(self):
        text = body(serves="<!-- e.g. `n9` -->", updates="<!-- - added `n8` -->\nNone")
        code, out = self.run_check(text=text)
        self.assertEqual(code, 1)
        self.assertNotIn("n9", out)
        self.assertNotIn("n8", out)

    def test_missing_acceptance_section_or_reference_fails(self):
        text = body(serves="- `n1`").split("## Accepted change proposals")[0]
        code, out = self.run_check(text=text)
        self.assertEqual(code, 1)
        self.assertIn('no "Accepted change proposals" section', out)
        code, out = self.run_check(text=body(serves="- `n1`", acceptances="<!-- - `fixture-change` revision 1 by `alice` -->"))
        self.assertEqual(code, 1)
        self.assertIn("List at least one recorded acceptance", out)

    def test_explanatory_paragraphs_with_valid_references_pass(self):
        # The paragraph that caused PR 60's formatting-only CI failure.
        explanation = "Revision 2 supersedes the broader implementation scope of revision 1; the earlier receipt remains immutable history and covers retained reasoning. David explicitly accepted revision 2 and also requested conflict resolution. Main had meanwhile migrated changelog.md into individual dated entries, so the approved announcement is now changelog/2026-10-15-rewind-reasoning-sessions.md; the path resolution is recorded in the receipt."
        reference = "- `fixture-change` revision 1 by `alice`"
        state = toy()
        state["change_acceptances"].append(receipt("later-change"))
        self.write(state)
        for acceptances in (f"{explanation}\n\n{reference}",
                            f"{reference}\n\n{explanation}",
                            f"{reference}\n\n{explanation}\n\n- `later-change` revision 1 by `alice`",
                            f"Historical context mentions `unknown` revision 9 by `bob`.\n\n{reference}"):
            with self.subTest(acceptances=acceptances):
                code, out = self.run_check(text=body(serves="- `n1`", acceptances=acceptances))
                self.assertEqual(code, 0, out)

    def test_explanatory_paragraph_without_reference_fails(self):
        code, out = self.run_check(text=body(serves="- `n1`", acceptances="Alice approved this change.\n\nThe receipt is `fixture-change` revision 1 by `alice`."))
        self.assertEqual(code, 1)
        self.assertIn("List at least one recorded acceptance", out)

    def test_unknown_proposal_version_or_participant_fails(self):
        for reference in ("- `unknown` revision 1 by `alice`", "- `fixture-change` revision 2 by `alice`", "- `fixture-change` revision 1 by `bob`"):
            for explanation in ("", "This paragraph explains the approval history.\n\n"):
                with self.subTest(reference=reference, explanation=explanation):
                    code, out = self.run_check(text=body(serves="- `n1`", acceptances=explanation + reference))
                    self.assertEqual(code, 1)
                    self.assertIn("No recorded acceptance", out)

    def test_malformed_or_duplicate_reference_fails(self):
        valid = "- `fixture-change` revision 1 by `alice`"
        for reference in ("- yes", "- `fixture-change` revision 0 by `alice`", f"{valid}\n{valid}", f"{valid}\n\nThis paragraph separates duplicate references.\n\n{valid}"):
            for explanation in ("", "This paragraph explains the approval history.\n\n"):
                with self.subTest(reference=reference, explanation=explanation):
                    code, out = self.run_check(text=body(serves="- `n1`", acceptances=explanation + reference))
                    self.assertEqual(code, 1)
                    self.assertIn("acceptance reference", out)

    def test_explanatory_paragraph_cannot_supply_path_coverage(self):
        (self.repo / "extra.md").write_text("Unapproved change\n")
        self.git("add", "extra.md")
        acceptances = "The approval also covers extra.md.\n\n- `fixture-change` revision 1 by `alice`"
        code, out = self.run_check(text=body(serves="- `n1`", acceptances=acceptances))
        self.assertEqual(code, 1)
        self.assertIn("outside the cited approved scope: extra.md", out)

    def test_malformed_receipt_metadata_fails(self):
        for field, value in (("mode", "voice"), ("by", "assistant"), ("recorded_at", "2026-10-14T12:00:00"), ("scope", ""), ("proposal_revision", True)):
            with self.subTest(field=field):
                state = toy()
                state["change_acceptances"][0][field] = value
                self.write(state)
                code, out = self.run_check(text=body(serves="- `n1`"))
                self.assertEqual(code, 1)
                self.assertIn("Invalid state", out)

    def test_legacy_receipt_without_paths_cannot_cover_a_pr(self):
        state = toy()
        del state["change_acceptances"][0]["approved_paths"]
        self.write(state)
        code, out = self.run_check(text=body(serves="- `n1`"))
        self.assertEqual(code, 1)
        self.assertIn("has no approved_paths", out)

    def test_uncovered_tracked_file_fails(self):
        (self.repo / "extra.md").write_text("Extra change\n")
        self.git("add", "extra.md")
        code, out = self.run_check(text=body(serves="- `n1`"))
        self.assertEqual(code, 1)
        self.assertIn("outside the cited approved scope: extra.md", out)

    def test_unrelated_untracked_files_are_not_part_of_the_pr(self):
        (self.repo / "private-draft.md").write_text("Not included\n")
        (self.repo / "README.md").write_text("The study's scope is call-centre tasks.\n")
        self.assertEqual(self.run_check(text=body(serves="- `n1`"))[0], 0)

    def test_code_only_change_does_not_endorse_reasoning(self):
        (self.repo / "README.md").write_text("The study's scope is call-centre tasks.\n")
        self.assertEqual(self.run_check(text=body(serves="- `n1`"))[0], 0)
        state = yaml.safe_load((self.repo / STATE).read_text())
        self.assertTrue(all(n["status"] == "proposed" for n in state["trees"]["current_reality"]["nodes"]))
        self.assertFalse(any("accepted_by" in n for n in state["trees"]["current_reality"]["nodes"]))

    def test_uncovered_node_or_link_fails_even_when_pr_lists_it(self):
        for category, item in (("nodes", dict(toy()["trees"]["current_reality"]["nodes"][0], id="n3")),
                               ("links", dict(with_link(toy())["trees"]["current_reality"]["links"][0], id="l2"))):
            with self.subTest(category=category):
                state = toy()
                state["trees"]["current_reality"][category].append(item)
                self.write(state)
                code, out = self.run_check(text=body(updates=f"- added `{item['id']}`"))
                self.assertEqual(code, 1)
                self.assertIn(f"outside the cited approved scope: {item['id']}", out)

    def test_multiple_cited_proposals_cover_staged_and_committed_files(self):
        state = toy()
        state["change_acceptances"].append(receipt("extra-change", ["extra.md"]))
        self.write(state)
        (self.repo / "extra.md").write_text("Another approved change\n")
        self.git("add", STATE, "extra.md")
        text = body(serves="- `n1`", acceptances="- `fixture-change` revision 1 by `alice`\n- `extra-change` revision 1 by `alice`")
        self.assertEqual(self.run_check(text=text)[0], 0)
        self.git("commit", "-q", "-m", "approved changes")
        self.assertEqual(self.run_check(text=text)[0], 0)
        self.assertEqual(self.run_check(text=body(serves="- `n1`"))[0], 1)

    def test_rename_requires_approval_for_both_paths(self):
        self.git("mv", "README.md", "renamed.md")
        state = toy()
        state["change_acceptances"].append(receipt("rename", [STATE, "renamed.md"]))
        self.write(state)
        text = body(serves="- `n1`", acceptances="- `rename` revision 1 by `alice`")
        code, out = self.run_check(text=text)
        self.assertEqual(code, 1)
        self.assertIn("outside the cited approved scope: README.md", out)
        text = body(serves="- `n1`", acceptances="- `fixture-change` revision 1 by `alice`\n- `rename` revision 1 by `alice`")
        self.assertEqual(self.run_check(text=text)[0], 0)

    def test_changed_or_removed_earlier_receipt_fails(self):
        for remove in (False, True):
            with self.subTest(remove=remove):
                state = toy()
                if remove:
                    state["change_acceptances"] = []
                else:
                    state["change_acceptances"][0]["source_text"] = "a rewritten reply"
                state["change_acceptances"].append(receipt("new-change"))
                self.write(state)
                code, out = self.run_check(text=body(serves="- `n1`", acceptances="- `new-change` revision 1 by `alice`"))
                self.assertEqual(code, 1)
                self.assertIn("Earlier acceptance receipt was changed or removed", out)

    def test_duplicate_yaml_keys_fail_before_checking_approval(self):
        with (self.repo / STATE).open("a") as handle:
            handle.write("change_acceptances: []\n")
        code, out = self.run_check(text=body(serves="- `n1`"))
        self.assertEqual(code, 1)
        self.assertIn("Duplicate YAML key", out)

    def test_generated_markdown_round_trip_keeps_checklist_collapsed(self):
        self.write(with_link(toy()))
        code, generated = self.run_check("--suggest", "--format", "markdown")
        self.assertEqual(code, 0)
        text = "## What this changes\n\nScope qualification.\n\n" + generated + "\n## Accepted change proposals\n\n- `fixture-change` revision 1 by `alice`\n"
        code, out = self.run_check(text=text)
        self.assertEqual(code, 0, out)

    def test_unresolved_connection_note_is_required(self):
        state = toy()
        state["trees"]["current_reality"]["nodes"][0]["text"] += " Scope is still under review."
        self.write(state)
        _, before, after = check.load_documents([STATE], "main", self.repo)
        generated = check.diagrams.markdown(before, after)
        note = check.diagrams.connection_note(check.diagrams.fragments(before, after)[0])
        self.assertTrue(note)
        text = body(serves="- `n1`", updates="- changed `n1`", diagrams=generated.replace(note, ""))
        code, out = self.run_check(text=text)
        self.assertEqual(code, 1)
        self.assertIn("unresolved-connection notes", out)

    def test_backlog_only_change_requires_its_generated_diagram(self):
        state = toy()
        state["trees"]["current_reality"]["backlog"].append({"ref": "n1", "work": "check_sample", "note": "Find whether the study sampled other roles."})
        self.write(state)
        code, out = self.run_check(text=body(serves="- `n1` — the study result"))
        self.assertEqual(code, 0, out)
        for diagram in ("## Reasoning changes\n\nNo node, link or backlog changes; see the scope below.\n",):
            code, out = self.run_check(text=body(serves="- `n1` — the study result", diagrams=diagram))
            self.assertEqual(code, 1, out)
            self.assertIn("generated, visible Mermaid diagrams", out)

    def test_missing_or_altered_diagram_fails(self):
        self.write(with_link(toy()))
        _, before, after = check.load_documents([STATE], "main", self.repo)
        accurate = check.diagrams.markdown(before, after)
        for diagram in ("", accurate.replace("limits scope", "causes"), accurate.replace("[Proposed]", "[Accepted]")):
            with self.subTest(diagram=diagram[:80]):
                code, out = self.run_check(text=body(updates="- added `l1`", diagrams=diagram))
                self.assertEqual(code, 1)
                self.assertIn("generated, visible Mermaid diagrams", out)

    def test_supported_display_configuration_changes_pass(self):
        self.write(with_link(toy()))
        _, before, after = check.load_documents([STATE], "main", self.repo)
        accurate = check.diagrams.markdown(before, after)
        original = "---\nconfig:\n  htmlLabels: false\n  flowchart:\n    wrappingWidth: 360\n---"
        variants = [
            original.replace("360", "720"),
            "---\nconfig:\n  flowchart:\n    wrappingWidth: 480\n  htmlLabels: false\n---",
            "---\nconfig: {flowchart: {wrappingWidth: 480}, htmlLabels: false}\n---",
            "---\nconfig:\n  htmlLabels: false # Preserve complete SVG labels.\n---",
        ]
        for configuration in variants:
            with self.subTest(configuration=configuration):
                text = body(updates="- added `l1`", diagrams=accurate.replace(original, configuration))
                code, out = self.run_check(text=text)
                self.assertEqual(code, 0, out)

    def test_unsupported_or_malformed_display_configuration_fails_clearly(self):
        self.write(with_link(toy()))
        _, before, after = check.load_documents([STATE], "main", self.repo)
        accurate = check.diagrams.markdown(before, after)
        original = "---\nconfig:\n  htmlLabels: false\n  flowchart:\n    wrappingWidth: 360\n---"
        variants = [
            "", original.replace("false", "true"),
            original.replace("false", "'false'"),
            original.replace("  htmlLabels: false\n", ""),
            original.replace("360", "0"), original.replace("360", "-1"),
            original.replace("360", "true"), original.replace("360", "'720'"),
            original.replace("config:", "config: ["),
            original.replace("config:", "config:\n  themeCSS: '.node { display: none }'"),
            original.replace("  htmlLabels: false", "  htmlLabels: true\n  htmlLabels: false"),
            original.replace("config:", "title: Extra diagram text\nconfig:"),
        ]
        for configuration in variants:
            with self.subTest(configuration=configuration):
                text = body(updates="- added `l1`", diagrams=accurate.replace(original, configuration))
                code, out = self.run_check(text=text)
                self.assertEqual(code, 1, out)
                self.assertIn("Invalid Mermaid display configuration in diagram 1", out)

    def test_display_changes_do_not_allow_altered_reasoning(self):
        self.write(with_link(toy()))
        _, before, after = check.load_documents([STATE], "main", self.repo)
        accurate = check.diagrams.markdown(before, after).replace("wrappingWidth: 360", "wrappingWidth: 720")
        for diagram in (
            accurate.replace("limits scope", "causes"),
            accurate.replace("[Proposed]", "[Accepted]"),
            accurate.replace("call centre workers only", "all workers"),
            accurate.replace(".-> n0", ".-> n1"),
        ):
            with self.subTest(diagram=diagram[:80]):
                code, out = self.run_check(text=body(updates="- added `l1`", diagrams=diagram))
                self.assertEqual(code, 1, out)
                self.assertIn("generated, visible Mermaid diagrams", out)

    def test_diagrams_inside_details_do_not_count_as_visible(self):
        self.write(with_link(toy()))
        _, before, after = check.load_documents([STATE], "main", self.repo)
        diagram = check.diagrams.markdown(before, after).replace("## Reasoning changes\n", "")
        hidden = "## Reasoning changes\n\n<details><summary>Hidden</summary>\n\n" + diagram + "\n</details>"
        code, out = self.run_check(text=body(updates="- added `l1`", diagrams=hidden))
        self.assertEqual(code, 1)
        self.assertIn("generated, visible Mermaid diagrams", out)

    def test_expanded_or_visible_update_list_fails(self):
        self.write(with_link(toy()))
        for text in (body(updates="- added `l1`", collapsed=False), body(updates="- added `l1`").replace("<details>", "<details open>"), body(updates="- added `l1`").replace("</details>", "</details>\n\n- added `l1`")):
            with self.subTest(text=text[:60]):
                code, out = self.run_check(text=text)
                self.assertEqual(code, 1)
                self.assertTrue("closed <details>" in out or "no visible duplicate list" in out, out)

    def test_tree_move_is_a_declared_change(self):
        state = toy()
        moved = state["trees"]["current_reality"]["nodes"].pop()
        state["trees"]["future_reality"] = {"nodes": [moved], "links": [], "backlog": []}
        self.write(state)
        code, out = self.run_check(text=body(updates="- changed `n2`"))
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()


def predicted(commitment=True, reports=()):
    """A toy injection with a predicted benefit and a reservation, optionally with a feedback commitment."""
    state = toy()
    contribution = [{"by": "alice", "attribution": "explicit", "mode": "text"}]
    nodes = [("i1", "injection", "Alice tries remote work on one comparable shift."),
             ("p1", "predicted_effect", "Alice completes more comparable calls during that shift."),
             ("u1", "undesirable_effect", "Alice may find help harder to get | remotely.")]
    state["trees"]["future_reality"] = {"nodes": [{"id": i, "kind": k, "text": t, "status": "proposed", "contributions": deepcopy(contribution)} for i, k, t in nodes],
                                        "links": [], "backlog": []}
    state["change_acceptances"].append(dict(receipt("outcome-change"), node_ids=["i1", "p1", "u1"], link_ids=[]))
    if commitment:
        snap = lambda i, k, t: {"ref": i, "tree": "future_reality", "kind": k, "standing": "proposed", "text": t}
        state["feedback_requests"] = [{"id": "remote-trial", "revision": 1, "created_by": "alice", "recorded_at": "2026-10-20T10:00:00Z",
                                       "about": snap(*nodes[0]), "feedback_from": ["alice"], "ready_when": "After the shift.",
                                       "benefits": [snap(*nodes[1])], "reservations": [snap(*nodes[2])], "reports": list(reports)}]
    return state


REPORT = {"id": "r1", "by": "alice", "recorded_at": "2026-10-21T15:00:00Z", "readiness": "experienced",
          "text": "I finished more calls,\nbut have not checked help.", "evidence_type": "self_report",
          "outcomes": [{"ref": "p1", "verdict": "observed", "note": "Shift record."}, {"ref": "u1", "verdict": "not_assessed", "note": "Not yet."}]}


class ExpectedOutcomeTests(unittest.TestCase):
    setUp, tearDown, git, write, run_check = CheckTests.setUp, CheckTests.tearDown, CheckTests.git, CheckTests.write, CheckTests.run_check

    def full_body(self, outcomes=None, serves=""):
        code, suggestion = self.run_check("--suggest", "--format", "markdown")
        self.assertEqual(code, 0, suggestion)
        if outcomes is not None:
            suggestion = re.sub(r"## Expected outcomes\n.*?(?=## Reasoning changes)", outcomes, suggestion, flags=re.S)
        acceptances = "- `fixture-change` revision 1 by `alice`\n- `outcome-change` revision 1 by `alice`"
        return f"## What this changes\n\nSomething.\n\n{suggestion}\n\n## Reasoning this serves\n\n{serves}\n\n## Accepted change proposals\n\n{acceptances}\n"

    def test_generated_commitment_section_passes_and_shows_both_outcomes(self):
        self.write(predicted())
        text = self.full_body()
        self.assertIn("**`remote-trial` revision 1**: new feedback commitment", text)
        self.assertIn("| Expected benefit | Future Reality · Predicted effect · Proposed: Alice completes more", text)
        self.assertIn("| Possible harmful consequence | Future Reality · Undesirable effect · Proposed: Alice may find help harder to get \\| remotely. |", text)
        self.assertIn("| Feedback from | Alice |", text)
        code, out = self.run_check(text=text)
        self.assertEqual(code, 0, out)

    def test_missing_or_altered_commitment_section_fails(self):
        self.write(predicted())
        code, out = self.run_check(text=self.full_body(outcomes=""))
        self.assertEqual(code, 1)
        self.assertIn('no "Expected outcomes" section', out)
        text = self.full_body().replace("After the shift.", "Whenever.")
        code, out = self.run_check(text=text)
        self.assertEqual(code, 1)
        self.assertIn("generated block `remote-trial` revision 1", out)

    def test_reports_added_to_an_existing_commitment_are_shown(self):
        base = predicted()
        self.write(base)
        self.git("add", STATE)
        self.git("commit", "-q", "-m", "commitment")
        self.git("branch", "-f", "main")
        self.write(predicted(reports=[REPORT]))
        text = self.full_body(serves="- `i1`")
        self.assertNotIn("new feedback commitment", text)
        self.assertIn("**Feedback recorded for `remote-trial` revision 1**", text)
        self.assertIn("- Alice · 2026-10-21T15:00:00Z · experienced: “I finished more calls, but have not checked help.”", text)
        self.assertIn("  - Expected benefit `p1`: observed", text)
        self.assertIn("  - Possible harmful consequence `u1`: not assessed", text)
        code, out = self.run_check(text=self.full_body(serves="- `i1`"))
        self.assertEqual(code, 0, out)

    def test_prediction_without_commitment_needs_a_reason(self):
        self.write(predicted(commitment=False))
        text = self.full_body()
        self.assertIn("No feedback commitment: REPLACE WITH REASON (predictions: `p1`, `u1`)", text)
        code, out = self.run_check(text=text)
        self.assertEqual(code, 1)
        self.assertIn("Predictions without a feedback commitment: `p1`, `u1`", out)
        code, out = self.run_check(text=text.replace("REPLACE WITH REASON", "Generic historical prediction; nobody can observe it"))
        self.assertEqual(code, 0, out)

    def test_change_without_predictions_needs_no_section(self):
        self.write(with_link(toy()))
        code, out = self.run_check(text=body(updates="- added `l1` — `n2` limits the scope of `n1`"))
        self.assertEqual(code, 0, out)
