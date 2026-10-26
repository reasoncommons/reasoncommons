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

## Failure and retry

Snapshot creation precedes view generation so accepted history is not lost if view generation fails. HTML and SVG files are replaced atomically. If generation fails, report it and rerun the same command; it regenerates views from history without creating a duplicate revision. Retry before making another accepted update when practical, so users can inspect the change they just agreed to.

The helper is for one driver saving turns sequentially, not simultaneous writers or a background file watcher. Run it after manual state changes are reviewed too. YAML remains the source of truth; never reconstruct state by parsing a diagram.
