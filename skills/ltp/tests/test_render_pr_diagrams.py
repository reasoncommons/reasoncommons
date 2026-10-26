"""Behavioral invariants for generated PR diagrams on the remote-work gold fixture."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/render_pr_diagrams.py"
SPEC = importlib.util.spec_from_file_location("pr_diagrams", SCRIPT)
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


def node(ident, text, standing="proposed"):
    return {"id": ident, "kind": "observation", "text": text, "status": standing,
            "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}]}


def link(ident, sources, target, standing="proposed", relation="limits_scope"):
    return {"id": ident, "from": sources, "to": target, "relation": relation, "status": standing,
            "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}]}


def document(nodes=(), links=()):
    return {"fixture.yaml": {"trees": {"current_reality": {"nodes": list(nodes), "links": list(links), "backlog": []}}}}


class PRDiagramTests(unittest.TestCase):
    def setUp(self):
        self.gain = node("gain", "The call-centre study reported a 13% productivity gain on solo call-handling tasks.")
        self.scope = node("scope", "The result may not generalise to creative and collaborative knowledge work.")
        self.limits = link("limits", ["gain"], "scope")

    def test_added_link_includes_actual_endpoints_and_metadata(self):
        before = document([self.gain, self.scope])
        after = document([self.gain, self.scope], [self.limits])
        fragments = render.fragments(before, after)
        self.assertEqual(len(fragments), 1)
        self.assertEqual(fragments[0]["node_ids"], ["gain", "scope"])
        self.assertEqual(fragments[0]["link_ids"], ["limits"])
        source = fragments[0]["source"]
        self.assertIn("CONTEXT · [Proposed]<br/>Observation<br/>", source)
        self.assertIn("ADDED · limits scope", source)
        self.assertNotIn("CURRENT REALITY", source)
        self.assertIn("may not generalise", source)
        self.assertIn("CONTEXT", source)

    def test_changed_statement_shows_previous_and_new_qualifications(self):
        before = document([self.gain])
        revised = deepcopy(self.gain)
        revised["text"] = "The reported gain partially reversed when workers chose to return to the office."
        source = render.fragments(before, document([revised]))[0]["source"]
        self.assertIn('%% node "gain" old', source)
        self.assertIn('%% node "gain" new', source)
        self.assertIn("PREVIOUS", source)
        self.assertIn("CHANGED", source)
        self.assertIn(self.gain["text"], source.replace("<br/>", " "))
        self.assertIn(revised["text"], source.replace("<br/>", " "))

    def test_removal_uses_previous_standing_and_statement(self):
        old = deepcopy(self.scope)
        old["status"] = "accepted"
        before = document([self.gain, old], [self.limits])
        fragment = render.fragments(before, document([self.gain]))[0]
        self.assertIn("REMOVED · [Accepted]<br/>Observation", fragment["source"])
        self.assertIn("may not generalise", fragment["source"])
        self.assertEqual(fragment["link_ids"], ["limits"])

    def test_joint_link_keeps_old_and_new_topology(self):
        tasks = node("tasks", "The reported gain concerns solo call-handling tasks specifically.")
        before = document([self.gain, self.scope, tasks], [self.limits])
        joint = deepcopy(self.limits)
        joint["from"] = ["gain", "tasks"]
        joint["relation"] = "qualifies"
        source = render.fragments(before, document([self.gain, self.scope, tasks], [joint]))[0]["source"]
        self.assertIn('%% link "limits" old', source)
        self.assertIn('%% link "limits" new', source)
        self.assertEqual(source.count('(("AND"))'), 1)
        self.assertIn("PREVIOUS · limits scope", source)
        self.assertIn("CHANGED · qualifies", source)

    def test_context_does_not_expand_to_unrelated_branches(self):
        remote = node("other", "An unrelated study result.")
        extra = link("extra", ["scope"], "other")
        before = document([self.gain, self.scope, remote], [self.limits, extra])
        revised = deepcopy(self.gain)
        revised["text"] += " The study was specific to that setting."
        fragment = render.fragments(before, document([revised, self.scope, remote], [self.limits, extra]))[0]
        self.assertEqual(fragment["node_ids"], ["gain", "scope"])
        self.assertEqual(fragment["link_ids"], ["limits"])
        self.assertNotIn("unrelated", fragment["source"])

    def test_disconnected_nodes_share_one_tree_diagram_without_invented_edges(self):
        fragments = render.fragments({}, document([self.gain, self.scope]))
        self.assertEqual(len(fragments), 1)
        fragment = fragments[0]
        self.assertEqual(fragment["node_ids"], ["gain", "scope"])
        self.assertEqual(fragment["link_ids"], [])
        self.assertNotIn("-->", fragment["source"])
        self.assertNotIn(".->", fragment["source"])
        text = render.markdown({}, document([self.gain, self.scope]))
        self.assertEqual(text.count("```mermaid"), 1)
        self.assertNotIn("fragment 1", text)
        self.assertIn("Their connections remain unresolved", text)
        self.assertIn('subgraph loose["Not yet connected"]', text)
        self.assertNotIn("`gain`", text)

    def test_disconnected_chains_share_a_diagram_but_different_trees_do_not(self):
        other = node("other", "Another finding with a qualified scope.")
        scope2 = node("scope2", "Its applicability remains uncertain.")
        extra = link("extra", ["other"], "scope2")
        after = document([self.gain, self.scope, other, scope2], [self.limits, extra])
        after["fixture.yaml"]["trees"]["goal"] = {"nodes": [node("goal", "Understand applicability.")], "links": []}
        diagrams = render.fragments({}, after)
        self.assertEqual([d["tree"] for d in diagrams], ["goal", "current_reality"])
        current = diagrams[1]
        self.assertEqual(current["link_ids"], ["extra", "limits"])
        self.assertEqual(current["group_count"], 2)
        self.assertEqual(current["unconnected_node_ids"], [])
        self.assertIn("2 disconnected group(s)", render.connection_note(current))

    def test_labels_escape_markup_and_opaque_ids_do_not_control_roles(self):
        item = node('end " odd', 'A "quoted" finding & <scope> may apply.')
        item["kind"] = "goal"
        after = document()
        after["fixture.yaml"]["trees"] = {"goal": {"nodes": [item], "links": [], "backlog": []}}
        source = render.fragments({}, after)[0]["source"]
        self.assertIn("ADDED · [Proposed]<br/>Goal<br/>", source)
        labels = "\n".join(line for line in source.splitlines() if not line.strip().startswith("%%"))
        self.assertNotIn("odd", labels)
        self.assertNotIn("GOAL", labels)
        self.assertIn("#quot;quoted#quot;", source)
        self.assertIn("#amp; #lt;scope#gt;", source)
        self.assertIn('n0["', source)

    def test_rendering_is_deterministic_and_never_changes_state(self):
        after = document([self.gain, self.scope], [self.limits])
        original = deepcopy(after)
        first = render.markdown({}, after)
        self.assertEqual(after, original)
        after["fixture.yaml"]["trees"]["current_reality"]["nodes"].reverse()
        self.assertEqual(first, render.markdown({}, after))

    def test_nodes_show_their_short_label_and_fall_back_to_text(self):
        labelled = deepcopy(self.scope)
        labelled["label"] = "The gain may not hold for creative work."
        source = render.fragments({}, document([self.gain, labelled], [self.limits]))[0]["source"]
        self.assertIn("ADDED · [Proposed]<br/>Observation<br/>The gain may not hold for creative<br/>work.", source)
        self.assertNotIn("collaborative knowledge", source)
        self.assertIn("13% productivity gain", source.replace("<br/>", " "))

    def test_label_only_edit_is_one_relabelled_node(self):
        before = document([self.gain, self.scope], [self.limits])
        after = deepcopy(before)
        after["fixture.yaml"]["trees"]["current_reality"]["nodes"][1]["label"] = "The gain may not hold for creative work."
        source = render.fragments(before, after)[0]["source"]
        self.assertIn("RELABELLED · [Proposed]", source)
        self.assertNotIn("PREVIOUS", source)
        self.assertEqual(source.count('%% node "scope"'), 1)
        self.assertEqual(source.count('%% link "limits"'), 1)
        revised = deepcopy(after)
        revised["fixture.yaml"]["trees"]["current_reality"]["nodes"][1]["text"] += " It concerned solo tasks."
        source = render.fragments(before, revised)[0]["source"]
        self.assertIn("PREVIOUS · [Proposed]", source)
        self.assertIn("CHANGED · [Proposed]", source)

    def test_relabelled_node_does_not_widen_the_view(self):
        other = node("other", "An unrelated study result.")
        extra = link("extra", ["other"], "scope")
        before = document([self.gain, self.scope, other], [self.limits, extra])
        after = deepcopy(before)
        nodes = after["fixture.yaml"]["trees"]["current_reality"]["nodes"]
        nodes[0]["text"] += " The study was specific to that setting."
        nodes[1]["label"] = "The gain may not hold for creative work."
        fragment = render.fragments(before, after)[0]
        self.assertEqual(fragment["node_ids"], ["gain", "scope"])
        self.assertNotIn("unrelated", fragment["source"])
        alone = deepcopy(before)
        alone["fixture.yaml"]["trees"]["current_reality"]["nodes"][2]["label"] = "Another study."
        fragment = render.fragments(before, alone)[0]
        self.assertEqual(fragment["node_ids"], ["other", "scope"])
        self.assertEqual(fragment["unconnected_node_ids"], [])

    def test_receipts_do_not_fabricate_tree_changes(self):
        before = document([self.gain])
        after = deepcopy(before)
        after["fixture.yaml"]["change_acceptances"] = [{"scope": "Fixture approval"}]
        self.assertEqual(render.fragments(before, after), [])
        self.assertNotIn("```mermaid", render.markdown(before, after))

    def test_backlog_changes_hang_from_their_statement_without_ids(self):
        before = document([self.gain, self.scope], [self.limits])
        before["fixture.yaml"]["trees"]["current_reality"]["backlog"] = [{"ref": "gain", "work": "test_scope", "note": "Check the original study."}]
        after = deepcopy(before)
        after["fixture.yaml"]["trees"]["current_reality"]["backlog"][0]["note"] += " Then compare with a creative-work sample."
        after["fixture.yaml"]["trees"]["current_reality"]["backlog"].append({"ref": "limits", "work": "find_counterexample", "evaluation_plan": "Look for a creative team that kept the gain."})
        fragment = render.fragments(before, after)[0]
        self.assertEqual(fragment["backlog_keys"], ["gain|test_scope", "limits|find_counterexample"])
        self.assertEqual(fragment["node_ids"], ["gain", "scope"])
        source = fragment["source"]
        # Notes stay in the YAML; diagrams show the label, or the work named in words.
        self.assertIn("CHANGED · Backlog<br/>Test scope", source)
        self.assertNotIn("creative-work sample", source)
        after["fixture.yaml"]["trees"]["current_reality"]["backlog"][1]["label"] = "Find a creative team that kept the gain."
        source = render.fragments(before, after)[0]["source"]
        self.assertIn("ADDED · Backlog<br/>Find a creative team that kept the<br/>gain.", source)
        self.assertNotIn("Look for a creative", source)
        self.assertIn("b0 -.- n0", source)
        self.assertIn("b1 -.- n0", source)
        self.assertIn("b1 -.- n1", source)
        labels = "\n".join(line for line in source.splitlines() if not line.strip().startswith("%%"))
        for hidden in ("test_scope", "find_counterexample", "limits|"):
            self.assertNotIn(hidden, labels)
        self.assertIn("```mermaid", render.markdown(before, after))


if __name__ == "__main__":
    unittest.main()
