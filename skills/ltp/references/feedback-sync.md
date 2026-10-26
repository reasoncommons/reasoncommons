# Sharing feedback with Git

Use the same actual reasoning YAML for native sessions and the Discord host on one machine. Other checkouts synchronise that file through an explicitly authorised Git remote and branch. The YAML owns predictions and observations; local policy, baseline and delivery-status files are transport metadata. Sharing is not evidence of a predicted benefit or reasoning endorsement.

## Configure once per checkout

Obtain standing authorisation for automatic feedback commits and pushes to a named destination. A feedback reply does not authorise a new destination. Resolve the actual state file and human authorising sharing; record their actual reply:

```bash
python3 <skill-directory>/scripts/feedback_sync.py <state.yaml> configure --remote origin --branch main --by <participant-id> --source-text '<actual standing authorisation>'
```

Configuration validates the existing shared file and records the remote URL, branch, path, participant and reply in the state file's local hidden directory. It fetches but does not publish. Each machine needs its own Git credentials and this one-time configuration. A changed remote URL requires explicit reconfiguration. `disable` removes the policy and retains the reasoning file. This neither installs the skill nor enables Discord messaging.

A linked Git worktree, such as the fresh one a Claude Code session creates, uses its main checkout's authorisation for the same reasoning file when the remote URL matches, so sharing does not silently stop in every new session. The first sync records the inherited policy locally with `inherited_from`, and each sync result says which checkout's authorisation it used. Inheritance never covers a different file or remote URL. When the main checkout disables or changes its authorisation, worktrees stop sharing at their next sync. `disable` in a worktree stays in force there until that worktree is configured again. When suggesting a configure command, name the branch other participants read (the remote's default branch), not a session's own branch.

## Session entry and capture

Run `python3 <skill-directory>/scripts/feedback_sync.py <state.yaml> sync` before selecting feedback and again after a feedback save and normal view validation. Reread the resulting YAML before deriving the recipient's queue. Without configuration the command stays local and makes no network request. A standing policy needs no repeat approval or PR for routine sharing.

Save the person's words immediately through the native file editor. The deterministic sync helper is an explicit exception to the manual-write rule: it reconciles validated feedback into the actual file under the Discord host's existing state lock. Native editing remains a single-writer operation: capture through an active bot writer or pause it before native editing. Read before editing and preserve other contributions. A busy lock means wait for that writer, not overwrite it.

Only immutable feedback commitments, appended reports and derived review backlog are published. Local code, node changes, approval receipts, other backlog edits and staged files stay local. New expectations need their referenced reasoning to be shared already; publish those definitions through their authorised reasoning/implementation workflow first. Conflicting definitions or versions stay local for reconciliation.

## Delivery and recovery

`state: shared` is returned only after a remote fetch verifies the records. Say **Shared successfully** and retain its commit reference when useful. `state: local` means **Saved locally; sharing incomplete** or **Saved locally; sharing is not configured**. On entry, explain that shared state may be stale. Preserve unsent responses and retry the same sync command after connectivity or conflicts are resolved; do not resubmit feedback or infer an outcome from delivery status.

Independent reports merge by immutable request/version and report IDs. A reused ID with different content or an edited prediction stops sharing. Report contents remain immutable; chronology determines the latest deferral regardless of arrival order. The helper retains unsent observations in the actual YAML and unpushed commits under local Git refs, tries at most two pushes, and checks for a successful push after a lost response. It never force-pushes or resets local work.

Feedback commits use a private Git index and the destination branch's current parent. After verified sharing or refresh, the helper fast-forwards the checkout's branch to the shared commit only when the checkout is on the configured branch, the commits it lacks change nothing but the reasoning file, that file already matches the shared commit and nothing is staged for it; the ref update is a compare-and-swap. Otherwise it leaves the branch and reports `checkout: behind` or `unchanged` with the reason, including the exact command when restoring the file and pulling is lossless. It never pulls in code or other upstream changes; those stay with the person's own `git pull`. New entries are inserted without rewriting unchanged ones, falling back to replacing the smallest affected list. The delivery receipt determines sharing. Skill implementation updates still require updating the installed local checkout after their PR is merged; confirm that activation before a real trial.

Discord recovers prepared saves before syncing, refreshes before selecting feedback, and attempts sharing after the local capture journal completes. Sharing failures cannot undo saved observations. Proactive prompts are postponed if configured sharing cannot be refreshed. These hooks run with sessions or the existing explicitly enabled dispatcher; no background service is created by the standalone skill.

## Review the reasoning

Use `feedback.add_report`, or create equivalent `review_outcome_feedback` backlog work when editing by hand. Compare original prediction, actual execution, observation opportunity and attributed evidence. Keep partial assessments and reservations outstanding. Revise reasoning only when warranted under the normal standing and endorsement rules; sharing never completes review automatically.
