# Beads sync and recovery

The embedded Dolt database is the task source of truth. Git tracks its configuration and hooks; the database travels through `refs/dolt/data` on the same GitHub repository. JSONL is for deliberate migration/interchange, not ongoing sync. Do not restore `.beads/issues.jsonl` as a tracked file or enable automatic export.

## New clone

```sh
git config core.hooksPath .beads/hooks
git config beads.role maintainer
bd bootstrap --yes
bd dolt pull
bd status
```

Use `bd bootstrap`, rather than initializing a second independent database. It detects the existing remote history. For a linked worktree, use the main checkout's database through a gitignored `.beads/redirect`; do not initialize another one.

## Everyday work

Run `git pull` and `bd dolt pull` before working. Track tasks with `bd create`, `bd update`, `bd dep` and `bd close`. The tracked pre-push hook pushes Dolt as well as Git; post-merge and branch-checkout hooks pull Dolt. Guards prevent recursive hooks; a sync failure is reported without blocking the Git operation. If a hook reports a failure, run `bd dolt pull` / `bd dolt push` manually and resolve it before claiming tasks are synced. Beads-only changes still need `bd dolt push`.

Verify with `bd context`, `bd status`, `bd dolt remote list`, and `git ls-remote origin refs/dolt/data`. The remote is `git+ssh://git@github.com/reasoncommons/reasoncommons.git`. Embedded mode has no server; `bd doctor` / `bd sql` may not support it.

## Recovery

Back up the entire local `.beads` directory before repairs, including the embedded database and ignored audit/runtime tables. Take an independent remote copy. `bd export --all` is useful migration evidence, but does not preserve complete Dolt history, audit tables or settings.

If histories have no common ancestor, do not force-push or discard either side. Reconcile records in an isolated clone based on the existing remote history. Import verified snapshots using the timestamp-aware importer, preserve labels, comments, dependencies, memory and settings, and inspect every changed status. Check for concurrent local/remote changes before publishing and installing the repaired database. Verify a fresh clone and a normal push/pull round trip before retiring old stores.

## Recovery on 2026-10-26

The local history held 38 issues; the independent remote contained schema only. An older tracked JSONL contained 87 issues. Reconciliation recovered all 91 distinct source issues, preserving four local-only tasks and restoring 53 missing tasks. Nine newer legacy records were applied, including three documented closures for retired app-era skills. No reasoning was endorsed or changed.

The original local and remote database stores, source exports and verification evidence were archived outside the repository. All 108 original audit events and local settings were retained in the repaired local database; audit/runtime tables remain clone-local under Beads' default ignore policy. The repaired shared database descends from the existing remote, so publishing required no force-push. The legacy tracked JSONL was removed to prevent stale automatic imports. The repair itself is tracked as a separate Bead.
