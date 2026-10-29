# Accepted snapshots and diagrams

After a feedback save and this validation, run configured [feedback synchronisation](feedback-sync.md). Native edits still use file-editing tools; the deterministic sync helper is the explicit exception that may reconcile validated records into the working YAML. It refreshes views after incoming changes. Generated history and diagrams remain local.

After saving all state changes from a conversational turn, run:

```bash
python3 <skill-directory>/scripts/update_views.py <working-state.yaml> --summary "Accepted the revised quote-delay explanation"
```

Resolve `<skill-directory>` from this skill's location. `--summary` is optional; use a short description of the accepted change. The helper validates YAML roles, references, attribution, and acceptance consistency before creating artifacts. It never edits the working file or decides what to accept.

Python needs PyYAML. The helper draws SVG directly and wraps it in a standalone HTML page; it does not need Graphviz, Node, a Mermaid renderer, or network access. Open the HTML file in a browser or preview it in Codex. The companion SVG is useful for embedding elsewhere.

For the default `reason-commons.yaml`, generated files live alongside it in:

```text
.reason-commons/
  history/
    000001.yaml
    000002.yaml
  diagrams/
    current/
      current_reality.html
      current_reality.svg
    changes/
      current_reality.html
      current_reality.svg
```

Other state filenames use a matching hidden directory (`workshop.yaml` → `.workshop/`); `--output-dir` overrides this. Keep a separate history directory for each working file. Paths are returned by the helper. These are local generated artifacts; do not commit, publish, or send them elsewhere as part of ordinary facilitation.

## When a revision is created

Compare the accepted portion of working state with the latest saved snapshot. Create one numbered snapshot for all accepted changes from that turn, even when several trees changed. With no previous snapshot, the first accepted content is an addition; a project containing only proposals creates no snapshot yet.

Compare nodes by stable ID, kind, text, cross-tree reference IDs, and assumption text. Compare links by stable ID, endpoints, relation, and assumption text. Additions, changes, removals, and loss of acceptance count. Backlog edits, proposals, contributor corrections, extra endorsers, project-change acceptance receipts, active-tree switches, and list reordering do not trigger a revision. Challenges trigger a revision when they change accepted status or reasoning. The helper cannot judge whether wording changes are substantive: resolve acceptance in the conversation before running it.

Each snapshot contains the entire working YAML at that moment, including WIP, plus revision metadata. The latest snapshot therefore need not contain subsequent WIP-only edits; resume from the working file. History is never modified in place. No additional previous-state cache is used.

## The two views

- **Full:** all accepted nodes and accepted links between them in that tree, including isolated accepted nodes. Backlog membership does not filter them.
- **Latest change:** added, changed, and removed accepted elements compared with the preceding accepted state. Changed nodes show previous and current wording; changed links show the old and new connections. Removed items show their last accepted content, never newer proposed wording. Include changed-link endpoints and one-hop neighbors of changed nodes as muted context. Joint causes use an AND connector.

Color and text labels distinguish added, changed, removed, and context items. Cross-tree traces appear as references on nodes; they do not fabricate causal arrows between trees. The first change view shows all initial accepted content as added. Removing all accepted content leaves an empty full view and a change view showing removals.

Update only affected trees. Keep each tree's latest change view when another tree changes, when users switch focus, or during WIP-only turns. The helper reconstructs that tree's latest change from numbered snapshots if an artifact must be regenerated. Keep both HTML views available as optional inspection links when useful or requested, labeled accepted-only; opening an export is not required to continue the conversation. Do not read diagram details aloud unless asked. The companion SVGs contain the same diagrams.

## The whole commons in a browser

```bash
python3 <skill-directory>/scripts/open_commons.py <working-state.yaml>
```

This writes the whole working file as the pages the Reason Commons demo site uses for one commons: an overview, a map of the questions, a page for each tree, every statement and connection with its contributors, endorsers, assumptions, challenges and open work, open questions, outcome reports when there are any, and an About page. Unlike the two views above, it shows every standing, each marked as recorded. Every page says it is a private view.

The pages go in `site/` inside the file's hidden directory (`.reason-commons/site/` for `reason-commons.yaml`); `--output-dir` overrides this. The helper prints JSON with `output`, `open` (the overview as a file URL) and the statement, connection and standing counts. A rebuild replaces only the files it wrote before, and it will not write into a non-empty folder it did not make. `--serve` serves the folder on 127.0.0.1 only, on a free port or the one given, and adds the `url` to open; it keeps running until stopped. The Claude desktop app's built-in browser needs this, because it shows a local file without its styles. Start the served helper there through the browser's preview tool, with a `.claude/launch.json` entry such as:

```json
{"version": "0.0.1", "configurations": [{"name": "commons-view", "runtimeExecutable": "python3",
  "runtimeArgs": ["<skill-directory>/scripts/open_commons.py", "reason-commons.yaml", "--serve", "8879"], "port": 8879}]}
```

The view does not change when the working file does. Run the helper again without `--serve` to rebuild the same folder; a running server then serves the new pages on reload.

The renderer is a copy of the demo site's, in the skill's `viewer/` folder; see its README. Like the other generated files, the pages are local: do not commit, publish or send them as part of ordinary facilitation. Publishing a commons is a separate decision about what to share and with whose consent.

## Failure and retry

Snapshot creation precedes view generation so accepted history is not lost if view generation fails. HTML and SVG files are replaced atomically. If generation fails, report it and rerun the same command; it regenerates views from history without creating a duplicate revision. Retry before making another accepted update when practical, so users can inspect the change they just agreed to.

The helper is for one driver saving turns sequentially, not simultaneous writers or a background file watcher. Run it after manual state changes are reviewed too. YAML remains the source of truth; never reconstruct state by parsing a diagram.
