# Reason Commons in use: a site of commons

A static, read-only site at [`/demos/reason-commons-in-use/index.html`](../../website/demos/reason-commons-in-use/index.html) showing what a platform of commons could look like. A commons is a goal and the reasoning a group builds around it with the Reason Commons skill. The site lists accepted reasoning from Rufus and David's collaboration; Gandhi 2.0, a proposed source reconstruction of a Second Renaissance Forum discussion; Re-membering, a proposed reconstruction of Margeret Heath’s supplied talks with PDF page references; and a clearly labelled fictional example, Willow Lane Primary. Nothing on the site edits a commons; contributions start from a copyable brief taken to the reader's own AI.

## Pages

| Page | What it answers |
| --- | --- |
| `index.html` | What is a commons, and which ones can I read? |
| `how-it-works.html` | How is a commons built, what are the six questions, and what do the standings mean? This is the one page that names the Logical Thinking Process. |
| `<commons>/index.html` | The overview: the goal, what stands in the way, the conflict and the change chosen, actions, and who contributed and accepted. |
| `<commons>/map.html` | The six questions, each drawn small in its real shape. |
| `<commons>/goal.html`, `in-the-way.html`, `conflict.html`, `change.html`, `prerequisites.html`, `actions.html` | One question each: a diagram read in that tree's direction, an outline view, and the statements no connection reaches yet. |
| `<commons>/items.html` | Every statement and connection. `items.html#<id>` shows one item on its own (CSS `:target`), with a diagram of its neighbours, its contributors and endorsers, assumptions, challenges, open work, history and a brief for the skill. |
| `<commons>/questions.html`, `learning.html` | Open questions, and expected-versus-reported outcomes. Generated only when the commons publishes them, which today means only the example. |
| `<commons>/changes.html`, `about.html` | Releases with earlier wording kept, and what the record is and isn't. |

Diagrams are static SVG laid out at build time in `diagrams.py`: layered for the trees, the classic five-box arrangement for a conflict, and role groups for statements without connections. Every arrow comes from a published link; a link with several sources meets at one "and" junction before its single arrow. Text is wrapped with measured Alegreya Sans advance widths, so it cannot overflow its box. The font files are the unchanged Latin subsets from the reference pages, under the SIL Open Font License (`fonts/OFL.txt`).

## Build and check

From the public repository root:

```sh
python3 apps/reasoning-demo/build.py
python3 -m unittest discover -s apps/reasoning-demo -p 'test_*.py'
python3 apps/reasoning-demo/build.py --check
node --check apps/reasoning-demo/app.js
python3 scripts/export-website.py
python3 scripts/check-website.py
python3 -m http.server 8878 --bind 127.0.0.1 --directory website
```

Open `http://127.0.0.1:8878/demos/reason-commons-in-use/index.html`. Every page is complete without JavaScript; `app.js` adds the diagram/outline switch, statement search, path highlighting and clipboard copying, and redirects the earlier `?view=…&tree=…&item=…` links to the new pages. `--check` compares all 62 generated files and fails on unexpected files in the published folder. With PyYAML installed it also re-projects the fictional example and source reconstructions from their public working files and fails if any pinned snapshot has drifted.

## Four records, distinct publication boundaries

**Ours.** The authoritative collaboration record is in the private product repository and is never copied here. `publication.json` holds the reviewed allowlist of 50 statement IDs and 14 connection IDs, approved display names and the pinned accepted-only projection (projection version 1), unchanged from `accepted-reasoning-demo-2026-10-22` revision 1; the redesign was accepted as `commons-site-redesign-2026-10-22` revision 1. Routine builds and CI use the pinned projection, so they need no private access. For an authorized refresh:

```sh
python3 apps/reasoning-demo/build.py --refresh /absolute/path/to/authorized/reason-commons.yaml
```

The refresh validates the working state with the skill's validator, then exports only the selected fields of the selected items, all of which must still be accepted. Proposed and disputed reasoning, assumptions, challenges, backlog, outcome reports, receipts, paths and notes stay private. Publishing any of them needs its own selection approval.

**The fictional example.** `examples/willow-lane/reason-commons.yaml` is an invented working file in the skill's conversational format, checked by the skill's own validator, with feedback snapshots that match its statements exactly. `examples/willow-lane/publication.json` selects its items and adds display names, roles and an authored release history. Its projection (version 2) keeps standings, prior endorsement of disputed items, assumptions, challenges, open work, cross-tree traces and reports, and is accepted by the build only when `is_example` is true. Every example page carries a "Fictional example" banner, its URL and data say `example-`, and its briefs say there is no shared record behind it. To change it, edit the working file and run:

```sh
python3 apps/reasoning-demo/build.py --refresh-example
```

**Gandhi 2.0.** `ltp/gandhi-2-0/reason-commons.yaml` is an AI reconstruction of the Second Renaissance Forum thread *What Would Make a Second Renaissance Possible?*, drawing on two supplied analyses of it. It has 233 proposed statements and 238 proposed connections: the analysis's goal map, causal tree, all five conflicts, ten changes with their effects, fifteen risks each with its remedy, the alternatives raised in the thread, thirty-six first steps and eight actions. Every item credits the forum posts or essays it draws on: a forum credit names a post and that post's author, an essay credit cites the section the analysis points to, and the analysis's own reconstructions and inferences say so. The AI stays the only contributor, because it selected, worded and connected everything; credits never become authorship or endorsement, and nothing is quoted. The registry at `commons/gandhi-2-0/publication.json` pins the selection, the thread's 36 posts with their authors and dates, reviewed source descriptions, titled views for every question but the goal, the overview's blocks, retired items and the release history. Each view draws its own statements plus every connection into them; a source that belongs to another part joins as a muted box, so a joint condition is never split. A statement may sit in more than one view, as in the analysis's own sub-trees. Projection version 4 permits only proposed AI reconstruction with no endorsers or feedback commitments/reports, and refuses a credit naming anyone other than the cited post's author, an essay not shared by its author, a statement left out of every view, an overview path step that is not a published connection, chain or cross-question reference, a published item recorded as retired, or a proposed role on anything but an action. It reuses the qualification checks without changing version 1's accepted-only boundary or version 2's fictional-example requirement. Every page has a source-reconstruction banner; inspect an item for its credits, linked posts and inference labels. Original documents, local paths, approval receipts and unselected fields are not exported. Refresh after an authorised edit:

```sh
python3 apps/reasoning-demo/build.py --refresh-reconstruction
```

The opening view is built from the registry's overview blocks: the six conditions, one path from a problem through its conflict and a change to the goal and a first action, the conflict behind central intervention with the other four in brief, a proposed comparison with its possible harm, an unassigned first task and a table of whose ideas the map draws on. Two relations draw differently: `feeds_back_to` returns round the right-hand side as a labelled loop and stays out of the layer ranking, and `prevents` ends in a bar at the risk a remedy is meant to prevent. One banner says that everything is proposed, so cards and diagram boxes carry credits instead of a standing badge. Actions show "Who: unassigned" with the analysis's proposed role. There is no trial result, assigned host or participant endorsement. See [the source and review record](../../docs/product/gandhi-2-0-source-review.md).

**Re-membering.** `ltp/re-membering/reason-commons.yaml` reconstructs the practical argument of Margeret Heath’s *Being-Becoming With the World, Talk 1: Re-membering* from five directly supplied original PDFs: a 20-page slide deck, 33-page spoken script with notes, nine-page extended-passages companion, seven-page glossary of 72 terms and 14-page indexed bibliography. Margeret Heath is their sole credited author. Its 82 statements and 66 connections all remain proposed, attributed to the AI’s reconstruction, with no human endorsers or feedback commitments. Every item has a source locator and an explicit basis: paraphrase, AI reconstruction or AI inference. The source documents are companions, not independent corroboration; the script supplies the main evidence and consent qualifications, the glossary clarifies concepts, and the bibliography separates cited work from Heath’s syntheses. Its source-checking annotations are not independent verification by this commons.

The registry at `commons/re-membering/publication.json` selects the public items, five sources, sole author, titled views, overview blocks and three-release history. Its reviewed `presentation` fields override the site’s default summary, description and scope; identity and publication boundaries cannot be overridden. A `supplied_document` source has exactly `id`, `kind`, `title`, `description` and a known `author`; it requires no invented forum post, admits only its own reference bases and is credited as a directly read document. Existing forum-shared essays retain their original author/post checks and rendering. The original PDFs, local paths, receipts and private records never enter the projection. The shared publisher preserves the earlier accepted-only and fictional-example boundaries and the existing Gandhi 2.0 pages.

The opening now presents three attributed observations of Heath’s process account before one possible practical application. A reviewed `account` block is allowed only first, only for supplied documents and only for observation items; it uses existing cards and links to the songline, timing and enmindment explanation. The source observations have no invented causal links. Author-credit text acknowledges feedback on an earlier map while preserving unendorsed standing for the current revision. The learning view includes a reciprocal coordination–capacity loop, with new links explicitly sourced as AI inferences; some uncertainty may be generative, while novelty can also overwhelm or harm. Assessment can revise capacities and purposes as well as the next action.

All six views are populated: a goal and its necessary conditions, a connected candidate causal explanation, the stability–participation conflict, three routes to improvement with pressure and surveillance branches, candidate obstacles and readiness dependencies, and five illustrative actions. The practice and tool-review branches share readiness and proceed in parallel before assessment; a feedback connection returns assessment to mapping. Joint inputs stay whole across titled parts, and prevention remains a hypothesis. Conditions in the proposed action sequence are labelled “Illustrative condition” and actions “Who: unassigned”; neither observed conditions nor a real pilot is implied. Twenty-one review entries remain open; the questions page groups them by twenty referenced items. Source notes retain the distinctions between evidence for coupling, contested constitution of mind and the author’s participatory philosophical position. The six views are temporary analytical cuts through reciprocal processes across timescales. Re-project public reconstructions with the existing `--refresh-reconstruction` command after an authorised edit; routine CI reads only the pinned snapshots and public working files. See [the source and review record](../../docs/product/re-membering-source-review.md).

## Visible sources and historical revisions

Source reconstructions show a shelf of labelled document representations on the overview, and directory cards show a compact stack with the published source count. Cards lead to native source disclosures on About, where the source description, availability, citation counts and three linked examples retain every locator and attribution basis for that source. Sources without page-count metadata retain their published title and type; no cover, document availability or independent corroboration is invented. This currently serves Re-membering and Gandhi 2.0; commons without source metadata are left unchanged.

Re-membering's `commons/re-membering/review.json` contains the three already-public release snapshots, originating commit IDs and SHA-256 fingerprints, plus reviewed source-card metadata and the focused comparison selection. `revisions.py` verifies the archives with the same public projection allowlist and renders the approved agency comparison from exact historical labels, full wording and connections. Shared nodes keep matching positions. The presentation does not read Git or private working records at build time, and does not change `reasoning.json`. This is one curated comparison, not a general visual diff engine.

On Changes, the graphical comparison and exact statement wording are sibling native `<details>` sections, both closed initially. Each detailed release is also closed initially. A bookmark opens only the targeted section; native expansion and the CSS text view work without JavaScript. Phone widths show complete textual outlines instead of shrinking diagrams. Historical “after” text uses its own release snapshot; records without archives explicitly label any displayed latest text “Current wording.” The feedback story identifies a paraphrase relayed by David and keeps author assessment open; it establishes neither retraining nor endorsement.

## Meaning the site preserves

- Standing is spelled out and shown by border style as well as colour: accepted for now (solid), proposed (dashed), disputed (dotted). Earlier acceptance of a disputed item is shown as history, never as current acceptance. Where every item has the same standing, as in a source reconstruction, one banner states it instead of a badge on each item.
- Contribution and acceptance are separate. AI-originated ideas are attributed to the AI; imported statements with no known author say so. In a source reconstruction, a credit says whose post or essay an idea comes from; it is neither contribution to the commons nor agreement with the AI's wording.
- Our accepted-only record groups statements without accepted connections by role, with no arrows. Qualified public records draw proposed connections as proposed, including joint conditions. No constraint, root cause, sequence or evidence rating is inferred from layout.
- Outcome verdicts keep their meaning: observed, not observed, unclear, not assessed and awaiting a report stay distinct, and no trial is called a success.
- The example's people, places and reports are invented. Nothing in it is evidence about a real project.

## Release and rollback

Publish only `website/`. Run the build, tests, drift and website checks, then use the existing separate Flowershow preview target when authenticated; do not change production settings to test this page. Rollback is a reviewed revert of the demo change on the publishing branch. If selected content of ours needs withdrawal, remove it from the allowlist and snapshot, rebuild, publish and request host cache invalidation; third-party copies cannot be recalled.

## Review evidence

See [the review record](../../docs/product/reasoning-demo-review.md) for what was checked and what remains open. Human comprehension, coherence for a newcomer and willingness to test are still untested.
