# Expected outcomes and feedback

For sharing between checkouts, follow [feedback-sync.md](feedback-sync.md). Refresh authorised shared records before deriving the queue, and sync after saving reports. Preserve immediate local capture when sharing fails; state whether sharing was verified. Routine sync does not endorse reasoning or authorise code changes.

Use this when preparing a change trial, resuming a participant's session or recording their feedback. The shared reasoning YAML owns expectations and reports. Delivery journals may cache transport state but never determine whether a predicted outcome happened.

## Capture before the trial

Identify the intervention or action, the benefits and credible harmful consequences being tested, who can report on each, and what experience/evidence lets them judge. `feedback_from` must contain actual participant IDs; assignment records who can provide evidence, not a promise to respond. Timing is optional: use a quoted timezone-aware `ask_after` when useful, and `ready_when` for an observation opportunity such as “after trying the change on one real decision.” An undated request remains discoverable on the recipient's next session; an unknown exposure calls for a readiness question. If the providers or observation opportunity differ materially, use separate requests. Preserve lack of a provider as unfinished reasoning rather than pretending a trial is ready. Do not backdate a forecast or manufacture an exposure, observation, contribution or agreement.

Prepare a commitment with `feedback.new_request(state, id, about, benefits, reservations, feedback_from, by, ready_when=...)`, or use native file editing to write the same structure. Its statement snapshots must match the actual saved nodes at capture. Timing and readiness text are optional, but facilitate how the person could observe the outcome. Every substantive expectation revision gets the next revision under the same request ID, with fresh snapshots and its own reports; old versions remain inspectable and can receive evidence about the earlier trial. Do not silently transfer an earlier report to a new prediction.

```yaml
feedback_requests:
- id: remote-work-trial
  revision: 1
  created_by: alice
  recorded_at: '2026-10-20T10:00:00Z'
  about: {ref: trial, tree: future_reality, kind: injection, standing: proposed, text: Alice tries remote work on one comparable call-handling shift.}
  feedback_from: [alice]
  ready_when: After the comparable shift and review of its work record.
  benefits:
  - {ref: gain, tree: future_reality, kind: predicted_effect, standing: proposed, text: Alice completes more comparable calls during that shift.}
  reservations:
  - {ref: isolation, tree: future_reality, kind: undesirable_effect, standing: proposed, text: Alice may have more difficulty obtaining help during the remote shift.}
  reports: []
```

The example is fictional scaffolding using the remote-work toy topic; do not import it into a real collaboration. Its predictions are not claims that the cited study established them. At least one benefit or reservation is required; either list may be empty when none has been recorded. Snapshot fields are `ref`, `tree`, `kind`, `standing` and full `text`; they describe the original reasoning, not current acceptance.

## Request and record

At session entry, run `python3 <skill-directory>/scripts/feedback.py <state.yaml> --participant <actual-driver>`. The read-only CLI returns **Feedback request** responses with both benefit and reservation snapshots. `--format json` provides the same queue to hosts; `--include-waiting` exposes scheduled/deferred work for inspection without making it due. Show one actionable request first, follow explicit user redirection, and do not require a response to continue. A standalone skill cannot wake itself; a configured host must run between-session reminders.

Record a report under the exact request revision with a stable unique `id`, assigned human `by`, clock-derived `recorded_at`, `readiness` (`experienced`, `not_yet`, `cannot_assess`), the person's actual `text`, `evidence_type: self_report`, and an `outcomes` list. Each outcome has its snapshot `ref`, `verdict` and explanation `note`. Preserve source evidence where supplied; optional `observed_at` is the actual observation time, not an invented timestamp. Optional `defer_until` must be in the future. Preserve transport references in `source` where provided by the host. A quote naming Rufus is not authenticated evidence that Rufus submitted it; record such hearsay separately as the driver's attributed observation.

Outcome verdicts are `observed`, `not_observed`, `unclear`, `not_assessed` and `unavailable`. `not_observed` is the participant's scoped report, not proof that an effect is absent everywhere. `unclear` records an inconclusive assessment; `unavailable` explicitly records missing/unrecoverable evidence. Both preserve the uncertainty for reasoning review. `not_assessed`, an omitted outcome or a readiness-only reply leaves that outcome open. So does `unclear`: the provider's latest assessment of each outcome counts, in order of `recorded_at`, so an outcome last found unclear returns to their queue with the earlier note, a later `observed`, `not_observed` or `unavailable` settles it, and a later `unclear` reopens it. Offer deferral when someone expects to judge it later, so the question does not recur before they can answer. A not-yet-experienced report cannot assert observed/not-observed outcomes. Unexpected effects belong in the person's text and, when useful, separate proposed reasoning with attribution.

```yaml
reports:
- id: report-alice-1
  by: alice
  recorded_at: '2026-10-21T15:00:00Z'
  readiness: experienced
  text: I finished more calls, but I have not checked how quickly I could get help.
  evidence_type: self_report
  outcomes:
  - {ref: gain, verdict: observed, note: More comparable calls were completed according to my shift record.}
  - {ref: isolation, verdict: not_assessed, note: I have not assessed access to help yet.}
```

This answers only the benefit for Alice. Other providers and the reservation remain pending. Never infer an outcome from nonresponse, a sent notification, action completion or elapsed time. After a report, compare original prediction, exposure/execution, evidence, observation opportunity and outcome; propose only warranted reasoning changes. Feedback submission is neither endorsement nor an automatic causal verdict.

## Preservation and follow-up

When reconciling independent checkouts, preserve request versions and report contents by ID. Chronological ordering of immutable reports may change without rewriting an observation; the latest recorded report determines deferral. Use `feedback.add_report` or its equivalent review-backlog update even for native file capture, so observations remain work to interpret rather than merely stored responses.

Use native file tools to save a session's changes, then run `update_views.py` as usual. Before replacing existing feedback records, compare before/after using `feedback.guard_transition`; request versions are immutable except for appended reports, and existing reports cannot be rewritten or removed. The Discord host enforces this before committing its staged save. The read-only queue always derives unresolved outcomes per provider from YAML; restart, changed focus and a delivered prompt do not discard them. If evidence is lost, explicitly record `unavailable` with an explanation instead of claiming success or absence of harm. A separate reasoning backlog can retain the consequences of an inconclusive or harmful result even after its feedback has been recorded.

The Discord surface uses the same helper and canonical state. Its deterministic feedback command accepts the displayed version and the authenticated participant's own report, without requiring a model call. Optional proactive delivery is configured by the operator, limited to a mapped participant in a configured channel, and bounded per request version. Failed or uncertain delivery leaves evidence unresolved; uncertain sends require operator reconciliation rather than an automatic repeat. No deployment, credentials or real messages are implied by capturing a request.
