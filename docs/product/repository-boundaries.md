# Repository boundaries and website cutover

The repository has one shared reasoning model and distinct homes for project work, installable skills, runnable applications and public material. [The project map](../../README.md) is the entry point; [the docs map](../README.md) explains the working areas.

## Ownership

| Artifact | Canonical location | Public delivery |
| --- | --- | --- |
| Collaboration claims, contributions, acceptance and reasoning backlog | `collab/reason-commons.yaml` in the private [reasoncommons/product](https://github.com/reasoncommons/product) repo (moved 2026-10-21) | Not in this public repo |
| Task ownership, status and handoff | Beads embedded Dolt database; synced through the GitHub Dolt remote | Outside the website root |
| Product research, experiments and design | `docs/product/` | Deliberate public output belongs in `website/` |
| Positioning, editorial briefs, scripts and critiques | `docs/marketing/` | Finished pieces under `website/` |
| Public-safe business/funding/partnership work | `docs/business/` | Deliberately selected public output only |
| Skill packages, helpers, fixtures and tests | `skills/<skill>/` | Install from the repository; public guide exported to `/skills` |
| Application code, configuration, tests and operating instructions | `apps/<app>/` | Publish built output deliberately if needed |
| Current static dashboard and browser demos | `website/dashboard/`, `website/demos/` | Same public URLs as before |
| Library conversion helpers and their baseline | `docs/references/logical-thinking-process-dettmer/scripts/` | Converted chapters, source PDF and images under `website/library/` |

The main Reason Commons app has a [separate repository](https://github.com/Promise-Foundation/reason-commons). `apps/discord/` establishes ownership for prospective bot work; it contains no bot implementation. This repository has no dashboard source build system to move into `apps/`. The compiled bundle embeds its sample data; see [dashboard notes](dashboard.md).

This Git repository is public. Private funding assessments and applications retain their existing private locations. Excluding a document from website publishing does not make its Git history private.

## Canonical sources and explicit exports

Run these from the repository root:

```sh
python3 scripts/export-website.py
python3 scripts/check-website.py
```

The exporter reads the reviewed manifest at `scripts/website-content.json`. It refreshes only three declared public artifacts: root `motivation.md`, `skills/README.md` and `ltp/ltp-model.yaml`. The `claim-tree-annotation.md` fixture stopped being exported on 2026-10-21 and stays in the repository as internal test data. Markdown exports identify their source; links to unpublished skill/project files point to canonical GitHub locations. Edit the source and rerun the exporter. CI fails if an export drifts.

The existing public homepage moved to `website/README.md`; the root README is now the project map. `NEXT.md`, generated from the retired app's interchange model, was removed on 2026-10-21; Beads and GitHub issues hold the work.

`website/` contains no project working directories, installable skill internals, editorial `_process` folders or symlinks to outside sources. The normal website check verifies the publishing boundary, current exports, required public routes and local links/assets. `python3 scripts/check-website.py --migration` additionally audits this branch’s historical move map, unchanged media/dashboard bytes and canonical skill wiring; those historical move/byte checks are not permanent restrictions on future project work. Current public article and asset paths stay unchanged: `/website` is a filesystem root selection, not a URL prefix.

Working routes under `/docs`, `/NEXT` and installable skill internals stop being published. Public links to retained project work point to GitHub; the public `/skills` installation guide remains. Old references to retired skills in changelog entries link to the relevant historical revision rather than claiming the packages still exist today.

## Preview and rendering

`website/.flowershow` retains the separate `reasoncommons-preview` target. If the Flowershow CLI is installed and authenticated, preview with:

```sh
fl website --yes
```

This publishes only the website folder and does not traverse `.agents` or the collaboration state. Compare returned CSS/JS bytes with the local files before diagnosing a stale preview as a source failure. The [agent rules](../../AGENTS.md) retain the known preview-cache caveat.

When the CLI/account is unavailable, use local rendering to inspect the homepage, a scrolling explainer and the static dashboard at desktop and phone widths. Local Markdown rendering is an approximation of Flowershow, so record that limitation; a successful local check is not a verified cloud build. Check excluded working files return 404 from the selected root.

## Coordinated production cutover

The live Flowershow site currently follows `main`. Moving content without changing its configured root, or changing the root before that content is available, can temporarily break the site. Treat the merge and root switch as one scheduled cutover:

1. Review the branch and verify `python3 scripts/check-website.py`, reasoning state/approval coverage, and a separate preview. Freeze unrelated merges during the short cutover.
2. Record the current production repository, branch and root-directory setting in the deployment session. Confirm the live site is `ltp-issue-trees` / `reasoncommons.com`, and that the branch's `website/README.md`, `website/config.json` and `website/custom.css` are present. The root setting is managed in Flowershow site settings; it is not set by `website/.flowershow`, which is the preview CLI target.
3. Merge the reviewed branch and set the production site's root directory to `/website` in coordination. If Flowershow permits pausing GitHub synchronization, pause it around those two operations and resume afterward. Otherwise allow for a brief inconsistent interval; do not claim a zero-downtime switch.
4. After the production build completes, check `/`, `/about`, `/skills`, `/ltp`, `/glossary`, `/library`, `/blog`, `/changelog`, an explainer HTML page, the annotation demo, a talk and the dashboard. Verify loaded CSS/JS bytes and check on a phone-width viewport.
5. Verify working reasoning, `/docs` and skill implementation paths are absent from the site. Record the actual production root, deployed commit and results in the implementation handoff.

Rollback requires reverting the migration commit and restoring the recorded previous root setting together. Never publish the repository root merely to compensate for a failed subfolder configuration. This implementation branch does not perform the production merge or root switch.

## Evidence and remaining questions

The migration separates the previously mixed public-method and working-reasoning material under `ltp/`, moves project-root publishing into an explicit folder and removes draft/extraction material from that folder. Its file manifest names every move. Validation evidence belongs in the linked implementation bead and the shared reasoning backlog.

The expected reduction in technical debt remains a prediction. Observe actual work after adoption: can a contributor locate the owner of a change, do exports stay current, and do applications or skills acquire unintended dependencies on published files? Completing the file moves does not establish that benefit or endorse the proposed reasoning.

## Branch verification checkpoint — 2026-10-16

The local migration passed 77 reasoning-helper tests, 535 public link/asset checks, the historical move/media audit, export/checker failure contracts, the remote-work reasoning toy case and a six-tree interchange dashboard export. The library checker passed against its existing six-warning baseline without regenerating the book. All nine earlier approval receipts and accepted reasoning were preserved; 401 of 445 moved files, including all moved media and the dashboard/CSS/JS artifacts, are byte-identical to the accepted base. Six open Beads descriptions received path-only updates with their ownership and status preserved.

Desktop and 375px local rendering had no JavaScript errors. The homepage and scrolling explainer had no phone overflow. The dashboard phone tool flags six tab elements inside its existing horizontally scrollable navigation; the document remains 375px wide and its compiled bytes are unchanged. Requests for the working collaboration YAML, project docs, skill internals and NEXT.md returned 404.

The Flowershow CLI is not installed in this environment. No cloud preview, production root change, main merge or remote push was performed. Local Markdown rendering approximates the host; cloud rendering and the coordinated production cutover remain to be verified in a deployment session.
