#!/usr/bin/env python3
"""Snapshot accepted reasoning and derive full/change HTML and SVG views.

Requires PyYAML; diagrams are drawn as inline SVG with no renderer dependency.
The working YAML is read-only to this helper; history is never overwritten.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import html
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import textwrap
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

_feedback_spec = importlib.util.spec_from_file_location("reason_commons_feedback", Path(__file__).with_name("feedback.py"))
feedback = importlib.util.module_from_spec(_feedback_spec)
_feedback_spec.loader.exec_module(feedback)


KINDS = {
    "goal": {"goal", "critical_success_factor", "necessary_condition"},
    "current_reality": {"undesirable_effect", "cause"},
    "conflict": {"objective", "need", "prerequisite"},
    "future_reality": {"injection", "existing_condition", "predicted_effect", "desirable_effect", "undesirable_effect"},
    "prerequisite": {"objective", "obstacle", "intermediate_objective"},
    "transition": {"existing_condition", "need", "action", "expected_effect"},
}
TRACES = ("addresses", "derived_from", "implements")
TREE_OF = {}  # node ID -> tree name for the state being rendered; lets views describe traces without IDs.
LABEL_MAX = 100  # A label is the one-sentence form diagrams show; text stays the full statement of record.


def valid_label(item):
    label = item.get("label")
    return label is None or (isinstance(label, str) and bool(label.strip()) and len(label) <= LABEL_MAX and "\n" not in label)


def shown(node):
    """What a diagram draws for a statement: its short label when one exists, otherwise the full text."""
    return node.get("label") or node["text"]


def trace_line(key, refs):
    """Describe cross-tree traces by count and tree, e.g. "Addresses 2 Current Reality statements"."""
    groups = {}
    for ref in refs:
        groups[TREE_OF.get(ref)] = groups.get(TREE_OF.get(ref), 0) + 1
    parts = [f"{n} {name.replace('_', ' ').title() + ' ' if name else ''}statement{'' if n == 1 else 's'}"
             for name, n in sorted(groups.items(), key=lambda item: (item[0] is None, item[0] or ""))]
    return f"{key.replace('_', ' ').capitalize()} {' and '.join(parts)}"
EMPTY = {"nodes": {}, "links": {}}


class StateLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys rather than silently losing reasoning."""


def unique_mapping(loader, node):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise ValueError(f"Duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node)
    return mapping


StateLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load(path):
    return yaml.load(path.read_text(), Loader=StateLoader)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def acceptance_time(value, field, prefix, utc=False):
    require(isinstance(value, str), f"{prefix}.{field} must be a quoted ISO 8601 timestamp.")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{prefix}.{field} must be an ISO 8601 timestamp.") from None
    require(stamp.tzinfo is not None, f"{prefix}.{field} must include a timezone.")
    if utc:
        require(stamp.utcoffset() == timezone.utc.utcoffset(stamp), f"{prefix}.{field} must be UTC.")


def validate_change_acceptances(state, people):
    receipts = state.get("change_acceptances", [])
    require(isinstance(receipts, list), "change_acceptances must be a list.")
    seen = set()
    for index, receipt in enumerate(receipts):
        prefix = f"change_acceptances[{index}]"
        require(isinstance(receipt, dict), f"{prefix} must be a mapping.")
        for field in ("proposal_ref", "source_text", "scope", "timezone"):
            require(isinstance(receipt.get(field), str) and receipt[field].strip(), f"{prefix}.{field} must be nonempty text.")
        revision = receipt.get("proposal_revision")
        require(type(revision) is int and revision > 0, f"{prefix}.proposal_revision must be a positive integer.")
        by = receipt.get("by")
        require(isinstance(by, str) and by in people, f"{prefix}.by must identify a configured human participant.")
        require(receipt.get("mode") == "text", f"{prefix}.mode must be text.")
        require(receipt.get("source") == "conversation", f"{prefix}.source must be conversation.")
        acceptance_time(receipt.get("recorded_at"), "recorded_at", prefix, utc=True)
        if "accepted_at" in receipt:
            acceptance_time(receipt["accepted_at"], "accepted_at", prefix)
        try:
            ZoneInfo(receipt["timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"{prefix}.timezone must be an IANA timezone.") from None
        for field in ("node_ids", "link_ids"):
            refs = receipt.get(field)
            require(isinstance(refs, list) and all(isinstance(ref, str) and ref.strip() for ref in refs), f"{prefix}.{field} must be a list of historical IDs.")
            require(len(refs) == len(set(refs)), f"{prefix}.{field} contains duplicate IDs.")
        require(not set(receipt["node_ids"]) & set(receipt["link_ids"]), f"{prefix} repeats an ID as both node and link.")
        if "approved_paths" in receipt:
            paths = receipt["approved_paths"]
            require(isinstance(paths, list), f"{prefix}.approved_paths must be a list of exact repository-relative paths.")
            for path in paths:
                require(isinstance(path, str) and path and "\x00" not in path and "\\" not in path,
                        f"{prefix}.approved_paths must contain exact repository-relative paths.")
                require(not PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts
                        and str(PurePosixPath(path)) == path and path != ".",
                        f"{prefix}.approved_paths must contain normalized repository-relative paths.")
            require(len(paths) == len(set(paths)), f"{prefix}.approved_paths contains duplicate paths.")
        key = (receipt["proposal_ref"], revision, by)
        require(key not in seen, f"Duplicate change acceptance: {key}")
        seen.add(key)


def validate(state):
    require(isinstance(state, dict) and state.get("schema_version") == 1, "Expected schema_version: 1.")
    people = state.get("participants", {})
    require(isinstance(people, dict) and "assistant" not in people, "Configure human participants; assistant is reserved.")
    require(state.get("driver") in people, "Driver must be a configured participant.")
    validate_change_acceptances(state, people)
    feedback.validate(state)
    trees = state.get("trees", {})
    require(isinstance(trees, dict) and state.get("active_tree") in trees, "active_tree must exist.")
    all_ids, all_nodes = set(), set()
    for name, tree in trees.items():
        require(name in KINDS and isinstance(tree, dict), f"Unknown tree: {name}")
        for key in ("nodes", "links", "backlog"):
            require(isinstance(tree.get(key), list), f"{name}.{key} must be a list.")
        nodes = {}
        for item in tree["nodes"] + tree["links"]:
            ident = item.get("id")
            require(isinstance(ident, str) and ident and ident not in all_ids, f"Invalid or duplicate ID: {ident}")
            all_ids.add(ident)
            require(item.get("status", "proposed") in {"proposed", "accepted", "disputed"}, f"Invalid status: {ident}")
            require(valid_label(item), f"A label must be one line of at most {LABEL_MAX} characters: {ident}")
            require(isinstance(item.get("contributions"), list) and item["contributions"], f"Missing contributions: {ident}")
            for c in item["contributions"]:
                require(c.get("by") in people or c.get("by") == "assistant", f"Unknown contributor: {ident}")
                require(c.get("attribution") in {"explicit", "speaker_label", "driver_default", "assistant"}, f"Invalid attribution: {ident}")
                require(c.get("mode") in {"text", "voice", "unknown"}, f"Invalid mode: {ident}")
                require((c["by"] == "assistant") == (c["attribution"] == "assistant"), f"Assistant attribution mismatch: {ident}")
            if item.get("status") == "accepted":
                endorsers = item.get("accepted_by")
                require(isinstance(endorsers, list) and endorsers and all(p in people for p in endorsers), f"Accepted item needs human accepted_by: {ident}")
            for key in ("assumptions", "challenges"):
                require(isinstance(item.get(key, []), list), f"{ident}.{key} must be a list.")
                for note in item.get(key, []):
                    require(isinstance(note.get("text"), str) and (note.get("by") in people or note.get("by") == "assistant"), f"Invalid {key}: {ident}")
        for node in tree["nodes"]:
            require(node.get("kind") in KINDS[name] | {"observation"}, f"Invalid kind: {node['id']}")
            require(isinstance(node.get("text"), str) and node["text"].strip(), f"Missing text: {node['id']}")
            nodes[node["id"]] = node
        all_nodes.update(nodes)
        for link in tree["links"]:
            sources = link.get("from")
            require(isinstance(sources, list) and sources and all(s in nodes for s in sources), f"Invalid source(s): {link['id']}")
            require(link.get("to") in nodes, f"Invalid target: {link['id']}")
            require(isinstance(link.get("relation"), str) and link["relation"], f"Missing relation: {link['id']}")
            if link.get("status") == "accepted":
                require(all(nodes[n].get("status") == "accepted" for n in sources + [link["to"]]), f"Accepted link {link['id']} requires accepted endpoints; revise dependent links when a node loses acceptance.")
        local_ids = set(nodes) | {link["id"] for link in tree["links"]}
        for task in tree["backlog"]:
            require(task.get("ref") in local_ids and isinstance(task.get("work"), str) and task["work"], f"Invalid backlog reference/work in {name}.")
            require(valid_label(task), f"A backlog label must be one line of at most {LABEL_MAX} characters: {task.get('work')}")
    for tree in trees.values():
        for node in tree["nodes"]:
            for key in TRACES:
                refs = node.get(key, [])
                require(isinstance(refs, list) and all(ref in all_nodes for ref in refs), f"Unresolved {key}: {node['id']}")


def accepted(state):
    """Semantic projection; contributor edits and WIP do not create revisions."""
    result = {}
    for name, tree in state.get("trees", {}).items():
        view = {"nodes": {}, "links": {}}
        for category in view:
            for item in tree[category]:
                if item.get("status") != "accepted":
                    continue
                fields = ("kind", "text") if category == "nodes" else ("to", "relation")
                value = {key: item[key] for key in fields}
                if category == "links":
                    value["from"] = sorted(set(item["from"]))
                else:
                    for key in TRACES:
                        if item.get(key):
                            value[key] = sorted(set(item[key]))
                if item.get("assumptions"):
                    value["assumptions"] = sorted({a["text"] for a in item["assumptions"]})
                view[category][item["id"]] = value
        if view != EMPTY:
            result[name] = view
    return result


def delta(before, after):
    return {kind: {ident: ("added" if ident not in before[kind] else "removed" if ident not in after[kind] else "changed")
                   for ident in sorted(before[kind].keys() | after[kind].keys())
                   if before[kind].get(ident) != after[kind].get(ident)}
            for kind in ("nodes", "links")}


def quote(value):
    return json.dumps(str(value), ensure_ascii=False)


def attrs(**values):
    return ", ".join(f"{key}={quote(value)}" for key, value in values.items())


def node_text(node):
    lines = [node["kind"].replace("_", " ").upper()]
    lines.extend(textwrap.wrap(shown(node), 44, break_long_words=True) or [""])
    for key in TRACES:
        if node.get(key):
            lines.extend(textwrap.wrap(trace_line(key, node[key]), 44))
    for assumption in node.get("assumptions", []):
        lines.extend(textwrap.wrap(f"Assumes: {assumption}", 44))
    return "\n".join(lines)


def graph(name, before, after, changes=False):
    diff = delta(before, after)
    node_ids = set(after["nodes"])
    link_ids = set(after["links"])
    if changes:
        node_ids = set(diff["nodes"])
        link_ids = set(diff["links"])
        # One hop around changed nodes; changed-link endpoints do not expand further.
        for view in (before, after):
            for ident, link in view["links"].items():
                ends = set(link["from"] + [link["to"]])
                if ident in link_ids or ends & set(diff["nodes"]):
                    link_ids.add(ident)
                    node_ids.update(ends)
    title = name.replace("_", " ").title() + (" — latest accepted changes" if changes else " — accepted reasoning")
    if changes:
        title += "\nADDED: green · CHANGED: amber · REMOVED: red/dashed · CONTEXT: gray"
    out = ["digraph reasoning {", "  graph [" + attrs(rankdir="LR" if name == "transition" else "BT", label=title, labelloc="t", fontname="Arial", fontsize=16, pad=0.3, nodesep=0.4, ranksep=0.65, bgcolor="white") + "];",
           '  node [shape="box", style="rounded,filled", fontname="Arial", fontsize=12, margin="0.16,0.12"];',
           '  edge [fontname="Arial", fontsize=10, arrowsize=0.7];']
    colors = {"added": ("#18734a", "#eaf7ef"), "changed": ("#996000", "#fff4d6"), "removed": ("#b23b3b", "#fff0f0"), "context": ("#9aa3ad", "#f5f6f7"), "accepted": ("#475569", "#f8fafc")}
    for ident in sorted(node_ids):
        node = after["nodes"].get(ident, before["nodes"].get(ident))
        status = diff["nodes"].get(ident, "context") if changes else "accepted"
        label = node_text(node)
        if changes:
            label = status.upper() + "\n" + label
        if status == "changed":
            label += "\nPreviously:\n" + node_text(before["nodes"][ident])
        color, fill = colors[status]
        out.append(f"  {quote(ident)} [" + attrs(id=ident, label=label, color=color, fillcolor=fill, fontcolor="#64748b" if status == "context" else "#17212e", style="rounded,filled,dashed" if status == "removed" else "rounded,filled") + "];")
    used = set(before["nodes"]) | set(after["nodes"])
    for ident in sorted(link_ids):
        status = diff["links"].get(ident, "context") if changes else "accepted"
        variants = [(after["links"].get(ident, before["links"].get(ident)), status)]
        if status == "changed":
            variants.insert(0, (before["links"][ident], "removed"))
        for link, style in variants:
            color = colors[style][0]
            label = link["relation"].replace("_", " ")
            if changes:
                label = style.upper() + ": " + label
            for assumption in link.get("assumptions", []):
                label += "\n" + "\n".join(textwrap.wrap("Assumes: " + assumption, 36))
            settings = dict(color=color, fontcolor=color, style="dashed" if style in {"removed", "context"} else "solid", penwidth=1 if style == "context" else 1.7)
            sources = link["from"]
            if len(sources) > 1:
                hub = f"__and_{ident}_{style}"
                while hub in used:
                    hub += "_"
                used.add(hub)
                out.append(f"  {quote(hub)} [" + attrs(label="AND", shape="diamond", color=color, fillcolor="white", fontsize=9, width=0.4, height=0.3) + "];")
                for source in sources:
                    out.append(f"  {quote(source)} -> {quote(hub)} [" + attrs(**settings, arrowhead="none") + "];")
                sources = [hub]
            extra = {"dir": "both", "constraint": "false"} if link["relation"] == "conflicts_with" else {}
            out.append(f"  {quote(sources[0])} -> {quote(link['to'])} [" + attrs(**settings, **extra, label=label, id=f"{ident}-{style}" if changes else ident) + "];")
    if not node_ids:
        out.append('  "__empty" [label="No accepted reasoning", shape="plaintext", fillcolor="white"];')
    return "\n".join(out + ["}", ""])


def wrap_svg(text, width=34):
    lines = []
    for paragraph in str(text).splitlines() or [""]:
        lines.extend(textwrap.wrap(paragraph, width, break_long_words=True, break_on_hyphens=False) or [""])
    return lines


def svg_graph(name, before, after, changes=False):
    """Render a dependency-free, top-to-bottom SVG flow diagram."""
    diff = delta(before, after)
    node_ids, link_ids = set(after["nodes"]), set(after["links"])
    if changes:
        node_ids, link_ids = set(diff["nodes"]), set(diff["links"])
        for view in (before, after):
            for ident, link in view["links"].items():
                ends = set(link["from"] + [link["to"]])
                if ident in link_ids or ends & set(diff["nodes"]):
                    link_ids.add(ident)
                    node_ids.update(ends)
    nodes = {ident: after["nodes"].get(ident, before["nodes"].get(ident)) for ident in node_ids}
    links = []
    for ident in link_ids:
        status = diff["links"].get(ident, "context") if changes else "accepted"
        if status == "changed":
            links.append((ident, before["links"][ident], "removed"))
        links.append((ident, after["links"].get(ident, before["links"].get(ident)), status))

    # Assign simple ranks from roots; cyclic or disconnected nodes begin a new rank.
    incoming = {ident: 0 for ident in nodes}
    children = {ident: [] for ident in nodes}
    for _, link, _ in links:
        if link["to"] in incoming:
            for source in link["from"]:
                if source in incoming and source != link["to"]:
                    incoming[link["to"]] += 1
                    children[source].append(link["to"])
    ranks = {ident: 0 for ident, degree in incoming.items() if degree == 0}
    pending = list(ranks)
    while pending:
        parent = pending.pop(0)
        for child in children[parent]:
            incoming[child] -= 1
            ranks[child] = max(ranks.get(child, 0), ranks[parent] + 1)
            if incoming[child] == 0:
                pending.append(child)
    for ident in nodes:
        ranks.setdefault(ident, 0)
    # Repeatedly relax ranks, bounded to avoid cycles growing without limit.
    for _ in range(max(0, len(nodes) - 1)):
        for _, link, _ in links:
            target = link["to"]
            sources = [s for s in link["from"] if s in ranks]
            if target in ranks and sources and target not in sources:
                ranks[target] = max(ranks[target], max(ranks[s] for s in sources) + 1)

    width, node_w, gap_x, gap_y = 320, 270, 70, 34
    grouped = {}
    for ident in sorted(nodes):
        grouped.setdefault(ranks[ident], []).append(ident)
    heights, wrapped = {}, {}
    for ident, node in nodes.items():
        lines = [node["kind"].replace("_", " ").upper()] + wrap_svg(shown(node))
        for key in TRACES:
            if node.get(key):
                lines.extend(wrap_svg(trace_line(key, node[key])))
        for assumption in node.get("assumptions", []):
            lines.extend(wrap_svg("Assumes: " + assumption))
        status = diff["nodes"].get(ident, "context") if changes else "accepted"
        if changes:
            lines.insert(0, status.upper())
        if status == "changed":
            lines.extend(["PREVIOUSLY:"] + wrap_svg(shown(before["nodes"][ident])))
        wrapped[ident] = lines
        heights[ident] = max(94, 42 + len(lines) * 18)
    positions = {}
    for rank, group in grouped.items():
        y = 56
        for ident in group:
            positions[ident] = (40 + rank * (node_w + gap_x), y)
            y += heights[ident] + gap_y
    max_rank = max(grouped, default=0)
    svg_w = max(380, 80 + (max_rank + 1) * (node_w + gap_x))
    svg_h = max((y for rank, group in grouped.items() for ident in group for y in [positions[ident][1] + heights[ident] + 40]), default=180)
    colors = {"added": ("#18734a", "#eaf7ef"), "changed": ("#996000", "#fff4d6"), "removed": ("#b23b3b", "#fff0f0"), "context": ("#9aa3ad", "#f5f6f7"), "accepted": ("#475569", "#f8fafc")}
    title = name.replace("_", " ").title() + (" — latest accepted changes" if changes else " — accepted reasoning")
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(title)}" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="auto">',
             '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="context-stroke"/></marker></defs>',
             '<style>text{font-family:Arial,sans-serif;fill:#17212e}.edge{fill:none;stroke-width:1.8}.node{stroke-width:1.6}</style>',
             f'<text x="24" y="30" font-size="20" font-weight="700">{html.escape(title)}</text>']
    for ident, link, status in links:
        color = colors[status][0]
        tx, ty = positions[link["to"]]
        sources = [source for source in link["from"] if source in positions and source != link["to"]]
        target_x, target_y = tx + node_w / 2, ty
        dash = ' stroke-dasharray="6 5"' if status in {"removed", "context"} else ""
        if len(sources) > 1:
            source_points = [(positions[s][0] + node_w / 2, positions[s][1] + heights[s]) for s in sources]
            hub_x = sum(point[0] for point in source_points) / len(source_points)
            hub_y = (sum(point[1] for point in source_points) / len(source_points) + target_y) / 2
            for x1, y1 in source_points:
                parts.append(f'<path class="edge" d="M{x1:g},{y1:g} L{hub_x:g},{hub_y:g}" stroke="{color}"{dash}/>')
            parts.append(f'<path d="M{hub_x - 15:g},{hub_y:g} l15,-12 15,12 -15,12 z" fill="#fff" stroke="{color}" stroke-width="1.6"/>')
            parts.append(f'<text x="{hub_x:g}" y="{hub_y + 4:g}" text-anchor="middle" font-size="9" fill="{color}">AND</text>')
            parts.append(f'<path class="edge" d="M{hub_x:g},{hub_y + 12:g} C{hub_x:g},{(hub_y + target_y) / 2:g} {target_x:g},{(hub_y + target_y) / 2:g} {target_x:g},{target_y:g}" stroke="{color}" marker-end="url(#arrow)"{dash}/>')
            lx, ly = (hub_x + target_x) / 2, (hub_y + target_y) / 2
        elif sources:
            sx, sy = positions[sources[0]]
            x1, y1 = sx + node_w / 2, sy + heights[sources[0]]
            mid = (y1 + target_y) / 2
            parts.append(f'<path class="edge" d="M{x1:g},{y1:g} C{x1:g},{mid:g} {target_x:g},{mid:g} {target_x:g},{target_y:g}" stroke="{color}" marker-end="url(#arrow)"{dash}/>')
            lx, ly = (x1 + target_x) / 2, mid
        else:
            continue
        label = (status.upper() + ": " if changes else "") + link["relation"].replace("_", " ")
        parts.append(f'<text x="{lx:g}" y="{ly:g}" text-anchor="middle" font-size="12" fill="{color}">{html.escape(label)}</text>')
    for ident, node in nodes.items():
        x, y = positions[ident]
        status = diff["nodes"].get(ident, "context") if changes else "accepted"
        stroke, fill = colors[status]
        dash = ' stroke-dasharray="6 5"' if status == "removed" else ""
        parts.append(f'<rect class="node" x="{x}" y="{y}" width="{node_w}" height="{heights[ident]}" rx="12" fill="{fill}" stroke="{stroke}"{dash}/>')
        for i, line in enumerate(wrapped[ident]):
            weight = ' font-weight="700"' if i == 0 or line in {"PREVIOUSLY:"} else ""
            parts.append(f'<text x="{x + 14}" y="{y + 25 + i * 18}" font-size="{"11" if i == 0 else "13"}"{weight}>{html.escape(line)}</text>')
    if not nodes:
        parts.append(f'<text x="24" y="90" font-size="16">No accepted reasoning</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def html_page(svg):
    return '<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reasoning diagram</title><style>body{margin:0;padding:24px;background:#fff;color:#17212e}main{max-width:1200px;margin:auto;overflow:auto}svg{min-width:360px;height:auto}</style><main>' + svg + '</main></html>\n'


def write_atomic(path, content, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        handle.write(content)
    try:
        if exclusive:
            os.link(temp, path)  # Atomic publication without replacing existing history.
        else:
            os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def update(state_path, output=None, summary=None):
    state_path = Path(state_path).resolve()
    state = load(state_path)
    validate(state)
    output = Path(output).resolve() if output else state_path.parent / ("." + state_path.stem)
    history = output / "history"
    paths = sorted(history.glob("[0-9][0-9][0-9][0-9][0-9][0-9].yaml"))
    snapshots = [load(path) for path in paths]
    for i, snap in enumerate(snapshots):
        validate(snap)
        require(snap.get("revision") == i + 1 and paths[i].stem == f"{i + 1:06d}" and snap.get("previous_revision") == (i if i else None), "History is incomplete or inconsistent; do not overwrite it.")
    projections = [accepted(s) for s in snapshots]
    previous = projections[-1] if projections else {}
    current = accepted(state)
    changed = sorted(name for name in previous.keys() | current.keys() if previous.get(name, EMPTY) != current.get(name, EMPTY))
    if changed:
        revision = len(snapshots) + 1
        snapshot = deepcopy(state)
        snapshot.update(revision=revision, previous_revision=revision - 1 or None,
                        change={"at": datetime.now(timezone.utc).isoformat(), "driver": state["driver"], "summary": summary or "Updated accepted reasoning in " + ", ".join(changed), "trees": changed})
        write_atomic(history / f"{revision:06d}.yaml", yaml.safe_dump(snapshot, sort_keys=False, allow_unicode=True), exclusive=True)
        projections.append(current)
    # For each tree, keep its latest actual change even when another tree changes.
    TREE_OF.clear()
    TREE_OF.update({node["id"]: name for name, tree in state.get("trees", {}).items() for node in tree["nodes"]})
    # Labels are presentation: they do not create accepted revisions, but views draw the current ones.
    labels = {node["id"]: node["label"] for tree in state.get("trees", {}).values() for node in tree["nodes"] if node.get("label")}

    def labelled(view):
        return {**view, "nodes": {i: {**n, "label": labels[i]} if i in labels else n for i, n in view["nodes"].items()}}
    rendered = []
    for name in sorted({n for projection in projections for n in projection}):
        for index in range(len(projections) - 1, -1, -1):
            after = projections[index].get(name, EMPTY)
            before = projections[index - 1].get(name, EMPTY) if index else EMPTY
            if after != before:
                break
        svgs = {view: svg_graph(name, labelled(before), labelled(after), changes=view == "changes") for view in ("current", "changes")}
        bases = {view: output / "diagrams" / view / name for view in svgs}
        if all(base.with_suffix(".svg").exists() and base.with_suffix(".html").exists()
               and base.with_suffix(".svg").read_text() == svgs[view]
               for view, base in bases.items()):
            continue
        for view, base in bases.items():
            write_atomic(base.with_suffix(".svg"), svgs[view])
            write_atomic(base.with_suffix(".html"), html_page(svgs[view]))
        rendered.append(name)
    return {"revision": len(projections), "changed_trees": changed, "rendered_trees": rendered, "output": str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--summary")
    args = parser.parse_args()
    try:
        print(json.dumps(update(args.state, args.output_dir, args.summary), indent=2))
    except (ValueError, KeyError, TypeError, AttributeError, OSError, RuntimeError, yaml.YAMLError) as error:
        print(f"reason-commons: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
