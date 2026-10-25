# Commons site UX across all commons

David accepted `commons-site-ux-plan-2026-10-25` revision 1 with the exact typed reply `accept`; the receipt was recorded privately at 2026-10-25T16:14:18Z and validated before this plan was saved. Epic: `reasoncommons-i0e` (`bd ready --label commons-ux`). The plan proposes an order of work. Each phase needs its own Change proposal and typed acceptance before implementation, and accepting this plan endorses no reasoning.

## Why the whole site, not just Gandhi 2.0

The [Gandhi 2.0 UX critique](../../reviews/gandhi-2-0-ux-critique/README.md) reviewed one commons, but all five commons (Gandhi 2.0, Re-membering, Wisdom and AI, Reason Commons and Willow Lane), the hub and How it works are built by one generator in [apps/reasoning-demo/](../../../apps/reasoning-demo/): `pages.py`, `diagrams.py`, `styles.css` and `app.js`. Nearly every finding is a generator fix that reaches every commons at once. Only a few items need copy written for each commons.

Reading the code changed four parts of the critique's plan:

- **Reading direction is mostly a wording problem.** The layered layout already puts each statement above the ones that lead to it (`layered()` in `diagrams.py`), so the goal, the problems, the desired effects and the objective are already at the top. What differs is each page's "How to read it" line (`TREES` in `pages.py`), the `overcomes` arrows, which point down, and the conflict cloud. R7 is therefore cheap and moves early.
- **Context boxes can't take the critique's dashed outline.** Dashed borders already mean "proposed" across the site, so boxes from other parts need a different marker.
- **The Overview rebuild (R1) reverses part of the accepted goal-first design** (`commons-overview-and-map-2026-10-25`, see [2026-10-25-commons-overview.md](2026-10-25-commons-overview.md)), which puts contribution before the story and keeps the fuller account collapsed. Changing that is David's decision, taken in phase 3.
- **Usage tracking (R16) would break the footer's promise** that nothing a visitor does is sent anywhere. The user tests stay; tracking is left out.

## The domain model stays as it is

The domain model is the reasoning and what is published from it: statements, connections, kinds, relations and standings; credits, source references, backlog and release history; the registries (`publication.json`, `review.json`), the working YAML files and projection versions; and every `reasoning.json` export. No phase changes any of them. The work stays in `pages.py`, `diagrams.py` (drawing only), `styles.css`, `app.js`, the generated pages and the tests, plus the editorial `front_page` copy in `site.json`, which the generator's README already treats as presentation that cannot alter reasoning. Every PR in this plan shows this diff is empty:

```sh
git diff --stat origin/main -- ltp apps/reasoning-demo/commons apps/reasoning-demo/examples apps/reasoning-demo/publication.json 'website/demos/reason-commons-in-use/*/reasoning.json'
```

## Phases

Sizes are relative: S, M, L. Critique references are to its recommendations R1–R16 and its section lists.

### 1 · Fix what's broken — now, S, one PR (`reasoncommons-i0e.1`)

- Line the Changes page back up with the rest of the site; the likely cause is `.changes-wrap{max-width:1400px}` at desktop widths in `styles.css`.
- Raise tab counts and small metadata to the AA contrast minimum (they measure 2.44:1).
- Put spaces between the lines of each diagram box, so it is read aloud and copied as real words.
- Fix the reversed connection labels on statement pages: "Needed for this" and "This is needed for" replace "Leads into".
- Reword assumption labels in plain language, such as "Assumption behind arrow 1 · proposed by the AI".
- Draw boxes from other parts at full contrast, with a "from part N" tag.
- One Diagram/Outline switch per page, and a choice made on desktop no longer forces diagrams on phones.
- Give each Outline section its own heading, and use one live status region on Statements instead of about 480.
- Centre "Where it sits" on the statement it is about, and show a cue wherever a diagram is cut off.
- Add a favicon and Open Graph and Twitter preview tags to every page.

Fixes R3, R6, part of R8 and the accessibility list.

### 2 · One frame for every page — now, M (`reasoncommons-i0e.2`, after phase 1)

- The same header on every tab, a "Demo" marker by the logo and one home link.
- On phones, a menu for the site navigation and a shorter header, so the page title is on the first screen.
- Plainer labels: "Changes" becomes "History"; "A question to explore next" becomes "Where to start"; tab counts say what they count; card labels drop the question's short name; "proposed" is said once, then the badge and borders carry it.
- A "What you're looking at" strip on every commons page, built from the commons' kind, sources and byline, with one optional line of copy where a name needs explaining, as "Gandhi 2.0" does.
- One reading line and one legend for all diagrams, with colours by role. The 19 statement types stay; only how they are coloured changes.
- One home for each kind of content: sources and credits on About, conflicts on Conflict, one-line links elsewhere.
- Fewer CSS breakpoints (15 today).

Fixes R2, the display parts of R4, R5, R7 and part of R13.

### 3 · The Overview as a guided read — next, M plus writing (`reasoncommons-i0e.3`, after phase 2)

- Order the page as: the "What you're looking at" strip; the argument in brief; the existing path from problem to action as one vertical chain, each card shown once (rendered differently, the registry is not edited); the six questions, each with a one-line answer instead of a thumbnail; then ways to respond.
- Show sources as a plain list instead of the faux covers.
- Before it ships: David's decision on reversing the accepted goal-first order; an argument in brief for each of the five commons, written as editorial copy and checked against the record (drafted during phases 1 and 2); and a baseline 5-second and 60-second test with a few people.

Fixes R1 and R14.

### 4a · A diagram viewer — next, L (`reasoncommons-i0e.4`, after phase 2)

- Diagrams fit the page width by default, open in a full-screen pan-and-zoom view, and never scroll vertically inside the page.
- Long pages get a part index and a sticky 1-to-6 question stepper.
- Each diagram gets a "skip this diagram" link.
- Outlines on phones collapse below the second level, with "expand all".
- Actions are shown as one table.

Fixes R8, part of R13 and the missing internal navigation.

### 4b · Small statement pages, a side panel and filters — next, L, alongside 4a (`reasoncommons-i0e.5`, after phase 2)

- One small page per statement and connection plus a light list; Gandhi 2.0's 4.6 MB file becomes pages of about 10 KB, and old `items.html#id` links keep working.
- Clicking a box opens the statement in a side panel on the question page.
- Filters for type, person, question, standing and open question, with every count linking to its filtered list.
- Open questions becomes a filtered list that counts one thing.

Fixes R9 and R12.

### 5 · Paths for the people credited and for responders — next, M (`reasoncommons-i0e.6`, after 4b)

- "Is this you?" pages built from the existing credits.
- A "not what I meant" link on each statement that opens a prefilled public GitHub draft, as Get involved already does.
- One Respond box that turns what someone types into a GitHub draft or a brief for their AI.
- Nothing is written into the record.

Fixes R10 and R11.

### 6 · Check it worked — after phases 3 and 5 (`reasoncommons-i0e.7`)

Re-run the critique's 5-second, 60-second, participant and diagram tests as moderated sessions, and compare with the phase 3 baseline.

## Why this order

- Phase 1 is cheap, its fixes are clear-cut, and it needs no design decisions.
- Phase 2 touches every page, and the later phases build on it.
- Phase 3 helps first-time visitors most, but it needs writing and a decision, so the drafting starts now.
- 4a and 4b are the heaviest engineering and don't depend on each other.
- Phase 5 reuses 4b's per-person filter and small statement pages.

## Changed or left out to keep the domain model intact

- **One wording of the goal (R4):** the goal statement stays as it is. Only the headline changes, and it is labelled as a short form.
- **Participant flags (R10):** these become GitHub drafts, not feedback or endorsement recorded in the record.
- **The 3,150 px First steps part:** splitting it would edit the registry's views, so the diagram viewer handles it instead.
- **Showing how the record was made (R15):** this needs a conversation transcript that can be published, which is a separate decision.
- **Usage tracking (R16):** left out; see above.

## How we'll know it worked

- The critique's targets: 4 of 5 first-time visitors can say what the page is after 5 seconds; 3 of 5 can state the argument after 60 seconds without opening an accordion; a credited participant finds their statements in under 30 seconds; a reader follows one chain from a cause to the goal without sideways scrolling at 1280 px.
- Checks in each PR: the domain-model diff above is empty; contrast is at least 4.5:1; `node scripts/phone-check.mjs` reports no overflow on every commons; the page title is on the first screen at 375 px; the build, tests, `--check` and `scripts/check-website.py` pass.
