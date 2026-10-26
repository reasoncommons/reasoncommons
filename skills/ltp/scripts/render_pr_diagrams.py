#!/usr/bin/env python3
"""Generate one Mermaid change diagram per affected tree of a PR's complete conversational YAML diff.

Normally called through check_pr_trees.py --suggest --format markdown.
Standalone: render_pr_diagrams.py --base origin/main path/to/reason-commons.yaml
No files, reasoning standing, snapshots or views are changed.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import textwrap


TREE_ORDER = ("goal", "current_reality", "conflict", "future_reality", "prerequisite", "transition")
STANDING = {"accepted": "Accepted", "proposed": "Proposed", "disputed": "Disputed"}
WIDTH = 38  # GitHub renders these SVG text lines unclipped; widget views use render_view.WIDTH.
STYLES = {
    "added": "fill:#eef9f0,stroke:#238636,color:#17212e,stroke-width:2px",
    "changed": "fill:#eef5ff,stroke:#0969da,color:#17212e,stroke-width:2px",
    "removed": "fill:#fff1f0,stroke:#cf222e,color:#17212e,stroke-dasharray:5 3",
    "relabelled": "fill:#eef5ff,stroke:#0969da,color:#17212e,stroke-dasharray:4 2",
    "previous": "fill:#f6f8fa,stroke:#6e7781,color:#17212e,stroke-dasharray:3 3",
    "context": "fill:#f6f8fa,stroke:#8c959f,color:#17212e",
}
LEGEND = "ADDED / CHANGED / REMOVED describe this PR; PREVIOUS shows the earlier version; RELABELLED gives an unchanged statement a new short label; CONTEXT is unchanged neighboring reasoning. Nodes show each statement's one-sentence label where it has one; the full statements are in the update list below. Each statement shows its standing ([Accepted] for now, [Proposed] or [Disputed]) and kind. Solid arrows are accepted links and dotted arrows proposed ones; disputed links say so. Joint conditions use AND. Backlog notes hang from the statement or link they concern by a dotted line."


def escape(value):
    for raw, code in (("&", "#amp;"), ('"', "#quot;"), ("<", "#lt;"), (">", "#gt;")):
        value = value.replace(raw, code)
    return value.replace("\n", "<br/>")


def trees(documents):
    result = {}
    for state in documents.values():
        for name, tree in (state or {}).get("trees", {}).items():
            current = result.setdefault(name, {"nodes": {}, "links": {}, "backlog": {}})
            for category in ("nodes", "links"):
                for item in tree[category]:
                    if item["id"] in current[category]:
                        raise ValueError(f"Duplicate {category} ID: {item['id']}")
                    current[category][item["id"]] = item
            # Backlog items have no ID; reference and work identify one, numbered when repeated.
            for item in tree.get("backlog") or []:
                key, n = f"{item.get('ref')}|{item.get('work')}", 1
                while (key if n == 1 else f"{key}|{n}") in current["backlog"]:
                    n += 1
                current["backlog"][key if n == 1 else f"{key}|{n}"] = item
    return result


def wrap(text, width=WIDTH):
    return textwrap.wrap(text, width, break_long_words=False, break_on_hyphens=False)


def human(key):
    return key.replace("_", " ").capitalize()


def differences(old, new):
    return {ident for ident in old.keys() | new.keys() if old.get(ident) != new.get(ident)}


def ends(link):
    return set(link["from"] + [link["to"]])


def components(nodes, links):
    adjacency = {ident: set() for ident in nodes}
    for link in links:
        members = ends(link)
        for ident in members:
            adjacency[ident].update(members - {ident})
    remaining = set(nodes)
    groups = []
    while remaining:
        group, pending = set(), [min(remaining)]
        while pending:
            ident = pending.pop()
            if ident not in group:
                group.add(ident)
                pending.extend(adjacency[ident] - group)
        groups.append(group)
        remaining -= group
    return groups


def node_label(item, operation):
    # The diagram title names the tree, so nodes carry only change, standing, kind and statement.
    standing = item.get("status", "proposed")
    lines = [f"{operation.upper()} · [{STANDING[standing]}]", human(item["kind"])] + wrap(item.get("label") or item["text"])
    for objection in item.get("challenges", []) if standing == "disputed" else []:
        lines += wrap(f"Objection ({objection['by']}): {objection['text']}")
    return escape("\n".join(lines))


def backlog_label(before, after, operation):
    """A backlog note shows its one-sentence label, or the work named in words; the full note stays in the YAML."""
    item = after or before
    return escape("\n".join([f"{operation.upper()} · Backlog"] + wrap(item.get("label") or human(item["work"]))))


def without_label(item):
    return {key: value for key, value in item.items() if key != "label"}


def source(name, old, new, selected_nodes, selected_links, changed_backlog=(), loose=()):
    # SVG text avoids the host's capped HTML foreignObject labels clipping lines.
    direction = "TB" if len(selected_nodes) <= 3 else "LR"
    lines, aliases = ["---", "config:", "  htmlLabels: false", "  flowchart:", "    wrappingWidth: 360", "---", f"flowchart {direction}"], {}
    changed_nodes = differences(old["nodes"], new["nodes"])
    # A label-only edit leaves the statement itself unchanged: draw it once, not as a before/after pair.
    relabelled = {i for i in changed_nodes if i in old["nodes"] and i in new["nodes"]
                  and without_label(old["nodes"][i]) == without_label(new["nodes"][i])}
    changed_nodes -= relabelled
    for ident in sorted(selected_nodes, key=lambda i: (i in loose, i)):
        if ident in loose and ident == min(loose):
            lines.append('  subgraph loose["Not yet connected"]')
        before, after = old["nodes"].get(ident), new["nodes"].get(ident)
        if before and after and ident in changed_nodes:
            variants = [("old", before, "previous"), ("new", after, "changed")]
        elif ident in relabelled:
            variants = [("new", after, "relabelled")]
        elif after:
            variants = [("new", after, "added" if before is None else "context")]
        else:
            variants = [("old", before, "removed")]
        for version, item, operation in variants:
            alias = f"n{len(aliases)}"
            aliases[(ident, version)] = alias
            lines.append(f"  %% node {json.dumps(ident)} {version}")
            lines.append(f'  {alias}["{node_label(item, operation)}"]')
            lines.append(f"  class {alias} {operation}")
        if ident in loose and ident == max(loose):
            lines.append("  end")
    def endpoint(ident, version):
        return aliases.get((ident, version)) or aliases[(ident, "new" if version == "old" else "old")]
    junction = 0
    for ident in sorted(selected_links):
        before, after = old["links"].get(ident), new["links"].get(ident)
        if before and after and before != after:
            variants = [("old", before, "previous"), ("new", after, "changed")]
        elif before and after:
            variants = [("new", after, "context")]
            if ends(before) & changed_nodes:
                variants.insert(0, ("old", before, "previous"))
        elif after:
            variants = [("new", after, "added")]
        else:
            variants = [("old", before, "removed")]
        for version, item, operation in variants:
            disputed = " · disputed" if item.get("status") == "disputed" else ""
            label = escape(f"{operation.upper()} · {item['relation'].replace('_', ' ')}{disputed}")
            lines.append(f"  %% link {json.dumps(ident)} {version}")
            sources = [endpoint(n, version) for n in sorted(set(item["from"]))]
            target = endpoint(item["to"], version)
            accepted = item.get("status", "proposed") == "accepted"
            if len(sources) > 1:
                joint = f"j{junction}"
                junction += 1
                lines.append(f'  {joint}(("AND"))')
                for start in sources:
                    lines.append(f"  {start} {'-->' if accepted else '-.->'} {joint}")
                start = joint
            else:
                start = sources[0]
            lines.append(f'  {start} -- "{label}" --> {target}' if accepted else f'  {start} -. "{label}" .-> {target}')
    for number, key in enumerate(sorted(changed_backlog)):
        before, after = old["backlog"].get(key), new["backlog"].get(key)
        operation = "changed" if before and after else "added" if after else "removed"
        alias = f"b{number}"
        lines.append(f"  %% backlog {json.dumps(key)} {'old' if operation == 'removed' else 'new'}")
        lines.append(f'  {alias}["{backlog_label(before, after, operation)}"]')
        lines.append(f"  class {alias} {operation}")
        ref = (after or before)["ref"]
        link = new["links"].get(ref) or old["links"].get(ref)
        for target in (sorted(set(link["from"] + [link["to"]])) if link else [ref]):
            lines.append(f"  {alias} -.- {endpoint(target, 'new')}")
    lines.extend(f"  classDef {operation} {style}" for operation, style in STYLES.items())
    return "\n".join(lines)


def fragments(before_documents, after_documents):
    before, after = trees(before_documents), trees(after_documents)
    empty = {"nodes": {}, "links": {}, "backlog": {}}
    result = []
    for name in sorted(before.keys() | after.keys(), key=lambda n: TREE_ORDER.index(n)):
        old, new = before.get(name, empty), after.get(name, empty)
        changed_nodes = differences(old["nodes"], new["nodes"])
        changed_links = differences(old["links"], new["links"])
        changed_backlog = differences(old["backlog"], new["backlog"])
        if not changed_nodes and not changed_links and not changed_backlog:
            continue
        # A backlog change brings in the statement or link it concerns, with the same one-hop context.
        refs = {(new["backlog"].get(k) or old["backlog"][k])["ref"] for k in changed_backlog}
        # A label-only edit is presentation: show the node, but do not widen the view around it.
        relabel_only = {i for i in changed_nodes if i in old["nodes"] and i in new["nodes"]
                        and without_label(old["nodes"][i]) == without_label(new["nodes"][i])}
        focus = (changed_nodes - relabel_only) | {r for r in refs if r in old["nodes"] or r in new["nodes"]}
        selected_links = set(changed_links) | {r for r in refs if r in old["links"] or r in new["links"]}
        selected_nodes = set(focus)

        def expand(around):
            # One hop around these nodes, plus every selected link's old/new endpoints.
            # Context endpoints do not pull in unrelated branches of the full tree.
            for tree in (old, new):
                for ident, link in tree["links"].items():
                    if ident in selected_links or ends(link) & around:
                        selected_links.add(ident)
                        selected_nodes.update(ends(link))
        expand(focus)
        # A relabelled node outside the view keeps its links, so it is not shown as unconnected.
        expand({i for i in relabel_only if i not in selected_nodes})
        selected_nodes |= relabel_only
        all_links = [tree["links"][ident] for tree in (old, new) for ident in selected_links if ident in tree["links"]]
        groups = components(selected_nodes, all_links)
        isolated = sorted(next(iter(group)) for group in groups if len(group) == 1
                          and not any(next(iter(group)) in ends(link) for link in all_links))
        result.append({"tree": name, "node_ids": sorted(selected_nodes), "link_ids": sorted(selected_links),
                       "backlog_keys": sorted(changed_backlog), "group_count": len(groups), "unconnected_node_ids": isolated,
                       "source": source(name, old, new, selected_nodes, selected_links, changed_backlog,
                                        isolated)})
    return result


def connection_note(diagram):
    """Describe disconnected display groups without asserting missing causal links."""
    if diagram["group_count"] <= 1 and not diagram["unconnected_node_ids"]:
        return ""
    note = f"This change view has {diagram['group_count']} disconnected group(s); no connecting links are shown between them."
    if diagram["unconnected_node_ids"]:
        count = len(diagram["unconnected_node_ids"])
        note += f" {count} statement(s) under “Not yet connected” have no links here. Their connections remain unresolved."
    return note


def markdown(before_documents, after_documents):
    diagrams = fragments(before_documents, after_documents)
    lines = ["## Reasoning changes", ""]
    if not diagrams:
        return "\n".join(lines + ["No node, link or backlog changes; see the scope below.", ""])
    lines += [LEGEND, ""]
    for diagram in diagrams:
        title = diagram["tree"].replace("_", " ").title()
        lines += [f"**{title} · changed reasoning with neighboring context**", ""]
        note = connection_note(diagram)
        if note:
            lines += [note, ""]
        lines += ["```mermaid", diagram["source"], "```", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("states", nargs="+")
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("pr_check", Path(__file__).with_name("check_pr_trees.py"))
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    _, before, after = check.load_documents(args.states, args.base, None)
    for state in after.values():
        check.views.validate(state)
    print(markdown(before, after))


if __name__ == "__main__":
    main()
