# Make sources and feedback revisions visible

Accepted proposal: `re-membering-feedback-prototype-2026-10-24` revision 1. This document records the design and delivery plan for a local review prototype; the approval receipt is retained privately. The prototype does not change the published commons, its reasoning, or its standings.

## The reader’s task

A first-time visitor should be able to identify the material used to construct a commons. A returning reviewer should be able to recognize a concern they raised, inspect the resulting revision in context, and distinguish a published revision from their endorsement of its interpretation.

## First prototype

Open `apps/reasoning-demo/prototypes/feedback-and-sources.html` in a browser, directly or through a local server. It is a self-contained HTML page with embedded licensed Alegreya Sans fonts, static historical SVG diagrams, native expandable sections, a CSS text-view switch and a small anchor-opening enhancement. It has no external runtime or submission controls. Desktop presents the archived diagrams side by side; phones present both snapshots as complete text outlines at readable sizes. Source cards lead to expandable source descriptions, counts of statements and connections citing each document, representative exact source locators and links to the published items.

The opening contains five distinct document cards for the slide deck, spoken script, extended passages, glossary and bibliography. The cards are labelled representations rather than reproductions of the original PDFs. All five are companion documents by Margeret Heath for one talk. Counts of documents or citations are not independent corroboration or a confidence score.

The visible feedback story attributes a paraphrase of author feedback relayed by David, shows the resulting agency revision, and leaves author assessment open. It makes a change to the reasoning record inspectable without claiming AI retraining or an automated review process. The prototype does not publish the private messages.

## Evidence and comparison baseline

The exact release Margeret saw is unconfirmed. The comparison therefore identifies the previous and current published releases explicitly and does not call either one the version she reviewed.

| Release | Git commit | Public snapshot SHA-256 |
| --- | --- | --- |
| 2026-10-23.2 | `4b22478f17d69eb17100b20993c00e47235838c1` | `57adbb7203c5fbba6796d52fb0b78fb38adbafaf32e5d3a51179bb4ebc06ef6b` |
| 2026-10-24.1 | `954a0978216014f1d14d5a9dc2fd5993b2fa417a` | `62483940c449795ea7cd3e2faa124e2580acfc5b7f033122185ccc84f5d5804e` |

Both snapshots come from `apps/reasoning-demo/commons/re-membering/publication.json` at the named commits. The HTML embeds only reviewed public historical evidence, keyed by release and stable IDs, in its `historical-evidence` JSON block. The private collaboration state is never used to populate the page.

The comparison uses the actual three-node `rm-f-attune` → `rm-f-variation` → `rm-f-learning` path. It preserves the two existing `contributes_to` connections. The revised snapshot adds `rm-f-coordination` and `rm-f-capacities`, with `rm-fl-coordination`, `rm-fl-capacities`, `rm-fl-retuning` and `rm-fl-capacity-learning`. The feedback arrow is explicitly `feeds_back_to`. All five nodes and all six displayed connections remain proposed. There are no omitted joint inputs in this fragment because each displayed link has one source.

Shared statements retain matching diagram positions. Archived short labels appear in the diagrams and text outlines; the complete before-and-after wording of the three revised statements and full wording of the two added predictions appear below. The selected views are marked as fragments, and the existing current-map link places them in their larger context. The broader distinction between source account and practical inference remains open for review.

## Delivery sequence

| Stage | Work | Completion evidence |
| --- | --- | --- |
| 1. Establish the evidence | Pin release snapshots and source metadata; map feedback concerns to actual revisions; retain uncertainty about the reviewed release. | Snapshot hashes, exact statements, labels, IDs and endpoints agree with Git. |
| 2. Review one complete example | Build five source cards, the visible feedback story and one complete agency comparison. | Local prototype, readable historical text and diagrams, working source and comparison anchors. |
| 3. Extend after review | Add comparisons for the process account becoming the opening and uncertainty changing purposes; integrate the approved design into the shared publisher. | A separately accepted implementation scope and user review. This stage has not been implemented. |
| 4. Evaluate comprehension and integrate | Test with willing readers, revise, then check generated pages and a separate deployment preview before live integration. | Reader evidence plus historical, accessibility and publishing checks. No human test or deployment has been conducted by this prototype. |

## Reusable design for any commons

Use source cards on each overview and a compact stack with a source count on directory cards or other constrained surfaces. Preserve readable titles alongside any cover thumbnails. An expanded source view should identify title, author, type, version, availability and role; connect it to the passages and reasoning that actually use it. Distinguish sources directly read from background works merely mentioned by another document, and companion versions from independent evidence. When a source is unavailable for publication, retain an accurate title card and public-safe metadata.

Maintain a reviewed feedback-to-revision record separate from reports about trials of real-world interventions. Each record needs the concern and attribution basis, reviewed release when known, comparison releases, exact affected item IDs, conceptual explanation, and the remaining review question. A published response is not a verdict that the concern is resolved. Keep the original predictions and all historical wording fixed to their releases rather than reading historical “after” text from the latest snapshot.

Choose the presentation by the revision: aligned subgraphs for topology changes, aligned statement cards for wording changes, and a comparison of the page opening for changes in ordering or emphasis. Add no causal arrows to source-account observations that have no recorded connections. Start every change accordion collapsed. Keep a short summary visible, then show a focused before-and-after comparison only when its heading is activated. Allow multiple comparisons to remain open and make them directly linkable. Keep longer exact-wording evidence in a separate sibling accordion rather than expanding the graphical section into a long report. The short feedback story remains visible outside the accordions. The existing detailed release history remains available for inspection.

## Reader review protocol

Invite willing readers to inspect the prototype without a guided explanation, then ask: What was this commons built from? What changed because of feedback? Has Margeret endorsed the revised interpretation? Ask the returning reviewer to locate a relevant concern and explain the resulting change without rereading the full commons. Margeret’s separate assessment would concern fidelity to her meaning and what remains missing. No participant, feedback commitment, deadline or outcome is assigned here.

## Verification record

Implementation bead: `reasoncommons-vtr`. The local prototype and this plan are complete. Technical verification was performed on 24 October 2026; actual author assessment and newcomer comprehension remain untested. No shared publisher, working reasoning, generated website page or live deployment was changed.

- Compare every displayed node, label, full statement and edge with its exact pinned release; verify all source counts and locators against the current pinned public snapshot.
- Inspect desktop and a real 375px viewport for reading order, diagram legibility and page overflow.
- Exercise keyboard opening and closing of the agency and source disclosures, visible focus, and the CSS text-view switch.
- Confirm source and comparison bookmarks open their target; with scripts blocked, check the native disclosures, text view and all historical content remain readable.
- Verify local and published link targets, absence of private messages and paths, and unchanged generated public output.

No full-site test suite is needed for an isolated buildless prototype unless verification exposes a shared dependency or an implementation change is proposed.

### Completed checks

| Check | Result |
| --- | --- |
| Historical accuracy | Pass: eight node appearances and eight link appearances across the two exact snapshots, every archived label and endpoint, all six before/after wording cells, and the two added full predictions agree with the pinned public evidence. |
| Sources and links | Pass: five source records and their statement/connection citation counts match the snapshot. All locators and attribution bases for representative linked statements are retained. Local anchors and every linked published item, source, question and view target resolve in the existing generated public files. |
| Desktop and phone | Pass: real 1440px and 375px DevTools viewport checks report equal viewport and document widths with no overflowing elements. The source shelf, feedback story and both comparison layouts were visually inspected. Intermediate widths stack diagrams to retain legibility. |
| Keyboard and reading modes | Pass: Enter collapses and reopens the agency comparison and source disclosure; Space toggles the CSS text comparison; focus remains visible. Source cards open the matching source panel, and comparison anchors expose the open comparison. |
| Script-free reading | Pass: a separate localhost response with `Content-Security-Policy: script-src 'none'; object-src 'none'` preserves static historical diagrams, complete wording, native source disclosures and the CSS text switch. Keyboard interaction was exercised there. |
| Scope and publication | Pass: prototype evidence contains no private paths, messages, receipts or PDFs; existing publisher code, public working reasoning and generated website output are unchanged. Files remain local and uncommitted; no messages, PR or publication were performed. |

Review screenshots were produced as local QA artifacts. The Codex in-app browser permits HTTP previews but blocks direct `file:` URLs; the deliverable is therefore the self-contained saved HTML file, which can be opened directly by the user in a normal browser. Temporary QA servers are stopped at handoff. No server is needed by the saved file.

## Next step after prototype delivery

Review the five-source presentation and this one complete agency comparison with David. Establish which release Margeret actually saw before presenting a personalized comparison to her. If the presentation helps, prepare a separate scoped proposal to integrate it into the shared publisher and add the process and uncertainty comparisons. That integration, author review and reader test have not been performed.

## Accordion correction after David’s review

David clarified that change details must be contained in accordion sections so a viewer can compare before and after without being overwhelmed. The prototype previously expanded its agency section on load. Within the already accepted revision 1 scope, both change sections now start collapsed: the first contains the focused graphical comparison and explanation, and the second contains the exact statement wording. Opening a source or a bookmarked comparison remains available. Historical evidence, source metadata and reasoning standing are unchanged. Correction checks pass: both accordions are closed on initial load; Enter opens and closes each independently; opening the graphical section leaves the exact-wording table hidden, and opening the wording section leaves the graphical section hidden. Historical content checks still pass, and the real 1440px and 375px checks report no overflow. The live website remains unchanged.

## Accepted publisher integration

David accepted `re-membering-feedback-integration-2026-10-24` revision 1 with the exact typed reply `accept`; the receipt was recorded privately at 2026-10-24T17:52:56Z and validated before integration edits. This later scope covers the actual generated pages, separate preview, PR, merge after checks and required repository reviews, and live verification. It supersedes the local-only delivery limit for this integration without changing the historical prototype receipt. Implementation bead: `reasoncommons-y5f`.

The approved agency design is integrated into the real Changes page with two independently collapsed comparison sections and collapsed release history. The overview shows five source cards and the visible feedback story. Gandhi 2.0 reuses the source shelf and disclosures from its eight published source records; directory cards show a compact source stack. Public archived snapshots are checked against fingerprints and the publication allowlist; no nodes, links, standings or public reasoning JSON change. Additional process or uncertainty comparisons remain future work, outside this integration.

All 85 meaningful publication, topology, attribution, archival and rendering tests pass. All 62 generated files and website exports are current; 4,961 links/assets pass with no errors. Local desktop and real 375px layouts, expanded graph and wording sections, keyboard-independent disclosure, source bookmarks, CSS text mode and script-disabled reading have been checked. The separate [hosted preview](https://zubitgr4-anon.flowershow.me/demos/reason-commons-in-use/re-membering/changes.html) expires on 1 November 2026. Hosted defaults, independent expansion, source locators and text mode were inspected. Direct asset-byte retrieval returns HTTP 403, so hosted byte equality is not claimed. Author fidelity and actual newcomer comprehension remain open. PR and live delivery are pending at this checkpoint.
