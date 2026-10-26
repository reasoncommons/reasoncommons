# Pull requests that carry reasoning and approval

For a project whose conversational reasoning YAML lives in its own repository. A PR carries the reviewed implementation, the actual tree updates and the recorded typed acceptance of the displayed proposal versions it implements. It names the reasoning served so reviewers can follow the work toward the goal.

## From proposal to PR

1. Show the Change proposal with its ID, revision, reasoning, tree updates, exact covered file paths and validation plan.
2. Wait for typed human acceptance; record the reply, participant, scope, proposal version, recording time and `approved_paths` in `change_acceptances`. Save the intended tree updates and validate before implementation.
3. Implement and test the approved scope. A material expansion needs a revised proposal and fresh acceptance before the extra edits.
4. Include the implementation, reasoning changes and receipt together in the PR. When the change carries a prediction, show its feedback commitment under **Expected outcomes**. Show visible rendered diagrams of the changed reasoning before a collapsed complete update list. Cite the existing receipt rather than requesting acceptance again for the same approved version and scope.
5. Review the final diff against the accepted scope before merging. Implementation approval, PR review and reasoning endorsement are separate decisions. Creating or merging a PR does not set node/link status to accepted or complete unresolved backlog work.

## The template

Save as `.github/pull_request_template.md`, replacing the state-file path:

```markdown
## What this changes

<!-- One or two sentences. -->

## Expected outcomes

<!-- Generated with --suggest --format markdown: each feedback commitment or report in the diff, or "No feedback commitment: <reason>" for unassigned predictions, or None. -->

## Reasoning changes

<!-- Visible generated Mermaid diagrams of the YAML diff. Generate this section and the collapsed list with:
python3 skills/ltp/scripts/check_pr_trees.py path/to/reason-commons.yaml --base origin/main --suggest --format markdown -->

## Reasoning this serves

<!-- Existing node or link IDs from path/to/reason-commons.yaml, one per line. Leave empty only if Tree updates lists new reasoning. -->

## Tree updates

<details>
<summary>Complete checked change list</summary>

<!-- Every added, changed or removed node/link, or None; keep this list collapsed. Describe backlog work separately. -->

</details>

## Accepted change proposals

<!-- One saved acceptance reference per line, using this exact format:
- `proposal-id` revision 1 by `participant-id`
The receipt must cover the changed files and tree IDs. -->

## Validation

<!-- Checks completed, remaining uncertainty, and review of implementation against the accepted scope. -->
```

GitHub fills a new PR's description with the template in the browser. Agents or `gh pr create --body-file` must fill these sections themselves. An acceptance reference is not a fresh proposal or a request to endorse the reasoning. Several proposals may be delivered in one PR; list the relevant receipt versions individually.

Explanatory paragraphs may appear before, between or after the approval references under **Accepted change proposals**, for example to explain how one revision supersedes another. Only explicit list items declare approval references, and each must use the format above. Prose alone, including an inline mention of a receipt, does not supply approval or scope coverage. Malformed list items, duplicate or unknown references, and uncovered changes still fail the check.

## What the check establishes

`scripts/check_pr_trees.py` compares the working tree with the merge base of `--base` and `HEAD`, across one or more state files. In the reasoning sections, a list item's first backticked ID is its claim; later IDs, such as link endpoints, are description. Template comments are ignored. The checker validates current conversational state using the sibling `update_views.py` helper without writing snapshots or views. `render_pr_diagrams.py` derives one change diagram per affected tree from the old and new YAML, with one-hop context around changed nodes and the statements that changed backlog work refers to, and the old/new endpoints of changed links. Keep all three scripts together when using them in another repository.

The check fails when:

- a stated tree update has no matching node/link change, a verb disagrees, an actual node/link change is unstated, a served ID does not exist, or required reasoning sections are missing;
- the visible diagrams are missing or their graph source differs from the generated YAML diff, their display configuration is unsupported, they appear after the update list or are hidden inside a collapsed block;
- generated unresolved-connection notes are missing beside the visible diagrams;
- the complete update list is visible, expanded by default or incomplete inside the collapsed block;
- the current YAML or acceptance metadata is invalid, or an earlier acceptance receipt has been changed or removed;
- the Accepted change proposals section is missing, has no explicit approval reference, contains a malformed approval-reference list item, or names an unrecorded proposal version and participant;
- a cited receipt lacks `approved_paths`, a changed file is outside the cited paths, or a changed node/link ID is outside the cited tree-item IDs.

Use exact repository-relative paths, including the state file and coordination files covered by the proposal. Paths are literal names, not globs; renames require both the old and new names. Coverage may come from several cited receipts. Uncited receipts cannot supply coverage. Receipt additions and backlog/coordination edits are covered through their file paths and textual scope; the Tree updates list still describes node/link changes. Historical node/link IDs remain valid receipt references after removal.

The working-tree check includes tracked and staged changes, including staged new files. Untracked drafts are outside the PR until explicitly staged. Run after staging the intended files, then repeat against the committed branch if its diff changes. CI checks the committed PR head. Old conversational receipts without `approved_paths` remain valid records, but need a new scoped approval to supply PR file coverage; do not retrofit an earlier reply to an expanded approval.

These checks establish declared coverage, not that code inside an approved file fulfills the intended change, that a stored reply came from the human, or that approval preceded editing. Review the implementation and original conversation for those questions. The checker never changes reasoning standing.

## Generate and inspect the diagrams

```sh
python3 skills/ltp/scripts/check_pr_trees.py path/to/reason-commons.yaml --base origin/main --suggest --format markdown
```

This emits the **Expected outcomes** section, the visible **Reasoning changes** section and the closed **Tree updates** details block together. Put a short change summary before the diagrams, and the served reasoning, backlog, acceptance references and validation afterward. Preserve the generated Mermaid graph source: CI checks it against the YAML diff, including qualification text, actual topology, standing and kind labels, backlog notes, AND conditions, previous wording and removed items. Display configuration is validated separately: YAML formatting and key order may vary, and `config.flowchart.wrappingWidth` may be omitted or set to a positive integer. Keep `config.htmlLabels: false`; other configuration fields, malformed YAML and duplicate keys are rejected with a configuration-specific error. If the reasoning needs correcting, edit the YAML through the approved workflow and regenerate. `--format diagrams` emits only the diagram section; the original `--format list` remains available for tooling, but a flat list alone is not a complete PR description.

**Expected outcomes** shows every feedback commitment version the PR adds, as a table of the change being evaluated, each expected benefit and possible harmful consequence with tree, kind and standing at capture, who gives feedback, any `ask_after` time and the observation opportunity. Reports appended to an existing version are listed with author, time, readiness, the person's words and the verdict on each outcome, so a PR that records feedback shows it. CI requires the generated blocks verbatim, so a hand-written summary cannot drift from the YAML. If the PR adds a Future Reality predicted or undesirable effect that no commitment covers, the generated placeholder `No feedback commitment: REPLACE WITH REASON` must be replaced with an actual reason, such as a generic historical prediction nobody can observe. A commitment names an actual provider; never invent one to satisfy the check.

Each affected tree has one diagram containing all its changed branches and neighboring context. Disconnected observations stay together in that tree diagram without invented arrows, grouped under “Not yet connected”; generated notes identify disconnected display groups and unresolved statement connections. This is a change view, not the whole tree: groups may connect through unchanged reasoning outside the bounded context. The diagram's heading names the tree; each node shows the change and its standing on one line (`ADDED · [Proposed]`), its kind on the next, then the statement's one-sentence label (or full text when it has none), with no identifiers. The collapsed update list keeps the full statements. A label-only edit is drawn once as RELABELLED. ADDED, CHANGED and REMOVED describe the PR diff; PREVIOUS shows an earlier version and CONTEXT gives unchanged neighboring reasoning. These are separate from the standing: [Accepted] for now, [Proposed] or [Disputed]. Solid arrows are accepted links and dotted arrows proposed ones; disputed links say so. Color supplements explicit text labels. Added, revised or removed backlog work appears as a note attached by a dotted line to the statement or link it concerns, showing its one-sentence label or the work named in words, so a backlog-only PR still has a generated diagram that the check requires. A PR with no node, link or backlog changes needs no invented diagram; describe its scope normally.

Inspect the actual GitHub description for rendered diagrams, readable labels and a collapsed list. A successful source check does not prove rendering or usability. Do not replace generated diagrams with a decorative process chart or expand the technical checklist into the main explanation.

Keep the generated frontmatter as the starting point, including the [Mermaid label setting](https://mermaid.js.org/config/schema-docs/config-properties-htmllabels.html) `htmlLabels: false`: SVG labels avoid the clipping observed with GitHub's capped HTML labels. Supported wrapping-width changes do not alter the checked reasoning. Inspect the full statements, including long metadata lines, rather than counting rendered frames alone.

## Run locally and in CI

```sh
python3 skills/ltp/scripts/check_pr_trees.py path/to/reason-commons.yaml --base origin/main --body-file /tmp/pr-body.md
```

Save as `.github/workflows/tree-check.yml`, adjusting the state-file path:

```yaml
name: Tree check
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
permissions:
  contents: read
jobs:
  tree-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pyyaml
      - name: Test reasoning and approval helpers
        run: python3 -m unittest discover -s skills/ltp/tests
      - name: Check tree updates and recorded acceptance coverage
        env:
          PR_BODY: ${{ github.event.pull_request.body }}
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
        run: |
          printf '%s\n' "$PR_BODY" > "$RUNNER_TEMP/pr-body.md"
          python3 skills/ltp/scripts/check_pr_trees.py path/to/reason-commons.yaml --base "$BASE_SHA" --body-file "$RUNNER_TEMP/pr-body.md"
```

The description passes through an environment variable rather than being interpolated into executable shell code. The `edited` trigger rechecks corrected descriptions; `synchronize` checks updated commits.

### Require the check before merging

Running the workflow reports a result; branch protection makes that result a merge requirement. This repository records its main-branch protection request in `.github/branch-protection.json`: require `tree-check` from the GitHub Actions app (ID 15368), require the branch to be up to date and enforce these requirements for administrators. This does not add a reviewer-count requirement. Other repositories must verify their own check name and app ID before adopting the configuration.

For this repository, an administrator can apply the recorded configuration with the [Update branch protection API](https://docs.github.com/en/rest/branches/branch-protection#update-branch-protection):

```sh
gh api --method PUT repos/life-itself/reasoncommons/branches/main/protection --input .github/branch-protection.json
gh api repos/life-itself/reasoncommons/branches/main/protection
```

Before applying it, inspect existing protection and active rules and preserve any additional requirements introduced since this configuration was recorded. Confirm the response includes `required_status_checks.strict: true`, `checks` containing `tree-check` with `app_id: 15368`, and `enforce_admins.enabled: true`. The JSON file records the desired settings; committing it alone does not apply them. A PR with a pending or failed required check must be corrected and rechecked before merging. A successful check still does not establish semantic conformance, consent authenticity or reasoning endorsement.

## Small changes

A small fix still follows the proposal and typed acceptance rule, names the reasoning served, and makes the meaningful annotation or backlog update described by the proposal. Write None in the Tree updates list only for no node/link edits; backlog work appears in the generated diagrams and in the proposal, scope and result. Reuse existing reasoning rather than inventing claims to fill a template. If the connection to the goal is missing or the requirement encourages loose citations, record that gap or challenge and resolve it before implementation.
