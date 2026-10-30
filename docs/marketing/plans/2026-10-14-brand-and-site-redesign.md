---
title: Brand and site redesign
created: 2026-10-14
status: paused 2026-10-30 — next: brand narrative v2 and feel v0 (see "What next")
epic: reasoncommons-91c
---

# Brand and site redesign

Develop a clear brand narrative for Reason Commons, then redesign reasoncommons.com around it. Sequence: **story → positioning → structure → look and feel → build**. Each stage ends with a review by Rufus before the next starts. Work is tracked in Beads (`bd list --parent reasoncommons-91c`); this page holds the plan and a running decision log. Supersedes the positioning in [2026-09-01-site-positioning-and-landing-redesign.md](2026-09-01-site-positioning-and-landing-redesign.md) once stage 3 is accepted.

## Stages

| # | Bead | Stage | Gate |
|---|------|-------|------|
| 1 | `reasoncommons-91c.1` | Brand narrative: the core ideas, how they connect, what we offer (internal doc) | Rufus reviews |
| 2 | `reasoncommons-91c.3` | Positioning: one-liner, value propositions, tone and feel | — |
| 3 | `reasoncommons-91c.4` | Red-team the positioning with critic agents, then revise | Rufus reviews |
| 4 | `reasoncommons-91c.5` | Site structure and key page content | Rufus reviews |
| 5 | `reasoncommons-91c.6` | Look and feel: mood board, 2–3 directions, Flowershow theme | Rufus picks |
| 6 | `reasoncommons-91c.7` | Build Home, Use it, Guides, About; preview | Rufus reviews |
| 7 | `reasoncommons-91c.8` | Ship to main, changelog entry | — |
| side | `reasoncommons-91c.2` | Remove copyright-risk and private files from the live site | own approval |

Every stage that changes repo files gets its own small proposal and typed acceptance (repo rule). Proposals are kept short and approved one chunk at a time.

## Where we got to (2026-10-30)

Session paused here; pick up in fresh sessions from the beads below.

| Area | State |
|---|---|
| Brand | [brand.md](../brand/brand.md) on main (narrative and positioning merged, core plus appendices). Still under discussion: it reads like About-page material and the proposition is not yet distilled. |
| Proposition | Pain is clear: debates don't go anywhere, discussions don't accumulate, collaboration fractures. Candidate essences: *Make discussion add up* (lean), *Debates that go somewhere*, *A proven way to think together, now as easy as talking*. Trees and the 40-year LTP tradition are the proof, not the promise. |
| Classic brand narrative | Mostly missing: primary audience, vision (a transformation of how we think together, in groups, organisations and maybe at larger scale), mission, values. |
| IA and pages | [ia.md](../brand/ia.md) and [pages.md](../brand/pages.md) drafted 2026-10-18. They predate the commons and demo work on the site (PRs #110–#123), so revisit them. |
| Look and feel | First three directions rejected as standard; feel comes first. See [design-system/README.md](../design-system/README.md) for candidates, logo shortlist and links. |
| Process | Draft skill `designing-look-and-feel` in `life-itself/skills`: feel, mood board, 2–3 hero-only directions and logo on one living page, then full pages, then preview. |

## What next

| Order | Bead | Work | Gate |
|---|---|---|---|
| 1 | `reasoncommons-91c.9` | Brand narrative v2: proposition essence, audience, vision, mission, values, in small chunks | Rufus |
| 1 (parallel) | `reasoncommons-91c.10` | Feel v0: one phrase, three notes, character, what we are not | Rufus |
| 2 | `reasoncommons-91c.6` | Redo 2–3 directions from the feel on the living brief; pick a mark | Rufus picks |
| 2 | `reasoncommons-91c.5` | Revisit site structure against the current site and brand v2 | Rufus |
| 3 | `reasoncommons-91c.7`, `.8` | Build on the preview site, then ship with a changelog entry | Rufus |
| any | `reasoncommons-91c.2`, `.11` | Live-site file clean-up; repoint old brand filenames | own approval |

## Inputs so far

- [docs/marketing/brand-and-domain-naming.md](../brand-and-domain-naming.md) — the name, audience, naming brief.
- The talk *Where Does Our Thinking Go?* (`docs/marketing/talk/2r-research-group/` (deck at `website/talk/2r-research-group/slides.html`)) — the best existing articulation of the story.
- A distillation by a Fable agent (brand brief, IA, page outlines), 2026-10-14. Judged premature as a basis for the story; parked as input for stage 4.
- Method precedent: `life-itself/developmentalspaces.org/docs/branding/` and `life-itself/design/Process for developing a website.md`.

## Decision log

Newest last. Record decisions as they are made, not at the end.

- **2026-10-14** — The site's centre of gravity moves from *explain the idea* to *share the vision, then show it is real*. Three things, in order: (1) the vision — LTP and trees plus AI, and specifically trees integrated into discourse; (2) intro and guides, conceptually one thing — a short intro surfacing on the landing page, deep guides behind it (which also attract LTP practitioners); (3) skills and tools — the implementation we actually offer.
- **2026-10-14** — Skills are the main call to action (install / try), with pictures or a sense of a session; a video or animation may follow.
- **2026-10-14** — Why now has more than one layer: the cost barrier (a ~$2k/day consultant, used only where a $10M factory justified it), the cognitive barrier (holding six trees and keeping them updated), and a loop — the tools were hard to use, so no one used them, so no one knew about them, so they never became common practice. AI breaks the loop.
- **2026-10-14** — Audience: mission-aligned newcomers; people who would run the skill (stewards, facilitators, AI-native builders); LTP practitioners via the guides.
- **2026-10-14** — Not yet settled: the overarching frame. "Think together so the thinking accumulates" is not exciting enough; "transforms collaboration" is nearer. Also open: whether discourse clarity and team alignment are one story or two. "Where does our thinking go?" rejected as the headline.
- **2026-10-14** — Sequence agreed: nail the brand narrative and positioning (red-teamed) before any IA or design work. Plan tracked in Beads epic `reasoncommons-91c`.
- **2026-10-17** — Brand narrative draft v0 written (`docs/marketing/brand/brand-narrative.md`, unpublished — outside `website/`). Spine: the loop (hard and costly → unused → unknown → never common practice) and AI breaking it; trees from discourse as the leap; skills as proof. Awaiting review.
- **2026-10-17** — Rufus delegated the narrative's open calls. One story (thinking, then action), not two. LTP named once for credibility; practitioners as allies.
- **2026-10-17** — Positioning drafted and red-teamed by four critics (newcomer, practitioner, funder, excitement); revised to v2 (`docs/marketing/brand/positioning.md`, critiques in `docs/marketing/brand/redteam/`). Line: *Keep it human. Make it add up.* / *Every claim gets an address.* The accumulate/compound family of lines is dropped.
- **2026-10-17** — Rufus: the app is retired; the offer is skills and integrations (Discord next). The vision may run a little ahead of shipped work (live discourse annotation has been prototyped). History anchored on TOC (1970s, *The Goal* 1984), so "forty years" stands. Keep the six-idea summary verbatim.
- **2026-10-17** — Idea map added to the narrative: AI → trees, trees → AI (including the AI "memory" problem of sprawling threads and markdown files), discourse → tree, tree → discourse — with a table of what each surface foregrounds. Trees → AI is secondary for now but a distinct value proposition for the AI crowd and funders. Docs prefer simple tables and bullets over paragraphs.
- **2026-10-18** — Repo refactored (website moved to `website/`; working docs are no longer published). Brand work relocated to `docs/marketing/brand/` and this plan to `docs/marketing/plans/`; the `contentExclude` change was dropped as unneeded. The participant `.docx` now lives in `docs/product/`, off the site (partly resolves side bead `91c.2`).
- **2026-10-18** — Stage 4 drafts saved (`docs/marketing/brand/ia.md`, `pages.md`), adapted to the `website/` layout. Decided: nav *Use it · Guides · Vision · Blog · About*; Use it as a new page at `/use` (`/skills` stays the exported reference); the communities angle is a section of `/vision`; the loop is drawn as a tree; cost said as "consultancy rates" until sourced. Gate `91c.5` stays open until the mockups. Plan confirmed: artifact mockups first (shareable with David), then the full build on the preview Flowershow site, then live.
- **2026-10-18** — Narrative and positioning merged into `docs/marketing/brand/brand.md` (core + appendices). Rufus notes this is still being discussed: the narrative reads like About-page material, the proposition essence is not yet distilled, and a classic brand narrative (audience, vision, mission, etc.) is still mostly missing.
- **2026-10-30** — Session closed out. Rufus: there is now a good narrative of what is really going on, but it is About-page material; the proposition essence is not distilled and a classic brand narrative is only begun. Feel can proceed independently. New beads 91c.9 (brand narrative v2), 91c.10 (feel v0), 91c.11 (filename tidy).
