# Conversational YAML — version 1

Write `schema_version: 1`. This format is independent of the Reason Commons app. Keep one working file plus generated snapshots; omit unused trees and optional fields. Do not copy example participants or claims into a new project. Preserve existing content when updating an unversioned draft; do not silently reinterpret an unfamiliar schema version. Nodes lacking status in an earlier draft are proposed, never implicitly accepted; add their explicit status when editing them.

## Shape

```yaml
schema_version: 1
project: Quote turnaround
driver: alice
participants:
  alice: Alice
  bob: Bob
active_tree: current_reality
trees:
  current_reality:
    nodes:
      - id: n1
        kind: undesirable_effect
        text: Customers often wait more than three days for quotes.
        status: proposed
        contributions:
          - {by: bob, attribution: explicit, mode: text}
      - id: n2
        kind: cause
        text: Sales often waits for pricing approval.
        status: proposed
        contributions:
          - {by: alice, attribution: driver_default, mode: text}
    links:
      - id: l1
        from: [n2]
        to: n1
        relation: contributes_to
        status: proposed
        contributions:
          - {by: bob, attribution: explicit, mode: text}
    backlog:
      - ref: n1
        work: connect_or_explain
      - ref: l1
        work: test_causality
```

`driver` names a configured participant; `active_tree` names a tree present in the file. Each tree has `nodes`, `links`, and `backlog` lists, which may be empty. Give nodes and links stable IDs unique across the whole file. Reasoning references must resolve; acceptance receipts below preserve historical IDs even after removal.

## Node kinds

Use these exact tree keys and kinds. `observation` is also allowed in every tree for relevant material whose role is not yet clear; revisit it when useful rather than forcing a classification.

| Tree key | Allowed specialized kinds |
|---|---|
| `goal` | `goal`, `critical_success_factor`, `necessary_condition` |
| `current_reality` | `undesirable_effect`, `cause` |
| `conflict` | `objective`, `need`, `prerequisite` |
| `future_reality` | `injection`, `existing_condition`, `predicted_effect`, `desirable_effect`, `undesirable_effect` |
| `prerequisite` | `objective`, `obstacle`, `intermediate_objective` |
| `transition` | `existing_condition`, `need`, `action`, `expected_effect` |

In a conflict cloud, `prerequisite` represents either of the incompatible actions or positions believed necessary to meet the respective needs. In future reality, `injection` is the proposed change; `predicted_effect` is an intermediate consequence, and `undesirable_effect` describes a potential harmful consequence. These kinds describe roles, not truth or acceptance.

Each node has `id`, `kind`, `text`, `status`, and `contributions`. Node capture records a contribution, not a verified fact. A node may also have `label`: one sentence, one line and at most 100 characters, that diagrams show in place of `text` so they stay scannable. Write it when capturing or revising the statement, keep any qualifier its accuracy depends on, and revisit it whenever `text` changes. `text` remains the full statement of record: acceptance, challenges, text outlines and PR update lists use it. Labels are presentation, so editing one does not create an accepted revision, although views draw the current label. Diagrams fall back to `text` when a node has no label.

## Links and attribution

Each link has `id`, `from` (a list of node IDs), `to` (one node ID), `relation`, `status`, and `contributions`. Link endpoints belong to that tree. Multiple IDs in `from` mean conditions operating together (AND); alternative paths use separate links.

Use a clear relation such as `necessary_for`, `causes`, `contributes_to`, `conflicts_with`, `overcomes`, `produces`, or `precedes`. Read it from source to target: a condition is necessary for an objective, an intermediate objective overcomes an obstacle, an action produces an effect. A `precedes` link states order, not causation.

New nodes and links are `proposed`. Explicit endorsement makes them `accepted`, with `accepted_by: [alice]` recording human participant IDs. A clearly identified fragment may be accepted together. A substantive objection makes the item `disputed`. An accepted link requires all its endpoints to be accepted; when a node loses acceptance, return its accepted incident links to `proposed`. Follow the skill's conversational acceptance rules. Existing `accepted_by` may remain on a disputed item as a record of prior endorsement; only `status: accepted` determines inclusion in accepted views.

Each contribution has `by` (a participant ID or reserved value `assistant`), `attribution` (`explicit`, `speaker_label`, `driver_default`, or `assistant`), and `mode` (`text`, `voice`, or `unknown`). `by` identifies the originator of the idea, not whoever serialized it. The example link therefore belongs to Bob. Keep all contributors when combining genuine duplicates.

Nodes and links may have `assumptions: [{text: ..., by: ...}]` and `challenges: [{text: ..., by: ...}]`. Here too, `by` identifies the participant or assistant who supplied the content. A challenged node can carry `status: disputed`. Keep authorship separate from endorsement.

## Backlog is reasoning work

Each entry has `ref` (a node or link ID in this tree) and `work` (a short description of the remaining work), and may have a one-sentence `label` (at most 100 characters) that diagrams show instead of the work name. Useful labels include `connect_or_explain`, `test_causality`, `resolve_challenge`, and `examine_assumption`; these are examples, not an exhaustive vocabulary. Multiple tasks may reference the same item.

Assumptions and challenges stay on their owning node or link. Reference that owner in the backlog and add an optional `note` identifying the particular assumption or objection when needed. They do not need separate IDs.

For example, an unresolved objection to `l1` would add `{ref: l1, work: resolve_challenge}`. Keep work visible while it remains unresolved, even when the tree already has many links. Remove items from the backlog when their relevant reasoning has been addressed; drawing an arrow alone does not finish an item.

Backlog is independent of acceptance: accepted items with remaining work stay visible in accepted diagrams. Proposed and disputed items are excluded even if the backlog contains no task for them.

## Cross-tree traces

Nodes may optionally contain lists of node IDs from any tree:

| Field | Meaning | Example use |
|---|---|---|
| `addresses` | Problems or obstacles this item is intended to address | A future-reality injection references current-reality undesirable effects. |
| `derived_from` | Earlier reasoning this item was developed from | An injection references the conflict prerequisites that prompted it. |
| `implements` | A change or objective this item helps put into practice | A prerequisite objective references an injection; a transition action references a prerequisite intermediate objective. |

Use only existing IDs and meaningful traces supported by the discussion. These fields express intended relationships, not proof that a solution works or that a causal claim has been accepted. Test substantive reasoning through proposed links, assumptions, and challenges. No cross-tree link is required merely to fill out the model.

## Feedback commitments and outcome reports

The optional top-level `feedback_requests` list is defined in [feedback.md](feedback.md) and validated by `scripts/feedback.py` through the standard validator. Older files remain valid without it. Each immutable request version captures the original intervention and expected outcome statements, required named `feedback_from` participants, optional observation timing and append-only attributed reports. It is independent of reasoning acceptance and project-change approval. A queue is derived from these records, not stored as a second source of truth. Feedback-only changes remain working state and do not create an accepted-reasoning snapshot.

## Project-change acceptance receipts

Use the optional top-level `change_acceptances` list for typed user approval of a displayed Change proposal. It is separate from node/link `status` and `accepted_by`: approving implementation does not endorse the reasoning or verify a prediction. Older working files without receipts remain valid. Follow [responses.md](responses.md) to obtain acceptance from the actual human after the proposal is shown; a validator can check the record's structure, not authenticate its origin or judge consent.

```yaml
change_acceptances:
  - proposal_ref: change-quote-approval-2026-10-14
    proposal_revision: 1
    by: alice
    recorded_at: '2026-10-14T12:00:00Z'
    timezone: Europe/Berlin
    mode: text
    source: conversation
    source_text: Yes, I accept this proposal.
    scope: Add a pricing-review checklist and the proposed injection n3 with its test backlog.
    node_ids: [n3]
    link_ids: []
    approved_paths: [docs/pricing-review-checklist.md, reason-commons.yaml]
```

Each receipt requires a nonempty `proposal_ref`, positive integer `proposal_revision`, configured human participant `by`, nonempty exact typed `source_text`, nonempty accepted `scope`, `mode: text`, `source: conversation`, and `node_ids`/`link_ids` lists (empty when appropriate). Use nonempty, unique strings for historical IDs. The participant must be established from the session, not guessed or assigned to `assistant`. Proposal ID, revision and participant together identify a unique receipt; several humans may each accept the same version without implying unanimity is required.

For repository changes, also record `approved_paths`: the exact repository-relative file paths covered by the displayed proposal and typed acceptance, including the reasoning state and any coordination or delivery files the proposal covers. Use normalized paths with `/` separators, no absolute paths, `..` components or duplicates. These are literal file names, not directory or wildcard permissions; a rename needs both the old and new paths. Earlier conversation receipts without this optional field remain valid but cannot supply PR file coverage. Preserve them and obtain a new scoped approval when needed rather than rewriting them.

The PR's **Accepted change proposals** section identifies each receipt by proposal ID, revision and participant. The union of those receipts' `approved_paths`, `node_ids` and `link_ids` must cover the changed files and node/link IDs. A receipt's scope must also describe approved backlog work. The PR checker rejects altered or removed earlier receipts. Coverage checks cannot determine whether code inside an approved file fulfills the intended scope, authenticate the human reply, or prove that acceptance preceded editing; review the conversation and implementation for those questions. Opening or merging a PR does not endorse reasoning or finish its backlog automatically. See [pull-requests.md](pull-requests.md).

`recorded_at` is a quoted ISO 8601 UTC timestamp obtained when recording (`Z` or `+00:00`), not an inferred user submission time. `timezone` records the session's known IANA timezone; use `UTC` if unavailable. Optional `accepted_at` may hold an actual timezone-aware submission timestamp only when supplied by the host; never invent one. A material revision gets a new revision number and fresh typed acceptance.

Append receipts; preserve their reply, scope and time when tree items are revised or removed. `node_ids` and `link_ids` identify the approved tree changes, including removed items, and need not still exist in the working tree. Backlog work and other approved artifacts belong in the scope snapshot. Save the receipt and intended tree updates, then validate before implementation. Recording an already-given acceptance or ordinary conversational capture requires no recursive proposal. Receipt-only changes do not create an accepted-reasoning revision.

## Snapshots

The helper copies the complete working state, including WIP, into each immutable snapshot triggered by an accepted change. It adds `revision`, `previous_revision` (null for the first), and `change` containing `at`, `driver`, `summary`, and affected `trees`. These fields belong to snapshots; the working file does not need to maintain them. History preserves previous wording and removed items without `superseded_by` or embedded history fields. See [views.md](views.md) for generation and comparison rules.
