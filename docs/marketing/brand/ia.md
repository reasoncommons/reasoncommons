# Reason Commons — information architecture (stage 4, 2026-10-17; adapted to the repository refactor 2026-10-18)

Derived from `docs/marketing/brand/brand-narrative.md` (six ideas, idea map, "what we foreground where"), `docs/marketing/brand/positioning.md` (the line, today/next, value propositions, tone) and the decision log in `docs/marketing/plans/2026-10-14-brand-and-site-redesign.md`. Supersedes the 2026-10-14 distillation draft; its inventory is kept and updated below. Visual design is stage 5 and is not covered here.

## 0. What the refactor changed (2026-10-18)

- The published site is only `website/`: the Flowershow publish root, with its own `website/config.json` and `website/custom.css`. Public URL paths are unchanged; `/website` is a root selection, not a URL prefix.
- The homepage source is `website/README.md`; the root `README.md` is now the project map. **The README/index split this draft recommended is done.**
- Working material is outside the root: `docs/marketing/` (brand, plans, talk, explainer process), `docs/product/`, `docs/theory/`, `docs/ltp_trees/` and others. None of `/docs/*`, `/NEXT`, or skill internals is published; the Rufus–David collaboration material moved to the private reasoncommons/product repo on 2026-10-21.
- Four canonical files are exported into `website/` by `python3 scripts/export-website.py` (manifest `scripts/website-content.json`): `motivation.md`, `claim-tree-annotation.md`, `skills/README.md`, `ltp/ltp-model.yaml`. Never edit the generated copies; edit the source and re-run the exporter.
- `python3 scripts/check-website.py` checks the boundary (no `docs/`, `scripts/`, `_process`, dot-folders or symlinks under `website/`; nothing but `README.md` under `website/skills/`), export drift, local links, the required routes and every nav `href`, and that retired working routes stay unpublished. **It replaces most of the `contentExclude` advice in the earlier draft**: `website/config.json` now has `"contentExclude": []`, because working files are simply not in the root.
- Every site-config change in this document targets `website/config.json`. Any nav item added there becomes a route the checker requires, so `/guides`, `/vision` and the Use it page must exist before the nav changes.

## 1. Top nav

Five items plus the GitHub icon, as decided on 2026-10-18. Order is the order of the story: what you can do, what is underneath, where it goes, what we write, who we are.

| Item | Path | Job | Lead idea (idea map) |
|---|---|---|---|
| Use it | `/use` (see §6; `/skills` stays the install reference) | The main call to action: install the skill, run a first conversation, see what a session looks like, what the words mean, what is next. | Trees → AI, AI → trees |
| Guides | `/guides` | One depth section, two levels: the short illustrated introduction (`/explainers`), then the method proper (`/ltp`, glossary, library, working papers on GitHub). Resolves #15. | The method |
| Vision | `/vision` | Where this is going and why it matters: trees as infrastructure for human–AI reasoning, the idea map with status words, the communities section (`/vision#communities`), everything built so far, the ask. | Trees → AI, then discourse ↔ tree |
| Blog | `/blog` | Essays and build notes, dated and authored. | — |
| About | `/about` | Who, status today, lineage, how we work, follow and contact. | — |

- Dropped from nav (current `website/config.json` has seven items): **Introduction** and **Guide** (merged into **Guides**), **Demos** (becomes "sketches" inside `/vision`), **Glossary** (a reference page inside Guides), **Changelog** (linked from Home foot, Use it, Vision, About). `/demos`, `/glossary`, `/changelog` and `/explainers` stay in the checker's `required_routes`, so dropping them from the nav does not unpublish them.
- Home is the logo, not a nav item.
- Nav labels never use LTP vocabulary; the method is named once on Home and then inside Guides.

## 2. Sitemap

Source paths are under `website/` unless stated.

```
/                                   Home (website/README.md) — the line, a real session, why now, trees in a minute, where this is going
├── /use                            Use it (new website/use.md) — install, first conversation, a session, what you see, with a group, from documents, next (Discord)
├── /skills                         Skills reference (exported from skills/README.md; edit the canonical file only)
│     raw SKILL.md files are no longer on the site: they live on GitHub; npx skills reads the repo
├── /guides                         Guides landing — one section, two levels (new website/guides/index.md)
│   ├── /explainers                 level one: the short illustrated introduction (explainers v2 chapters; URL kept)
│   ├── /ltp  + /ltp/00…09          level two: the method and the worked Second Renaissance analysis
│   ├── /glossary                   level two: every term, anchored
│   ├── /library                    level two: reading list
│   └── working papers              level two: link to docs/theory/ on GitHub (no longer published)
├── /vision                         Vision (new website/vision.md) — idea map 2×2 with status words; trees → AI; the loop; prototyped; communities (#communities); what's next; the ask; built so far
│   ├── /dashboard/index.html       the real Second Renaissance tree, clickable (gets the #14 intro)
│   ├── /claim-tree-annotation-demo/index.html   the four-step animation (fix #4)
│   ├── /talk/2r-research-group     talk landing (required route) → slides.html, demo-c/index.html
│   └── /demos                      sketches: two mockups, Goal Aligner
├── /blog  + 3 posts  (authors resolve to /people/*)
├── /about                          what, where we are, who, lineage, how we work, follow / contact / contribute
└── /changelog                      what shipped, dated (linked from Home foot, Use it, Vision, About)
```

## 3. Inventory of currently published paths

Re-derived on 2026-10-18 from the actual `website/` tree on `brand/redesign` (current with `main`), not from a live probe. The 2026-10-17 live probes were unreliable (transient 404s for Markdown and HTML alike); re-probe after the production root switch, per the cutover checklist in `docs/product/repository-boundaries.md`.

Verdicts: **keep** (URL and role unchanged, copy may change), **move** (content goes elsewhere, URL gets a stub or is dropped), **hide** (stays published but leaves the sidebar via `contentHide` in `website/config.json`), **retire** (removed from `website/` and its role ends). Items in bead `reasoncommons-91c.2` are marked "pending bead 91c.2" and not decided here.

| Path | Source | What it is | Verdict | Reason / how |
|---|---|---|---|---|
| `/` | `website/README.md` | Homepage | **Keep**, rewrite | Already separate from the root GitHub README (done by the refactor). Rewrite per `pages.md` §1. |
| `/about` | `website/about.md` | About | **Keep**, rewrite | Status, strands and "no app yet" wording are stale; app and "spaces" references go. See `pages.md`. |
| `/people/rufus-pollock`, `/people/david-joseph` | `website/people/*.md` | Blog author profiles | **Keep**, out of nav | New since the earlier inventory. *Making work add up* lists `authors: [ "David Joseph" ]` rather than the `david-joseph` slug; check it resolves. |
| `/skills` | `website/skills/README.md`, exported from `skills/README.md` | Skills reference | **Keep** as the install reference; Use it is a separate page (§6) | Fix "the Reason Commons app imports" / "space" wording and the raw-URL line in the canonical `skills/README.md`, then re-export. |
| `/skills/*/SKILL.md` + `references/` | — (canonical `skills/<name>/`) | Raw skills | **Retired by the refactor** | Listed in `retired_working_routes`; the checker fails if they reappear. `npx skills add reasoncommons/reasoncommons` reads GitHub and still works. The paste-the-URL path `https://reasoncommons.com/skills/reason-commons/SKILL.md`, still printed in `skills/README.md`, now 404s: replace it with the `raw.githubusercontent.com/reasoncommons/reasoncommons/main/skills/ltp/SKILL.md` URL. |
| `/guides` | new `website/guides/index.md` | New landing | **Add** | One nav item for two levels without moving any URL. Resolves #15. |
| `/vision` | new `website/vision.md` | New page | **Add** | Trees → AI for funders and the AI crowd, the idea map, `#communities`, the exhibits. |
| `/use` | new `website/use.md` | New page | **Add** | The Use it page (§6). |
| `/explainers` + pieces + `scroller.css/js` | `website/explainers/` | Series index, three scroll pieces, two plain versions, *Whose Map Is It* | **Keep path; replace contents per explainers v2** | Becomes Guides level one; header links up to `/guides`. Retired pieces move out of the root (their process material is already in `docs/marketing/explainers/<slug>/`; git history keeps the HTML), leaving meta-refresh stubs at the old `index.html` paths. Do not use an `_archive/` folder inside `website/`. Until chapters ship, the index lists the current plain pieces under the two series headings with a one-line "chapters coming" note. |
| `/ltp` + `/ltp/00…09` | `website/ltp/` | LTP guide + the Second Renaissance analysis | **Keep**; Guides level two | Rewrite the landing: lineage named fully, bridge to the skill, link up to `/guides` and `/explainers`. |
| `/ltp/ltp-model.yaml` | exported from `ltp/ltp-model.yaml` | Raw YAML | **Hide** | Add to `contentHide` in `website/config.json` (do not drop the export). |
| `/glossary` | `website/glossary.md` | Glossary | **Keep**; out of nav | Guides level two; linked from Use it ("when the skill says current reality tree"). |
| `/library` | `website/library/README.md` | Reading list | **Keep** | Guides level two. |
| `/library/logical-thinking-process-dettmer/*` | `website/library/logical-thinking-process-dettmer/` (README, 10 chapter files, 251 page images, `source/logical-thinking-process-dettmer.pdf`) | Dettmer derivative and source PDF | **pending bead 91c.2** | Still published. Conversion helpers are in `docs/references/logical-thinking-process-dettmer/scripts/`. `/library` links to it, so whatever 91c.2 decides must also edit that row. |
| `/blog` + 3 posts | `website/blog/` | Blog | **Keep**; in nav | Add dates and authors to the index lines. *Making work add up* (2026-10-13) is the worked example linked from Use it and Vision. |
| `/demos` | `website/demos/index.md` | "Demos & experiments": 7 mockups, Goal Aligner, the talk | **Keep page, out of nav, reframe as "Sketches"** | Reached only from `/vision`. Keep *Pencil & Ink* and *TOC-native Wireframes*; take the other five mockups out of `website/demos/` (or `contentHide` them). The dead `/talk/index.html` link is already gone. |
| `/demos/goal-aligner/` + `/alignment/index.html` stub | `website/demos/goal-aligner/`, `website/alignment/index.html` | Experiment + redirect stub | **Keep** | Labelled sketch. The stub is the site's redirect pattern; `/alignment/index.html` is a required route. |
| `/claim-tree-annotation-demo/index.html` | `website/claim-tree-annotation-demo/` | Four-step animation | **Keep**; linked from Vision | Label "animated sketch of the vision"; fix #4. Not on Home's main path. |
| `/dashboard/index.html` (+ `/dashboard/projects` hidden) | `website/dashboard/` | Read-only viewer, Second Renaissance analysis | **Keep**; linked from Vision and `/ltp` | Reframe as "the real tree you can click", deep link `#/second-renaissance/goal-tree`, add the #14 intro. Drop "Reason Commons space" wording. `contentHide` still lists `/dashboard/assets`, which no longer exists in the tree; remove it. |
| `/talk/2r-research-group` | `website/talk/2r-research-group/README.md` | Talk landing (still the drafting brief, `status: drafting`) | **Keep**, rewrite | A required route, so it cannot simply be hidden. Rewrite as a short public page (what the talk is, links to deck and Demo C); it currently refers to `notes.md`, which moved to `docs/marketing/talk/2r-research-group/`. |
| `/talk/2r-research-group/slides.html`, `demo-c/index.html` | `website/talk/2r-research-group/` | The deck; the contributions review page | **Keep**; linked from Vision | "The talk" and "a room's contributions, read against the tree — prototype". |
| `/talk/2r-research-group/demo-c/proposals.yaml` | same | Demo C data | **Hide** | Add to `contentHide`; the page loads it. |
| `/motivation` | exported from root `motivation.md` | SCQH problem framing | **Keep, demote** | Link from About as "the problem framing (SCQH)"; no nav or Home link. Refresh its stale streams list in the root file and re-export. |
| `/changelog` | `website/changelog/` | Dated shipped work | **Keep**; out of nav | Public proof of "it's real"; linked from Home foot, Use it, Vision, About. |
| `/claim-tree-annotation` | exported from root `claim-tree-annotation.md` | 2026-06 process spec with the toy fixture | **Retire** from the site | A spec with ASCII tables is not a visitor page, and `/docs/claim-tree-annotation` is no longer a public target. Remove its entry from `scripts/website-content.json` and the generated copy; keep the root file canonical (AGENTS.md points to it); fix inbound links to point at GitHub. Optional one-line stub page at `website/claim-tree-annotation.md` linking to GitHub. |

**Removed by the refactor (no longer published; no action needed in this IA):**

| Former path | Now at | Earlier verdict |
|---|---|---|
| `/docs/theory/*` | `docs/theory/` (11 essays) | Keep → now linked on GitHub from Guides level two |
| `/docs/ltp_trees/*` | `docs/ltp_trees/` | Keep → source for `/ltp` and the dashboard, GitHub only |
| `/docs/dashboard`, `/docs/demo-c`, `/docs/beads-reasoning`, `/docs/naming-the-tree`, `/docs/brand-and-domain-naming` | `docs/product/dashboard.md`, `docs/product/demo-c.md`, `docs/beads-reasoning.md`, `docs/marketing/naming-the-tree.md`, `docs/marketing/brand-and-domain-naming.md` | Keep out of nav → link to GitHub from About "contribute" |
| `/docs/notes/*` | **no longer exists** in the repo | — |
| `/docs/testing-reason-commons-scannability` | `docs/product/testing-reason-commons-scannability.md` | Hide → done |
| `/docs/plans`, `/docs/brand`, `/docs/superpowers` | `docs/marketing/plans/`, `docs/product/plans/`, `docs/marketing/brand/`; `docs/superpowers` **no longer exists** | Keep excluded → done |
| `/docs/The Theory of Constraints and the Logical Thinking Process - Learning to Think Better` | `docs/` (same filename) | 91c.2 → off the site; bead 91c.2's description is stale on this point |
| `/docs/prompts/LTP_BACKGROUND_PROMPT` | `docs/prompts/LTP_BACKGROUND_PROMPT.md` | 91c.2 → off the site; still in the public Git repo |
| `/talk/2r_participant_contributions_test.docx` | `docs/product/demo-c/2r_participant_contributions_test.docx` | 91c.2 → off the site; still in the public Git repo |
| `/talk/2r-research-group/notes`, `/script`, `/slides-brief` | `docs/marketing/talk/2r-research-group/` | Hide → done |
| `/ltp/reason-commons`, `/ltp/rufus-david-collab` | `ltp/rufus-david-collab/` | Keep excluded → done |
| `/NEXT` | root `NEXT.md` (in `retired_working_routes`) | Hide → done |
| `/skills/project-ltp/` | **no longer exists** in the repo | Hide → done |
| `.beads`, `.github`, `/scripts`, `/drafts`, `AGENTS.md`, `CLAUDE.md` | outside `website/` (`drafts/` **no longer exists**) | Hide → done; sidebar leakage is solved by the boundary, not by `contentExclude` |

## 4. URL changes and redirect stubs

No server redirects. The existing pattern is a meta-refresh `index.html` stub (`website/alignment/index.html` → `/demos/goal-aligner/`). After any change, run `python3 scripts/check-website.py`; if a retired page should stay reachable, add its route to `required_routes` only if a stub remains.

| Old URL | New home | Mechanism |
|---|---|---|
| `/explainers/01-bottleneck/index.html`, `/02-thinking-made-visible/`, `/03-five-shapes/`, `/01-bottleneck-plain/` | First chapter of the *Why fixes don't stick* series | Meta-refresh `index.html` stub in each old folder under `website/explainers/`; real content leaves the root (git history keeps it). |
| `/explainers/second-renaissance/`, `/second-renaissance-plain/`, `/whose-map-is-it/` | First chapter of the *Where does the thinking go?* series | Same stub pattern. |
| `/claim-tree-annotation` | GitHub `claim-tree-annotation.md` | Drop the export; optional one-line Markdown stub with the GitHub link; fix internal inbound links. |
| `/skills/ltp/SKILL.md` and other raw skill files | GitHub (raw or blob) | Already retired by the refactor. Update every printed URL (`skills/README.md`, Use it page) to the GitHub raw URL. |
| `/demos` | unchanged | Framing changes, URL does not. |
| `/talk/index.html` (already dead) | — | No remaining inbound links in `website/` except historical changelog prose; no action. |

## 5. User journeys

| | Who | Path | Success |
|---|---|---|---|
| J1 | Forum member who heard the talk | `/` → sees the line and a real session → "Where this is going" → `/vision#communities` → the real tree in `/dashboard` → `/use` or updates signup | Can say what the vision is, has seen the real tree, knows the skill exists and that forum reading is "prototyped", not shipped. |
| J2 | Facilitator or steward who wants to try it | `/use` (direct or from Home's primary button) → install line → first prompt → "What you are looking at" → runs it → `/glossary#current-reality-tree` when a term appears | A saved `reason-commons.yaml` from a real conversation within fifteen minutes. |
| J3 | LTP or TOC practitioner, via search | Google "current reality tree example" → `/glossary#…` → `/ltp` six-trees table and the worked analysis → "the skill picks the tree and holds all six" → `/use` | Installs it on a tree they already keep; tells us where it is wrong. |
| J4 | Funder, partner or AI-crowd reader | `/vision` (from an email or a post) → idea map with status words → trees → AI and the memory problem → `/blog/making-work-add-up` and `/changelog` as proof → `/about#contact` | Can state the thesis, the status and the ask without a call; sees the work shipping. |

## 6. The Use it page and the exported skills README

`skills/README.md` is canonical and exported to `website/skills/README.md` (`/skills`). Options:

| Option | What | Verdict |
|---|---|---|
| A | Website-only `website/skills/index.md` beside the export | **Not viable.** The checker rejects any file under `website/skills/` other than `README.md`, and `README.md` and `index.md` would compete for the same `/skills` route. |
| B | Rewrite canonical `skills/README.md` into the Use it page | **No.** It is also the GitHub package README that installers and agents read; video slots, status chips and `custom.css` HTML do not belong there, and GitHub would not render them. |
| C | New website-only page `website/use.md` at `/use`; nav "Use it" → `/use`; `/skills` stays the exported reference | **Recommended.** No change to the exporter, manifest or checker; boundary-clean; `/skills` and every inbound link to it keep working. Keep the install block on `/use` to the one command plus a link to `/skills` for variants, so the duplicated text stays small. |
| D | Re-point the export to e.g. `website/skills/reference.md` and make `website/skills/README.md` the website-only Use it page | Fallback if Rufus wants `/skills` itself to be the front door. Needs an edit to `scripts/website-content.json` and to the `website/skills/` rule in `scripts/check-website.py`. |

Whatever is chosen, fix the canonical `skills/README.md` (app/"space" wording; the retired `reasoncommons.com/skills/reason-commons/SKILL.md` URL) and re-run `python3 scripts/export-website.py`.

## 7. Decided (2026-10-18)

Approved by Rufus on 2026-10-18:

- **Blog is in the nav.** Five items: Use it · Guides · Vision · Blog · About.
- **The communities angle is a section of Vision**, at `/vision#communities`, not its own page. Promote to `/communities` when Discord ships.
- **The loop is drawn as a tree** on Home and reused on Vision.
- **The cost figure is softened** to "expert facilitators at consultancy rates" until a source is in hand.
- (Done by the refactor, not a choice) The homepage source is `website/README.md`, separate from the root GitHub README.
