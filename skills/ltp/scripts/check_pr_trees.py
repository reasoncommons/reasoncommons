#!/usr/bin/env python3
"""Check PR reasoning, tree updates and recorded acceptance of the declared scope.

    check_pr_trees.py --base origin/main --body-file pr.md reason-commons.yaml
    check_pr_trees.py --base origin/main --suggest reason-commons.yaml

The body's "Reasoning this serves" section names existing node or link IDs; its "Tree
updates" section lists every node and link the branch adds, changes or removes, optionally
starting with the verb. Each is one list item whose first backticked ID is the claim.

The Accepted change proposals section names each receipt as:
    - `proposal-id` revision 1 by `participant-id`
Explanatory paragraphs may accompany these explicit list items.
The check validates working state and receipts, preserves earlier receipts, and
requires cited approvals to cover changed paths and node/link IDs. Coverage is
structural; reviewers still judge implementation meaning and approval authenticity.
--suggest prints the Tree updates list without requiring acceptance; with --format markdown it
also prints the Expected outcomes section generated from feedback commitments and reports in the
diff. The body must contain those generated blocks, and Future Reality predicted or undesirable
effects added without any commitment need a "No feedback commitment: <reason>" line.

Compares the working tree with the merge base of --base and HEAD.
"""

import argparse
import importlib.util
from pathlib import Path
import re
import subprocess
import sys

import yaml

SPEC = importlib.util.spec_from_file_location("pr_state_views", Path(__file__).with_name("update_views.py"))
views = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(views)
DIAGRAM_SPEC = importlib.util.spec_from_file_location("pr_diagrams", Path(__file__).with_name("render_pr_diagrams.py"))
diagrams = importlib.util.module_from_spec(DIAGRAM_SPEC)
DIAGRAM_SPEC.loader.exec_module(diagrams)

SERVES = "reasoning this serves"
UPDATES = "tree updates"
ACCEPTANCES = "accepted change proposals"
DIAGRAMS = "reasoning changes"
EXPECTED = "expected outcomes"
VERBS = ("added", "changed", "removed")
ID = re.compile(r"`([A-Za-z0-9][\w-]*)`")
ACCEPTANCE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+`([A-Za-z0-9][\w-]*)`\s+revision\s+([1-9]\d*)\s+by\s+`([A-Za-z0-9][\w-]*)`(?:\s+[—–-]\s+.*)?\s*$")


def items(state):
    """Every node and link by ID, with its tree and category."""
    found = {}
    for tree, content in ((state or {}).get("trees") or {}).items():
        for category in ("nodes", "links"):
            for item in (content or {}).get(category) or []:
                found[item["id"]] = (tree, category, item)
    return found


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def load_documents(paths, base, cwd):
    """Full documents at the merge base and in the working tree."""
    result = git(cwd, "merge-base", base, "HEAD")
    if result.returncode:
        raise SystemExit(f"Cannot find the merge base of {base} and HEAD: {result.stderr.strip()}")
    merge_base = result.stdout.strip()
    before, after = {}, {}
    for path in paths:
        old = git(cwd, "show", f"{merge_base}:{path}")
        before[path] = yaml.load(old.stdout, Loader=views.StateLoader) if old.returncode == 0 else None
        current = Path(cwd or ".") / path
        after[path] = views.load(current) if current.exists() else None
    return merge_base, before, after


def document_items(documents):
    found = {}
    for state in documents.values():
        for ident, item in items(state).items():
            if ident in found:
                raise ValueError(f"Duplicate reasoning ID across state files: {ident}")
            found[ident] = item
    return found


def load_states(paths, base, cwd):
    """Items at the merge base and in the working tree, across all state files."""
    _, before, after = load_documents(paths, base, cwd)
    return document_items(before), document_items(after)


def changed_paths(base, cwd):
    """Include both sides of renames; NUL separators preserve unusual filenames."""
    result = git(cwd, "diff", "--name-only", "--no-renames", "-z", base, "--")
    if result.returncode:
        raise ValueError(f"Cannot read changed paths: {result.stderr.strip()}")
    return set(filter(None, result.stdout.split("\x00")))


def changes(before, after):
    """(verb, id, tree, category, item) for each added, changed or removed item, in file order."""
    found = []
    for id_, (tree, category, item) in after.items():
        if id_ not in before:
            found.append(("added", id_, tree, category, item))
        elif before[id_] != (tree, category, item):
            found.append(("changed", id_, tree, category, item))
    for id_, (tree, category, item) in before.items():
        if id_ not in after:
            found.append(("removed", id_, tree, category, item))
    return found


def sections(body):
    """Section text keyed by lower-cased heading, with HTML comments removed."""
    body = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)
    found, heading = {}, None
    for line in body.splitlines():
        match = re.match(r"\s*#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            heading = match.group(1).strip().lower()
            found[heading] = []
        elif heading is not None:
            found[heading].append(line)
    return {heading: "\n".join(lines) for heading, lines in found.items()}


def claims(text):
    """(verb or None, id) per line: the first backticked ID, and a verb that starts the list item.

    Later IDs on a line, such as a link's endpoints, are description rather than claims.
    """
    found = []
    for line in (text or "").splitlines():
        id_ = ID.search(line)
        if not id_:
            continue
        verb = re.match(r"\s*(?:[-*+]|\d+[.)])?\s*(\w+)", line)
        verb = verb.group(1).lower() if verb and verb.group(1).lower() in VERBS else None
        found.append((verb, id_.group(1)))
    return found


def describe(change):
    verb, id_, tree, category, item = change
    if category == "nodes":
        detail = f"{tree}, {item.get('kind')}, {item.get('status')}): {item.get('text')}"
    else:
        sources = " + ".join(f"`{source}`" for source in item.get("from") or [])
        detail = f"{tree} link, {item.get('status')}): {sources} {item.get('relation', '').replace('_', ' ')} `{item.get('to')}`"
    return f"- {verb} `{id_}` ({detail}"


def check(body, before, after):
    """Problems with the body's claims, as a list of messages."""
    parts = sections(body)
    serves = [id_ for _, id_ in claims(parts.get(SERVES))]
    stated = claims(parts.get(UPDATES))
    actual = {change[1]: change[0] for change in changes(before, after)}
    problems = []
    if UPDATES not in parts:
        problems.append('The description has no "Tree updates" section. Write "None" there if the pull request changes no reasoning.')
    if not serves and not stated:
        problems.append('The pull request names no reasoning. List the node or link it serves under "Reasoning this serves", or the reasoning it adds under "Tree updates".')
    for id_ in serves:
        if id_ not in after:
            problems.append(f"Serves `{id_}`, which is not a node or link in the reasoning YAML.")
    stated_ids = {}
    for verb, id_ in stated:
        stated_ids.setdefault(id_, verb)
    for id_, verb in stated_ids.items():
        if id_ not in actual:
            problems.append(f"Lists `{id_}` as a tree update, but the YAML does not change it.")
        elif verb and verb != actual[id_]:
            problems.append(f"Lists `{id_}` as {verb}, but the YAML shows it {actual[id_]}.")
    for id_, verb in actual.items():
        if id_ not in stated_ids:
            problems.append(f"The YAML {verb} `{id_}`, but the Tree updates section does not list it.")
    return problems


def folded_updates(found):
    content = "\n".join(describe(change) for change in found) if found else "None"
    return "## Tree updates\n\n<details>\n<summary>Complete checked change list</summary>\n\n" + content + "\n\n</details>\n"


PREDICTIONS = {"predicted_effect", "undesirable_effect"}
NO_COMMITMENT = re.compile(r"^\s*No feedback commitment:\s*(.+?)\s*$", re.M)
PLACEHOLDER = "REPLACE WITH REASON"


def cell(text):
    """One table cell or quote: whitespace collapsed, pipes escaped."""
    return " ".join(str(text).split()).replace("|", "\\|")


def outcome_item(item):
    return (f"{item['tree'].replace('_', ' ').title()} · {item['kind'].replace('_', ' ').capitalize()} · "
            f"{item['standing'].capitalize()}: {cell(item['text'])}")


def request_versions(documents):
    found = {}
    for state in documents.values():
        for request in (state or {}).get("feedback_requests") or []:
            found[(request["id"], request["revision"])] = (request, state)
    return found


def commitment_block(request, state):
    names = (state.get("participants") or {})
    rows = [("Change being evaluated", outcome_item(request["about"]))]
    for label, field in (("Expected benefit", "benefits"), ("Possible harmful consequence", "reservations")):
        rows += [(label, outcome_item(item)) for item in request[field]] or [(label, "None recorded.")]
    rows.append(("Feedback from", ", ".join(cell(names.get(person, person)) for person in request["feedback_from"])))
    if request.get("ask_after"):
        rows.append(("Ask after", cell(request["ask_after"])))
    rows.append(("Observation opportunity", cell(request.get("ready_when") or "Not recorded.")))
    lines = [f"**`{request['id']}` revision {request['revision']}**: new feedback commitment", "",
             "| | Recorded expectation |", "| --- | --- |"]
    return "\n".join(lines + [f"| {label} | {value} |" for label, value in rows])


def reports_block(request, state, reports):
    names = (state.get("participants") or {})
    labels = {item["ref"]: label for label, field in (("Expected benefit", "benefits"), ("Possible harmful consequence", "reservations"))
              for item in request[field]}
    lines = [f"**Feedback recorded for `{request['id']}` revision {request['revision']}**", ""]
    for report in reports:
        lines.append(f"- {cell(names.get(report['by'], report['by']))} · {report['recorded_at']} · "
                     f"{report['readiness'].replace('_', ' ')}: “{cell(report['text'])}”")
        for outcome in report.get("outcomes") or []:
            lines.append(f"  - {labels.get(outcome['ref'], 'Outcome')} `{outcome['ref']}`: {outcome['verdict'].replace('_', ' ')}")
    return "\n".join(lines)


def expected_outcomes(before_documents, after_documents, found):
    """Generated blocks for feedback commitments and reports in the diff, and uncovered predictions."""
    before, after = request_versions(before_documents), request_versions(after_documents)
    blocks = []
    for key, (request, state) in after.items():
        if key not in before:
            blocks.append(commitment_block(request, state))
        seen = {report["id"] for report in before[key][0]["reports"]} if key in before else set()
        added = [report for report in request["reports"] if report["id"] not in seen]
        if added:
            blocks.append(reports_block(request, state, added))
    covered = {item["ref"] for request, _ in after.values() for field in ("benefits", "reservations") for item in request[field]}
    uncovered = [ident for verb, ident, tree, category, item in found
                 if verb == "added" and category == "nodes" and tree == "future_reality"
                 and item.get("kind") in PREDICTIONS and ident not in covered]
    return blocks, uncovered


def outcomes_section(blocks, uncovered):
    content = list(blocks)
    if uncovered:
        content.append(f"No feedback commitment: {PLACEHOLDER} (predictions: " + ", ".join(f"`{i}`" for i in uncovered) + ")")
    if not content:
        content = ["None: this change adds no feedback commitments, reports or predictions."]
    return "## Expected outcomes\n\n" + "\n\n".join(content) + "\n"


def normalized(text):
    return "\n".join(line.rstrip() for line in (text or "").splitlines())


def check_outcomes(body, blocks, uncovered):
    if not blocks and not uncovered:
        return []
    parts = sections(body)
    if EXPECTED not in parts:
        return ['The description has no "Expected outcomes" section. Run --suggest --format markdown.']
    content, problems = normalized(parts[EXPECTED]), []
    for block in blocks:
        if normalized(block) not in content:
            title = block.splitlines()[0].strip("*")
            problems.append(f"Expected outcomes must contain the generated block {title}, matching the YAML. Run --suggest --format markdown.")
    reasons = [reason for reason in NO_COMMITMENT.findall(content) if PLACEHOLDER not in reason]
    if uncovered and not reasons:
        problems.append("Predictions without a feedback commitment: " + ", ".join(f"`{i}`" for i in uncovered)
                        + '. Add a commitment, or state "No feedback commitment: <reason>" under Expected outcomes.')
    return problems


DETAILS = re.compile(r"<details\b([^>]*)>.*?<summary\b[^>]*>.*?</summary>(.*?)</details\s*>", re.S | re.I)
MERMAID = re.compile(r"^```mermaid\s*\n(.*?)^```\s*$", re.M | re.S)


def diagram_graph(source):
    """Validate bounded display options, then return the unchanged graph source."""
    lines = source.strip().splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("Keep Mermaid frontmatter with config.htmlLabels: false.")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("Close the Mermaid frontmatter with ---.") from None
    document = yaml.load("\n".join(lines[1:end]), Loader=views.StateLoader)
    if not isinstance(document, dict) or set(document) != {"config"}:
        raise ValueError("Frontmatter may contain only config.")
    config = document["config"]
    if not isinstance(config, dict) or set(config) - {"htmlLabels", "flowchart"}:
        raise ValueError("Supported display options are htmlLabels and flowchart.wrappingWidth.")
    if config.get("htmlLabels") is not False:
        raise ValueError("Keep config.htmlLabels: false so complete SVG labels remain visible.")
    flowchart = config.get("flowchart", {})
    if not isinstance(flowchart, dict) or set(flowchart) - {"wrappingWidth"}:
        raise ValueError("The only supported flowchart option is wrappingWidth.")
    if "wrappingWidth" in flowchart:
        width = flowchart["wrappingWidth"]
        if type(width) is not int or width <= 0:
            raise ValueError("flowchart.wrappingWidth must be a positive integer.")
    return "\n".join(lines[end + 1:]).strip()


def check_presentation(body, before_documents, after_documents, found):
    # Backlog-only changes have no node/link updates but still get a generated diagram.
    generated = diagrams.fragments(before_documents, after_documents)
    if not found and not generated:
        return []
    parts = sections(body)
    problems = []
    content = parts.get(DIAGRAMS, "")
    # Diagrams must be visible, rather than inside the collapsed technical list.
    visible = DETAILS.sub("", content)
    supplied = []
    invalid_configuration = False
    for number, source in enumerate(MERMAID.findall(visible), 1):
        try:
            supplied.append(diagram_graph(source))
        except (ValueError, TypeError, yaml.YAMLError) as error:
            invalid_configuration = True
            problems.append(f"Invalid Mermaid display configuration in diagram {number}: {error}")
    expected = [diagram_graph(diagram["source"]) for diagram in generated]
    if any(diagrams.connection_note(diagram) not in visible for diagram in generated):
        problems.append("Show the generated unresolved-connection notes beside the tree diagrams.")
    if not invalid_configuration and supplied != expected:
        problems.append("Reasoning changes must contain the generated, visible Mermaid diagrams matching the YAML diff. Run --suggest --format markdown.")
    if DIAGRAMS not in parts or UPDATES not in parts or list(parts).index(DIAGRAMS) > list(parts).index(UPDATES):
        problems.append("Show Reasoning changes before the collapsed Tree updates list.")
    updates = parts.get(UPDATES, "")
    folded = DETAILS.findall(updates)
    if not folded or any(re.search(r"(?:^|\s)open(?:\s|=|$)", attrs, re.I) for attrs, _ in folded):
        problems.append("Keep the complete Tree updates list in a closed <details> block.")
    hidden_ids = {ident for attrs, content in folded if not re.search(r"(?:^|\s)open(?:\s|=|$)", attrs, re.I)
                  for _, ident in claims(content)}
    if any(change[1] not in hidden_ids for change in found) or claims(DETAILS.sub("", updates)):
        problems.append("Every declared tree update must be inside the collapsed list, with no visible duplicate list.")
    return problems


def receipt_key(receipt):
    return (receipt["proposal_ref"], receipt["proposal_revision"], receipt["by"])


def check_acceptances(body, before_documents, after_documents, paths, tree_changes):
    """Check declared approval coverage; do not infer human consent or claim truth."""
    problems, receipts = [], {}
    for path, state in after_documents.items():
        if state is None:
            problems.append(f"Missing working reasoning state: {path}")
            continue
        try:
            views.validate(state)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            problems.append(f"Invalid state {path}: {error}")
            continue
        local = {receipt_key(r): r for r in state.get("change_acceptances", [])}
        for previous in (before_documents.get(path) or {}).get("change_acceptances", []):
            if local.get(receipt_key(previous)) != previous:
                problems.append(f"Earlier acceptance receipt was changed or removed in {path}: {receipt_key(previous)}")
        for key, receipt in local.items():
            if key in receipts:
                problems.append(f"Ambiguous acceptance receipt across state files: {key}")
            receipts[key] = receipt
    parts = sections(body)
    if ACCEPTANCES not in parts:
        problems.append('The description has no "Accepted change proposals" section.')
    cited, covered_paths, covered_nodes, covered_links = set(), set(), set(), set()
    for line in parts.get(ACCEPTANCES, "").splitlines():
        # Prose explains the approval history; only list items declare receipts.
        if not re.match(r"\s*(?:[-*+]|\d+[.)])(?:\s|$)", line):
            continue
        match = ACCEPTANCE.fullmatch(line)
        if not match:
            problems.append(f"Invalid acceptance reference: {line.strip()}. Use - `proposal-id` revision 1 by `participant-id`.")
            continue
        key = (match[1], int(match[2]), match[3])
        if key in cited:
            problems.append(f"Duplicate acceptance reference: {key}")
        cited.add(key)
        receipt = receipts.get(key)
        if receipt is None:
            problems.append(f"No recorded acceptance for {key[0]} revision {key[1]} by {key[2]}.")
            continue
        if "approved_paths" not in receipt:
            problems.append(f"Acceptance {key[0]} revision {key[1]} has no approved_paths; capture a scoped approval rather than extending an earlier receipt.")
            continue
        covered_paths.update(receipt["approved_paths"])
        covered_nodes.update(receipt["node_ids"])
        covered_links.update(receipt["link_ids"])
    if not cited:
        problems.append("List at least one recorded acceptance of a displayed proposal version.")
    for path in sorted(paths - covered_paths):
        problems.append(f"Changed file is outside the cited approved scope: {path}")
    for _, ident, _, category, _ in tree_changes:
        covered = covered_nodes if category == "nodes" else covered_links
        if ident not in covered:
            problems.append(f"Changed {category[:-1]} is outside the cited approved scope: {ident}")
    return problems


def main(argv=None, cwd=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("states", nargs="+", help="reasoning YAML files, relative to the repository root")
    parser.add_argument("--base", required=True, help="base branch or commit, such as origin/main")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--body-file", help="file holding the pull request description")
    mode.add_argument("--suggest", action="store_true", help="print the Tree updates list for this branch")
    parser.add_argument("--format", choices=("list", "diagrams", "markdown"), default="list", help="suggestion format; markdown includes diagrams and the collapsed list")
    args = parser.parse_args(argv)
    try:
        base, before_documents, after_documents = load_documents(args.states, args.base, cwd)
        before, after = document_items(before_documents), document_items(after_documents)
        found = changes(before, after)
        if args.suggest:
            if args.format == "list":
                print("\n".join(describe(change) for change in found) if found else "None")
            else:
                for state in after_documents.values():
                    views.validate(state)
                if args.format == "markdown":
                    print(outcomes_section(*expected_outcomes(before_documents, after_documents, found)))
                print(diagrams.markdown(before_documents, after_documents))
                if args.format == "markdown":
                    print(folded_updates(found))
            return 0
        body = Path(args.body_file).read_text()
        paths = changed_paths(base, cwd)
        problems = check(body, before, after)
        problems += check_acceptances(body, before_documents, after_documents, paths, found)
        problems += check_presentation(body, before_documents, after_documents, found)
        problems += check_outcomes(body, *expected_outcomes(before_documents, after_documents, found))
    except (ValueError, KeyError, TypeError, AttributeError, OSError, yaml.YAMLError) as error:
        problems = [str(error)]
    if problems:
        print("Tree check failed:")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    serves = [id_ for _, id_ in claims(sections(body).get(SERVES))]
    print(f"Tree check passed: serves {len(serves)} existing item(s); {len(found)} tree update(s) match the YAML; recorded acceptances cover {len(paths)} changed file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
