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

Open `http://127.0.0.1:8878/demos/reason-commons-in-use/index.html`. Every page is complete without JavaScript; `app.js` adds the diagram/outline switch, statement search, path highlighting and clipboard copying, and redirects the earlier `?view=…&tree=…&item=…` links to the new pages. `--check` compares all 72 generated files and fails on unexpected files in the published folder. With PyYAML installed it also re-projects the fictional example and source reconstructions from their public working files and fails if any pinned snapshot has drifted.

## Records with distinct publication boundaries

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

## Purpose, participation, sources and historical revisions

Each commons overview opens with a plain-language expression of its published goal, an explicit Get involved route (practice for the fictional example), and one question drawn from a public statement or connection. The reviewed `front_page` metadata in `site.json` is editorial presentation: it cannot alter reasoning, standing or endorsement, and its reference must be in the public projection. Selecting an invitation does not record a group-agreed priority. The exact goal and its standing remain inspectable, and all fuller overview material remains in a native, initially closed disclosure.

Get involved offers three concrete starts: an example, an assumption to question or help with interpretation. Each has a contextual brief for an AI and a script-free reading/copying fallback. Real commons also link to a prefilled draft in the public project issue tracker; a visitor reviews and posts it there. Nothing is sent automatically or incorporated into the reasoning by opening a link or copying a brief. The invented Willow Lane example provides practice only and has no sharing recipient. The contribution destination is explicitly allowlisted to the public project repository.

Source reconstructions retain compact provenance near the opening, full document representations in an initially closed source disclosure, and source cards alongside source descriptions on About. Cards lead to native source disclosures where availability, citation counts and linked examples retain every locator and attribution basis for that source. No original cover, document availability or independent corroboration is invented. The directory places the goal, featured question and involvement route before provenance.

Re-membering's `commons/re-membering/review.json` keeps its three already-public release snapshots, originating commit IDs and fingerprints. The authentic graph and wording comparisons and detailed releases remain separate, initially collapsed disclosures on Changes. Historical labels, wording and connections remain fixed to their own snapshots, with shared nodes in matching positions. The short overview feedback account leads to the comparison while keeping author judgment open; neither retraining nor endorsement is established. Public `reasoning.json` and the working reasoning are unchanged by the overview redesign.

Map pages retain their existing routes and all six question destinations, with the published goal as context. A file existing in Git is insufficient evidence of live delivery: after publication, inspect the actual Map and all six pages and reject JSON errors or incomplete HTML. The 25 October review found the live host missing these already-generated files; the hosting repair is tracked with the implementation and must be verified separately from local build success. Every generated HTML page carries CSS and JavaScript versions derived from their content. A changed asset therefore changes each page's delivery fingerprint while keeping its body and public reasoning intact. This both refreshes GitHub-driven publication and avoids stale asset references.

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

## Wisdom and AI

`commons/wisdom-ai/publication.json` registers the public [Wisdom and AI](https://ai.lifeitself.org/) research agenda through the same source-reconstruction projection and page generator as Gandhi 2.0. `ltp/wisdom-ai/reason-commons.yaml` preserves the seven proposed statements and four proposed links from the initial example. The source is a set of questions, so its `web_page` references allow AI inference or a related-question reference, not source-author attribution of an asserted answer. Every proposed item records its exact starting question; unresolved question locators fail the build. The page author is the author of the research questions, not an endorser or contributor of the proposed answers.

The explicitly selected `commons/wisdom-ai/source-questions.json` companion preserves the governing question and 93 question entries across four hierarchies. Its schema rejects unreviewed fields, duplicate IDs and off-page source links. The About page presents the complete hierarchies with the shared outline and disclosure components, without requiring JavaScript. The Map and question-page navigation include only the three reasoning trees actually recorded; no conflict, prerequisite or action sequence is invented. All diagram geometry, fonts, colours, standing treatments, statement-detail pages, outline switches, copyable briefs and navigation come from the shared components. No separate stylesheet or viewer is introduced.

After a deliberate edit to the canonical example, refresh only its registry using `refresh_reconstruction` from `build.py`, then run the normal build, tests and `--check`. The generic `--refresh-reconstruction` option refreshes every reconstruction, so use it only when all those sources are intended to be refreshed. Keep the original capture date and SHA-256 unless the source page itself has been recaptured. Preserve source-question text and hierarchy when updating the capture. The earlier `/demos/wisdom-ai/index.html` route redirects to `/demos/reason-commons-in-use/wisdom-ai/index.html`.
