"""Commons shared by their own participants: the publication file, its checks, and the pages' reading of it.

A group using the ltp skill chooses what to share, each named person consents to being named, and the skill writes
one `publication.json`. It arrives by pull request in `submissions/<slug>/`; a maintainer reviews it before it goes
live. The same checks run in the skill before anything is shared and in the site build, which is why this module
depends only on the renderer (`pages`, `diagrams`) and is copied into the skill with it.
"""
from copy import deepcopy
import json
import re

import diagrams
import pages

VERSION = 1
LICENCE = pages.SHARED_LICENCE[0]
CONSENT_HOW = pages.CONSENT_HOW
ASSISTANT = "AI assistant"
TREE_KINDS = {  # The skill's schema; test_build checks it matches the build's.
    "goal": {"goal", "critical_success_factor", "necessary_condition"},
    "current_reality": {"undesirable_effect", "cause"},
    "conflict": {"objective", "need", "prerequisite"},
    "future_reality": {"injection", "existing_condition", "predicted_effect", "desirable_effect", "undesirable_effect"},
    "prerequisite": {"objective", "obstacle", "intermediate_objective"},
    "transition": {"existing_condition", "need", "action", "expected_effect"},
}
TRACES = ("addresses", "derived_from", "implements")
FIELDS = {"submission_version", "slug", "title", "summary", "submitted_by", "licence", "released_on", "people", "trees"}
NODE_FIELDS = {"id", "kind", "text", "label", "status", "accepted_by", "contributors", "assumptions", "challenges", *TRACES}
LINK_FIELDS = {"id", "from", "to", "relation", "status", "accepted_by", "contributors", "assumptions", "challenges"}
SLUG = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,46}[a-z0-9])?")
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")
GITHUB = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
RESERVED = {"index", "how-it-works", "styles", "app", "fonts", "reasoning", "submissions"}
MAX_ITEMS = 1000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, limit):
    return isinstance(value, str) and value.strip() != "" and len(value) <= limit and value == value.strip()


def validate(data, taken=()):
    """Every check a shared commons must pass, in the skill and in the build. `taken` holds slugs already in use."""
    require(isinstance(data, dict) and set(data) == FIELDS, "A shared commons has exactly these fields: " + ", ".join(sorted(FIELDS)))
    require(data["submission_version"] == VERSION, f"Unsupported submission version: {data['submission_version']}")
    slug = data["slug"]
    require(isinstance(slug, str) and SLUG.fullmatch(slug) and slug not in RESERVED, f"Invalid slug: {slug!r}; use lower-case letters, digits and hyphens")
    require(slug not in set(taken), f"The slug {slug!r} is already used on the site")
    require(text(data["title"], 80), "The title must be 1 to 80 characters")
    require(text(data["summary"], 300), "The summary must be 1 to 300 characters")
    by = data["submitted_by"]
    require(isinstance(by, dict) and set(by) == {"name", "github"} and text(by["name"], 80)
            and isinstance(by["github"], str) and GITHUB.fullmatch(by["github"]), "submitted_by needs a name and a GitHub username")
    require(data["licence"] == LICENCE, f"Shared commons are published under {LICENCE}")
    require(isinstance(data["released_on"], str) and DATE.fullmatch(data["released_on"]), "released_on must be a YYYY-MM-DD date")
    people = data["people"]
    require(isinstance(people, list), "people must be a list")
    named = set()
    for person in people:
        require(isinstance(person, dict) and set(person) == {"name", "consent"} and text(person["name"], 80), "Each person needs a name and a consent")
        require(person["name"] not in named and person["name"] != ASSISTANT, f"Invalid or repeated person: {person['name']}")
        consent = person["consent"]
        require(isinstance(consent, dict) and set(consent) == {"given_on", "how"} and isinstance(consent["given_on"], str)
                and DATE.fullmatch(consent["given_on"]) and consent["how"] in CONSENT_HOW, f"Invalid consent for {person['name']}")
        named.add(person["name"])
    require(by["name"] in named, "The person who shares it must be named with their consent")
    trees = data["trees"]
    require(isinstance(trees, dict) and trees and set(trees) <= set(TREE_KINDS), "trees must hold one or more of: " + ", ".join(TREE_KINDS))
    seen, nodes_of, missing = set(), {}, set()

    def names(values, where, humans_only=False):
        require(isinstance(values, list) and all(isinstance(v, str) for v in values), f"Invalid names in {where}")
        for name in values:
            require(not (humans_only and name == ASSISTANT), f"Only people can accept: {where}")
            if name != ASSISTANT and name not in named:
                missing.add(name)

    for name, tree in trees.items():
        require(isinstance(tree, dict) and set(tree) == {"nodes", "links", "backlog"}
                and all(isinstance(tree[k], list) for k in tree), f"{name} needs nodes, links and backlog lists")
        local = {}
        for key, allowed in (("nodes", NODE_FIELDS), ("links", LINK_FIELDS)):
            for item in tree[key]:
                require(isinstance(item, dict), f"Invalid item in {name}")
                ident = item.get("id")
                require(isinstance(ident, str) and IDENT.fullmatch(ident) and ident not in seen, f"Invalid or repeated ID: {ident!r}")
                seen.add(ident)
                required = {"id", "status", "accepted_by", "contributors"} | ({"kind", "text"} if key == "nodes" else {"from", "to", "relation"})
                require(required <= set(item) <= allowed, f"Unexpected or missing fields on {ident}")
                status = item["status"]
                require(status in pages.STANDING, f"Invalid standing on {ident}")
                names(item["accepted_by"], ident, humans_only=True)
                require(bool(item["accepted_by"]) == (status == "accepted") or status == "disputed", f"Only an accepted item lists who accepted it, and it must: {ident}")
                names(item["contributors"], ident)
                require(item["contributors"], f"Who contributed {ident} is missing")
                for note in ("assumptions", "challenges"):
                    entries = item.get(note, [])
                    require(isinstance(entries, list), f"Invalid {note} on {ident}")
                    for entry in entries:
                        require(isinstance(entry, dict) and set(entry) == {"text", "by"} and text(entry["text"], 2000), f"Invalid {note} on {ident}")
                        names([entry["by"]], ident)
                if key == "nodes":
                    require(item["kind"] in TREE_KINDS[name] | {"observation"}, f"Invalid kind on {ident}: {item['kind']}")
                    require(text(item["text"], 2000), f"Invalid statement text on {ident}")
                    require("label" not in item or text(item["label"], 100), f"A label is one line of up to 100 characters: {ident}")
                    local[ident] = item
                    nodes_of[ident] = item
        for link in tree["links"]:
            ident = link["id"]
            ends = link["from"] + [link["to"]] if isinstance(link["from"], list) else []
            require(link["from"] and len(set(link["from"])) == len(link["from"]) and set(ends) <= set(local), f"A connection's ends must be statements in the same tree: {ident}")
            require(isinstance(link["relation"], str) and re.fullmatch(r"[a-z_]{1,40}", link["relation"]), f"Invalid relation on {ident}")
            require(link["status"] != "accepted" or all(local[e]["status"] == "accepted" for e in ends), f"An accepted connection needs accepted ends: {ident}")
        ids = set(local) | {l["id"] for l in tree["links"]}
        for task in tree["backlog"]:
            require(isinstance(task, dict) and {"ref", "work"} <= set(task) <= {"ref", "work", "label", "note"} and task["ref"] in ids
                    and text(task["work"], 80) and all(text(task[k], 2000) for k in ("label", "note") if k in task), f"Invalid open work in {name}")
    require(seen, "There are no statements to share")
    require(len(seen) <= MAX_ITEMS, f"At most {MAX_ITEMS} statements and connections can be shared")
    for item in nodes_of.values():
        for trace in TRACES:
            refs = item.get(trace, [])
            require(isinstance(refs, list) and set(refs) <= set(nodes_of), f"{trace} on {item['id']} names a statement that isn't shared")
    require(not missing, "Named without their consent: " + ", ".join(sorted(missing)))
    return data


def to_pages(data):
    """The pages' reading of a shared commons; it adds nothing the file lacks."""
    people = [p["name"] for p in data["people"]]
    trees = {}
    for name in pages.TREE_ORDER:
        if name not in data["trees"]:
            continue
        source = deepcopy(data["trees"][name])

        def credit(names):
            return [{"name": n, "role": "assistant" if n == ASSISTANT else "human"} for n in names]
        nodes = [{**n, "contributors": credit(n["contributors"]), "assumptions": n.get("assumptions", []), "challenges": n.get("challenges", [])} for n in source["nodes"]]
        links = [{**l, "contributors": credit(l["contributors"]), "assumptions": l.get("assumptions", []), "challenges": l.get("challenges", [])} for l in source["links"]]
        closing = diagrams.loop_links(links)
        for link in links:  # Drawn round the side; the relation stays as shared.
            if link["id"] in closing:
                link["loop"] = True
        trees[name] = {"name": name, "nodes": nodes, "links": links, "backlog": source["backlog"]}
    statements = sum(len(t["nodes"]) for t in trees.values())
    connections = sum(len(t["links"]) for t in trees.values())
    focus = None
    if "current_reality" in trees:
        parts, _ = diagrams.components(trees["current_reality"])
        if parts:
            focus = max(parts, key=lambda p: len(p["ids"]))["ids"][0]
    return {
        "slug": data["slug"], "kind": "shared", "name": data["title"], "title": data["title"], "byline": pages.names(people),
        "summary": data["summary"], "description": f"{pages.plural(statements, 'statement')} and {pages.plural(connections, 'connection')}, shared by {pages.names(people)}.",
        "scope": "What the people named here chose to share from their working record, each standing as they recorded it. Reason Commons reviewed the submission but hasn't checked the reasoning.",
        "overview": {"conditions": "What the goal needs, as the people who shared it record it.",
                     "obstacles": "Read from the bottom up: each arrow means “contributes to”. The largest connected part is shown here.",
                     "obstacles_focus": focus,
                     "change": "Where needs pull two ways, as recorded, and any change that has been accepted.",
                     "actions": "The actions recorded, each with what it should achieve.",
                     "learning": "What people reported after trying a change."},
        "is_shared": True, "is_example": False, "is_reconstruction": False,
        "submitted_by": deepcopy(data["submitted_by"]), "licence": data["licence"],
        "consents": [{"name": p["name"], **p["consent"]} for p in data["people"]],
        "archives": {}, "source_questions": {}, "sources": [], "authors": {}, "views": {}, "overview_blocks": [], "retired": [], "review": {},
        "release_id": data["released_on"], "date": data["released_on"],
        "people": [{"name": n, "role": "Shared it" if n == data["submitted_by"]["name"] else ""} for n in people],
        "trees": trees, "feedback": [], "history": [],
        "json": json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    }
