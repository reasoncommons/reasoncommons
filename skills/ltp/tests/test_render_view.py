"""Checks for the in-chat view renderer on a small fixture."""

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/render_view.py"
SPEC = importlib.util.spec_from_file_location("render_view", SCRIPT)
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


def node(ident, text, status="accepted", **extra):
    item = {"id": ident, "kind": "cause", "text": text, "status": status, "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}], **extra}
    if status == "accepted":
        item["accepted_by"] = ["alice"]
    return item


def link(ident, sources, target, status="accepted"):
    item = {"id": ident, "from": sources, "to": target, "relation": "contributes_to", "status": status, "contributions": [{"by": "alice", "attribution": "explicit", "mode": "text"}]}
    if status == "accepted":
        item["accepted_by"] = ["alice"]
    return item


def state():
    nodes = [
        node("a", "Sales is hard"),
        node("b", "No product-market fit"),
        node("c", "No customers"),
        node("d", "Only own time"),
        node("e", "Funding not applied for"),
        node("f", "Loose accepted fact"),
        node("g", "A proposed cause", "proposed"),
        node("h", "A disputed claim", "disputed", challenges=[{"text": "Superseded", "by": "bob"}]),
    ]
    links = [
        link("l1", ["a"], "c"),
        link("l2", ["b"], "c"),
        link("l3", ["c", "e"], "d"),
        link("l4", ["g"], "c", "proposed"),
    ]
    tree = {"nodes": nodes, "links": links, "backlog": []}
    return {"schema_version": 1, "driver": "alice", "participants": {"alice": "Alice", "bob": "Bob"}, "active_tree": "current_reality", "trees": {"current_reality": tree, "goal": {"nodes": [], "links": [], "backlog": []}}}


class RenderViewTests(unittest.TestCase):
    def setUp(self):
        render.PEOPLE.update(alice="Alice", bob="Bob")
        self.tree = state()["trees"]["current_reality"]

    def test_counts_skip_empty_trees_and_zero_standings(self):
        self.assertEqual(render.counts(state()), "Current reality (6 accepted · 1 proposed · 1 disputed)")

    def test_accepted_view_keeps_each_node_once_and_joint_causes_joint(self):
        source, shown, links, common, context = render.mermaid("current_reality", self.tree, "accepted")
        self.assertEqual((len(shown), len(links), context), (6, 3, []))
        self.assertEqual(common, "contributes to")
        labels = re.findall(r'\["(\[A\][^"]*)"\]', source)
        self.assertEqual(len(labels), len(set(labels)), "a node was drawn twice")
        self.assertIn('j3(("AND"))', source)
        self.assertNotIn("A proposed cause", source)
        self.assertIn('subgraph loose["Not yet linked"]', source)

    def test_proposed_view_shows_other_standing_endpoints_as_context(self):
        source, shown, links, _, context = render.mermaid("current_reality", self.tree, "proposed")
        self.assertEqual((shown, context), (["g"], ["c"]))
        self.assertIn("[Accepted]<br/>Cause<br/>No customers", source)
        self.assertNotIn("CURRENT REALITY", source)
        self.assertRegex(source, r"class n2 context")
        self.assertIn("-.->", source)

    def test_disputed_view_names_the_objector(self):
        source = render.mermaid("current_reality", self.tree, "disputed")[0]
        self.assertIn("Objection (Bob): Superseded", source)

    def test_node_metadata_names_standing_and_kind_not_tree_and_preserves_statement(self):
        examples = {
            "goal": "necessary_condition",
            "current_reality": "undesirable_effect",
            "conflict": "prerequisite",
            "future_reality": "injection",
            "prerequisite": "obstacle",
            "transition": "expected_effect",
        }
        for tree, kind in examples.items():
            with self.subTest(tree=tree, kind=kind):
                # The ID deliberately does not encode the tree or kind.
                item = node("opaque-id", 'A qualified statement: sometimes "this" holds.', "proposed", kind=kind)
                content = {"nodes": [item], "links": [], "backlog": []}
                source = render.mermaid(tree, content, "proposed")[0]
                kind_name = kind.replace("_", " ").capitalize()
                self.assertIn(f"[Proposed]<br/>{kind_name}<br/>", source)
                self.assertNotIn(tree.replace("_", " ").upper(), source)
                self.assertNotIn("opaque-id", source)
                self.assertIn(render.escape(item["text"]), source)
                outline = render.text_outline(tree, content, "proposed")
                self.assertIn(f"[Proposed] {kind_name}: " + item["text"], outline)

    def test_markdown_view_preserves_topology_and_scope_for_each_standing(self):
        for standing in render.STANDINGS:
            with self.subTest(standing=standing):
                source, shown, links, common, context = render.mermaid("current_reality", self.tree, standing)
                response = render.markdown("current_reality", self.tree, standing)
                embedded = response.split("```mermaid\n", 1)[1].split("\n```", 1)[0]
                self.assertEqual(embedded, source)
                self.assertEqual(response.splitlines()[0], render.heading("current_reality", standing, shown, links, context))
                self.assertTrue(response.endswith(render.not_shown(self.tree, standing)))
                if common:
                    self.assertIn(f"Each arrow reads “{common}”.", response)

    def test_text_outline_lists_each_link_once(self):
        outline = render.text_outline("current_reality", self.tree, "accepted")
        self.assertTrue(outline.startswith("CURRENT REALITY — ACCEPTED ONLY (6 nodes, 3 links)"))
        self.assertIn("AND( [Accepted] Cause: No customers + [Accepted] Cause: Funding not applied for )", outline)
        self.assertEqual(outline.count("<- "), 3)
        self.assertIn("Not yet linked:\n  [Accepted] Cause: Loose accepted fact", outline)
        self.assertTrue(outline.endswith("Not shown: 1 proposed, 1 disputed. Say “show proposed” or “show disputed”."))

    def test_widget_labels_fit_the_host_without_wrapping(self):
        # The Claude widget host neither wraps label text nor widens labels past about 200px.
        long = node("long", "A statement long enough that it would run far past the width the widget host gives each label line.", "accepted")
        tree = {"nodes": [long], "links": [], "backlog": []}
        page = render.widget("current_reality", tree, "accepted")
        source = json.loads(page.split("mermaid.render('", 1)[1].split("', ", 1)[1].rsplit(");\nconst host", 1)[0])
        lines = [line for label in re.findall(r'\["(.*?)"\]', source) for line in label.split("<br/>")]
        self.assertLessEqual(max(map(len, lines)), render.WIDTH)
        self.assertIn("A statement long enough that it would run far past the width the widget host gives each label line.", " ".join(lines[2:]))
        markdown = render.markdown("current_reality", tree, "accepted")
        self.assertIn(long["text"], markdown)

    def test_views_draw_short_labels_but_the_outline_keeps_full_statements(self):
        item = node("x", "A long statement whose qualification matters: only for call-centre work.", "accepted")
        item["label"] = "The gain holds only for call-centre work."
        tree = {"nodes": [item], "links": [], "backlog": []}
        source = render.mermaid("current_reality", tree, "accepted")[0]
        self.assertIn("The gain holds only for call-centre work.", source)
        self.assertNotIn("A long statement", source)
        self.assertIn("A long statement whose qualification matters", render.text_outline("current_reality", tree, "accepted"))

    def test_widget_embeds_source_safely(self):
        page = render.frame('flowchart LR\n  a["</script> `${x}`"]', "HEAD <b>")
        embedded = re.search(r"mermaid\.render\('rc-[0-9a-f]+', (.*)\);", page).group(1)
        self.assertNotIn("</script>", embedded)
        self.assertEqual(json.loads(embedded.replace("<\\/", "</")), 'flowchart LR\n  a["</script> `${x}`"]')
        self.assertIn("HEAD &lt;b&gt;", page)
        self.assertNotIn("__", page)

    def test_frame_offers_a_taller_view_for_expanded_windows(self):
        # The widget's height follows its content, so an expanded side window only gains height when the frame grows.
        page = render.frame('flowchart LR\n  a["A"]', "HEAD")
        self.assertIn("#rcv{position:relative;height:380px;", page)
        self.assertIn("#rcv.tall{height:720px}", page)
        self.assertIn('<button id="ztall" aria-pressed="false">Taller</button>', page)
        self.assertIn("box.classList.toggle('tall')", page)
        self.assertIn("on ? 'Shorter' : 'Taller'", page)

    def test_cli_defaults_to_accepted_and_refuses_empty_standing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.yaml"
            path.write_text(yaml.safe_dump(state(), allow_unicode=True))
            run = lambda *a: subprocess.run([sys.executable, str(SCRIPT), str(path), *a], capture_output=True, text=True)
            out = run("--tree", "current_reality")
            native = run("--tree", "current_reality", "--format", "markdown")
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertEqual(native.stdout.strip(), render.markdown("current_reality", self.tree, "accepted"))
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("CURRENT REALITY — ACCEPTED ONLY (6 nodes, 3 links)", out.stdout)
            self.assertIn("ti-arrows-maximize", out.stdout)
            out = run("--tree", "goal")
            self.assertNotEqual(out.returncode, 0)


if __name__ == "__main__":
    unittest.main()
