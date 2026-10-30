#!/usr/bin/env python3
"""Prepare a commons for sharing on the Reason Commons site, and preview it, without sharing anything.

From the working YAML and the group's choices (which trees, which standings, whether to include assumptions and
challenges, and open work), write the one `publication.json` a pull request to the site adds, and a preview of the
pages it would make. Everyone the selection names must have agreed in `share_consents`, under the name they chose;
otherwise nothing is written and the people still to ask are listed. The site's own checks run on the result. Opening
the pull request is a separate, explicit step: see references/sharing.md.
"""
import argparse
from datetime import datetime, timezone
from functools import partial
import http.server
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("reason_commons_open", HERE / "open_commons.py")
viewer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(viewer)
pages, views = viewer.pages, viewer.views
import submissions  # noqa: E402  (the site's own checks, copied into viewer/ beside the renderer)

STANDINGS = ("accepted", "proposed", "disputed")
SITE = {**viewer.SITE, "contribution_url": "https://github.com/reasoncommons/reasoncommons/issues/new"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare(state, *, slug, title, summary, github, submitter=None, trees=None, standings=STANDINGS, notes=False, open_work=False, today=None):
    """The publication file for the chosen selection, or an error naming who still has to agree."""
    people = viewer.display_names(state)
    consents = {c["participant"]: c for c in state.get("share_consents", [])}  # The latest entry for each person counts.
    submitter = submitter or state["driver"]
    require(submitter in people, f"Unknown participant: {submitter}")
    present = [n for n in pages.TREE_ORDER if state.get("trees", {}).get(n, {}).get("nodes")]
    chosen = list(trees or present)
    require(chosen and set(chosen) <= set(present), "Choose trees that hold statements: " + ", ".join(present))
    require(set(standings) <= set(STANDINGS) and standings, "Standings are accepted, proposed and disputed")
    named, missing = set(), set()

    def name(person):
        if person == "assistant":
            return submissions.ASSISTANT
        if person not in consents:
            missing.add(person)
            return people.get(person, person)
        named.add(person)
        return consents[person]["name"]

    def notes_of(item):
        return {key: [{"text": n["text"], "by": name(n["by"])} for n in item[key]] for key in ("assumptions", "challenges") if notes and item.get(key)}

    selected = {}
    for tree_name in [n for n in pages.TREE_ORDER if n in chosen]:
        source = state["trees"][tree_name]
        nodes = [n for n in source["nodes"] if n.get("status", "proposed") in standings]
        kept = {n["id"] for n in nodes}
        links = [l for l in source.get("links", []) if l.get("status", "proposed") in standings and set(l["from"] + [l["to"]]) <= kept]
        selected[tree_name] = (nodes, links, kept | {l["id"] for l in links})
    node_ids = {i for _, (nodes, _, _) in selected.items() for i in (n["id"] for n in nodes)}
    out = {}
    for tree_name, (nodes, links, ids) in selected.items():
        tree = {"nodes": [], "links": [], "backlog": []}
        for node in nodes:
            item = {"id": node["id"], "kind": node["kind"], "text": node["text"], "status": node.get("status", "proposed"),
                    "accepted_by": [name(p) for p in node.get("accepted_by", [])], "contributors": list(dict.fromkeys(name(c["by"]) for c in node.get("contributions", [])))}
            if node.get("label"):
                item["label"] = node["label"]
            for trace in submissions.TRACES:
                refs = [r for r in node.get(trace, []) if r in node_ids]
                if refs:
                    item[trace] = refs
            item.update(notes_of(node))
            tree["nodes"].append(item)
        for link in links:
            item = {"id": link["id"], "from": list(link["from"]), "to": link["to"], "relation": link["relation"], "status": link.get("status", "proposed"),
                    "accepted_by": [name(p) for p in link.get("accepted_by", [])], "contributors": list(dict.fromkeys(name(c["by"]) for c in link.get("contributions", [])))}
            item.update(notes_of(link))
            tree["links"].append(item)
        if open_work:
            tree["backlog"] = [{k: task[k] for k in ("ref", "work", "label", "note") if k in task} for task in state["trees"][tree_name].get("backlog", []) if task["ref"] in ids]
        out[tree_name] = tree
    name(submitter)
    if missing:
        raise ValueError("Not yet agreed to be named: " + ", ".join(sorted(f"{people.get(p, p)} ({p})" for p in missing))
                         + ". Ask each of them, or leave out what they contributed, accepted or noted.")
    order = [p for p in people if p in named]
    publication = {
        "submission_version": submissions.VERSION, "slug": slug, "title": title, "summary": summary,
        "submitted_by": {"name": consents[submitter]["name"], "github": github}, "licence": submissions.LICENCE,
        "released_on": today or datetime.now(timezone.utc).date().isoformat(),
        "people": [{"name": consents[p]["name"], "consent": {"given_on": consents[p]["given_at"][:10], "how": consents[p]["source"]}} for p in order],
        "trees": out,
    }
    return submissions.validate(publication)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--slug", required=True, help="Lower-case words joined by hyphens; the address on the site")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True, help="One sentence, up to 300 characters")
    parser.add_argument("--github", required=True, help="GitHub username of the person sharing it")
    parser.add_argument("--submitter", help="Participant ID of the person sharing it; the driver by default")
    parser.add_argument("--trees", help="Comma-separated trees to share; all trees with statements by default")
    parser.add_argument("--standings", default=",".join(STANDINGS), help="Comma-separated standings to share")
    parser.add_argument("--notes", action="store_true", help="Include assumptions and challenges")
    parser.add_argument("--open-work", action="store_true", help="Include open work (the backlog)")
    parser.add_argument("--output-dir", type=Path, help="Defaults to share/ in the file's hidden directory")
    parser.add_argument("--serve", nargs="?", const=0, type=int, metavar="PORT", help="Serve the preview on 127.0.0.1 until stopped")
    args = parser.parse_args()
    try:
        state_path = args.state.resolve()
        state = views.load(state_path)
        views.validate(state)
        publication = prepare(state, slug=args.slug, title=args.title, summary=args.summary, github=args.github, submitter=args.submitter,
                              trees=args.trees.split(",") if args.trees else None, standings=tuple(args.standings.split(",")),
                              notes=args.notes, open_work=args.open_work)
        out = args.output_dir.resolve() if args.output_dir else state_path.parent / ("." + state_path.stem) / "share"
        folder = out / publication["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "publication.json").write_text(json.dumps(publication, ensure_ascii=False, indent=2) + "\n")
        data = {**submissions.to_pages(publication), "source_file": state_path.name}
        preview = pages.render_private(SITE, data)
        preview[f'{publication["slug"]}/reasoning.json'] = data["json"]
        viewer.write(viewer.with_assets(preview), out / "preview")
        counts = {}
        for tree in publication["trees"].values():
            for item in tree["nodes"] + tree["links"]:
                counts[item["status"]] = counts.get(item["status"], 0) + 1
        result = {"publication": str(folder / "publication.json"), "open": (out / "preview" / publication["slug"] / "index.html").as_uri(),
                  "named": [p["name"] for p in publication["people"]], "standings": counts,
                  "statements": sum(len(t["nodes"]) for t in publication["trees"].values()),
                  "connections": sum(len(t["links"]) for t in publication["trees"].values())}
        server = None
        if args.serve is not None:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", args.serve), partial(viewer.QuietHandler, directory=str(out / "preview")))
            result["url"] = f'http://127.0.0.1:{server.server_address[1]}/{publication["slug"]}/index.html'
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
