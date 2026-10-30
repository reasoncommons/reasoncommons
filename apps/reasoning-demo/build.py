#!/usr/bin/env python3
"""Build the read-only site of commons from reviewed public projections.

Ordinary builds and CI use the snapshot pinned in each publication registry. Refreshing
our commons requires an explicit, authorized working-state path and the existing allowlist;
the fictional example refreshes from its own public working file. No working-state path,
approval receipt, private note or unselected reasoning is published.
"""
import argparse
from copy import deepcopy
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEST = ROOT / "website/demos/reason-commons-in-use"
sys.path.insert(0, str(HERE))
import diagrams  # noqa: E402
import pages  # noqa: E402
import revisions  # noqa: E402
import submissions  # noqa: E402

SUBMISSIONS = HERE / "submissions"  # Commons shared by their participants, one folder each, found without a site.json entry.

TREE_KINDS = {
    "goal": {"goal", "critical_success_factor", "necessary_condition"},
    "current_reality": {"undesirable_effect", "cause"},
    "conflict": {"objective", "need", "prerequisite"},
    "future_reality": {"injection", "existing_condition", "predicted_effect", "desirable_effect", "undesirable_effect"},
    "prerequisite": {"objective", "obstacle", "intermediate_objective"},
    "transition": {"existing_condition", "need", "action", "expected_effect"},
}
KINDS = set().union(*TREE_KINDS.values()) | {"observation"}
RELATIONS = {"necessary_for", "contributes_to", "conflicts_with", "causes", "produces", "overcomes", "precedes"}
NODE_FIELDS = {"id", "kind", "text", "label", "status", "accepted_by", "contributors", "acceptance_context"}
LINK_FIELDS = {"id", "from", "to", "relation", "status", "accepted_by", "contributors", "acceptance_context"}
TRACES = ("addresses", "derived_from", "implements")
NODE_FIELDS_V2 = NODE_FIELDS | {"assumptions", "challenges", *TRACES}
LINK_FIELDS_V2 = LINK_FIELDS | {"assumptions", "challenges"}
STANDINGS = {"proposed", "accepted", "disputed"}
VERDICTS = {"observed", "not_observed", "unclear", "not_assessed", "unavailable"}
READINESS = {"experienced", "not_yet", "cannot_assess"}
CHANGE_TYPES = {"added", "revised", "disputed", "accepted", "removed", "report", "credited"}
UNKNOWN = {"name": "Original contributor not identified", "role": "unknown"}
ASSISTANT = {"name": "AI assistant", "role": "assistant"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def esc(value):
    return html.escape(str(value), quote=True)


def read_json(path):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f"Duplicate key: {key}")
            obj[key] = value
        return obj
    return json.loads(path.read_text(), object_pairs_hook=unique)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def skill_helpers():
    helper = ROOT / "skills/ltp/scripts/update_views.py"
    spec = importlib.util.spec_from_file_location("rc_views", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contributors(item, people):
    result = []
    for contribution in item["contributions"]:
        who = contribution["by"]
        if contribution["attribution"] == "driver_default":
            entry = dict(UNKNOWN)
        elif who == "assistant":
            entry = dict(ASSISTANT)
        else:
            require(who in people, f"Unselected contributor: {who}")
            entry = {"name": people[who], "role": "human"}
        if entry not in result:
            result.append(entry)
    return result


# ---------------------------------------------------------------- projection 1: our selection, accepted and proposed
# The Reason Commons commons is the only one that records acceptance. An accepted item keeps its named
# endorsers and recorded context; a proposed one is published without endorsers. Nothing disputed is selected.

def project(state, registry):
    """Only explicit IDs and explicit fields cross the publication boundary."""
    require(state.get("schema_version") == 1, "Unsupported working-state version")
    people = registry["people"]
    result = {"projection_version": 1, **deepcopy(registry["release"]), "trees": {}}
    for name, selection in registry["selection"].items():
        require(name in TREE_KINDS and name in state["trees"], f"Unknown tree: {name}")
        source = state["trees"][name]
        output = {"nodes": [], "links": []}
        for key in ("nodes", "links"):
            indexed = {item["id"]: item for item in source[key]}
            for ident in selection[key]:
                require(ident in indexed, f"Selected item is missing: {ident}")
                item = indexed[ident]
                status = item.get("status", "proposed")
                require(status in {"accepted", "proposed"}, f"Selected item is disputed: {ident}")
                if status == "accepted":
                    require(item.get("accepted_by"), f"Missing endorsement: {ident}")
                    require(all(p in people for p in item["accepted_by"]), f"Unselected endorser: {ident}")
                    public = {"id": ident, "status": "accepted",
                              "accepted_by": [people[p] for p in item["accepted_by"]],
                              "contributors": contributors(item, people),
                              "acceptance_context": item.get("acceptance_source", "No acceptance date was recorded.")}
                else:
                    require(not item.get("accepted_by"), f"Proposed item lists endorsers: {ident}")
                    public = {"id": ident, "status": "proposed", "accepted_by": [], "contributors": contributors(item, people)}
                if key == "nodes":
                    public.update(kind=item["kind"], text=item["text"])
                    if item.get("label"):
                        public["label"] = item["label"]
                else:
                    public.update({field: deepcopy(item[field]) for field in ("from", "to", "relation")})
                output[key].append(public)
        result["trees"][name] = output
    validate_projection(result, registry)
    return result


def validate_attribution(item, approved, ident):
    require(item.get("contributors"), f"Missing attribution: {ident}")
    for c in item["contributors"]:
        require(set(c) == {"name", "role"}, f"Invalid attribution fields: {ident}")
        require(c in (UNKNOWN, ASSISTANT) or (c["role"] == "human" and c["name"] in approved), f"Unselected contributor: {ident}")


def validate_projection(data, registry):
    require(data.get("projection_version") == 1, "Unsupported projection version")
    require(set(data) == {"projection_version", "release_id", "snapshot_date", "title", "trees"}, "Unexpected public field")
    require(set(data["trees"]) == set(registry["selection"]), "Selection/tree mismatch")
    approved = set(registry["people"].values())
    seen = set()
    for name, tree in data["trees"].items():
        ids = {n["id"] for n in tree["nodes"]}
        for key, allowed in (("nodes", NODE_FIELDS), ("links", LINK_FIELDS)):
            require([i["id"] for i in tree[key]] == registry["selection"][name][key], f"Selection mismatch: {name}.{key}")
            for item in tree[key]:
                ident = item["id"]
                require(ident not in seen and re.fullmatch(r"[a-z0-9-]+", ident), f"Invalid/duplicate ID: {ident}")
                seen.add(ident)
                require(set(item) <= allowed, f"Unreviewed public fields: {ident}")
                require(item.get("status") in {"accepted", "proposed"}, f"Invalid public standing: {ident}")
                if item["status"] == "accepted":
                    require(item.get("accepted_by") and set(item["accepted_by"]) <= approved, f"Invalid endorsers: {ident}")
                    require(isinstance(item.get("acceptance_context"), str), f"Missing recorded context: {ident}")
                else:
                    require(item.get("accepted_by") == [] and "acceptance_context" not in item, f"Proposed item cannot list endorsers: {ident}")
                validate_attribution(item, approved, ident)
                if key == "nodes":
                    require(item.get("kind") in KINDS and isinstance(item.get("text"), str) and item["text"].strip(), f"Invalid statement: {ident}")
                else:
                    require(item.get("relation") in RELATIONS, f"Unsupported relationship: {ident}")
                    require(isinstance(item.get("from"), list) and item["from"] and len(set(item["from"])) == len(item["from"]), f"Invalid sources: {ident}")
                    require(set(item["from"] + [item["to"]]) <= ids, f"Missing published endpoint: {ident}")
                    accepted = {n["id"] for n in tree["nodes"] if n["status"] == "accepted"}
                    require(item["status"] != "accepted" or set(item["from"] + [item["to"]]) <= accepted, f"Accepted link needs accepted endpoints: {ident}")


# ---------------------------------------------------------------- projection 2: the fictional example, proposed only

def person(who, people):
    if who == "assistant":
        return ASSISTANT["name"]
    require(who in people, f"Unselected participant: {who}")
    return people[who]


def project_v2(state, registry, check=True):
    """A selection that keeps standings, qualifications, open work, outcome reports and history."""
    require(state.get("schema_version") == 1, "Unsupported working-state version")
    people = registry["people"]
    public_nodes = {i for selection in registry["selection"].values() for i in selection["nodes"]}
    result = {"projection_version": 2, "is_example": registry["is_example"], **deepcopy(registry["release"]),
              "people": [{"name": people[k], "role": registry["roles"][k]} for k in people],
              "trees": {}, "feedback": [], "history": deepcopy(registry["history"])}
    for name, selection in registry["selection"].items():
        require(name in TREE_KINDS and name in state["trees"], f"Unknown tree: {name}")
        source = state["trees"][name]
        output = {"nodes": [], "links": [], "backlog": []}
        for key in ("nodes", "links"):
            indexed = {item["id"]: item for item in source[key]}
            for ident in selection[key]:
                require(ident in indexed, f"Selected item is missing: {ident}")
                item = indexed[ident]
                public = {"id": ident, "status": item.get("status", "proposed"),
                          "accepted_by": [person(p, people) for p in item.get("accepted_by", [])],
                          "contributors": contributors(item, people)}
                if item.get("acceptance_source"):
                    public["acceptance_context"] = item["acceptance_source"]
                if key == "nodes":
                    public.update(kind=item["kind"], text=item["text"])
                    if item.get("label"):
                        public["label"] = item["label"]
                    for trace in TRACES:
                        refs = [r for r in item.get(trace, []) if r in public_nodes]
                        if refs:
                            public[trace] = refs
                else:
                    public.update({field: deepcopy(item[field]) for field in ("from", "to", "relation")})
                for note in ("assumptions", "challenges"):
                    if item.get(note):
                        public[note] = [{"text": n["text"], "by": person(n["by"], people)} for n in item[note]]
                output[key].append(public)
        chosen = set(selection["nodes"]) | set(selection["links"])
        output["backlog"] = [{k: task[k] for k in ("ref", "work", "label", "note") if k in task}
                             for task in source.get("backlog", []) if task["ref"] in chosen]
        result["trees"][name] = output
    for request in state.get("feedback_requests", []):
        if request["id"] not in registry["feedback"]:
            continue
        public = {key: deepcopy(request[key]) for key in ("id", "revision", "recorded_at", "about", "benefits", "reservations") if key in request}
        public.update(created_by=person(request["created_by"], people), feedback_from=[person(p, people) for p in request["feedback_from"]])
        if request.get("ready_when"):
            public["ready_when"] = request["ready_when"]
        public["reports"] = [{"id": r["id"], "by": person(r["by"], people), "recorded_at": r["recorded_at"], "readiness": r["readiness"],
                              "text": r["text"], "evidence_type": r["evidence_type"], "outcomes": deepcopy(r["outcomes"])}
                             for r in request["reports"]]
        result["feedback"].append(public)
    if check:  # A reconstruction checks its own copy, once retired items are set aside.
        validate_v2(result, registry)
    return result


def validate_v2(data, registry):
    require(data.get("projection_version") == 2, "Unsupported projection version")
    require(set(data) == {"projection_version", "is_example", "release_id", "snapshot_date", "title", "people", "trees", "feedback", "history"}, "Unexpected public field")
    require(data["is_example"] is registry["is_example"] is True, "Projection 2 is reserved for the labelled fictional example")
    require(set(data["trees"]) == set(registry["selection"]), "Selection/tree mismatch")
    approved = set(registry["people"].values())
    names = approved | {ASSISTANT["name"]}
    require([p["name"] for p in data["people"]] == list(registry["people"].values()), "People mismatch")
    seen, nodes_by_id = set(), {}
    for name, tree in data["trees"].items():
        require(set(tree) == {"nodes", "links", "backlog"}, f"Unexpected tree fields: {name}")
        for key, allowed in (("nodes", NODE_FIELDS_V2), ("links", LINK_FIELDS_V2)):
            require([i["id"] for i in tree[key]] == registry["selection"][name][key], f"Selection mismatch: {name}.{key}")
            for item in tree[key]:
                ident = item["id"]
                require(ident not in seen and re.fullmatch(r"[a-z0-9-]+", ident), f"Invalid/duplicate ID: {ident}")
                seen.add(ident)
                require(set(item) <= allowed, f"Unreviewed public fields: {ident}")
                require(item.get("status") in STANDINGS, f"Invalid standing: {ident}")
                require(set(item.get("accepted_by", [])) <= approved, f"Invalid endorsers: {ident}")
                require(item["status"] == "proposed" and not item["accepted_by"], f"Only the Reason Commons commons publishes accepted or disputed reasoning: {ident}")
                validate_attribution(item, approved, ident)
                for note in ("assumptions", "challenges"):
                    for entry in item.get(note, []):
                        require(set(entry) == {"text", "by"} and entry["by"] in names and entry["text"].strip(), f"Invalid {note}: {ident}")
                if key == "nodes":
                    require(item.get("kind") in TREE_KINDS[name] | {"observation"} and item.get("text", "").strip(), f"Invalid statement: {ident}")
                    nodes_by_id[ident] = item
        local = {n["id"]: n for n in tree["nodes"]}
        for link in tree["links"]:
            require(re.fullmatch(r"[a-z_]+", link.get("relation", "")), f"Unsupported relationship: {link['id']}")
            require(link["from"] and len(set(link["from"])) == len(link["from"]) and set(link["from"] + [link["to"]]) <= set(local), f"Missing endpoint: {link['id']}")
            if link["status"] == "accepted":
                require(all(local[i]["status"] == "accepted" for i in link["from"] + [link["to"]]), f"Accepted link needs accepted endpoints: {link['id']}")
        ids = set(local) | {l["id"] for l in tree["links"]}
        for task in tree["backlog"]:
            require(task["ref"] in ids and set(task) <= {"ref", "work", "label", "note"}, f"Invalid open work in {name}")
    for node in nodes_by_id.values():
        for trace in TRACES:
            require(set(node.get(trace, [])) <= set(nodes_by_id), f"Unpublished trace: {node['id']}")
    reports = set()
    for request in data["feedback"]:
        outcomes = [o["ref"] for o in request["benefits"] + request["reservations"]]
        for snap in [request["about"]] + request["benefits"] + request["reservations"]:
            require(snap["ref"] in nodes_by_id and snap.get("standing") == "proposed", f"Unpublished or accepted feedback statement: {snap['ref']}")
        require(set(request["feedback_from"]) <= approved and request["created_by"] in names, "Unselected feedback people")
        for report in request["reports"]:
            require(report["by"] in request["feedback_from"] and report["readiness"] in READINESS, f"Invalid report: {report['id']}")
            require(report["evidence_type"] == "self_report", f"Reports are attributed self-reports: {report['id']}")
            for answer in report["outcomes"]:
                require(answer["ref"] in outcomes and answer["verdict"] in VERDICTS, f"Invalid outcome: {report['id']}")
            reports.add(report["id"])
    for release in data["history"]:
        require(set(release) == {"release_id", "date", "title", "summary", "changes"}, "Unexpected history fields")
        for change in release["changes"]:
            require(change["type"] in CHANGE_TYPES - {"accepted", "disputed"} and set(change) <= {"type", "refs", "note", "before"}, "Unexpected change entry")
            require(set(change["refs"]) <= seen | reports, f"History refers to unpublished material in {release['release_id']}")
    require(data["history"] and data["history"][-1]["release_id"] == data["release_id"], "The latest history entry must be this release")


# ---------------------------------------------------------------- projection 4: an unendorsed, credited source reconstruction

# A forum credit names a post and its actual author; a document credit cites a section the analysis points to;
# the analysis itself reconstructs or infers. Each kind of source admits only its own bases.
REF_BASES = {"forum": {"paraphrase", "related"}, "document": {"cited"}, "analysis": {"reconstruction", "inference"},
             "supplied_document": {"paraphrase", "reconstruction", "inference", "related"},
             "web_page": {"inference", "related"},
             "supplied_analysis": {"paraphrase", "reconstruction", "inference", "related"}}


def source_kind(source):
    if source.get("kind") in {"supplied_document", "web_page", "supplied_analysis"}:
        return source["kind"]
    return "forum" if "posts" in source else "document" if "author" in source else "analysis"


def project_reconstruction(state, registry):
    """Reuse qualification checks without opening either existing publication boundary."""
    require(registry.get("publication_kind") == "source_reconstruction", "Not a source reconstruction")
    example_registry = {**registry, "is_example": True}
    result = project_v2(state, example_registry, check=False)
    result.pop("is_example")
    result.update(projection_version=4, publication_kind="source_reconstruction", authors=deepcopy(registry["authors"]),
                  sources=deepcopy(registry["sources"]), views=deepcopy(registry.get("views", {})),
                  overview=deepcopy(registry.get("overview", [])), retired=deepcopy(registry.get("retired", [])))
    for name, tree in result["trees"].items():
        source = state["trees"][name]
        for key in ("nodes", "links"):
            indexed = {item["id"]: item for item in source[key]}
            for item in tree[key]:
                item["source_refs"] = deepcopy(indexed[item["id"]].get("source_refs", []))
                if indexed[item["id"]].get("proposed_role"):
                    item["proposed_role"] = indexed[item["id"]]["proposed_role"]
        chosen = {i["id"] for i in tree["nodes"] + tree["links"]}
        for public, task in zip(tree["backlog"], [t for t in source.get("backlog", []) if t["ref"] in chosen]):
            if task.get("source_refs"):
                public["source_refs"] = deepcopy(task["source_refs"])
    validate_reconstruction(result, registry)
    return result


def validate_source_refs(refs, sources, ident):
    require(isinstance(refs, list) and refs, f"Missing source locator: {ident}")
    for ref in refs:
        source = sources.get(ref.get("source_id")) if isinstance(ref, dict) else None
        require(source is not None, f"Invalid source locator: {ident}")
        kind = source_kind(source)
        if kind == "forum":
            require(set(ref) == {"source_id", "post", "author", "basis"} and type(ref["post"]) is int and str(ref["post"]) in source["posts"], f"Invalid source locator: {ident}")
            require(ref["author"] == source["posts"][str(ref["post"])]["author"], f"Credit names someone other than the author of post {ref['post']}: {ident}")
        else:
            require(set(ref) == {"source_id", "locator", "basis"} and isinstance(ref["locator"], str) and ref["locator"].strip(), f"Invalid source locator: {ident}")
        require(ref["basis"] in REF_BASES[kind], f"Invalid source locator: {ident}")


def validate_views(data):
    for name, views in data["views"].items():
        require(name in data["trees"] and isinstance(views, list) and views, f"Views for an unpublished tree: {name}")
        tree = data["trees"][name]
        node_ids, covered, seen = {n["id"] for n in tree["nodes"]}, set(), set()
        for view in views:
            require(isinstance(view, dict) and set(view) == {"id", "title", "summary", "nodes"} and re.fullmatch(r"[a-z0-9-]+", view["id"]) and view["id"] not in seen, f"Invalid view in {name}")
            require(all(isinstance(view[k], str) and view[k].strip() for k in ("title", "summary")), f"Invalid view in {name}")
            members = set(view["nodes"])
            require(view["nodes"] and len(members) == len(view["nodes"]) and members <= node_ids, f"View {view['id']} names unpublished statements")
            seen.add(view["id"])
            covered |= members
        require(covered == node_ids, f"Every statement in {name} must appear in a view")  # So every connection is drawn where its target is.


OVERVIEW_BLOCKS = {"account": {"eyebrow", "title", "text", "ids", "link"},
                   "cards": {"eyebrow", "title", "text", "ids", "link"}, "spine": {"eyebrow", "title", "text", "hops"},
                   "clouds": {"eyebrow", "title", "text", "featured"}, "wider": {"eyebrow", "title", "text"}, "credits": {"eyebrow", "title", "text"}}
TRACE_HOPS = {"addresses", "derived_from", "implements"}


def validate_overview(data, items, tree_of):
    require(isinstance(data["overview"], list), "Invalid overview")
    for index, block in enumerate(data["overview"]):
        kind = block.get("type") if isinstance(block, dict) else None
        require(kind in OVERVIEW_BLOCKS and set(block) == OVERVIEW_BLOCKS[kind] | {"type"}, "Invalid overview block")
        require(all(isinstance(block[k], str) and block[k].strip() for k in ("eyebrow", "title", "text")), "Invalid overview copy")
        if kind in {"cards", "account"}:
            require(block["ids"] and all(i in items for i in block["ids"]), "Overview names unpublished items")
            require(isinstance(block["link"], list) and len(block["link"]) == 2 and all(isinstance(x, str) and x for x in block["link"]), "Invalid overview link")
        if kind == "account":
            require(index == 0 and all(source_kind(s) == "supplied_document" for s in data["sources"]),
                    "A source account must come first and refer to supplied documents")
            require(all(items[i].get("kind") == "observation" for i in block["ids"]),
                    "A source account must identify attributed observations, not practical predictions")
        if kind == "clouds":
            require(block["featured"] in {v["id"] for v in data["views"].get("conflict", [])}, "The featured conflict must be a conflict view")
        if kind == "spine":  # Every step of the path is a published link or cross-tree reference.
            for hop in block["hops"]:
                require(set(hop) == {"from", "to", "via"} and hop["from"] in items and hop["to"] in items, "Invalid path step")
                if hop["via"] in TRACE_HOPS:
                    require(hop["to"] in items[hop["from"]].get(hop["via"], []), f"No published reference from {hop['from']} to {hop['to']}")
                else:
                    require(hop["via"] == "path" and tree_of[hop["from"]] == tree_of[hop["to"]]
                            and diagrams.path_between(data["trees"][tree_of[hop["from"]]], hop["from"], hop["to"]) is not None, f"No published path from {hop['from']} to {hop['to']}")


def validate_reconstruction(data, registry):
    require(data.get("projection_version") == 4 and data.get("publication_kind") == registry.get("publication_kind") == "source_reconstruction", "Unsupported reconstruction publication")
    require(set(data) == {"projection_version", "publication_kind", "release_id", "snapshot_date", "title", "people", "authors", "trees", "feedback", "history", "sources", "views", "overview", "retired"}, "Unexpected reconstruction field")
    authors = data["authors"]
    require(authors == registry["authors"] and isinstance(authors, dict) and authors, "Unreviewed reconstruction authors")
    for key, person in authors.items():
        require(re.fullmatch(r"[a-z0-9-]+", key) and isinstance(person, dict) and set(person) == {"name", "role"} and all(isinstance(v, str) and v.strip() for v in person.values()), "Invalid source author")
    require(data["sources"] == registry["sources"] and data["sources"], "Unreviewed reconstruction sources")
    sources = {}
    for source in data["sources"]:
        kind = source_kind(source)
        extra = ({"url", "posts"} if kind == "forum" else {"author", "shared_in_post"} if kind == "document"
                 else {"kind", "author", "url"} if kind in {"web_page", "supplied_analysis"} else {"kind", "author"} if kind in {"supplied_document", "supplied_analysis"} else set())
        if kind == "supplied_document" and "url" in source:  # A supplied document its author has published elsewhere.
            extra = extra | {"url"}
            require(isinstance(source["url"], str) and source["url"].startswith("https://"), f"Invalid supplied document link: {source['id']}")
        require(set(source) == {"id", "title", "description"} | extra and all(isinstance(source[k], str) and source[k].strip() for k in ("id", "title", "description")), "Invalid source description")
        require(re.fullmatch(r"[a-z0-9-]+", source["id"]) and source["id"] not in sources, "Invalid/duplicate source ID")
        if kind == "forum":
            require(isinstance(source["url"], str) and source["url"].startswith("https://") and isinstance(source["posts"], dict) and source["posts"], "Invalid forum source")
            for number, post in source["posts"].items():
                require(number.isdigit() and isinstance(post, dict) and set(post) == {"author", "date"} and post["author"] in authors and re.fullmatch(r"\d{4}-\d{2}-\d{2}", post["date"]), "Invalid forum post")
        if kind in {"web_page", "supplied_analysis"}:
            require(source["author"] in authors and isinstance(source["url"], str) and source["url"].startswith("https://"), "Invalid public web source")
        if kind in {"supplied_document", "supplied_analysis"}:
            require(source["author"] in authors, f"Unknown supplied document author: {source['id']}")
        sources[source["id"]] = source
    forums = [s for s in sources.values() if source_kind(s) == "forum"]
    require(len(forums) <= 1, "A reconstruction cites one forum thread")
    for source in sources.values():
        if source_kind(source) == "document":
            shared = str(source["shared_in_post"]) if type(source["shared_in_post"]) is int else None
            require(source["author"] in authors and forums and shared in forums[0]["posts"] and forums[0]["posts"][shared]["author"] == source["author"],
                    f"A document must be shared in a post by its author: {source['id']}")
    require(data["views"] == registry.get("views", {}) and isinstance(data["views"], dict), "Unreviewed views")
    validate_views(data)
    items = {i["id"]: i for t in data["trees"].values() for i in t["nodes"] + t["links"]}
    tree_of = {i["id"]: name for name, t in data["trees"].items() for i in t["nodes"] + t["links"]}
    require(data["overview"] == registry.get("overview", []), "Unreviewed overview")
    validate_overview(data, items, tree_of)
    require(data["retired"] == registry.get("retired", []) and isinstance(data["retired"], list), "Unreviewed retired items")
    retired = set()
    for gone in data["retired"]:  # Removed items stay nameable in history, never published as current.
        require(isinstance(gone, dict) and set(gone) == {"id", "release_id", "text", "note"} and all(isinstance(v, str) and v.strip() for v in gone.values()), "Invalid retired item")
        require(gone["id"] not in items and gone["id"] not in retired, f"A retired item cannot be published: {gone['id']}")
        retired.add(gone["id"])
    require(not data["feedback"] and not registry["feedback"], "A reconstruction cannot invent feedback commitments or reports")
    contribution_sources = registry.get("contribution_sources", {})
    require(isinstance(contribution_sources, dict), "Invalid analysis contribution policy")
    for participant, source_id in contribution_sources.items():
        source = sources.get(source_id)
        require(participant in registry["people"] and source is not None and source_kind(source) == "supplied_analysis",
                "Human analysis contributions require an explicitly selected supplied analysis")
        require(authors[source["author"]]["name"] == registry["people"][participant], "Analysis contributor must be the source author")
    qualified = deepcopy(data)
    for field in ("publication_kind", "authors", "sources", "views", "overview", "retired"):
        qualified.pop(field)
    qualified.update(projection_version=2, is_example=True)
    for tree in qualified["trees"].values():
        for item in tree["nodes"] + tree["links"]:
            require(item.get("status") == "proposed" and not item.get("accepted_by"), "A reconstruction must remain proposed without endorsers")
            refs = item.pop("source_refs", [])
            validate_source_refs(refs, sources, item["id"])
            if item.get("contributors") != [ASSISTANT]:
                allowed = [{"name": registry["people"][who], "role": "human"} for who, source_id in contribution_sources.items()
                           if any(ref["source_id"] == source_id and ref["basis"] in {"paraphrase", "reconstruction"} for ref in refs)]
                require(item.get("contributors") and all(c in allowed for c in item["contributors"]),
                        "A reconstruction cannot imply direct participant authorship without a matching reviewed analysis")
            if "proposed_role" in item:  # A role someone might take on, never an assignment.
                role = item.pop("proposed_role")
                require(item.get("kind") == "action" and isinstance(role, str) and role.strip(), f"Only an action can carry a proposed role: {item['id']}")
        for task in tree["backlog"]:
            if "source_refs" in task:
                validate_source_refs(task.pop("source_refs"), sources, f"open work on {task.get('ref')}")
    require(all(change["type"] in {"added", "credited", "revised", "removed"} for release in data["history"] for change in release["changes"]), "Reconstruction history cannot invent prior endorsement or results")
    for release in qualified["history"]:
        for change in release["changes"]:
            require(change["type"] != "removed" or set(change["refs"]) <= retired, "Only retired items can be recorded as removed")
            change["refs"] = [ref for ref in change["refs"] if ref not in retired]
        release["changes"] = [change for change in release["changes"] if change["refs"]]
    validate_v2(qualified, {**registry, "is_example": True})


# ---------------------------------------------------------------- site

def validate_front_page(entry, data):
    """Editorial invitations may refer to published items, never override reasoning or standing."""
    front = entry.get("front_page")
    if front is None:
        return
    require(isinstance(front, dict) and set(front) == {"headline", "intro", "question", "why", "focus_ref"}
            and all(isinstance(v, str) and v.strip() for v in front.values()), "Invalid front-page invitation")
    ids = {i["id"] for tree in data["trees"].values() for i in tree["nodes"] + tree["links"]}
    require(front["focus_ref"] in ids, "Featured invitation must reference published reasoning")


def load_site():
    site = read_json(HERE / "site.json")
    require(site.get("contribution_url") == "https://github.com/reasoncommons/reasoncommons/issues/new", "Unreviewed public contribution destination")
    commons = []
    for entry in site["commons"]:
        registry = read_json(HERE / entry["registry"])
        data = registry["snapshot"]
        if data.get("projection_version") == 1:
            require(entry["kind"] == "real", "Only the Reason Commons commons publishes acceptances")
            validate_projection(data, registry)
        elif data.get("projection_version") == 4:
            require(entry["kind"] == "reconstruction", "Only a labelled reconstruction uses projection 4")
            validate_reconstruction(data, registry)
        else:
            require(entry["kind"] == "example", "Only the labelled example uses projection 2")
            validate_v2(data, registry)
        require(registry.get("snapshot_sha256") == digest(data), f"Public snapshot fingerprint changed for {entry['slug']}; review and refresh explicitly")
        validate_front_page(entry, data)
        review_path = (HERE / entry["registry"]).with_name("review.json")
        review = revisions.validate(read_json(review_path), data, validate_reconstruction) if review_path.exists() else {}
        commons.append({"entry": entry, "registry": registry, "data": data, "review": review})
    taken = {c["entry"]["slug"] for c in commons}
    for path in sorted(SUBMISSIONS.glob("*/publication.json")):
        data = submissions.validate(read_json(path), taken)
        require(data["slug"] == path.parent.name, f"submissions/{path.parent.name}: the folder must be named after its slug, {data['slug']}")
        require(sorted(p.name for p in path.parent.iterdir()) == ["publication.json"], f"submissions/{path.parent.name} may hold only publication.json")
        taken.add(data["slug"])
        commons.append({"entry": {"slug": data["slug"], "kind": "shared"}, "submission": data})
    return site, commons


def validate_source_questions(data, sources):
    """A source agenda is a hierarchy of questions, never a graph of asserted causes."""
    require(isinstance(data, dict) and set(data) == {"source_id", "retrieved_on", "sha256", "governing_question", "questions"}, "Invalid source question record")
    source = next((s for s in sources if s["id"] == data["source_id"] and source_kind(s) == "web_page"), None)
    require(source is not None, "Source questions need a reviewed public web source")
    require(isinstance(data["retrieved_on"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["retrieved_on"]), "Invalid source capture date")
    require(isinstance(data["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", data["sha256"]), "Invalid source capture fingerprint")
    require(isinstance(data["governing_question"], str) and data["governing_question"].strip(), "Missing governing question")
    require(isinstance(data["questions"], list) and data["questions"], "Missing source question trees")
    seen = set()
    def visit(node):
        require(isinstance(node, dict) and set(node) == {"id", "text", "source_url", "children"}, "Invalid source question")
        ident = node["id"]
        require(isinstance(ident, str) and re.fullmatch(r"[a-z0-9-]+", ident) and ident not in seen, "Invalid or duplicate source question ID")
        seen.add(ident)
        require(isinstance(node["text"], str) and node["text"].strip(), "Empty source question")
        require(isinstance(node["source_url"], str) and node["source_url"].startswith(source["url"] + "#"), "Source question URL must stay within its reviewed page")
        require(isinstance(node["children"], list), "Invalid source subquestions")
        for child in node["children"]:
            visit(child)
    for node in data["questions"]:
        visit(node)


def publication_archives(registry, current):
    archives = {}
    for archive in registry.get("previous_releases", []):
        require(isinstance(archive, dict) and set(archive) == {"commit", "snapshot_sha256", "snapshot", "contribution_sources"}, "Invalid previous release")
        require(re.fullmatch(r"[0-9a-f]{40}", archive.get("commit", "")), "Invalid previous release commit")
        snapshot = archive["snapshot"]
        require(digest(snapshot) == archive["snapshot_sha256"], "Previous release fingerprint changed")
        historical = {k: snapshot[k] for k in ("publication_kind", "authors", "sources", "views", "overview", "retired")}
        # Resolve IDs from the archived author names, not current roles or endorsements.
        historical.update(people={str(i): p["name"] for i, p in enumerate(snapshot["people"])}, feedback=[],
                          selection={name: {key: [item["id"] for item in tree[key]] for key in ("nodes", "links")} for name, tree in snapshot["trees"].items()})
        policy = archive["contribution_sources"]
        require(isinstance(policy, dict), "Invalid archived analysis contribution policy")
        historical["contribution_sources"] = {key: policy[person] for key, person in historical["people"].items() if person in policy}
        require(set(policy) <= set(historical["people"].values()), "Unknown archived analysis contributor")
        validate_reconstruction(snapshot, historical)
        ident = snapshot["release_id"]
        require(ident not in archives and ident != current["release_id"], "Duplicate previous release")
        archives[ident] = snapshot
    if archives:
        require(set(archives) == {h["release_id"] for h in current["history"][:-1]}, "Previous release/history mismatch")
    return archives


def normalize(item):
    """One reading of either projection for the pages; nothing is added that the projection lacks."""
    if "submission" in item:
        return submissions.to_pages(item["submission"])
    presentation = item["registry"].get("presentation", {})
    require(isinstance(presentation, dict) and set(presentation) <= {"summary", "description", "scope"}
            and all(isinstance(v, str) and v.strip() for v in presentation.values()), "Invalid reviewed presentation")
    entry, data = {**item["entry"], **presentation}, item["data"]
    trees = {}
    for name in pages.TREE_ORDER:
        if name not in data["trees"]:
            continue
        source = data["trees"][name]
        nodes = [{"assumptions": [], "challenges": [], **n} for n in source["nodes"]]
        links = [{"assumptions": [], "challenges": [], **l} for l in source["links"]]
        trees[name] = {"name": name, "nodes": nodes, "links": links, "backlog": source.get("backlog", [])}
    if data["projection_version"] == 1:
        people = [{"name": n, "role": ""} for n in item["registry"]["people"].values()]
        history = [{"release_id": data["release_id"], "date": data["snapshot_date"], "title": "This release",
                    "summary": "Statements and connections selected from the working record with their original wording: accepted ones with their named endorsers and recorded context, and proposed ones that nobody has accepted yet.",
                    "changes": [{"type": "added", "refs": [i["id"] for t in trees.values() for i in t["nodes"] + t["links"]]}]}]
        feedback = []
    else:
        people, history, feedback = data["people"], data["history"], data["feedback"]
    source_questions = {}
    if item["registry"].get("source_questions"):
        relative = item["registry"]["source_questions"]
        require(relative == "source-questions.json", "Source question companion must use its declared file")
        source_questions = read_json((HERE / item["entry"]["registry"]).with_name(relative))
        validate_source_questions(source_questions, data["sources"])
        def question_texts(nodes):
            return {node["text"].removeprefix("So: ").casefold() for node in nodes} | set().union(*(question_texts(node["children"]) for node in nodes))
        locators = question_texts(source_questions["questions"])
        for tree in data["trees"].values():
            for published_item in tree["nodes"] + tree["links"]:
                for ref in published_item.get("source_refs", []):
                    if ref["source_id"] == source_questions["source_id"]:
                        require(ref["locator"].casefold() in locators, f"Unresolved source question: {published_item['id']}")
    archives = publication_archives(item["registry"], data) if item["registry"].get("previous_releases") else {}
    return {**entry, "archives": archives, "source_questions": source_questions, "is_example": entry["kind"] == "example", "is_reconstruction": entry["kind"] == "reconstruction", "sources": data.get("sources", []),
            "authors": data.get("authors", {}), "views": data.get("views", {}), "overview_blocks": data.get("overview", []), "retired": data.get("retired", []),
            "release_id": data["release_id"], "date": data["snapshot_date"],
            "title": data["title"], "review": item.get("review", {}), "people": people, "trees": trees, "feedback": feedback, "history": history,
            "json": json.dumps(data, ensure_ascii=False, indent=2) + "\n"}


def build_files(site, commons):
    normalized = [normalize(c) for c in commons]
    styles = (HERE / "styles.css").read_text()
    script = (HERE / "app.js").read_text()
    asset_versions = {"styles": hashlib.sha256(styles.encode()).hexdigest()[:16],
                      "script": hashlib.sha256(script.encode()).hexdigest()[:16]}
    outputs = pages.render(site, normalized, asset_versions=asset_versions)
    real = next(c for c in commons if c["entry"]["kind"] == "real")
    outputs["reasoning.json"] = json.dumps(real["data"], ensure_ascii=False, indent=2) + "\n"  # The earlier download path stays.
    for c in normalized:
        outputs[f'{c["slug"]}/reasoning.json'] = c["json"]
    outputs["styles.css"] = styles
    outputs["app.js"] = script
    for font in sorted((HERE / "fonts").iterdir()):
        outputs[f"fonts/{font.name}"] = font.read_bytes()
    return outputs


def refresh(registry, source):
    module = skill_helpers()
    state = module.load(source)
    module.validate(state)
    snapshot = project(state, registry)
    # Approval selects IDs, not whatever might be accepted by a future build.
    registry = deepcopy(registry)
    registry["snapshot"] = snapshot
    registry["snapshot_sha256"] = digest(snapshot)
    return registry


def refresh_example(entry, registry):
    module = skill_helpers()
    state = module.load(HERE / entry["source"])
    module.validate(state)
    registry = deepcopy(registry)
    registry["snapshot"] = project_v2(state, registry)
    registry["snapshot_sha256"] = digest(registry["snapshot"])
    return registry


def refresh_reconstruction(entry, registry):
    module = skill_helpers()
    state = module.load(HERE / entry["source"])
    module.validate(state)
    registry = deepcopy(registry)
    registry["snapshot"] = project_reconstruction(state, registry)
    registry["snapshot_sha256"] = digest(registry["snapshot"])
    return registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", type=Path, help="Explicit authorized working YAML; refresh only our selected public items and fields")
    parser.add_argument("--refresh-example", action="store_true", help="Re-project the fictional example from its public working file")
    parser.add_argument("--refresh-reconstruction", action="store_true", help="Re-project the selected public source reconstruction")
    parser.add_argument("--check", action="store_true", help="Read-only check of the reviewed snapshots and generated files")
    args = parser.parse_args()
    require(not ((args.refresh or args.refresh_example or args.refresh_reconstruction) and args.check), "Refresh and check are separate operations")
    site = read_json(HERE / "site.json")
    for entry in site["commons"]:
        path = HERE / entry["registry"]
        if entry["kind"] == "real" and args.refresh:
            path.write_text(json.dumps(refresh(read_json(path), args.refresh), ensure_ascii=False, indent=2) + "\n")
        if entry["kind"] == "example" and args.refresh_example:
            path.write_text(json.dumps(refresh_example(entry, read_json(path)), ensure_ascii=False, indent=2) + "\n")
        if entry["kind"] == "reconstruction" and args.refresh_reconstruction:
            path.write_text(json.dumps(refresh_reconstruction(entry, read_json(path)), ensure_ascii=False, indent=2) + "\n")
    site, commons = load_site()
    if args.check:
        for c in commons:  # The example must still be exactly what its working file projects to.
            if c["entry"]["kind"] in {"example", "reconstruction"}:
                try:
                    refresher = refresh_example if c["entry"]["kind"] == "example" else refresh_reconstruction
                    fresh = refresher(c["entry"], c["registry"])["snapshot"]
                except ModuleNotFoundError:
                    print("PyYAML unavailable: example working file not re-projected", file=sys.stderr)
                else:
                    require(fresh == c["data"], "Example snapshot no longer matches its working file; run --refresh-example")
    outputs = build_files(site, commons)
    if args.check:
        drift = [name for name, value in outputs.items()
                 if not (DEST / name).is_file() or (DEST / name).read_bytes() != (value if isinstance(value, bytes) else value.encode())]
        extra = sorted(str(p.relative_to(DEST)) for p in DEST.rglob("*") if p.is_file() and str(p.relative_to(DEST)) not in outputs)
        require(not drift, "Generated site drift: " + ", ".join(drift))
        require(not extra, "Unexpected files in the published folder: " + ", ".join(extra))
        print(f"Reviewed snapshots and all {len(outputs)} generated files: current")
    else:
        for name, value in outputs.items():
            target = DEST / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(value, bytes):
                target.write_bytes(value)
            else:
                target.write_text(value)
        print(f"Built {DEST.relative_to(ROOT)}: {len(outputs)} files from reviewed public snapshots")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(f"Demo build failed: {error}", file=sys.stderr)
        sys.exit(1)
