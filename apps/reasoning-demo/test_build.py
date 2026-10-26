"""Meaning, layout and publication-boundary checks; no private repository is needed."""
from collections import Counter, defaultdict
from copy import deepcopy
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urljoin, urlparse

spec = importlib.util.spec_from_file_location("demo_build", Path(__file__).with_name("build.py"))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
diagrams, pages = build.diagrams, build.pages

try:
    import yaml  # noqa: F401
    HAVE_YAML = True
except ModuleNotFoundError:
    HAVE_YAML = False


def node(ident, text="A useful condition.", status="accepted"):
    return {"id": ident, "kind": "goal" if ident == "goal" else "necessary_condition", "text": text, "status": status,
            "accepted_by": ["david"], "acceptance_source": "Accepted in the toy review.",
            "contributions": [{"by": "david", "attribution": "explicit", "mode": "text"}]}


def fixture():
    state = {"schema_version": 1, "trees": {"goal": {"nodes": [node("goal"), node("first"), node("second"), node("loose")],
             "links": [{"id": "joint", "from": ["first", "second"], "to": "goal", "relation": "necessary_for", "status": "accepted",
                        "accepted_by": ["david"], "acceptance_source": "Accepted in the toy review.",
                        "contributions": [{"by": "assistant", "attribution": "assistant", "mode": "text"}]}], "backlog": []}}}
    registry = {"registry_version": 1, "release": {"release_id": "toy.1", "snapshot_date": "2026-10-22", "title": "Toy project"},
                "people": {"david": "David Joseph"}, "selection": {"goal": {"nodes": ["goal", "first", "second", "loose"], "links": ["joint"]}}}
    return state, registry


def toy_tree(state, registry):
    tree = build.project(state, registry)["trees"]["goal"]
    return {"name": "goal", "backlog": [], "nodes": tree["nodes"], "links": tree["links"]}


def draw(tree):
    pieces, loose = diagrams.components(tree)
    label = lambda kind: pages.kind_label(tree["name"], kind)
    shapes = [diagrams.geometry(tree, p["ids"], p["links"], label) for p in pieces]
    nodes = {n["id"]: n for n in tree["nodes"]}
    return pieces, shapes, loose, "".join(diagrams.svg(s, nodes, lambda i: f"#{i}", "Toy") for s in shapes)


class ExportTests(unittest.TestCase):
    def test_only_explicitly_selected_accepted_fields_cross_boundary(self):
        state, registry = fixture()
        state["change_acceptances"] = [{"source_text": "RECEIPT_CANARY"}]
        state["trees"]["goal"]["nodes"].extend([node("private-accepted", "ACCEPTED_CANARY"), node("private-proposed", "PROPOSED_CANARY", "proposed"), node("private-disputed", "DISPUTED_CANARY", "disputed")])
        for item in state["trees"]["goal"]["nodes"]:
            item.update(source={"path": "/PRIVATE_PATH_CANARY"}, assumptions=[{"text": "ASSUMPTION_CANARY"}], challenges=[{"text": "CHALLENGE_CANARY"}])
            item["contributions"][0]["note"] = "NOTE_CANARY"
        state["trees"]["goal"]["backlog"] = [{"note": "BACKLOG_CANARY"}]
        output = json.dumps(build.project(state, registry))
        self.assertNotIn("CANARY", output)

    def test_a_downgraded_item_publishes_as_proposed_never_as_stale_acceptance(self):
        state, registry = fixture()  # proposed-reasoning-public r1: our commons publishes proposed items without endorsers.
        loose = state["trees"]["goal"]["nodes"][3]
        loose.update(status="proposed")
        loose.pop("accepted_by")
        public = next(n for n in build.project(state, registry)["trees"]["goal"]["nodes"] if n["id"] == "loose")
        self.assertEqual((public["status"], public["accepted_by"]), ("proposed", []))
        self.assertNotIn("acceptance_context", public)
        state, registry = fixture()
        state["trees"]["goal"]["nodes"][3]["status"] = "proposed"  # Endorsers left on a proposed item are refused.
        with self.assertRaisesRegex(ValueError, "lists endorsers"):
            build.project(state, registry)
        state, registry = fixture()
        state["trees"]["goal"]["nodes"][1]["status"] = "disputed"
        with self.assertRaisesRegex(ValueError, "disputed"):
            build.project(state, registry)
        state, registry = fixture()
        first = state["trees"]["goal"]["nodes"][1]
        first.update(status="proposed")
        first.pop("accepted_by")
        with self.assertRaisesRegex(ValueError, "accepted endpoints"):  # The accepted joint link cannot keep it.
            build.project(state, registry)
    def test_connection_downgrade_publishes_as_proposed(self):
        state, registry = fixture()
        link = state["trees"]["goal"]["links"][0]
        link.update(status="proposed")
        link.pop("accepted_by")
        public = build.project(state, registry)["trees"]["goal"]["links"][0]
        self.assertEqual((public["status"], public["accepted_by"]), ("proposed", []))
    def test_partial_joint_connection_fails(self):
        state, registry = fixture()
        registry["selection"]["goal"]["nodes"].remove("second")
        with self.assertRaisesRegex(ValueError, "Missing published endpoint"):
            build.project(state, registry)

    def test_missing_source_id_fails(self):
        state, registry = fixture()
        registry["selection"]["goal"]["nodes"].append("missing")
        with self.assertRaisesRegex(ValueError, "missing"):
            build.project(state, registry)

    def test_unknown_versions_fail(self):
        state, registry = fixture()
        state["schema_version"] = 20
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            build.project(state, registry)

    def test_unknown_names_are_not_silently_published(self):
        state, registry = fixture()
        state["trees"]["goal"]["nodes"][0]["accepted_by"] = ["not-selected"]
        with self.assertRaisesRegex(ValueError, "Unselected endorser"):
            build.project(state, registry)

    def test_unknown_original_contributor_is_not_the_driver(self):
        state, registry = fixture()
        state["trees"]["goal"]["nodes"][0]["contributions"] = [{"by": "david", "attribution": "driver_default", "mode": "unknown"}]
        output = build.project(state, registry)["trees"]["goal"]["nodes"][0]
        self.assertEqual(output["contributors"], [{"name": "Original contributor not identified", "role": "unknown"}])
        self.assertEqual(output["accepted_by"], ["David Joseph"])

    def test_ai_origin_and_human_endorsement_are_separate(self):
        state, registry = fixture()
        link = build.project(state, registry)["trees"]["goal"]["links"][0]
        self.assertEqual(link["contributors"], [{"name": "AI assistant", "role": "assistant"}])
        self.assertEqual(link["accepted_by"], ["David Joseph"])

    def test_unknown_channel_does_not_erase_explicit_authorship(self):
        state, registry = fixture()
        state["trees"]["goal"]["nodes"][0]["contributions"][0]["mode"] = "unknown"
        item = build.project(state, registry)["trees"]["goal"]["nodes"][0]
        self.assertEqual(item["contributors"], [{"name": "David Joseph", "role": "human"}])

    def test_unreviewed_fields_in_pinned_public_snapshot_fail(self):
        state, registry = fixture()
        data = build.project(state, registry)
        data["trees"]["goal"]["nodes"][0]["private_note"] = "hidden"
        with self.assertRaisesRegex(ValueError, "Unreviewed public fields"):
            build.validate_projection(data, registry)


class DiagramTests(unittest.TestCase):
    def test_joint_connection_meets_at_one_and_with_one_arrow(self):
        pieces, shapes, loose, svg = draw(toy_tree(*fixture()))
        self.assertEqual(svg.count('<a class="j '), 1)
        self.assertEqual(svg.count('class="e-head"'), 1)
        self.assertEqual(loose, ["loose"])
        self.assertNotIn('data-id="loose"', svg)

    def test_text_is_escaped_in_cards_diagrams_and_outlines(self):
        state, registry = fixture()
        state["trees"]["goal"]["nodes"][0]["text"] = '<script>alert("x")</script>'
        tree = toy_tree(state, registry)
        pieces, shapes, loose, svg = draw(tree)
        outline = diagrams.outline(tree, pieces[0]["ids"], pieces[0]["links"], lambda i: f"#{i}", lambda k: k)
        for output in (svg, outline):
            self.assertNotIn("<script>", output)
            self.assertIn("&lt;script&gt;", output)

    def test_cycles_are_refused_rather_than_redrawn(self):
        tree = {"name": "current_reality", "nodes": [{"id": i, "kind": "cause", "text": i, "status": "accepted"} for i in "ab"],
                "links": [{"id": "ab", "from": ["a"], "to": "b", "relation": "contributes_to", "status": "accepted"},
                          {"id": "ba", "from": ["b"], "to": "a", "relation": "contributes_to", "status": "accepted"}]}
        with self.assertRaisesRegex(ValueError, "cycle"):
            draw(tree)

    def test_a_feedback_loop_returns_round_the_right_instead_of_being_refused(self):
        tree = {"name": "current_reality", "nodes": [{"id": i, "kind": "cause", "text": i, "status": "accepted"} for i in "abc"],
                "links": [{"id": "ab", "from": ["a"], "to": "b", "relation": "contributes_to", "status": "accepted"},
                          {"id": "bc", "from": ["b"], "to": "c", "relation": "contributes_to", "status": "accepted"},
                          {"id": "ca", "from": ["c"], "to": "a", "relation": "feeds_back_to", "status": "accepted"}]}
        pieces, shapes, loose, svg = draw(tree)
        shape = shapes[0]
        loop = next(p for p in shape["paths"] if p["link"]["id"] == "ca")
        right = max(n["x"] + n["w"] for n in shape["nodes"].values())
        self.assertGreater(max(x for x, y in loop["points"]), right)  # Round the side, never through the boxes.
        self.assertLessEqual(max(x for x, y in loop["points"]), shape["w"])
        self.assertEqual(loop["points"][0][1], shape["nodes"]["c"]["y"])  # Leaves the top of its source,
        self.assertEqual(loop["points"][-1][1], shape["nodes"]["a"]["y"])  # and enters the top of its target.
        self.assertIn("feeds back", svg)
        self.assertEqual(svg.count('class="e-head"'), 3)

    def test_a_remedy_ends_in_a_bar_not_an_arrow(self):
        tree = {"name": "future_reality", "nodes": [{"id": "risk", "kind": "undesirable_effect", "text": "A risk.", "status": "proposed"},
                                                     {"id": "fix", "kind": "injection", "text": "A remedy.", "status": "proposed"}],
                "links": [{"id": "stop", "from": ["fix"], "to": "risk", "relation": "prevents", "status": "proposed"}]}
        pieces, shapes, loose, svg = draw(tree)
        self.assertEqual((svg.count('class="e-bar"'), svg.count('class="e-head"')), (1, 0))
        self.assertIn("is meant to prevent", svg)
        self.assertLess(shapes[0]["nodes"]["risk"]["y"], shapes[0]["nodes"]["fix"]["y"])

    def test_wrapping_never_exceeds_the_box(self):
        for line in diagrams.wrap("Supercalifragilisticexpialidocious-and-then-some " * 3, 120):
            self.assertLessEqual(diagrams.text_width(line, diagrams.TEXT_SIZE, diagrams.TEXT_WEIGHT), 120)


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site, cls.commons = build.load_site()
        cls.outputs = build.build_files(cls.site, cls.commons)
        cls.by_kind = {c["entry"]["kind"]: c for c in cls.commons}
        cls.real, cls.example = cls.by_kind["real"], cls.by_kind["example"]

    def trees(self):
        for c in self.commons:
            for name, tree in build.normalize(c)["trees"].items():
                yield c, name, tree

    def test_outputs_are_exactly_the_approved_files(self):
        pages_ = ["index", "map", "goal", "in-the-way", "conflict", "change", "prerequisites", "actions", "items", "changes", "about"]
        fonts = ["alegreya-sans-400.woff2", "alegreya-sans-500.woff2", "alegreya-sans-700.woff2", "alegreya-sans-400-italic.woff2", "OFL.txt"]
        expected = {"index.html", "how-it-works.html", "styles.css", "app.js", "reasoning.json", *(f"fonts/{f}" for f in fonts),
                    *(f"reason-commons/{p}.html" for p in pages_), "reason-commons/reasoning.json",
                    *(f"example-willow-lane/{p}.html" for p in pages_ + ["questions", "learning"]), "example-willow-lane/reasoning.json",
                    *(f"gandhi-2-0/{p}.html" for p in pages_ + ["questions"]), "gandhi-2-0/reasoning.json",
                    *(f"re-membering/{p}.html" for p in pages_ + ["questions"]), "re-membering/reasoning.json",
                    *(f"wisdom-ai/{p}.html" for p in ["index", "map", "goal", "in-the-way", "conflict", "change", "prerequisites", "actions", "items", "questions", "changes", "about"]), "wisdom-ai/reasoning.json",
                    *(f"persistent-systems/{p}.html" for p in pages_ + ["questions"]), "persistent-systems/reasoning.json",
                    *(f"prosocial-ai/{p}.html" for p in pages_ + ["questions"]), "prosocial-ai/reasoning.json"}
        self.assertEqual(set(self.outputs), expected)

    def test_our_reviewed_snapshot_is_unchanged(self):
        data = self.real["data"]
        count = lambda key, status: sum(1 for t in data["trees"].values() for i in t[key] if i["status"] == status)
        self.assertEqual((count("nodes", "accepted"), count("links", "accepted")), (63, 57))
        self.assertEqual((count("nodes", "proposed"), count("links", "proposed")), (62, 39))
        self.assertEqual(set(data["trees"]), set(pages.TREE_ORDER))
        self.assertEqual(data["release_id"], "2026-10-26.2")
        self.assertEqual(json.loads(self.outputs["reasoning.json"]), data)
        self.assertEqual(json.loads(self.outputs["reason-commons/reasoning.json"]), data)
    def test_snapshot_tampering_fails(self):
        registry = deepcopy(self.real["registry"])
        registry["snapshot"]["trees"]["goal"]["nodes"][0]["text"] = "A changed statement."
        build.validate_projection(registry["snapshot"], registry)
        self.assertNotEqual(build.digest(registry["snapshot"]), registry["snapshot_sha256"])

    def test_every_published_link_is_drawn_once_and_nothing_else(self):
        for c, name, tree in self.trees():
            pieces, loose = diagrams.components(tree)
            label = lambda kind, name=name: pages.kind_label(name, kind)
            svg = "".join(diagrams.svg(diagrams.geometry(tree, p["ids"], p["links"], label), {n["id"]: n for n in tree["nodes"]}, lambda i: i, name) for p in pieces)
            drawn = set(re.findall(r'<a class="e [^"]*" href="[^"]*" data-id="([^"]+)"', svg))
            self.assertEqual(drawn, {l["id"] for l in tree["links"]}, (c["entry"]["slug"], name))
            heads = sum(1 for l in tree["links"] if l["relation"] != "conflicts_with" and l["relation"] not in diagrams.BARRED)
            self.assertEqual(svg.count('class="e-head"'), heads, (c["entry"]["slug"], name))
            self.assertEqual(svg.count('class="e-bar"'), sum(l["relation"] in diagrams.BARRED for l in tree["links"]), (c["entry"]["slug"], name))
            self.assertEqual(svg.count('<a class="j '), sum(len(l["from"]) > 1 for l in tree["links"]), (c["entry"]["slug"], name))
            self.assertEqual(set(loose) | {i for p in pieces for i in p["ids"]}, {n["id"] for n in tree["nodes"]})

    def test_our_change_draws_only_its_published_proposed_connection(self):
        page = self.outputs["reason-commons/change.html"]
        self.assertIn('data-id="fr2-l-ai-spread"', page)
        self.assertEqual(page.count('data-id="fr2-l-'), 1)  # Accepted links from a change reach unpublished effects, so none is drawn.
    def test_boxes_never_overlap_and_text_fits(self):
        for c, name, tree in self.trees():
            label = lambda kind, name=name: pages.kind_label(name, kind)
            pieces, loose = diagrams.components(tree)
            shapes = [diagrams.geometry(tree, p["ids"], p["links"], label) for p in pieces]
            if tree["nodes"] and not tree["links"] and name == "conflict":
                shapes.append(diagrams.geometry(tree, [n["id"] for n in tree["nodes"]], [], label))
            for shape in shapes:
                boxes = list(shape["nodes"].values())
                for i, a in enumerate(boxes):
                    for line in a["lines"]:
                        self.assertLessEqual(diagrams.text_width(line, diagrams.TEXT_SIZE, diagrams.TEXT_WEIGHT), a["w"] - 2 * diagrams.PAD_X)
                    self.assertGreaterEqual(a["x"], 0)
                    self.assertLessEqual(a["x"] + a["w"], shape["w"])
                    for b in boxes[i + 1:]:
                        apart = a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"] or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"]
                        self.assertTrue(apart, (c["entry"]["slug"], name))

    def test_every_goal_tree_reads_top_to_bottom_and_nothing_else_does(self):
        for c, name, tree in self.trees():
            label = lambda kind, name=name: pages.kind_label(name, kind)
            for piece in diagrams.components(tree)[0]:
                shape = diagrams.geometry(tree, piece["ids"], piece["links"], label)
                where = (c["entry"]["slug"], name)
                self.assertEqual(bool(shape.get("hierarchy")), name == "goal", where)
                if not shape.get("hierarchy"):
                    continue
                self.assertLessEqual(shape["w"], 680, where)
                rows = list(shape["nodes"].values())
                self.assertEqual([r["y"] for r in rows], sorted(r["y"] for r in rows), where)  # Reading order is drawing order.
                for row in rows:
                    if row["parent"]:
                        parent = shape["nodes"][row["parent"]]
                        self.assertGreater(row["y"], parent["y"], where)
                        self.assertEqual(row["x"] - parent["x"], diagrams.INDENT, where)
                kids = Counter(r["parent"] for r in rows if r["parent"])
                self.assertEqual({i: r.get("kids", 0) for i, r in shape["nodes"].items()}, {i: kids.get(i, 0) for i in shape["nodes"]}, where)

    def test_only_indented_trees_offer_stepping_through(self):
        for name, page in self.outputs.items():
            if not name.endswith(".html"):
                continue
            hierarchies = len(re.findall(r'<svg class="rc-diagram[^>]* data-hierarchy', page))
            self.assertEqual(page.count('<div class="step-bar" hidden>'), hierarchies, name)
            if name.endswith("/goal.html"):
                self.assertEqual(hierarchies, 1, name)
            if name.endswith(("/in-the-way.html", "/conflict.html", "/change.html", "/items.html")):
                self.assertEqual(hierarchies, 0, name)
        page = self.outputs["reason-commons/goal.html"]
        self.assertIn('data-kids="5"', page)
        self.assertIn(">5 success factors</text>", page)

    def test_cloud_places_each_position_beside_the_need_it_serves(self):
        tree = build.normalize(self.example)["trees"]["conflict"]
        shape = diagrams.geometry(tree, [n["id"] for n in tree["nodes"]], tree["links"], lambda k: k)
        middle = lambda i: shape["nodes"][i]["y"] + shape["nodes"][i]["h"] / 2
        self.assertAlmostEqual(middle("wl-c-close"), middle("wl-c-need-safe"), delta=12)
        self.assertAlmostEqual(middle("wl-c-keep-open"), middle("wl-c-need-trade"), delta=12)

    def test_every_example_page_is_labelled_fictional_and_ours_never_is(self):
        for name, value in self.outputs.items():
            if not name.endswith(".html"):
                continue
            if name.startswith("example-willow-lane/"):
                self.assertIn('class="example-banner"', value, name)
                self.assertIn("Fictional example", value, name)
            elif name.startswith("reason-commons/"):
                self.assertNotIn("example-banner", value, name)
                self.assertNotIn("Willow Lane", value, name)
        self.assertTrue(json.loads(self.outputs["example-willow-lane/reasoning.json"])["is_example"])

    def test_every_item_is_readable_without_script(self):
        for c in self.commons:
            page = self.outputs[f'{c["entry"]["slug"]}/items.html']
            for tree in c["data"]["trees"].values():
                for item in tree["nodes"] + tree["links"]:
                    self.assertIn(f' id="{item["id"]}"', page)  # Not a diagram's data-id.
                    if "text" in item:
                        self.assertIn(build.esc(item["text"]), page)
        self.assertIn("Original contributor not identified", self.outputs["reason-commons/items.html"])

    def test_prior_endorsement_of_a_disputed_item_is_not_current_acceptance(self):
        # No published item is disputed today; a disputed item in our commons keeps earlier acceptance as history only.
        normalized = deepcopy(build.normalize(self.real))
        item = next(n for n in normalized["trees"]["goal"]["nodes"] if n["status"] == "accepted")
        item["status"] = "disputed"
        c = pages.Commons(normalized)
        detail = pages.item_detail(c, item["id"], self.site)
        facts = detail[detail.index('class="item-facts"'):detail.index("</aside>")]
        self.assertIn("Disputed; earlier accepted by", facts)
        self.assertNotIn("Accepted for now by", facts)
    def test_learning_keeps_awaiting_unclear_and_not_assessed_apart(self):
        page = self.outputs["example-willow-lane/learning.html"]
        for word in ("Awaiting report", "Unclear", "Not assessed", "Not observed", "Observed"):
            self.assertIn(word, page)
        self.assertIn("Still to report: Amara", page)

    def test_internal_links_and_anchors_resolve(self):
        class Collect(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links, self.ids = [], set()

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if attrs.get("id"):
                    self.ids.add(attrs["id"])
                if attrs.get("href"):
                    self.links.append(attrs["href"])
        parsed = {}
        for name, value in self.outputs.items():
            if name.endswith(".html"):
                parsed[name] = Collect()
                parsed[name].feed(value)
        for name, page in parsed.items():
            for href in page.links:
                url = urlparse(href)
                if url.scheme or href.startswith("/"):
                    continue  # Site-wide routes are checked by scripts/check-website.py.
                target = urljoin(name, url.path) if url.path else name
                self.assertTrue(target in self.outputs, (name, href))
                if url.fragment and target.endswith(".html"):
                    self.assertIn(url.fragment, parsed[target].ids, (name, href))

    def test_legacy_query_routes_redirect_to_the_new_pages(self):
        home = self.outputs["index.html"]
        for fragment in ("q.get('view')", "q.get('item')", "items.html#", "about.html", "location.replace"):
            self.assertIn(fragment, home)

    def test_public_artifacts_exclude_internal_state_and_mock_content(self):
        text = "\n".join(v for v in self.outputs.values() if isinstance(v, str))
        prose = re.sub(r"<svg\b.*?</svg>", "", text, flags=re.S)  # Diagram coordinates can contain any run of digits.
        for forbidden in ("1,284", "2,390"):
            self.assertNotIn(forbidden, prose)
        for forbidden in ("Calder", "change_acceptances", "feedback_requests", "/Users/", "driver_default", "funding/research/", "r-e-rufus-feedback-hard"):
            self.assertNotIn(forbidden, text)

    def test_our_commons_shows_proposed_funding_but_keeps_accepted_funding_out(self):
        # demo-v2-collab-source r2 left accepted funding and internal-collaboration items out; proposed-reasoning-public r1
        # publishes every proposed item, funding included, without endorsers.
        items = [i for t in self.real["data"]["trees"].values() for i in t["nodes"] + t["links"]]
        ids = {i["id"] for i in items}
        for excluded in ("g2-csf-resourced", "g2-nc-7-1", "cr2-ude-no-funding", "cr2-c-spare-time", "fr2-inj-funding",
                         "fr2-inj-g1-outward-owner", "fr2-eff-stage1-sessions", "cr2-l-shared-model-choices", "fr2-l-stage1-ai"):
            self.assertNotIn(excluded, ids)
        self.assertFalse(any(i.startswith("cf2-fund") for i in ids))
        funding = [i for i in items if re.search(r"Foresight|grant|Prototype Fund|priced", i.get("text", ""))]
        self.assertTrue(funding)
        self.assertTrue(all(i["status"] == "proposed" and not i["accepted_by"] for i in funding))
    def test_every_commons_counts_statements_and_connections_apart_and_explains_its_colours(self):
        for c in self.commons:
            normalized = build.normalize(c)
            statements = sum(len(t["nodes"]) for t in normalized["trees"].values())
            connections = sum(len(t["links"]) for t in normalized["trees"].values())
            for page in ("index", "map", "items"):
                self.assertIn(f'Statements <span>{statements} · {connections}</span>', self.outputs[f'{c["entry"]["slug"]}/{page}.html'])
            self.assertIn('class="legend legend-roles"', self.outputs[f'{c["entry"]["slug"]}/map.html'])


class ExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        site, commons = build.load_site()
        cls.entry, cls.registry, cls.data = next((c["entry"], c["registry"], c["data"]) for c in commons if c["entry"]["kind"] == "example")
        cls.real_ids = {i["id"] for c in commons if c["entry"]["kind"] == "real" for t in c["data"]["trees"].values() for i in t["nodes"] + t["links"]}

    @unittest.skipUnless(HAVE_YAML, "PyYAML is needed to read the example's working file")
    def test_working_file_passes_the_skill_validator_and_matches_the_snapshot(self):
        module = build.skill_helpers()
        state = module.load(build.HERE / self.entry["source"])
        module.validate(state)
        self.assertEqual(build.project_v2(state, self.registry), self.data)

    def test_example_is_entirely_proposed_and_keeps_its_qualifications(self):
        items = [i for t in self.data["trees"].values() for i in t["nodes"] + t["links"]]
        self.assertEqual({i["status"] for i in items}, {"proposed"})
        self.assertFalse(any(i["accepted_by"] for i in items))
        self.assertTrue(any(i.get("assumptions") for i in items) and any(i.get("challenges") for i in items))
        self.assertTrue(any(len(i.get("from", [])) > 1 for i in items))
        self.assertTrue(all(t["links"] for t in self.data["trees"].values()))
        self.assertEqual(len(self.data["history"]), 3)
        self.assertFalse({c["type"] for h in self.data["history"] for c in h["changes"]} & {"accepted", "disputed"})
        self.assertEqual(len(self.data["feedback"][0]["reports"]), 3)  # A trial needs no acceptance of the reasoning.
    def test_example_ids_never_collide_with_ours(self):
        ids = {i["id"] for t in self.data["trees"].values() for i in t["nodes"] + t["links"]}
        self.assertFalse(ids & self.real_ids)
        self.assertTrue(all(i.startswith("wl-") for i in ids))

    def test_only_our_commons_may_publish_acceptance(self):
        for standing, endorsers in (("accepted", ["Amara"]), ("disputed", [])):
            data = deepcopy(self.data)
            node = data["trees"]["goal"]["nodes"][0]
            node.update(status=standing, accepted_by=endorsers)
            with self.assertRaisesRegex(ValueError, "Only the Reason Commons commons"):
                build.validate_v2(data, self.registry)
        data = deepcopy(self.data)
        data["feedback"][0]["about"]["standing"] = "accepted"
        with self.assertRaisesRegex(ValueError, "accepted feedback statement"):
            build.validate_v2(data, self.registry)
    def test_history_cannot_mention_unpublished_material(self):
        data = deepcopy(self.data)
        data["history"][0]["changes"][0]["refs"].append("wl-not-published")
        with self.assertRaisesRegex(ValueError, "unpublished"):
            build.validate_v2(data, self.registry)

    def test_projection_two_is_reserved_for_the_labelled_example(self):
        registry = deepcopy(self.registry)
        registry["is_example"] = False
        with self.assertRaisesRegex(ValueError, "fictional example"):
            build.validate_v2(self.data, registry)


class ReconstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site, cls.commons = build.load_site()
        cls.record = next(c for c in cls.commons if c["entry"]["kind"] == "reconstruction")
        cls.registry, cls.data = cls.record["registry"], cls.record["data"]
        cls.outputs = build.build_files(cls.site, cls.commons)

    @unittest.skipUnless(HAVE_YAML, "PyYAML is needed for the public working file")
    def test_public_working_file_validates_and_matches_exactly(self):
        helper = build.skill_helpers()
        state = helper.load(build.HERE / self.record["entry"]["source"])
        helper.validate(state)
        self.assertEqual(build.project_reconstruction(state, self.registry), self.data)
        self.assertEqual(sum(len(t["nodes"]) for t in self.data["trees"].values()), 241)
        self.assertEqual(sum(len(t["links"]) for t in self.data["trees"].values()), 246)

    def test_existing_reviewed_snapshots_remain_byte_for_byte_the_same(self):
        expected = {"real": "7e657a452c2b5840c2168188ba1e139c46f8fcb5f8ee9e89ac74687cbe88de75",  # proposed-reasoning-public r1
                    "example": "02820685f155a154bcfeb8a35e71ce18771a6b31e6410afaf7ded14a4a30eef4"}
        for record in self.commons:
            if record["entry"]["kind"] in expected:
                self.assertEqual(build.digest(record["data"]), expected[record["entry"]["kind"]])

    def test_reconstruction_cannot_imply_endorsement_or_direct_human_authorship(self):
        for change, expected in [({"status": "accepted", "accepted_by": ["David Joseph"]}, "remain proposed"),
                                 ({"contributors": [{"name": "David Joseph", "role": "human"}]}, "participant authorship")]:
            data = deepcopy(self.data)
            data["trees"]["goal"]["nodes"][0].update(change)
            with self.assertRaisesRegex(ValueError, expected):
                build.validate_reconstruction(data, self.registry)

    def test_every_item_requires_a_known_source_and_an_explicit_basis(self):
        for refs in [[], [{"source_id": "invented", "locator": "p. 2", "basis": "reconstruction"}],
                     [{"source_id": "analysis-v2", "locator": "", "basis": "inference"}],
                     [{"source_id": "analysis-v2", "locator": "p. 2", "basis": "verified"}]]:
            data = deepcopy(self.data)
            data["trees"]["goal"]["nodes"][0]["source_refs"] = refs
            with self.assertRaisesRegex(ValueError, "source locator"):
                build.validate_reconstruction(data, self.registry)

    def test_feedback_and_earlier_endorsement_cannot_be_invented(self):
        data = deepcopy(self.data)
        data["feedback"] = [{"reports": [{"text": "It worked"}]}]
        with self.assertRaisesRegex(ValueError, "feedback commitments or reports"):
            build.validate_reconstruction(data, self.registry)
        data = deepcopy(self.data)
        data["history"][0]["changes"][0]["type"] = "accepted"
        with self.assertRaisesRegex(ValueError, "prior endorsement or results"):
            build.validate_reconstruction(data, self.registry)

    @unittest.skipUnless(HAVE_YAML, "PyYAML is needed for the public working file")
    def test_only_selected_public_fields_cross_the_reconstruction_boundary(self):
        state = build.skill_helpers().load(build.HERE / self.record["entry"]["source"])
        state["change_acceptances"] = [{"source_text": "PRIVATE_CANARY"}]
        for tree in state["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                item.update(private_note="PRIVATE_CANARY", source={"path": "/PRIVATE_CANARY"})
                item["contributions"][0]["note"] = "PRIVATE_CANARY"
        self.assertNotIn("PRIVATE_CANARY", json.dumps(build.project_reconstruction(state, self.registry)))
        data = deepcopy(self.data)
        data["trees"]["goal"]["nodes"][0]["source"] = {"path": "/PRIVATE_CANARY"}
        with self.assertRaisesRegex(ValueError, "Unreviewed public fields"):
            build.validate_reconstruction(data, self.registry)

    def test_every_reconstruction_page_is_labelled_and_sources_are_inspectable(self):
        for name, value in self.outputs.items():
            if name.startswith("gandhi-2-0/") and name.endswith(".html"):
                self.assertIn('class="reconstruction-banner"', value, name)
                self.assertIn("Everything here is proposed", value, name)
                self.assertIn("None of the discussion’s participants has endorsed it", value, name)
                self.assertNotIn("Fictional example", value, name)
        items = self.outputs["gandhi-2-0/items.html"]
        forum = next(s for s in self.data["sources"] if "posts" in s)
        for tree in self.data["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                for ref in item["source_refs"]:  # A forum credit links its post; anything else names its locator.
                    self.assertIn(pages.esc(f'{forum["url"]}/{ref["post"]}') if "post" in ref else pages.esc(ref["locator"]), items)
        for source in self.data["sources"]:
            self.assertIn(f'id="source-{source["id"]}"', self.outputs["gandhi-2-0/about.html"])
        self.assertIn("Inferred by the AI", items)
        self.assertIn("Paraphrased by the AI from this post", items)

    def test_overview_and_briefs_keep_the_trial_and_participation_provisional(self):
        overview = self.outputs["gandhi-2-0/index.html"]
        for wording in ("First step · Unassigned", "No trial is recorded here", "What would change our minds?", "suppress"):
            self.assertIn(wording, overview)
        self.assertNotIn("The change chosen", overview)
        c = pages.Commons(build.normalize(self.record))
        for ident in c.order:
            brief = pages.brief(c, ident, self.site)
            self.assertIn("Sources:", brief)
            self.assertIn("participants have not endorsed", brief)
            self.assertIn("Copying this brief submits nothing", brief)
        self.assertNotIn("gandhi-2-0/learning.html", self.outputs)

    def test_source_text_is_escaped_and_does_not_execute_markup(self):
        registry = deepcopy(self.registry)
        data = deepcopy(self.data)
        payload = '<img src=x onerror="alert(1)">'
        data["sources"][0]["title"] = payload
        registry["sources"][0]["title"] = payload
        data["trees"]["goal"]["nodes"][0]["source_refs"][-1]["locator"] = payload  # The analysis locator, after the forum credits.
        build.validate_reconstruction(data, registry)
        c = pages.Commons(build.normalize({**self.record, "data": data, "registry": registry}))
        for rendered in (pages.about_page(c, self.site), pages.items_page(c, self.site)):
            self.assertNotIn(payload, rendered)
            self.assertIn(pages.esc(payload), rendered)

    def test_goal_items_are_success_factors_and_selection_conditions_sit_under_the_fifth(self):
        goal = self.data["trees"]["goal"]
        kinds = {n["id"]: n["kind"] for n in goal["nodes"]}
        self.assertEqual(sorted(i for i, k in kinds.items() if k == "critical_success_factor"),
                         sorted(["g2-g-future", "g2-g-g2", "g2-g-capability", "g2-g-control", "g2-g-g5", "g2-g-g6"]))
        under_g5 = {l["from"][0] for l in goal["links"] if l["to"] == "g2-g-g5"}
        self.assertEqual(under_g5, {"g2-g-g5-between", "g2-g-g5-within"})
        self.assertTrue(all(kinds[i] == "necessary_condition" for i in under_g5))
        self.assertIn("Success factor", self.outputs["gandhi-2-0/goal.html"])

    def test_conflict_outline_names_the_conflict_instead_of_implying_a_sequence(self):
        clashes = [l["id"] for l in self.data["trees"]["conflict"]["links"] if l["relation"] == "conflicts_with"]
        self.assertEqual(len(clashes), 6)
        for file, expected in (("gandhi-2-0/index.html", clashes[:1]), ("gandhi-2-0/conflict.html", clashes)):
            self.assertNotIn('class="o-then">then', self.outputs[file])
            for ident in expected:
                self.assertIn(f'href="items.html#{ident}">conflicts with</a>', self.outputs[file])

    def broken(self, change, registry_too=False):
        """Validate a copy of the release after one change, expecting refusal."""
        data, registry = deepcopy(self.data), deepcopy(self.registry)
        change(data)
        if registry_too:
            change(registry)
        return lambda: build.validate_reconstruction(data, registry)

    def ref(self, data, ident, source_id):
        item = next(i for t in data["trees"].values() for i in t["nodes"] + t["links"] if i["id"] == ident)
        return next(r for r in item["source_refs"] if r["source_id"] == source_id)

    def test_a_credit_must_name_the_author_of_the_cited_post(self):
        self.assertEqual(self.ref(self.data, "g2-c-optional", "forum"), {"source_id": "forum", "post": 30, "author": "robert", "basis": "paraphrase"})
        swap = self.broken(lambda d: self.ref(d, "g2-c-optional", "forum").update(author="leif"))
        self.assertRaisesRegex(ValueError, "author of post 30", swap)

    def test_credits_need_a_real_post_or_locator_and_a_basis_that_fits_the_source(self):
        for change in (lambda r: r.update(post=99), lambda r: r.update(post="30"), lambda r: r.update(basis="cited"),
                       lambda r: r.update(quote="Words lifted from the post"), lambda r: r.pop("author")):
            check = self.broken(lambda d, change=change: change(self.ref(d, "g2-c-optional", "forum")))
            self.assertRaisesRegex(ValueError, "source locator", check)
        essay = self.broken(lambda d: self.ref(d, "g2-c-k5-objective", "last-first").update(basis="paraphrase"))
        self.assertRaisesRegex(ValueError, "source locator", essay)

    def test_a_document_must_be_shared_in_a_post_by_its_author(self):
        def move(record):
            next(s for s in record["sources"] if s["id"] == "paradox")["shared_in_post"] = 30  # Robert's post.
        self.assertRaisesRegex(ValueError, "shared in a post by its author", self.broken(move, registry_too=True))

    def test_views_cover_every_statement(self):
        def lose(record):
            del record["views"]["conflict"][4]
        self.assertRaisesRegex(ValueError, "must appear in a view", self.broken(lose, registry_too=True))
        def invent(record):
            record["views"]["prerequisite"][0]["nodes"].append("g2-p-not-published")
        self.assertRaisesRegex(ValueError, "names unpublished statements", self.broken(invent, registry_too=True))
        self.assertEqual(set(self.data["views"]), set(self.data["trees"]) - {"goal"})

    def test_every_part_draws_each_connection_with_all_its_sources(self):
        for name, tree in self.data["trees"].items():
            if name not in self.data["views"]:
                continue
            page = self.outputs[f'gandhi-2-0/{pages.TREES[name]["slug"]}.html']
            if name in ("prerequisite", "transition"):  # Plans have one view, not parts; each connection carries its id.
                shown = set(re.findall(r'data-link="([^"]+)"', page)) | set(re.findall(r'data-id="([^"]+)"', page))
                self.assertLessEqual({l["id"] for l in tree["links"]}, shown, name)
                continue
            drawn = set()
            for section in re.findall(r'<section class="tv".*?</section>', page, flags=re.S):
                svg = re.search(r'<svg class="rc-diagram.*?</svg>', section, flags=re.S).group(0)
                nodes = set(re.findall(r'<a class="n [^"]*" href="[^"]*" data-id="([^"]+)"', svg))
                for ident, ends in re.findall(r'<a class="e[^"]*" href="[^"]*" data-id="([^"]+)" data-ends="([^"]+)"', svg):
                    self.assertLessEqual(set(ends.split()), nodes, ident)  # A joint condition is never split across parts.
                    drawn.add(ident)
            self.assertEqual(drawn, {l["id"] for l in tree["links"]}, name)
        c = pages.Commons(build.normalize(self.record))
        for name, views in c.views.items():
            tree = c.trees[name]
            for view in views:
                links, context = diagrams.view_context(tree, set(view["nodes"]))
                shape = diagrams.geometry(tree, view["nodes"] + context, links, lambda k: pages.kind_label(name, k))
                boxes = list(shape["nodes"].values())
                for i, a in enumerate(boxes):
                    self.assertLessEqual(a["x"] + a["w"], shape["w"], view["id"])
                    for b in boxes[i + 1:]:
                        self.assertTrue(a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"] or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"], view["id"])
                self.assertTrue(all(x <= shape["w"] and y <= shape["h"] for p in shape["paths"] for x, y in p["points"]), view["id"])

    def test_loops_close_only_through_the_three_feedback_links(self):
        loops, closing = [], []
        for name, tree in self.data["trees"].items():
            onward = defaultdict(set)
            for link in tree["links"]:
                if link["relation"] in diagrams.FEEDBACK:
                    loops.append(link)
                elif link["relation"] not in diagrams.LATERAL:
                    for source in link["from"]:
                        lower, upper = (link["to"], source) if link["relation"] in diagrams.DOWNWARD else (source, link["to"])
                        onward[lower].add(upper)

            def reaches(start, goal):
                seen, stack = set(), [start]
                while stack:
                    current = stack.pop()
                    if current == goal:
                        return True
                    if current not in seen:
                        seen.add(current)
                        stack.extend(onward[current])
                return False
            for node in tree["nodes"]:  # Without the feedback links, nothing leads back to itself.
                self.assertFalse(any(reaches(upper, node["id"]) for upper in onward[node["id"]]), node["id"])
            # A loop closes when its target leads back to a source; a joint loop's other sources are conditions from outside it.
            closing += [l["id"] for l in tree["links"] if l["relation"] in diagrams.FEEDBACK and any(reaches(l["to"], s) for s in l["from"])]
        self.assertEqual([l["id"] for l in loops], ["g2-r-rel-r15", "g2-r-rel-r23", "g2-f-rel-f16"])
        # R15 is the analysis's own "mission drift reinforces normalisation": labelled feedback that closes no published chain.
        self.assertEqual(closing, ["g2-r-rel-r23", "g2-f-rel-f16"])
        c = pages.Commons(build.normalize(self.record))
        tree = c.trees["future_reality"]
        view = next(v for v in c.views["future_reality"] if v["id"] == "trust-capacity-selection")
        links, context = diagrams.view_context(tree, set(view["nodes"]))
        shape = diagrams.geometry(tree, view["nodes"] + context, links, lambda k: pages.kind_label("future_reality", k))
        joint = [p for p in shape["paths"] if p["link"]["id"] == "g2-f-rel-f16"]
        self.assertEqual((len(joint), sum(p["arrow"] for p in joint)), (3, 1))  # Two sources meet at one "and", then one arrow.
        self.assertEqual([j["link"]["id"] for j in shape["joins"]].count("g2-f-rel-f16"), 1)
        right = max(n["x"] + n["w"] for n in shape["nodes"].values())
        self.assertTrue(all(max(x for x, y in p["points"]) > right for p in joint))
        self.assertEqual(next(p for p in joint if p["arrow"])["points"][-1][1], shape["nodes"]["g2-f-e10"]["y"])
        page = self.outputs["gandhi-2-0/change.html"]
        self.assertIn('class="e-tag e-tag-loop"', page)
        self.assertIn("↺", page)  # The outline names the loop beside its source.

    def test_every_remedy_ends_in_a_bar_at_its_own_risk(self):
        tree = self.data["trees"]["future_reality"]
        kinds = {n["id"]: n["kind"] for n in tree["nodes"]}
        remedies = [l for l in tree["links"] if l["relation"] in diagrams.BARRED]
        self.assertEqual((len(remedies), len({l["to"] for l in remedies})), (15, 15))
        for link in remedies:
            self.assertEqual(([kinds[s] for s in link["from"]], kinds[link["to"]]), (["injection"], "undesirable_effect"), link["id"])
        page = self.outputs["gandhi-2-0/change.html"]
        self.assertEqual(set(re.findall(r'<a class="e e-prevent" href="[^"]*" data-id="([^"]+)"', page)), {l["id"] for l in remedies})
        self.assertIn("is meant to prevent", page)

    def test_the_overview_path_uses_only_published_links_and_references(self):
        overview = self.outputs["gandhi-2-0/index.html"]
        spine = next(b for b in self.data["overview"] if b["type"] == "spine")
        self.assertEqual(overview.count('class="sp-row"'), len(spine["hops"]))
        for hop in spine["hops"]:
            self.assertIn(f'href="items.html#{hop["to"]}"', overview)
        guidance = next(n for n in self.data["trees"]["future_reality"]["nodes"] if n["id"] == "g2-f-guidance")
        self.assertNotIn("g2-r-u01", guidance["addresses"])
        def unreferenced(record):
            next(b for b in record["overview"] if b["type"] == "spine")["hops"][0]["to"] = "g2-r-u01"
        self.assertRaisesRegex(ValueError, "No published reference", self.broken(unreferenced, registry_too=True))
        def across(record):
            next(b for b in record["overview"] if b["type"] == "spine")["hops"][2]["to"] = "g2-p-case"
        self.assertRaisesRegex(ValueError, "No published path", self.broken(across, registry_too=True))
        dangling = self.broken(lambda d: next(n for t in d["trees"].values() for n in t["nodes"] if n["id"] == "g2-f-guidance")["addresses"].append("g2-r-missing"))
        self.assertRaisesRegex(ValueError, "Unpublished trace", dangling)
        self.assertIn("<dt>Meant to address</dt>", self.outputs["gandhi-2-0/items.html"])
        self.assertIn("is meant to address", self.outputs["gandhi-2-0/change.html"])  # Each part lists its links beyond the part.

    def test_a_removed_connection_stays_in_history_and_is_never_published(self):
        gone = self.data["retired"][0]
        changes = self.outputs["gandhi-2-0/changes.html"]
        self.assertIn(pages.esc(gone["text"]), changes)
        self.assertIn("No longer published", changes)
        for name, value in self.outputs.items():
            if name.startswith("gandhi-2-0/") and name.endswith(".html"):
                self.assertNotIn(f'#{gone["id"]}"', value, name)
        revive = self.broken(lambda r: r["retired"].append(dict(gone, id="g2-f-guidance")), registry_too=True)
        self.assertRaisesRegex(ValueError, "retired item cannot be published", revive)
        unretired = self.broken(lambda d: d["history"][-1]["changes"].append({"type": "removed", "refs": ["g2-f-guidance"]}))
        self.assertRaisesRegex(ValueError, "Only retired items", unretired)

    def test_each_action_shows_an_unassigned_owner_and_its_proposed_role(self):
        actions = [n for n in self.data["trees"]["transition"]["nodes"] if n["kind"] == "action"]
        self.assertEqual(len(actions), 8)
        page = self.outputs["gandhi-2-0/actions.html"]
        for action in actions:
            self.assertIn(pages.esc(f'Who: unassigned · proposed role: {action["proposed_role"]}'), page)
        self.assertIn("<dt>Proposed role</dt>", self.outputs["gandhi-2-0/items.html"])
        assigned = self.broken(lambda d: d["trees"]["goal"]["nodes"][0].update(proposed_role="Someone"))
        self.assertRaisesRegex(ValueError, "Only an action can carry a proposed role", assigned)

    def test_one_banner_replaces_each_items_standing_in_this_commons_only(self):
        for path in ("gandhi-2-0/prerequisites.html", "gandhi-2-0/actions.html"):  # Plans keep their one grammar: each card says nobody has accepted it.
            self.assertIn('<span class="pv-none">Not accepted</span>', self.outputs[path])
        for name, value in self.outputs.items():
            if name.startswith("gandhi-2-0/") and name.endswith(".html"):
                self.assertNotIn("chip-proposed", value, name)
                self.assertNotIn('class="n-standing"', value, name)
                self.assertIsNone(re.search(r'class="(?:n|e|card|item-summary card)\b[^"]*is-proposed', value), name)
        self.assertIn("chip-proposed", self.outputs["example-willow-lane/items.html"])
        self.assertIn("Check at the host", self.outputs["gandhi-2-0/questions.html"])

    def test_all_six_conflicts_draw_as_clouds_with_credit_lines_that_fit(self):
        c = pages.Commons(build.normalize(self.record))
        tree = c.trees["conflict"]
        for view in c.views["conflict"]:
            nodes = {n["id"]: n for n in tree["nodes"] if n["id"] in view["nodes"]}
            links = [l for l in tree["links"] if l["to"] in nodes]
            self.assertIsNotNone(diagrams.cloud_roles(nodes, links), view["id"])
            shape = diagrams.geometry(tree, view["nodes"], links, lambda k: pages.kind_label("conflict", k))
            for placed in shape["nodes"].values():
                self.assertTrue(placed["credit"])
                for line in placed["credit"]:
                    self.assertLessEqual(diagrams.text_width(line, diagrams.CREDIT_SIZE, diagrams.CREDIT_WEIGHT), placed["w"] - 2 * diagrams.PAD_X)
            self.assertIn(f'id="view-{view["id"]}"', self.outputs["gandhi-2-0/conflict.html"])
        page = self.outputs["gandhi-2-0/conflict.html"]
        self.assertEqual(page.count("e-conflict"), 6)
        self.assertIn('class="n-credit"', page)
        self.assertIn("From Robert Bunge", page)

    def test_every_credited_post_is_linked_and_people_are_counted(self):
        forum = next(s for s in self.data["sources"] if "posts" in s)
        cited = {r["post"] for t in self.data["trees"].values() for i in t["nodes"] + t["links"] for r in i["source_refs"] if "post" in r}
        items = self.outputs["gandhi-2-0/items.html"]
        for post in cited:
            self.assertIn(f'href="{forum["url"]}/{post}"', items)
        overview = self.outputs["gandhi-2-0/index.html"]
        self.assertIn('id="credits"', overview)
        for name in ("Leif Eriksson", "Robert Bunge", "Justin", "The supplied analysis alone"):
            self.assertIn(name, overview)  # Justin's collapse thesis arrives with the alternatives.
        self.assertIn(f'href="{forum["url"]}/31"', items)

    def test_conflict_line_is_styled_apart_from_proposed_lines(self):
        css = self.outputs["styles.css"]
        proposed = css.index(".rc-diagram .e.is-proposed .e-line{")
        conflict = css.index(".rc-diagram .e.e-conflict .e-line{stroke:var(--clay)")
        self.assertGreater(conflict, proposed)  # Equal specificity, so the later rule wins.

    def test_release_is_readable_without_a_download_or_script(self):
        about = self.outputs["gandhi-2-0/about.html"]
        self.assertIn('id="release-json"', about)
        self.assertIn(pages.esc(build.normalize(self.record)["json"]), about)
        self.assertIn("Read or copy this release", about)
        self.assertNotIn(" download", about)


class SuppliedDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site, cls.commons = build.load_site()
        cls.record = next(c for c in cls.commons if c["entry"]["slug"] == "re-membering")
        cls.registry, cls.data = cls.record["registry"], cls.record["data"]
        cls.outputs = build.build_files(cls.site, cls.commons)
        cls.normalized = pages.Commons(build.normalize(cls.record))

    @unittest.skipUnless(HAVE_YAML, "PyYAML is needed for the public working file")
    def test_approved_reconstruction_validates_and_matches_snapshot(self):
        helper = build.skill_helpers()
        state = helper.load(build.HERE / self.record["entry"]["source"])
        helper.validate(state)
        self.assertEqual(build.project_reconstruction(state, self.registry), self.data)
        self.assertEqual(sum(len(t["nodes"]) for t in self.data["trees"].values()), 82)
        self.assertEqual(sum(len(t["links"]) for t in self.data["trees"].values()), 66)
        self.assertFalse(self.data["feedback"])
        for tree in self.data["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                self.assertEqual(item["status"], "proposed")
                self.assertEqual(item["accepted_by"], [])
                self.assertEqual(item["contributors"], [build.ASSISTANT])

    def test_direct_document_author_must_exist_without_fabricating_a_forum(self):
        self.assertEqual(len(self.data["sources"]), 5)
        self.assertEqual(set(self.data["authors"]), {"heath"})
        self.assertTrue(all(s["author"] == "heath" for s in self.data["sources"]))
        self.assertTrue(all(s["kind"] == "supplied_document" and "shared_in_post" not in s for s in self.data["sources"]))
        self.assertIsNone(self.normalized.forum)
        data, registry = deepcopy(self.data), deepcopy(self.registry)
        data["sources"][0]["author"] = registry["sources"][0]["author"] = "unknown"
        with self.assertRaisesRegex(ValueError, "Unknown supplied document author"):
            build.validate_reconstruction(data, registry)
        data, registry = deepcopy(self.data), deepcopy(self.registry)
        data["sources"][0]["shared_in_post"] = registry["sources"][0]["shared_in_post"] = 1
        with self.assertRaisesRegex(ValueError, "Invalid source description"):
            build.validate_reconstruction(data, registry)

    def test_a_direct_pdf_cannot_be_mislabeled_as_unread_secondary_citation(self):
        data = deepcopy(self.data)
        data["trees"]["goal"]["nodes"][0]["source_refs"][0]["basis"] = "cited"
        with self.assertRaisesRegex(ValueError, "Invalid source locator"):
            build.validate_reconstruction(data, self.registry)

    def test_pages_and_copyable_briefs_credit_heath_and_pdf_locators(self):
        items = self.outputs["re-membering/items.html"]
        for tree in self.data["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                text = pages.brief(self.normalized, item["id"], self.site)
                self.assertIn("I'm reading Re-membering", text)
                self.assertIn("Margeret Heath", text)
                self.assertIn("Copying this brief submits nothing", text)
                self.assertNotIn("Gandhi", text)
                self.assertNotIn("shared in post", text)
                for ref in item["source_refs"]:
                    self.assertIn(ref["locator"], text)
                    self.assertIn(pages.esc(ref["locator"]), items)
        self.assertIn("Paraphrased by the AI from this supplied document", items)
        self.assertIn("Reconstructed by the AI from the supplied passage", items)
        self.assertNotIn("Reconstructed by the supplied analysis", items)

    def test_every_page_preserves_standing_and_the_correct_origin(self):
        for name, value in self.outputs.items():
            if name.startswith("re-membering/") and name.endswith(".html"):
                self.assertIn("Everything here is proposed", value, name)
                self.assertIn("The source author commented on an earlier map; this revision awaits review and endorsement", value, name)
                for wrong in ("Gandhi", "Second Renaissance Forum", "Fictional example", "shared in post", "Laboratory, Forge"):
                    self.assertNotIn(wrong, value, (name, wrong))
        about = self.outputs["re-membering/about.html"]
        self.assertIn("companion documents, not independent bodies of evidence", about)
        self.assertIn("coupling–constitution", about)
        self.assertIn("cited studies have not been independently checked", about)
        self.assertIn("Margeret Heath is their sole author", about)
        self.assertNotIn("were not supplied", about)
        self.assertEqual({s["id"] for s in self.data["sources"]}, {"slides", "spoken-script", "extended-passages", "glossary", "bibliography"})

    def test_all_six_views_are_populated_without_claiming_an_actual_trial(self):
        for tree, path, counts in (("goal", "goal", (13, 12)), ("current_reality", "in-the-way", (16, 13)),
                                   ("conflict", "conflict", (5, 5)), ("future_reality", "change", (20, 18)),
                                   ("prerequisite", "prerequisites", (13, 12)), ("transition", "actions", (15, 6))):
            data = self.data["trees"][tree]
            self.assertEqual((len(data["nodes"]), len(data["links"])), counts)
            page = self.outputs[f"re-membering/{path}.html"]
            self.assertIn({"prerequisites": 'class="pv-map', "actions": 'class="pv-rows'}.get(path, 'class="rc-diagram'), page)
            self.assertNotIn("Not established yet", page)
        self.assertIn("illustrative, not observations", self.outputs["re-membering/about.html"])
        self.assertIn("Who: unassigned", self.outputs["re-membering/actions.html"])
        self.assertNotIn("Already true", self.outputs["re-membering/actions.html"])
        self.assertIn("Illustrative condition", self.outputs["re-membering/actions.html"])
        self.assertNotIn("re-membering/learning.html", self.outputs)

    def test_parts_preserve_all_connections_and_whole_joint_conditions(self):
        for name, tree in self.data["trees"].items():
            drawn = set()
            for view in self.data["views"][name]:
                links, context = diagrams.view_context(tree, set(view["nodes"]))
                visible = set(view["nodes"]) | set(context)
                for link in links:
                    drawn.add(link["id"])
                    self.assertLessEqual(set(link["from"] + [link["to"]]), visible)
            self.assertEqual(drawn, {link["id"] for link in tree["links"]}, name)

    def test_action_branches_share_readiness_and_close_with_reassessment(self):
        links = {l["id"]: l for l in self.data["trees"]["transition"]["links"]}
        self.assertIn("rm-t-2-effect", links["rm-tl-practice"]["from"])
        self.assertIn("rm-t-2-effect", links["rm-tl-audit"]["from"])
        self.assertNotIn("rm-t-3-effect", links["rm-tl-audit"]["from"])
        self.assertLessEqual({"rm-t-3-effect", "rm-t-4-effect"}, set(links["rm-tl-review"]["from"]))
        self.assertEqual((links["rm-tl-feedback"]["relation"], links["rm-tl-feedback"]["to"]), ("feeds_back_to", "rm-t-map"))
        page = self.outputs["re-membering/actions.html"]
        self.assertIn('data-id="rm-tl-feedback"', page)
        self.assertIn('pv-loop', page)
        self.assertIn("Feeds back into action 1", page)

    def test_reviewed_current_copy_and_history_preserve_their_distinct_scopes(self):
        current = self.outputs["re-membering/index.html"]
        self.assertIn("82 proposed statements and 66 proposed connections", self.outputs["re-membering/about.html"])
        self.assertIn("surveillance", current)
        self.assertIn("in parallel", current)
        self.assertEqual(self.data["history"][0]["release_id"], "2026-10-23.1")
        self.assertIn("18 proposed statements", self.data["history"][0]["summary"])
        self.assertEqual(self.data["release_id"], "2026-10-24.1")
        self.assertEqual(self.data["history"][1]["release_id"], "2026-10-23.2")
        before = {x["refs"][0]: x["before"] for x in self.data["history"][1]["changes"] if "before" in x}
        self.assertEqual(len(before), 5)
        item = next(n for n in self.data["trees"]["goal"]["nodes"] if n["id"] == "rm-g-goal")
        self.assertNotEqual(before["rm-g-goal"], item["text"])

    def test_source_account_precedes_and_is_distinct_from_the_application(self):
        overview = self.outputs["re-membering/index.html"]
        self.assertLess(overview.index('id="source-account"'), overview.index("One possible practical application"))
        self.assertIn('href="about.html#process-account"', overview)
        self.assertIn("AI’s proposed practical application", overview)
        source_ids = set(self.registry["overview"][0]["ids"])
        tree = self.data["trees"]["current_reality"]
        for node in tree["nodes"]:
            if node["id"] in source_ids:
                self.assertEqual(node["kind"], "observation")
                self.assertTrue(node["text"].startswith("Heath"))
        for link in tree["links"]:
            self.assertFalse(source_ids & set(link["from"] + [link["to"]]))
        about = self.outputs["re-membering/about.html"]
        for text in ('id="process-account"', "Following the songline", "Two movements of enmindment",
                     "pp. 7–8", "pp. 19–23", "philosophical starting point"):
            self.assertIn(text, about)

    def test_source_account_cannot_present_a_practical_prediction_as_the_authors_account(self):
        data, registry = deepcopy(self.data), deepcopy(self.registry)
        data["overview"][0]["ids"] = registry["overview"][0]["ids"] = ["rm-f-settle"]
        with self.assertRaisesRegex(ValueError, "attributed observations"):
            build.validate_reconstruction(data, registry)
        data, registry = deepcopy(self.data), deepcopy(self.registry)
        for record in (data, registry):
            record["overview"][0], record["overview"][1] = record["overview"][1], record["overview"][0]
        with self.assertRaisesRegex(ValueError, "source account must come first"):
            build.validate_reconstruction(data, registry)

    def test_reciprocal_process_is_an_unverified_loop_with_harmful_uncertainty_visible(self):
        tree = self.data["trees"]["future_reality"]
        links = {l["id"]: l for l in tree["links"]}
        feedback = links["rm-fl-retuning"]
        self.assertEqual((feedback["from"], feedback["to"], feedback["relation"]),
                         (["rm-f-capacities"], "rm-f-attune", "feeds_back_to"))
        for ident in ("rm-fl-coordination", "rm-fl-capacities", "rm-fl-retuning", "rm-fl-capacity-learning"):
            self.assertEqual(links[ident]["status"], "proposed")
            self.assertTrue(all(ref["basis"] == "inference" for ref in links[ident]["source_refs"]))
        page = self.outputs["re-membering/change.html"]
        self.assertIn('data-id="rm-fl-retuning"', page)
        self.assertIn("Novelty can also overwhelm or harm", page)
        self.assertIn("neither benefit nor an instruction to increase uncertainty", self.outputs["re-membering/items.html"])
        self.assertIn("capacities or purposes", self.outputs["re-membering/actions.html"])

    def test_presentation_cannot_override_identity_or_source_boundaries(self):
        record = deepcopy(self.record)
        record["registry"]["presentation"]["kind"] = "real"
        with self.assertRaisesRegex(ValueError, "Invalid reviewed presentation"):
            build.normalize(record)

    def test_benefit_requires_both_conditions_and_harm_remains_visible(self):
        tree = self.data["trees"]["future_reality"]
        joint = next(l for l in tree["links"] if l["id"] == "rm-fl-settle")
        self.assertEqual(joint["from"], ["rm-f-practice", "rm-f-consent"])
        data, registry = deepcopy(self.data), deepcopy(self.registry)
        data["trees"]["future_reality"]["nodes"] = [n for n in tree["nodes"] if n["id"] != "rm-f-consent"]
        registry["selection"]["future_reality"]["nodes"].remove("rm-f-consent")
        with self.assertRaises(ValueError):
            build.validate_reconstruction(data, registry)
        page = self.outputs["re-membering/change.html"]
        self.assertIn('data-id="rm-fl-protection"', page)
        self.assertIn('class="e-bar"', page)
        self.assertIn("pressure", self.outputs["re-membering/index.html"])
        self.assertIn("some participants feel less safe", self.outputs["re-membering/index.html"])

    @unittest.skipUnless(HAVE_YAML, "PyYAML is needed for the public working file")
    def test_original_files_receipts_and_private_notes_do_not_cross_boundary(self):
        state = build.skill_helpers().load(build.HERE / self.record["entry"]["source"])
        state["change_acceptances"] = [{"source_text": "PRIVATE_CANARY"}]
        state["import_context"]["path"] = "/Users/PRIVATE_CANARY.pdf"
        for tree in state["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                item["private_note"] = "PRIVATE_CANARY"
        public = json.dumps(build.project_reconstruction(state, self.registry))
        self.assertNotIn("PRIVATE_CANARY", public)
        for name, value in self.outputs.items():
            if name.startswith("re-membering/"):
                self.assertNotIn("/Users/", value)
                self.assertNotIn("change_acceptances", value)
                self.assertNotIn("source_text", value)



class PersistentSystemsTests(unittest.TestCase):
    """Stephen Le's documents: a supplied-document reconstruction that is not Margeret Heath's talks."""
    @classmethod
    def setUpClass(cls):
        cls.site, cls.commons = build.load_site()
        cls.record = next(c for c in cls.commons if c["entry"]["slug"] == "persistent-systems")
        cls.registry, cls.data = cls.record["registry"], cls.record["data"]
        cls.outputs = build.build_files(cls.site, cls.commons)

    @unittest.skipUnless(HAVE_YAML, "PyYAML is needed for the public working file")
    def test_reconstruction_validates_matches_snapshot_and_stays_proposed(self):
        helper = build.skill_helpers()
        state = helper.load(build.HERE / self.record["entry"]["source"])
        helper.validate(state)
        self.assertEqual(build.project_reconstruction(state, self.registry), self.data)
        self.assertEqual(sum(len(t["nodes"]) for t in self.data["trees"].values()), 62)
        self.assertEqual(sum(len(t["links"]) for t in self.data["trees"].values()), 45)
        for tree in self.data["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                self.assertEqual((item["status"], item["accepted_by"], item["contributors"]), ("proposed", [], [build.ASSISTANT]))
                self.assertTrue(item["source_refs"])

    def test_sources_are_stephen_les_documents_linked_to_their_originals(self):
        self.assertEqual(set(self.data["authors"]), {"le"})
        self.assertEqual(self.data["authors"]["le"]["name"], "Stephen Le")
        self.assertEqual({s["id"] for s in self.data["sources"]}, {"ap-summary", "ap-overview"})
        self.assertTrue(all(s["url"].startswith("https://github.com/dvdgdn/persistent-systems-theory/") for s in self.data["sources"]))
        about = self.outputs["persistent-systems/about.html"]
        self.assertIn("Read the original ↗", about)
        self.assertNotIn("the original file is not published here", about)
        data, registry = deepcopy(self.data), deepcopy(self.registry)
        data["sources"][0]["url"] = registry["sources"][0]["url"] = "http://example.org/"
        with self.assertRaisesRegex(ValueError, "Invalid supplied document link"):
            build.validate_reconstruction(data, registry)

    def test_pages_carry_only_this_commons_sources_and_wording(self):
        for name, page in self.outputs.items():
            if name.startswith("persistent-systems/"):
                for words in ("Heath", "the talks", "commented on an earlier map", "Why Things Last", "Thrival", "why-things-last"):
                    self.assertNotIn(words, page, (name, words))
        self.assertIn("<title>Persistent Systems Theory · Reason Commons</title>", self.outputs["persistent-systems/index.html"])
        self.assertIn("The source author has not reviewed or endorsed it.", self.outputs["persistent-systems/index.html"])


class ProsocialAITests(unittest.TestCase):
    """Atkins and Wilson's manuscript: one unpublished supplied document by two authors."""
    @classmethod
    def setUpClass(cls):
        cls.site, cls.commons = build.load_site()
        cls.record = next(c for c in cls.commons if c["entry"]["slug"] == "prosocial-ai")
        cls.registry, cls.data = cls.record["registry"], cls.record["data"]
        cls.outputs = build.build_files(cls.site, cls.commons)

    @unittest.skipUnless(HAVE_YAML, "PyYAML is needed for the public working file")
    def test_reconstruction_validates_matches_snapshot_and_stays_proposed(self):
        helper = build.skill_helpers()
        state = helper.load(build.HERE / self.record["entry"]["source"])
        helper.validate(state)
        self.assertEqual(build.project_reconstruction(state, self.registry), self.data)
        self.assertEqual(sum(len(t["nodes"]) for t in self.data["trees"].values()), 105)
        self.assertEqual(sum(len(t["links"]) for t in self.data["trees"].values()), 88)
        for tree in self.data["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                self.assertEqual((item["status"], item["accepted_by"], item["contributors"]), ("proposed", [], [build.ASSISTANT]))
                self.assertTrue(all(ref["locator"].startswith("p") for ref in item["source_refs"]), item["id"])

    def test_source_credits_both_authors_and_is_not_published(self):
        self.assertEqual([s["author"] for s in self.data["sources"]], ["atkins-wilson"])
        self.assertEqual(self.data["authors"]["atkins-wilson"]["name"], "Paul Atkins and David Sloan Wilson")
        self.assertNotIn("url", self.data["sources"][0])
        about = self.outputs["prosocial-ai/about.html"]
        self.assertIn("the original file is not published here", about)
        self.assertIn("does not cite the draft", about)

    def test_pages_do_not_borrow_another_commons_wording(self):
        for name, page in self.outputs.items():
            if name.startswith("prosocial-ai/") and name.endswith(".html"):
                for words in ("Heath", "the talks", "Stephen Le", "filing cabinet", "credited PDF page"):
                    self.assertNotIn(words, page, (name, words))
        self.assertIn("The source author has not reviewed or endorsed it.", self.outputs["prosocial-ai/index.html"])


class HistoricalReviewTests(unittest.TestCase):
    def setUp(self):
        self.site, self.commons = build.load_site()
        self.rm = next(c for c in self.commons if c["entry"]["slug"] == "re-membering")
        self.review = deepcopy(self.rm["review"])

    def test_archives_have_the_published_fingerprints(self):
        self.assertEqual([r["snapshot_sha256"] for r in self.review["releases"]][1:], [
            "57adbb7203c5fbba6796d52fb0b78fb38adbafaf32e5d3a51179bb4ebc06ef6b",
            "62483940c449795ea7cd3e2faa124e2580acfc5b7f033122185ccc84f5d5804e"])
        self.assertEqual(self.review["releases"][-1]["snapshot"], self.rm["data"])

    def test_archive_edit_and_private_fields_fail_closed(self):
        changed = self.review["releases"][1]
        changed["snapshot"]["trees"]["future_reality"]["nodes"][0]["text"] = "A later replacement."
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            build.revisions.validate(self.review, self.rm["data"], build.validate_reconstruction)
        changed["snapshot"]["private_note"] = "PRIVATE_CANARY"
        changed["snapshot_sha256"] = build.digest(changed["snapshot"])
        with self.assertRaisesRegex(ValueError, "Unexpected reconstruction field"):
            build.revisions.validate(self.review, self.rm["data"], build.validate_reconstruction)
        with self.assertRaisesRegex(ValueError, "Unreviewed review fields"):
            build.revisions.validate({**self.rm["review"], "private_note": "PRIVATE_CANARY"}, self.rm["data"], build.validate_reconstruction)

    def test_comparison_retains_all_selected_topology_and_shared_positions(self):
        import xml.etree.ElementTree as ET
        html = build.revisions.compare(self.review)
        svgs = [ET.fromstring(svg) for svg in re.findall(r'<svg class="comparison-graph".*?</svg>', html, re.S)]
        self.assertEqual(len(svgs), 2)
        node_sets, positions = [], []
        for svg, archive in zip(svgs, self.review["releases"][1:]):
            indexed = build.revisions.items(archive["snapshot"])
            nodes = {g.attrib["data-ref"]:g for g in svg.findall("g") if "data-ref" in g.attrib}
            node_sets.append(set(nodes))
            positions.append({i:(g.find("rect").attrib["x"],g.find("rect").attrib["y"]) for i,g in nodes.items()})
            for ident, g in nodes.items():
                self.assertEqual(g.attrib["data-label"], indexed[ident]["label"])
                self.assertEqual(g.find("title").text, indexed[ident]["text"])
            links = [g.attrib for g in svg.findall("g") if "data-link-ref" in g.attrib]
            expected = [l for l in archive["snapshot"]["trees"]["future_reality"]["links"] if set(l["from"]) <= set(nodes) and l["to"] in nodes]
            self.assertEqual({l["data-link-ref"] for l in links}, {l["id"] for l in expected})
            for link in links:
                record=indexed[link["data-link-ref"]]
                self.assertEqual((link["data-from"],link["data-to"],link["data-relation"]),(record["from"][0],record["to"],record["relation"]))
        self.assertEqual([len(ns) for ns in node_sets], [3,5])
        for ident in node_sets[0]:
            self.assertEqual(positions[0][ident],positions[1][ident])

    def test_all_changes_are_collapsed_and_comparison_content_is_inside_details(self):
        outputs=build.build_files(self.site,self.commons)
        class DisclosureParser(HTMLParser):
            def __init__(self):
                super().__init__(); self.stack=[]; self.details=[]; self.comparison_containers=[]
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if tag=="details":
                    self.details.append(attrs); self.stack.append(attrs.get("id"))
                if tag=="svg" and attrs.get("class")=="comparison-graph":
                    self.comparison_containers.append(self.stack[:])
            def handle_endtag(self,tag):
                if tag=="details": self.stack.pop()
        for path, html in outputs.items():
            if not path.endswith("/changes.html"): continue
            parser=DisclosureParser();parser.feed(html)
            self.assertTrue(parser.details)
            self.assertTrue(all("open" not in d for d in parser.details), path)
            if path.startswith("re-membering/"):
                self.assertEqual(parser.comparison_containers,[["agency-comparison"],["agency-comparison"]])
                self.assertEqual([d["id"] for d in parser.details][:2],["agency-comparison","agency-wording"])

    def test_source_usage_is_citation_count_and_every_example_keeps_all_locators(self):
        c=pages.Commons(build.normalize(self.rm))
        counts={"slides":(4,0),"spoken-script":(82,66),"extended-passages":(3,0),"glossary":(23,22),"bibliography":(36,36)}
        for source in c.sources:
            html=pages.source_detail(c,source,1,lambda s: "")
            ns,ls=counts[source["id"]]
            self.assertIn(pages.plural(ns,"statement"),html)
            self.assertIn(pages.plural(ls,"connection"),html)
            ids=re.findall(r'href="items.html#([^"]+)"',html)
            for ident in ids:
                for ref in c.items[ident]["source_refs"]:
                    if ref["source_id"]==source["id"]:
                        self.assertIn(pages.esc(ref["locator"]),html)
        overview=pages.reconstruction_overview(c,self.site)
        self.assertEqual(overview.count('class="document-card '),5)
        self.assertIn("Revision awaits Margeret’s review", overview)
        self.assertIn('changes.html#agency-comparison',overview)

    def test_prior_release_after_wording_does_not_drift_to_current_text(self):
        c=pages.Commons(build.normalize(self.rm))
        # This prior-release edit must read the archive, even if the current item changes later.
        c.items["rm-f-attune"]["text"]="LATER_TEXT_CANARY"
        html=pages.changes_page(c,self.site)
        self.assertNotIn("LATER_TEXT_CANARY",html)
        self.assertIn("After this release",html)
        self.assertIn("Adjust actions by listening to responses from bodies, people and environments.",html)


class GoalFirstOverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site, cls.records = build.load_site()
        cls.outputs = build.build_files(cls.site, cls.records)

    def test_every_overview_leads_with_purpose_question_and_participation(self):
        for record in self.records:
            slug=record["entry"]["slug"]
            page=self.outputs[slug+"/index.html"]
            self.assertLess(page.index('class="purpose-intro"'), page.index('id="get-involved"'))
            self.assertLess(page.index('id="featured-question-title"'),page.index('id="get-involved"'))
            self.assertLess(page.index('id="get-involved"'),page.index('id="read-reasoning"'))
            self.assertIn('href="#get-involved"',page)
            if record["data"].get("sources"):
                self.assertLess(page.index('id="get-involved"'),page.index('class="source-shelf"'))

    def test_sources_and_full_account_are_closed_without_hiding_entry_links(self):
        class Sections(HTMLParser):
            def __init__(self):
                super().__init__();self.details=[];self.stack=[];self.cards=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if tag=="details": self.details.append(a);self.stack.append(a.get("id"))
                if tag=="a" and "document-card" in a.get("class","").split():self.cards.append(self.stack[:])
            def handle_endtag(self,tag):
                if tag=="details":self.stack.pop()
        for slug in ["re-membering","gandhi-2-0"]:
            page=self.outputs[slug+"/index.html"];parser=Sections();parser.feed(page)
            self.assertTrue(all("open" not in d for d in parser.details))
            self.assertTrue(all("overview-sources" in ancestors for ancestors in parser.cards))
            self.assertEqual(len(re.findall(r'<a href="[^"]+"><span>0[1-6]</span>',page)),6)

    def test_editorial_invitation_rejects_unpublished_references_and_standing_overrides(self):
        record=deepcopy(self.records[0]);entry=record["entry"]
        entry["front_page"]["focus_ref"]="PRIVATE_ITEM_CANARY"
        with self.assertRaisesRegex(ValueError,"published reasoning"):
            build.validate_front_page(entry,record["data"])
        entry["front_page"]["focus_ref"]=self.records[0]["entry"]["front_page"]["focus_ref"]
        entry["front_page"]["status"]="accepted"
        with self.assertRaisesRegex(ValueError,"Invalid front-page invitation"):
            build.validate_front_page(entry,record["data"])

    def test_sharing_is_a_reviewable_public_draft_and_example_has_no_recipient(self):
        from urllib.parse import parse_qs
        class Links(HTMLParser):
            def __init__(self):super().__init__();self.shares=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if tag=="a" and "share-contribution" in a.get("class","").split():self.shares.append(a)
        for record in self.records:
            entry=record["entry"];page=self.outputs[entry["slug"]+"/index.html"];parser=Links();parser.feed(page)
            if entry["kind"]=="example":
                self.assertFalse(parser.shares)
                self.assertIn("there is no real group to send it to",page)
            else:
                self.assertEqual(len(parser.shares),3)
                for link in parser.shares:
                    u=urlparse(link["href"]);q=parse_qs(u.query)
                    self.assertEqual((u.scheme,u.netloc,u.path),("https","github.com","/reasoncommons/reasoncommons/issues/new"))
                    self.assertIn(entry["name"],q["title"][0]);self.assertIn(record["data"]["release_id"],q["body"][0])
                    self.assertIn(entry["front_page"]["focus_ref"],q["body"][0])
                    self.assertIn("My contribution:",q["body"][0]);self.assertIn("does not endorse",q["body"][0])
                self.assertIn("You review and post it on GitHub",page)

    def test_draft_briefs_retain_public_context_and_do_not_change_reasoning_exports(self):
        for record in self.records:
            entry=record["entry"];slug=entry["slug"];page=self.outputs[slug+"/index.html"]
            self.assertEqual(page.count('id="contribution-brief-'),3)
            self.assertIn(pages.esc(entry["front_page"]["question"]),page)
            self.assertIn("Copying this brief submits nothing",page)
            exported=json.loads(self.outputs[slug+"/reasoning.json"])
            self.assertEqual(exported,record["data"])
            self.assertNotIn("front_page",exported)

    def test_map_routes_have_html_goal_context_and_all_six_destinations(self):
        for record in self.records:
            slug=record["entry"]["slug"];page=self.outputs[slug+"/map.html"]
            self.assertTrue(page.startswith("<!doctype html>"));self.assertIn("One goal, " + ("six" if len(record["data"]["trees"]) == 6 else str(len(record["data"]["trees"]))) + " questions",page)
            self.assertEqual(page.count('class="mq"'),len(record["data"]["trees"]))
            goal=next(n for n in record["data"]["trees"]["goal"]["nodes"] if n["kind"]=="goal")
            self.assertIn(pages.esc(goal["text"]),page)
            for name in record["data"]["trees"]:
                path=pages.TREES[name]["slug"]+".html"
                self.assertIn('href="'+path+'"',page);self.assertIn(slug+"/"+path,self.outputs)

    def test_directory_prioritizes_goal_and_question_before_sources(self):
        page=self.outputs["index.html"]
        for entry in self.site["commons"]:
            start=page.index('<h3><a href="'+entry["slug"]+'/index.html"')
            end=page.index('</article>',start);card=page[start:end]
            self.assertLess(card.index('class="cc-goal"'),card.index('class="cc-question"'))
            if entry["kind"]=="reconstruction":
                self.assertLess(card.index('class="cc-question"'),card.index('class="source-mini"'))
            self.assertIn(entry["slug"]+'/index.html#get-involved',card)



class AssetDeliveryTests(unittest.TestCase):
    def test_all_html_uses_current_assets_and_only_head_changes_on_asset_refresh(self):
        import hashlib
        site,records=build.load_site();outputs=build.build_files(site,records)
        style_version=hashlib.sha256(outputs["styles.css"].encode()).hexdigest()[:16]
        script_version=hashlib.sha256(outputs["app.js"].encode()).hexdigest()[:16]
        htmls={name:value for name,value in outputs.items() if name.endswith(".html")}
        self.assertEqual(len(htmls),86)
        for name,page in htmls.items():
            self.assertIn('styles.css?v='+style_version,page,name)
            self.assertIn('app.js?v='+script_version,page,name)
        normalized=[build.normalize(r) for r in records]
        old=pages.render(site,normalized,asset_versions={"styles":"previous-style","script":"previous-script"})
        fresh=pages.render(site,normalized,asset_versions={"styles":"new-style","script":"new-script"})
        self.assertEqual(set(old),set(fresh))
        for name in old:
            self.assertNotEqual(old[name],fresh[name],name)
            self.assertEqual(old[name].split("<body",1)[1],fresh[name].split("<body",1)[1],name)
        self.assertNotIn("asset_versions",site)


class WisdomAIConventionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site, records = build.load_site()
        cls.record = next(r for r in records if r["entry"]["slug"] == "wisdom-ai")
        cls.normalized = build.normalize(cls.record)
        cls.commons = pages.Commons(cls.normalized)
        cls.outputs = build.build_files(cls.site, records)

    def test_public_web_source_cannot_be_mistaken_for_asserted_answers(self):
        data, registry = deepcopy(self.record["data"]), deepcopy(self.record["registry"])
        item = data["trees"]["goal"]["nodes"][0]
        self.assertEqual(item["contributors"], [{"name": "David Joseph", "role": "human"}])
        self.assertEqual(item["accepted_by"], [])
        next(r for r in item["source_refs"] if r["source_id"] == "wisdom-ai")["basis"] = "paraphrase"
        with self.assertRaisesRegex(ValueError, "Invalid source locator"):
            build.validate_reconstruction(data, registry)

    def test_web_source_requires_reviewed_author_and_https_url(self):
        for field, value in [("author", "unreviewed"), ("url", "javascript:alert(1)")]:
            data, registry = deepcopy(self.record["data"]), deepcopy(self.record["registry"])
            data["sources"][0][field] = registry["sources"][0][field] = value
            with self.assertRaisesRegex(ValueError, "Invalid public web source"):
                build.validate_reconstruction(data, registry)

    def test_question_hierarchy_rejects_duplicate_ids_and_unreviewed_fields(self):
        original = self.normalized["source_questions"]
        for change in ("duplicate", "field", "url"):
            data = deepcopy(original)
            if change == "duplicate":
                data["questions"][1]["id"] = data["questions"][0]["id"]
            elif change == "field":
                data["questions"][0]["private_note"] = "PRIVATE_CANARY"
            else:
                data["questions"][0]["source_url"] = "https://elsewhere.example/"
            with self.assertRaises(ValueError):
                build.validate_source_questions(data, self.record["data"]["sources"])

    def test_unresolved_source_question_is_rejected(self):
        record = deepcopy(self.record)
        next(r for r in record["data"]["trees"]["goal"]["nodes"][0]["source_refs"] if r["source_id"] == "wisdom-ai")["locator"] = "A question absent from the source"
        with self.assertRaisesRegex(ValueError, "Unresolved source question"):
            build.normalize(record)

    def test_all_original_questions_are_readable_without_javascript(self):
        def flatten(nodes):
            return [q for n in nodes for q in [n] + flatten(n["children"])]
        questions = flatten(self.normalized["source_questions"]["questions"])
        self.assertEqual(len(questions), 93)
        self.assertEqual([len(flatten([q])) for q in self.normalized["source_questions"]["questions"]], [22, 18, 35, 18])
        about = self.outputs["wisdom-ai/about.html"]
        for q in questions:
            self.assertIn(pages.esc(q["text"]), about)
        self.assertIn('class="rc-outline"', about)
        self.assertIn('id="source-questions"', about)
        self.assertNotIn('class="canvas"', about)

    def test_shared_assets_item_details_and_proposed_standing_are_used(self):
        for name in ["goal", "in-the-way", "change", "items", "about"]:
            page = self.outputs[f"wisdom-ai/{name}.html"]
            self.assertIn('../styles.css?v=', page)
            self.assertIn('../app.js?v=', page)
            self.assertNotIn('<style>', page)
            self.assertIn('Everything here is proposed', page)
        self.assertIn('items.html#g-wise-ai', self.outputs['wisdom-ai/goal.html'])
        self.assertIn('data-view-panel="outline"', self.outputs['wisdom-ai/goal.html'])
        self.assertIn('AI inference · source questions', self.outputs['wisdom-ai/goal.html'])
        self.assertNotIn('From Rufus Pollock', self.outputs['wisdom-ai/goal.html'])

    def test_item_brief_preserves_the_correct_source_and_authorship(self):
        page = self.outputs['wisdom-ai/items.html']
        self.assertIn('Research questions by', page)
        self.assertIn('Proposed analysis by', page)
        self.assertNotIn('Ideas from', page)
        self.assertNotIn('Gandhi 2.0', page)
        self.assertNotIn('Check the supplied analysis', page)
        brief = pages.brief(self.commons, 'g-wise-ai', self.site)
        self.assertIn('Wisdom and AI', brief)
        self.assertIn('research page poses questions', brief)
        self.assertNotIn('Gandhi', brief)

    def test_partial_map_navigation_reaches_only_published_trees(self):
        # The shared component still supports partial records even though this map is now complete.
        partial = deepcopy(self.normalized)
        keep = {"goal", "current_reality", "future_reality"}
        partial['trees'] = {k:v for k,v in partial['trees'].items() if k in keep}
        partial['views'] = {k:v for k,v in partial['views'].items() if k in keep}
        c = pages.Commons(partial)
        for name in keep:
            page = pages.tree_page(c, name, self.site)
            for absent in ["conflict.html", "prerequisites.html", "actions.html"]:
                self.assertNotIn('href="' + absent + '"', page)
        self.assertIn('Question 3 of 3', pages.tree_page(c, 'future_reality', self.site))

    def test_release_keeps_private_receipts_out_and_preserves_reasoning(self):
        exported = json.loads(self.outputs['wisdom-ai/reasoning.json'])
        self.assertEqual(sum(len(t['nodes']) for t in exported['trees'].values()), 72)
        self.assertEqual(sum(len(t['links']) for t in exported['trees'].values()), 42)
        self.assertNotIn('change_acceptances', exported)
        self.assertNotIn('source_context', exported)
        for tree in exported['trees'].values():
            for item in tree['nodes'] + tree['links']:
                self.assertEqual(item['status'], 'proposed')
                self.assertFalse(item['accepted_by'])


class WisdomAICompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site, records = build.load_site()
        cls.record = next(r for r in records if r['entry']['slug'] == 'wisdom-ai')
        cls.normalized = build.normalize(cls.record)
        cls.c = pages.Commons(cls.normalized)
        cls.outputs = build.build_files(cls.site, records)
        cls.data, cls.registry = cls.record['data'], cls.record['registry']

    def test_all_six_trees_have_the_proposed_counts_and_routes(self):
        expected = {'goal':(8,7), 'current_reality':(15,5), 'conflict':(5,5), 'future_reality':(18,9), 'prerequisite':(11,7), 'transition':(15,9)}
        self.assertEqual(set(self.data['trees']), set(expected))
        for name, (nodes,links) in expected.items():
            tree = self.data['trees'][name]
            self.assertEqual((len(tree['nodes']),len(tree['links'])), (nodes,links))
            self.assertIn('wisdom-ai/'+pages.TREES[name]['slug']+'.html', self.outputs)
            self.assertTrue(all(i['status']=='proposed' and not i['accepted_by'] for i in tree['nodes']+tree['links']))
        self.assertEqual(self.data['feedback'], [])

    def test_review_requires_four_joint_conditions_and_negative_branch_is_kept(self):
        links = {l['id']:l for l in self.data['trees']['future_reality']['links']}
        joint = links['f-review-revision']
        self.assertEqual(joint['from'], ['f-review','f-usable-evidence','f-authority-incentives','f-feasible-alternatives'])
        self.assertEqual(joint['to'], 'f-revision')
        self.assertEqual(links['f-review-reassurance']['to'],'f-unwarranted-reassurance')
        self.assertEqual(links['f-reassurance-action']['to'],'f-premature-action')
        future=self.outputs['wisdom-ai/change.html']
        self.assertIn('all of these together',future)
        self.assertIn('AND',future)
        self.assertIn('f-substantive-criteria',future)
        self.assertIn('f-preaction-safeguards',future)
        self.assertIn('reject this intervention',self.outputs['wisdom-ai/items.html'])

    def test_competing_diagnoses_are_joint_hypotheses_not_observations(self):
        tree=self.data['trees']['current_reality']
        self.assertEqual([len(l['from']) for l in tree['links']], [1,2,3,2,2])
        for branch in ['r-alignment-hypothesis','r-race-hypothesis','r-agency-hypothesis','r-moral-standing-hypothesis']:
            self.assertTrue(any(b['ref']==branch and b['work']=='test_causality' for b in tree['backlog']))
        self.assertIn('AI assistance could strengthen judgment', json.dumps(tree,ensure_ascii=False))
        self.assertIn('Uncertainty could instead encourage restraint', json.dumps(tree,ensure_ascii=False))

    def test_human_contribution_requires_explicit_matching_source_policy(self):
        for failure in ['no_policy','wrong_author','no_matching_locator','inferred_not_contributed','different_person']:
            data, registry=deepcopy(self.data),deepcopy(self.registry)
            item=data['trees']['goal']['nodes'][0]
            if failure=='no_policy':registry.pop('contribution_sources')
            elif failure=='wrong_author':
                data['sources'][1]['author']=registry['sources'][1]['author']='rufus'
            elif failure=='no_matching_locator':item['source_refs']=[r for r in item['source_refs'] if r['source_id']!='map-analysis']
            elif failure=='inferred_not_contributed':item['source_refs'][0]['basis']='inference'
            else:item['contributors']=[{'name':'Rufus Pollock','role':'human'}]
            with self.assertRaises(ValueError,msg=failure):build.validate_reconstruction(data,registry)

    def test_unmodified_ai_contributions_keep_their_origin(self):
        old=self.normalized['archives']['2026-10-25.1']
        initial={i['id']:i for t in old['trees'].values() for i in t['nodes']+t['links']}
        for ident in ['g-understand','g-revise','r-uncertainty','r-decisions','f-review','f-revision']:
            self.assertEqual(self.c.items[ident]['contributors'],initial[ident]['contributors'])
        self.assertEqual(self.c.items['g-wise-ai']['contributors'],[{'name':'David Joseph','role':'human'}])
        self.assertIn('Raised for examination by David Joseph',self.outputs['wisdom-ai/conflict.html'])
        self.assertIn('Supporting empirical evidence',self.outputs['wisdom-ai/items.html'])
        self.assertIn('Not supplied in this map',self.outputs['wisdom-ai/items.html'])

    def test_transition_steps_are_conditional_and_unassigned(self):
        tree=self.data['trees']['transition']
        for i in range(1,6):
            link=next(l for l in tree['links'] if l['id']==f't-{i}-produces')
            self.assertEqual(link['from'],[f't-{i}-condition',f't-{i}-action'])
            self.assertEqual(link['to'],f't-{i}-effect')
        text=self.outputs['wisdom-ai/items.html']
        self.assertIn('None recorded; owner and date unassigned',text)
        self.assertIn('Conditional premise, not a report',text)
        self.assertIn('If a safe test is unavailable',text)
        self.assertFalse(any(n.get('proposed_role') for n in tree['nodes']))

    def test_original_published_release_is_preserved_and_readable(self):
        old=self.normalized['archives']['2026-10-25.1']
        self.assertEqual(sum(len(t['nodes']) for t in old['trees'].values()),7)
        self.assertEqual(sum(len(t['links']) for t in old['trees'].values()),4)
        self.assertEqual(old['trees']['future_reality']['links'][0]['from'],['f-review'])
        self.assertEqual(old['trees']['goal']['nodes'][0]['text'],'People make informed, revisable choices about developing and using AI.')
        self.assertIn(pages.esc(old['trees']['goal']['nodes'][0]['text']),self.outputs['wisdom-ai/changes.html'])
        self.assertIn('Original published statements, connections and attribution',self.outputs['wisdom-ai/changes.html'])
        damaged=deepcopy(self.registry);damaged['previous_releases'][0]['snapshot']['trees']['goal']['nodes'][0]['text']='Changed history'
        with self.assertRaisesRegex(ValueError,'Previous release fingerprint'):build.publication_archives(damaged,self.data)

    def test_prior_release_does_not_gain_current_endorsement_or_attribution(self):
        old=self.normalized['archives']['2026-10-25.1']
        self.assertEqual(old['trees']['goal']['nodes'][0]['contributors'],[build.ASSISTANT])
        self.assertTrue(all(not i['accepted_by'] for t in old['trees'].values() for i in t['nodes']+t['links']))
        self.assertIn('proposed',json.dumps(old))


class PlanTests(unittest.TestCase):
    """What has to happen first, and who does what: steps in stages, actions in order, one grammar for standing."""

    @classmethod
    def setUpClass(cls):
        cls.site, records = build.load_site()
        cls.outputs = build.build_files(cls.site, records)
        cls.commons = {r["entry"]["slug"]: pages.Commons(build.normalize(r)) for r in records}

    def test_steps_sit_one_stage_after_the_longest_chain_before_them(self):
        widths = {}
        for slug in ("example-willow-lane", "re-membering", "wisdom-ai", "gandhi-2-0"):
            plan = diagrams.stages(self.commons[slug].trees["prerequisite"])
            for link in plan["needs"]:
                for source in link["from"]:
                    self.assertLess(plan["rank"][source], plan["rank"][link["to"]], link["id"])
            for step, rank in plan["rank"].items():
                if rank:
                    self.assertTrue(any(plan["rank"][s] == rank - 1 for s, _ in plan["pre"][step]), step)
            widths[slug] = [len(column) for column in diagrams.arrange(plan, set(plan["steps"]))]
            self.assertEqual(plan["unconnected"] + plan["loose"], [])
        self.assertEqual(widths["example-willow-lane"], [4, 1])
        self.assertEqual(widths["wisdom-ai"], [4, 1, 1])
        self.assertEqual(len(widths["gandhi-2-0"]), 9)
        page = self.outputs["gandhi-2-0/prerequisites.html"]
        self.assertEqual(len(re.findall(r'<section class="pv-col[ "]', page)), 9)
        self.assertEqual(page.count('<li class="pv-card'), 36)  # Each obstacle sits on the step that gets past it.
        self.assertEqual(page.count('<p class="pv-gp-l">Gets past</p>'), 36)

    def test_critical_path_marks_only_steps_without_slack(self):
        willow = diagrams.stages(self.commons["example-willow-lane"].trees["prerequisite"])
        self.assertEqual(diagrams.critical_path(willow), (set(), set()))  # Every chain is equally long.
        self.assertNotIn("Critical path", self.outputs["example-willow-lane/prerequisites.html"])
        wisdom = diagrams.stages(self.commons["wisdom-ai"].trees["prerequisite"])
        nodes, edges = diagrams.critical_path(wisdom)
        self.assertEqual(nodes, {"p-criteria", "p-practice", "p-authority", "p-test"})
        self.assertEqual(edges, {("p-criteria", "p-authority"), ("p-practice", "p-authority"), ("p-authority", "p-test")})
        self.assertIn("pv-crit", self.outputs["wisdom-ai/prerequisites.html"])

    def test_cards_mark_who_proposed_and_who_accepted(self):
        page = self.outputs["example-willow-lane/prerequisites.html"]
        order = re.search(r'<li class="pv-card pv-k-intermediate_objective pv-proposed[^"]*" data-node="wl-p-io-order".*?class="pv-foot".*?</div>', page, flags=re.S).group(0)
        self.assertIn('class="pv-av pv-av-by" title="Proposed by Dev"', order)
        self.assertIn('<span class="pv-none">Not accepted</span>', order)
        self.assertIn('data-link="wl-p-rel-over-order"', order)
        ours = self.outputs["reason-commons/prerequisites.html"]
        stage1 = re.search(r'<li class="pv-card [^"]*" data-node="pr2-obj-stage1".*?class="pv-foot".*?</div>', ours, flags=re.S).group(0)
        self.assertIn('title="Proposed by AI assistant"', stage1)
        self.assertIn('title="Proposed by Rufus Pollock"', stage1)
        for path, value in self.outputs.items():  # Only our commons shows filled acceptance marks.
            if path.endswith(".html") and not path.startswith("reason-commons/"):
                self.assertNotIn('pv-av-ok" title=', value, path)
        # The marks still render where an item is accepted.
        record = next(r for r in build.load_site()[1] if r["entry"]["slug"] == "example-willow-lane")
        normalized = deepcopy(build.normalize(record))
        node = next(n for n in normalized["trees"]["prerequisite"]["nodes"] if n["id"] == "wl-p-io-order")
        node.update(status="accepted", accepted_by=["Dev", "Amara"])
        guide, wide, after = pages.prerequisite_plan(pages.Commons(normalized))
        self.assertIn("Accepted for now by Dev and Amara.", wide)
        self.assertIn('class="pv-av pv-av-ok" title="Accepted for now by Dev"', wide)
    def test_actions_follow_the_recorded_order_or_a_timeline(self):
        willow = self.outputs["example-willow-lane/actions.html"]
        self.assertEqual(willow.count('<section class="pv-group">'), 2)
        self.assertIn('data-link="wl-t-rel-then">after 1</a>', willow)
        self.assertIn("pv-no-inputs", willow)  # No starting conditions are recorded, so none are shown.
        remembering = diagrams.action_steps(self.commons["re-membering"].trees["transition"])
        last = remembering["steps"][-1]
        self.assertEqual(([s["n"] for s, _ in last["after"]], [s["n"] for s, _ in last["loops"]]), ([3, 4], [1]))
        gandhi = self.outputs["gandhi-2-0/actions.html"]
        self.assertNotIn('<section class="pv-group">', gandhi)  # No order is recorded between these actions.
        self.assertIn("When each action is needed", gandhi)
        self.assertEqual(gandhi.count('class="pv-g-label"'), 8)
        self.assertIn("Choose a host and one function", gandhi)
        self.assertNotIn("When each action is needed", willow)

    def test_plans_are_complete_without_javascript(self):
        for slug in ("reason-commons", "example-willow-lane", "re-membering", "wisdom-ai", "gandhi-2-0"):
            for path in ("prerequisites", "actions"):
                page = self.outputs[f"{slug}/{path}.html"]
                cards = set(re.findall(r'class="pv-card [^"]*" data-node="([^"]+)"', page))
                links = set(re.findall(r'<a class="pv-hit" href="items.html#([^"]+)"', page))
                panels = set(re.findall(r'<template id="pv-d-([^"]+)"', page))
                self.assertEqual(cards, links, (slug, path))
                self.assertEqual(cards, panels, (slug, path))
            prereq = self.outputs[f"{slug}/prerequisites.html"]
            self.assertIn('<p class="pv-hint" hidden>', prereq)  # Tracing is offered only once the script can do it.
            needs = re.findall(r'<div class="pv-needs"><p>Needs</p><ul>(.*?)</ul></div>', prereq, flags=re.S)
            plan = diagrams.stages(self.commons[slug].trees["prerequisite"])
            self.assertEqual(sum(item.count("<li") for item in needs), sum(len(p) for p in plan["pre"].values()), slug)


if __name__ == '__main__':
    unittest.main()
