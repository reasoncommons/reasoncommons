You are an unattended scheduled cloud session on the Reason Commons repo, executing the **Explainers v2** plan. Nobody is watching live; Rufus reviews afterwards. Work carefully, commit often, and leave the repo clean.

## Read first

1. `AGENTS.md` (conventions: never hard-wrap Markdown, no blank lines inside raw HTML in Markdown, the `fl` preview caveats, which apply only to a local checkout).
2. `docs/marketing/plans/2026-09-18-explainers-v2.md` — the plan and its decisions.
3. `docs/marketing/explainers/series/voice-guide.md` and `docs/marketing/explainers/series/costar-teardown.md`.
4. `skills/illustrated-chapters/SKILL.md` if it exists yet (the chapter form, once built).

## Loop

Repeat until nothing is ready:

1. `git fetch origin` and merge `origin/main` into the `claude/explainers-v2` branch (create it from `origin/main` if it doesn't exist). All work goes on that branch.
2. `bd ready --label explainers-v2 --exclude-label human --exclude-type epic`. If empty, stop the loop.
3. Take the top issue: `bd show <id>` (read description, acceptance, notes, comments), `bd update <id> --claim`.
4. Do the work fully, to the acceptance criteria. Use subagents where the issue asks for an independent critique or read. Invoke relevant skills (e.g. the standalone [`scrollable-explainer`](https://github.com/rufuspollock/scrollable-explainer/blob/main/SKILL.md) for stage discipline, `illustrated-chapters` for form).
5. If it changes anything that renders: there is no preview site in the cloud (`fl` isn't available), so check the rendering another way. If Chrome is available, serve the files locally and check at phone width with `node scripts/phone-check.mjs <url> <out.png>` (emulates a 375px phone, lists overflowing elements, saves a screenshot; look at it). Don't use `--window-size=375`: headless Chrome won't go below 500px, so it crops a 500px layout and fakes clipping. Otherwise read the Markdown/HTML carefully. Rufus previews with `fl website --yes` when reviewing the PR.
6. Commit with a conventional message (end it with the `Claude-Session:` line if one is given to you), `git push` to `claude/explainers-v2`. Never push to `main`: it is the live site, and Rufus merges the draft PR after review.
7. `bd close <id> --reason "<one or two lines: what was done, where>"`, then run `bd dolt push` and confirm synchronization. Do not create or commit `.beads/issues.jsonl`; Dolt is canonical.
8. Go to 1.

## Rules

- **Never work on, update, or close an issue labelled `human`** (the arc gate). If you finish the issue that precedes the gate, write the summary for Rufus in the gate issue's notes (`bd update <gate-id> --append-notes "..."`), since that is its instruction.
- If you get stuck or a decision really needs Rufus, don't guess on something large: `bd update <id> --append-notes "Blocked: <why>"`, create a `-t decision` issue labelled `explainers-v2,human` assigned to "Rufus Pollock" that the stuck issue depends on (`bd dep add <id> <new-id>`), commit, push, and move on to other ready work.
- New work you discover inside the plan's scope: `bd create --parent reasoncommons-bnl -l explainers-v2 ...`. Out of scope: note it in your final summary, don't do it.
- Don't touch other open GitHub issues or unrelated parts of the site beyond what the issue says.
- Never leave uncommitted changes. If you must stop mid-issue, commit what is coherent, append notes on where you got to, and leave the issue in progress so the next session resumes it (`bd list --label explainers-v2 --status in_progress` — check this before step 2 and resume any found).
- When every child of the epic `reasoncommons-bnl` is closed, close the epic too.

## Finish

End with a short summary: issues closed, what shipped (preview/live URLs), anything waiting on Rufus.

The repository publishes only `website/`. Finished pieces are under `website/explainers/`, working scripts/critiques under `docs/marketing/explainers/`; validate with `python3 scripts/check-website.py` and preview with `fl website --yes`.
