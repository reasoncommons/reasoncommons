# AGENTS.md

Guide for AI agents (Claude Code, Codex, etc.) working in this repo. `CLAUDE.md` is a symlink to this file.

## What this is

Reason Commons helps people and groups work out what they are trying to achieve and what to do about it, with AI doing the structuring and the bookkeeping. It keeps who said what, what has been agreed and what is still open, so a group's thinking builds up instead of getting lost. Today it is the `ltp` skill for Claude Code, Codex and similar agents; there is no app. The Logical Thinking Process works underneath. A collaboration between Rufus Pollock and David Joseph.

## How we present Reason Commons

- Lead with what it changes for the people using it, not with the method or the data structure. The Logical Thinking Process is how it works underneath: name it where a page explains how it works (the Guide, the glossary, skill internals and skill trigger descriptions), not in titles, headlines or opening lines.
- Front-facing words are provisional and learned from use. Don't coin or fix vocabulary in copy, "tree of change" and "tree of action" included; describe plainly instead. Internal working words such as "claim tree" may stay in internal docs.
- Retired: issue trees; the Reason Commons app (`Promise-Foundation/reason-commons`) and its "spaces"; Abductio and Promise Protocol, which are not part of Reason Commons. `python3 scripts/check-website.py` rejects the retired terms on the site outside dated folders.
- Dated records keep their wording: changelog entries, blog posts, talk material, landing-lab results, dated plans, critiques and the YAML's acceptance receipts. Don't rewrite history to match.
- These are David's positions of 2026-10-21, awaiting Rufus's review (bead `reasoncommons-ffm.2`); see `docs/product/plans/2026-10-21-retire-outdated-framing.md`.

## Where to look

| Need | File |
|------|------|
| Project overview + references | `README.md` |
| Why this matters | `motivation.md` |
| Planning — streams, next actions | [GitHub issues](https://github.com/life-itself/reasoncommons/issues) |
| Resume the Rufus–David collaboration, funding work | Private repo [reasoncommons/product](https://github.com/reasoncommons/product) (moved 2026-10-21): bead `rcp-a4l` (START HERE) and `collab/reason-commons.yaml` there; workflow in [docs/beads-reasoning.md](docs/beads-reasoning.md) |
| Internal **gold-standard toy fixture** for testing skills (tree, doc, annotations) | `claim-tree-annotation.md` |
| Static animated demo of the 4-step vision | `website/claim-tree-annotation-demo/` |
| Reason Commons skill (ltp) — install + copy-paste prompts | `skills/` (see `skills/README.md`) |
| **Writing a scrolling visual explainer** — principles, patterns, worked teardown | [standalone scrollable-explainer skill](https://github.com/rufuspollock/scrollable-explainer/blob/main/SKILL.md) — **read before drafting scrolling explainers** |
| The explainer series itself | `website/explainers/`; process material in `docs/marketing/explainers/` |
| **Explainers v2** — the rework into short illustrated chapters | `docs/marketing/plans/2026-09-18-explainers-v2.md`; state in beads (`bd ready --label explainers-v2`) |

## Conventions

- **Never line-wrap Markdown.** One paragraph is one line, however long. This holds everywhere — files in this repo, GitHub issue and PR bodies, and comments. Hard-wrapped prose makes diffs useless (change three words and the whole paragraph re-flows), makes editing in a browser textarea miserable, and buys nothing: every renderer and editor soft-wraps already. Wrap only where the line break is content — list items, table rows, code blocks, and deliberate `<br>`-style breaks in verse or address blocks. If you are reflowing a paragraph you are about to edit anyway, unwrap it; do not reflow whole files just to convert them, because that buries the real change.
- **Skills** live in top-level `skills/<name>/` so they're usable outside Claude Code (e.g. Codex). `.claude/` is gitignored (local-only, see `.gitignore`), so to let Claude Code discover them, wire the symlinks locally:
  ```sh
  mkdir -p .claude/skills
  ln -s ../../skills/ltp .claude/skills/ltp
  ```
  `ltp-project` and `ltp-visualize` were retired on 2026-10-21 with the app whose import format they served; remove any local `.claude/skills` links to them.
- **Codex skills** are discovered under `.agents/skills/`. The repository tracks
  `.agents/skills/ltp` as a symlink to the same `skills/<name>/` directory, so edits stay shared
  between Claude Code and Codex. In the Codex app, invoke one explicitly, such as
  `$ltp`, or let its description trigger it automatically. Restart Codex if a newly added skill
  does not appear in the Skills sidebar.
- **Toy example first.** Validate any AI skill against the gold data in `claim-tree-annotation.md` before touching real applications (e.g. Second Renaissance).
- Keep `motivation.md` (why this matters) current; it's referenced from `README.md`. Plan-of-work tracking (streams, next actions) lives in GitHub issues, not a repo file.
- **Concern boundaries.** Shared reasoning lives in `ltp/`, project working material in `docs/`, installable packages and their helpers/tests in `skills/`, runnable software with its configuration/tests/operating instructions in `apps/`, deliberate public content in `website/`, and cross-project utilities in `scripts/`. See the root `README.md` map and `docs/product/repository-boundaries.md`. The Rufus–David collaboration reasoning and funding material live in the private reasoncommons/product repo; a public Git repository is still public outside the website root.
- **Explainers layout.** Finished scrolling pieces live at `website/explainers/<slug>/index.html`, with the series landing page at `website/explainers/index.md` and shared `scroller.css`/`scroller.js` beside it. Scripts, critiques, visual scripts and retired source articles live at `docs/marketing/explainers/<slug>/`; never put them in the publishing root. Read [standalone scrollable-explainer skill](https://github.com/rufuspollock/scrollable-explainer/blob/main/SKILL.md) before drafting. Link to the explicit `<slug>/index.html`; bare folders only resolve automatically for Markdown. Public prose and assets use their existing URL paths even though the source is now under `website/`.
- **Explicit website exports.** Keep `motivation.md`, `skills/README.md` and `ltp/ltp-model.yaml` canonical in their project locations. `python3 scripts/export-website.py` refreshes their declared public copies; do not edit those generated copies. `python3 scripts/check-website.py` checks export drift, the publishing boundary, local links/assets and preserved routes. Add a deliberate export rather than a symlink out of `website/`; never publish the working collaboration YAML or a private draft.
- **No blank lines inside raw HTML in Markdown.** A blank line ends the raw HTML
  block as far as the Markdown parser is concerned. Anything after it that's
  indented four spaces or more — which inline SVG almost always is — then parses
  as an *indented code block*, and the figure renders on the page as literal
  markup. Keep `<figure>`…`</figure>` and `<svg>`…`</svg>` unbroken:
  ```html
  <figure>
  <svg viewBox="0 0 640 260" role="img" aria-label="…">
    <rect x="20" y="60" width="90" height="90"/>
    <rect x="140" y="60" width="90" height="90"/>   <!-- no blank line above -->
  </svg>
  <figcaption>Figure 1 · …</figcaption>
  </figure>
  ```
  Group the SVG with comments or `<g>` elements if you want visual separation.
  This bites silently: the page still returns 200, so it only shows up if you
  look at it. After changing any Markdown that embeds HTML, check the rendered
  output for escaped markup — `curl -s <url> | grep '&lt;rect\|&lt;svg'` should
  come back empty. Allow a moment after `fl` for the rebuild; a fetch made
  mid-rebuild can return a stale page and mislead you either way.
- **Beads** (`bd`) tracks agent-executable work plans (e.g. Explainers v2); GitHub issues stay the place for project-level planning. Issues labelled `human` are gates only Rufus closes. Dolt is canonical; JSONL is migration/interchange only. Enable tracked hooks after cloning with `git config core.hooksPath .beads/hooks`: `git push` also pushes Beads, and merge/branch checkout pulls it. Manual fallback: `bd dolt pull` / `bd dolt push`. See [sync and recovery](docs/beads-sync-playbook.md).
- **Before implementation, show a typed proposal and record typed acceptance.** Follow the **Change proposal** template in [skills/ltp/references/responses.md](skills/ltp/references/responses.md). Every user request to change project code, documents, configuration or skills, including “fix it” and small changes, requires a complete user-visible proposal before implementation. Name the reasoning served and its standing, list concrete node/link/backlog updates, show their topology and state validation. Read-only inspection may come first. Give each proposal an ID and revision, then wait for the user's unambiguous typed acceptance of that displayed version and scope; the initial request is insufficient. Explain that this wait follows the user's acceptance-recording rule. Record the human identity, exact reply, scope, proposal version and recording time in the top-level `change_acceptances` log of the collaboration YAML, which lives in the private [reasoncommons/product](https://github.com/reasoncommons/product) repo at `collab/reason-commons.yaml`, save the intended tree updates and validate before editing implementation files. Material revisions need fresh typed acceptance; an already-accepted version needs no repeat approval. Final implementation reports use **Change result** and retain the reasoning trace and acceptance receipt. **Next step** recommends an action or inquiry that has not been performed. These rules apply even when the skill was not explicitly invoked. Implementation approval is distinct from reasoning endorsement; ordinary conversational capture, reasoning endorsement and recording an already-given acceptance need no additional proposal or approval.
- **Show proposal and tree diagrams rendered, not as text.** Before the first diagram of a session, read [skills/ltp/references/diagrams.md](skills/ltp/references/diagrams.md). In Codex desktop, return a fenced `mermaid` block; in the Claude desktop app, render through the inline widget using the documented template unchanged. Break every label line yourself (at most 26 characters in the Claude widget, which neither wraps nor widens labels), name each tree once in the heading or a per-tree group rather than in every node, spell out standing (`[Proposed]`, `[Accepted]`, `[Disputed]`) with the kind on its own line, draw each statement's one-sentence `label` rather than its full text (writing one when capturing or revising a statement), and keep IDs out of node text. Use text only when rendering is unavailable or fails.
- **Every pull request cites its recorded approval.** Fill the sections of `.github/pull_request_template.md`, including when writing the body yourself. Under *Accepted change proposal*, cite each saved receipt as ``- `proposal-id` revision 1 by `participant-id` ``, with `approved_paths` recorded before implementation. The collaboration YAML is private (moved to reasoncommons/product on 2026-10-21), so public PRs cite receipt IDs only and never copy private reasoning or funding detail; CI no longer checks reasoning or receipt coverage here. Review implementation meaning and the actual approval separately. Opening or merging a PR does not endorse proposed reasoning.
- **The Rufus–David collaboration lives in the private repo.** Its tree, acceptance receipts, feedback records, funding drafts and START HERE bead (`rcp-a4l`) moved to [reasoncommons/product](https://github.com/reasoncommons/product) on 2026-10-21; follow that repo's AGENTS.md to resume. [docs/beads-reasoning.md](docs/beads-reasoning.md) still describes the Beads/YAML split. Feedback sync is paused; don't configure it against this repo.
- **Preview before pushing to live.** `main` serves the live site (`reasoncommons.com`, Flowershow site `ltp-issue-trees`). The publishing root is `website/`; run `python3 scripts/export-website.py`, `python3 scripts/check-website.py`, then `fl website --yes` for the separate preview at https://reasoncommons-preview-rufuspollock.flowershow.me. `website/.flowershow` retains that preview target. Publishing this folder avoids traversing agent skill links and project working material. The initial migration needs a coordinated production root-directory switch to `/website`; follow `docs/product/repository-boundaries.md` before merging or deploying it. Do not change production just to test rendering.
  Preview asset delivery has served stale CSS/JS despite reporting a sync. If a preview looks wrong, compare the actual bytes, for example `md5 -q website/explainers/scroller.css` against `curl -sL https://reasoncommons-preview-rufuspollock.flowershow.me/explainers/scroller.css | md5 -q`. A stale preview is not evidence that the source is broken. See https://github.com/flowershow/flowershow/issues/1363.
- **Checking phone width.** Use `node scripts/phone-check.mjs <url> [out.png]`, which emulates a 375px device over the DevTools protocol and lists anything overflowing. Plain `chrome --headless --window-size=375,…` screenshots lie: headless Chrome won't size a window below 500px, so you get a cropped 500px layout with text apparently clipped at the right edge. That artefact is what GH #20 was first reported from.
- Root `README.md` and `AGENTS.md` retain their exact uppercase names for tooling. Published prose uses lowercase names where appropriate; the public homepage is `website/README.md`, and root `motivation.md` has an explicit public export at `/motivation`.

## Changelog

This repo follows the [life-itself changelog convention](https://github.com/life-itself/changelog) (`CONVENTION.md`). One file per entry in `website/changelog/`, named `YYYY-MM-DD-slug.md`, with frontmatter `date`, `title`, `authors` and `promote: false`. Flowershow builds the `/changelog` timeline from the folder, so there is no index file to maintain. Screenshots go in `website/changelog/images/`. Authors are handles matching a profile page in `website/people/` (e.g. `rufus-pollock` → `website/people/rufus-pollock.md`, with `title` and a GitHub `avatar`). At a session checkpoint, if something reader-facing shipped, draft an entry: default to none for routine sessions, and link to the live feature where there is one. Fetch and follow the convention for the full rules.
