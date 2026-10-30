#!/usr/bin/env python3
"""Show a whole commons in the browser, privately: turn a working YAML file into linked pages on this computer.

The file is checked with the skill's own validator, then every tree is written as the pages the Reason Commons
demo site uses for one commons: accepted, proposed and disputed items as recorded, participants' names,
assumptions, challenges, open work and outcome reports. Nothing is published or sent anywhere. The pages go to a
`site` folder in the file's hidden directory (`reason-commons.yaml` → `.reason-commons/site/`). `--serve` serves
them on 127.0.0.1 only, for a browser that will not open local files.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from functools import partial
import http.server
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
VIEWER = HERE.parent / "viewer"  # A copy of the demo site's renderer; see viewer/README.md.
sys.path.insert(0, str(VIEWER))
import pages  # noqa: E402

_views_spec = importlib.util.spec_from_file_location("reason_commons_views", HERE / "update_views.py")
views = importlib.util.module_from_spec(_views_spec)
_views_spec.loader.exec_module(views)

SLUG = "commons"
MANIFEST = ".ltp-site"  # The files this helper wrote, so a rebuild removes only its own stale pages.
TRACES = ("addresses", "derived_from", "implements")
ASSISTANT = {"name": "AI assistant", "role": "assistant"}
UNKNOWN = {"name": "Original contributor not identified", "role": "unknown"}
SITE = {"site_version": 1, "base_url": pages.PUBLIC_ROOT + "/demos/reason-commons-in-use/", "contribution_url": ""}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def display_names(state):
    people = {}
    for key, value in state.get("participants", {}).items():
        name = value.get("name") if isinstance(value, dict) else value
        people[key] = str(name or key)
    return people


def who(person, people):
    return ASSISTANT["name"] if person == "assistant" else people.get(person, person)


def contributors(item, people):
    result = []
    for contribution in item.get("contributions", []):
        entry = dict(ASSISTANT) if contribution["by"] == "assistant" else {"name": who(contribution["by"], people), "role": "human"}
        if entry not in result:
            result.append(entry)
    return result or [dict(UNKNOWN)]


def project(state, source_file, made_at):
    """Everything the pages show, from the whole working file; nothing is selected out but capture details and receipts."""
    people = display_names(state)
    present = [name for name in pages.TREE_ORDER if state.get("trees", {}).get(name, {}).get("nodes")]
    node_ids = {n["id"] for name in present for n in state["trees"][name]["nodes"]}
    trees = {}
    for name in present:
        source = state["trees"][name]
        tree = {"name": name, "nodes": [], "links": [], "backlog": []}
        for key in ("nodes", "links"):
            for item in source.get(key, []):
                public = {"id": item["id"], "status": item.get("status", "proposed"),
                          "accepted_by": [who(p, people) for p in item.get("accepted_by", [])],
                          "contributors": contributors(item, people)}
                for note in ("assumptions", "challenges"):
                    public[note] = [{"text": n["text"], "by": who(n["by"], people)} for n in item.get(note, [])]
                if key == "nodes":
                    public.update(kind=item["kind"], text=item["text"])
                    if item.get("label"):
                        public["label"] = item["label"]
                    for trace in TRACES:
                        refs = [r for r in item.get(trace, []) if r in node_ids]
                        if refs:
                            public[trace] = refs
                else:
                    public.update({"from": list(item["from"]), "to": item["to"], "relation": item["relation"]})
                tree[key].append(public)
        closing = pages.diagrams.loop_links(tree["links"])
        for link in tree["links"]:  # Drawn round the side, as the site draws a feedback loop; the relation stays as recorded.
            if link["id"] in closing:
                link["loop"] = True
        ids = {i["id"] for i in tree["nodes"] + tree["links"]}
        tree["backlog"] =[{k: task[k] for k in ("ref", "work", "label", "note") if k in task}
                           for task in source.get("backlog", []) if task.get("ref") in ids]
        trees[name] = tree
    require(trees, "No reasoning has been recorded yet, so there is nothing to show.")
    requests = state.get("feedback_requests", [])
    repeated = {r["id"] for r in requests if sum(1 for o in requests if o["id"] == r["id"]) > 1}
    feedback = []
    for request in requests:  # Each expectations version keeps its own reports.
        public = {k: deepcopy(request[k]) for k in ("revision", "recorded_at", "about", "benefits", "reservations") if k in request}
        public["id"] = f'{request["id"]}-v{request["revision"]}' if request["id"] in repeated else request["id"]
        public.update(created_by=who(request["created_by"], people), feedback_from=[who(p, people) for p in request["feedback_from"]])
        if request.get("ready_when"):
            public["ready_when"] = request["ready_when"]
        public["reports"] = [{"id": r["id"], "by": who(r["by"], people), "recorded_at": r["recorded_at"], "readiness": r["readiness"], "text": r["text"],
                              "outcomes": [{"ref": o["ref"], "verdict": o["verdict"], "note": o.get("note", "")} for o in r.get("outcomes", [])]}
                             for r in request.get("reports", [])]
        feedback.append(public)
    name = str(state.get("project") or Path(source_file).stem)
    humans = [people[k] for k in people]
    record = {"view": "private", "made_at": made_at, "source_file": source_file, "project": name,
              "people": humans, "trees": trees, "feedback": feedback}
    statements = sum(len(t["nodes"]) for t in trees.values())
    connections = sum(len(t["links"]) for t in trees.values())
    obstacles_focus = None
    if "current_reality" in trees:  # The overview draws the largest connected part of what stands in the way.
        parts, _ = pages.diagrams.components(trees["current_reality"])
        if parts:
            obstacles_focus = max(parts, key=lambda p: len(p["ids"]))["ids"][0]
    return {
        "slug": SLUG, "kind": "private", "name": name, "title": name, "byline": pages.names(humans),
        "summary": f"{name}, as {source_file} records it: {pages.plural(statements, 'statement')} and {pages.plural(connections, 'connection')}.",
        "description": f"Made from {source_file} on this computer. Nothing here is published.",
        "scope": "Everything in the working file as it is now: statements and connections of every standing, the assumptions and challenges on them, open work and outcome reports.",
        "overview": {"conditions": "What the goal needs, as the working file records it.",
                     "obstacles": "Read from the bottom up: each arrow means “contributes to”. The largest connected part is shown here.",
                     "obstacles_focus": obstacles_focus,
                     "change": "Where needs pull two ways, as recorded, and any change that has been accepted.",
                     "actions": "The actions recorded, each with what it should achieve.",
                     "learning": "What people reported after trying a change, beside what was expected."},
        "is_private": True, "is_example": False, "is_reconstruction": False, "source_file": source_file,
        "archives": {}, "source_questions": {}, "sources": [], "authors": {}, "views": {}, "overview_blocks": [], "retired": [], "review": {},
        "release_id": made_at[:10], "date": made_at,
        "people": [{"name": people[k], "role": "Driver" if k == state.get("driver") else ""} for k in people],
        "trees": trees, "feedback": feedback, "history": [],
        "json": json.dumps(record, ensure_ascii=False, indent=2) + "\n",
    }


def build(state_path, made_at=None):
    state_path = Path(state_path).resolve()
    state = views.load(state_path)
    views.validate(state)
    made_at = made_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    data = project(state, state_path.name, made_at)
    outputs = pages.render_private(SITE, data)
    outputs[f"{SLUG}/reasoning.json"] = data["json"]
    return data, with_assets(outputs)


def with_assets(outputs):
    """The stylesheet, script and fonts every page loads."""
    outputs["styles.css"] = (VIEWER / "styles.css").read_text()
    outputs["app.js"] = (VIEWER / "app.js").read_text()
    for font in sorted((VIEWER / "fonts").iterdir()):
        outputs[f"fonts/{font.name}"] = font.read_bytes()
    return outputs


def write(outputs, out):
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / MANIFEST
    require(manifest.exists() or not any(out.iterdir()), f"{out} holds files this helper did not write; choose another --output-dir.")
    previous = set(manifest.read_text().splitlines()) if manifest.exists() else set()
    for name in previous - set(outputs):
        stale = (out / name).resolve()
        if stale.is_file() and out.resolve() in stale.parents:
            stale.unlink()
    for name, value in outputs.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=target.parent, prefix=".tmp-")
        with os.fdopen(fd, "wb") as handle:
            handle.write(value if isinstance(value, bytes) else value.encode())
        os.replace(temp, target)
    manifest.write_text("".join(f"{name}\n" for name in sorted(outputs)))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--output-dir", type=Path, help="Folder for the pages; defaults to site/ in the file's hidden directory")
    parser.add_argument("--serve", nargs="?", const=0, type=int, metavar="PORT", help="Serve the pages on 127.0.0.1 until stopped; any free port by default")
    args = parser.parse_args()
    try:
        state_path = args.state.resolve()
        out = args.output_dir.resolve() if args.output_dir else state_path.parent / ("." + state_path.stem) / "site"
        data, outputs = build(state_path)
        write(outputs, out)
        standings = {}
        for tree in data["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                standings[item["status"]] = standings.get(item["status"], 0) + 1
        result = {"output": str(out), "open": (out / SLUG / "index.html").as_uri(),
                  "statements": sum(len(t["nodes"]) for t in data["trees"].values()),
                  "connections": sum(len(t["links"]) for t in data["trees"].values()), "standings": standings}
        server = None
        if args.serve is not None:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", args.serve), partial(QuietHandler, directory=str(out)))
            result["url"] = f"http://127.0.0.1:{server.server_address[1]}/{SLUG}/index.html"
        print(json.dumps(result, indent=2), flush=True)
    except (ValueError, KeyError, TypeError, AttributeError, OSError, views.yaml.YAMLError) as error:
        print(f"reason-commons: {error}", file=sys.stderr)
        return 1
    if server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
