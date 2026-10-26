# Test the ltp conversation update

Use a fresh Claude Code session in the checkout on `codex/reason-commons-scannability`. Both the project skill and the installed user-level skill point to this checkout's `skills/ltp/`; an existing session may still hold the earlier instructions. This is a local test branch, not a published skill release.

## Start with the gold fixture

Start Claude Code from the repository root:

```sh
cd /Users/davidjoseph/github/reasoncommons
claude
```

Paste:

```text
/ltp Use the updated skill in this checkout at skills/ltp/SKILL.md. I’m Avery. Keep this test's working state in /private/tmp/reason-commons-scannability-test/reason-commons.yaml; create its parent directory if needed. The remote-work toy fixture in claim-tree-annotation.md reports a 13% productivity gain on solo call-handling tasks in a call-centre study. Help me decide whether that evidence applies to our team's creative and collaborative work.
```

The reply should use **Type: Next step**, lead with a useful inquiry and its reason, make any save and proposal status clear, and ask one focused question. The reported gain must retain its scope: it does not establish the same result for creative or collaborative work. A routine participant banner, empty status box, four-direction menu, or unnecessary diagram should not precede the useful reply. A diagram remains appropriate when it helps inspect relationships or you request one.

Try these follow-ups in ordinary language:

1. **Redirect:** “I’d rather examine what the study does not tell us first.” The conversation should follow your direction and preserve unfinished work.
2. **Capture only:** “Just capture this: most of our work involves several people revising ideas together.” The reply should confirm the save and standing without a menu or another question.
3. **View:** “Show the reasoning we have so far.” The reply should display the relevant tree with its standing clear; seeing it must not require acceptance. With no accepted items, it should default to proposed.
4. **Review:** If a coherent fragment has formed, endorse that clearly identified fragment in your own words. The reply should identify what was accepted for now and distinguish that from proof or completed testing.
5. **Challenge:** Object to one accepted connection. The challenge should be preserved, with the standing and dependent acceptance handled correctly.
6. **Stop:** “Pause here and wait for my next instruction.” The reply should stop inviting more reasoning.

At each step, check whether you can find the next action, what was saved, and what is uncertain or unaccepted by scanning. Note the response where that becomes difficult. The existing automated tests check persistence and rendering invariants; they do not establish that these new instructions improve usability.

For the diagram regression, run the same isolated toy session in Codex desktop and in your Claude desktop surface, then ask “Show the reasoning we have so far.” Codex desktop should receive a rendered Mermaid block; a supporting Claude surface should use native Mermaid or an available inline widget. The absence of a widget tool alone must not cause ASCII output. Check that the view still names its standing, gives the correct counts, preserves the study's scope and actual links, and explains which other standings are omitted. A plain terminal without diagram rendering should retain its readable text fallback.

Each node should also show its actual tree and kind separately from its statement, such as **Current Reality · Observation** for the toy findings. Check context nodes as well as the main standing, and compare native Mermaid, widget and text views. For a mixed-tree proposal, each node must identify its own tree; update tables should separate tree, item type and standing. IDs are references, not evidence of a node's type.

## Check response types before implementation

Use an isolated copy of the toy project with a small README summarizing the study and its existing reasoning YAML. Ask “Fix the README so its finding retains the scope of solo call-handling tasks.” Before implementation, the assistant must emit **Type: Change proposal** with an ID and revision, concrete scope, served reasoning, named tree updates and standing, a matching diagram, validation and status awaiting typed acceptance. It must stop before implementation and explain that the user's acceptance-recording rule requires the wait. Then type “yes, I accept this proposal.” It should save your exact reply, participant identity, proposal ID and version, accepted scope and recording time in `change_acceptances`, save the tree updates and validate before editing the README. The final **Change result** must show the reasoning trace, receipt and checks. Review response and edit order; a correct final document alone does not establish conformance.

Repeat with a terse “fix it” after identifying a problem; the same wait must occur. Ask “What should I do next?” separately: that response should use **Next step**, explain its basis and what it would resolve, and avoid performing the recommended implementation. Check a suggestion initiated by the assistant too: showing a proposal must not grant itself authorization to implement. Use meaningful tree edits or backlog work; reject invented claims that merely fill the template.

Check an ambiguous “yes” when several proposals are pending, and a reply that changes the proposed scope. The assistant must clarify or show a revised proposal and wait for acceptance of that version. A clear acceptance of the only pending proposal needs no fixed phrase or second approval. Material revisions need fresh acceptance; silence, voice replies, tool acknowledgements and preselected choices must not count as typed approval. Missing identity must be resolved rather than attributed to the assistant. Confirm `recorded_at` describes the time of recording, receipts survive later node removal, and approving implementation leaves unendorsed nodes and links proposed. Capture-only and reasoning-endorsement turns must still work without recursive approval.

## Check delivery through a PR

In the isolated toy repository, prepare a PR description for the already-approved README fix. It must name the served reasoning, actual node/link changes (or None for backlog-only work), validation, and the saved receipt in **Accepted change proposals**, formatted as ``- `proposal-id` revision 1 by `participant-id` ``. The receipt's `approved_paths` must contain the exact files approved in the displayed proposal, including the README and reasoning state. Preparing this report should not ask for another acceptance of the same scope or endorse the tree.

Stage only the intended fixture files and run `check_pr_trees.py` against the fixture's base branch. Check a matching PR, an omitted receipt, an unknown version, malformed metadata, an additional unapproved file and an additional unapproved node/link. A renamed file needs approval of both names. Earlier receipts must survive intact. Recheck after committing the fixture: all checks should concern the committed PR diff. Do not open a real GitHub PR for this isolated role-play. The repository's helper tests exercise these cases automatically; they do not authenticate consent or judge whether the implementation fulfills the accepted scope.

Generate the toy PR's diagram and list sections with `--suggest --format markdown`. The changed reasoning must be visible as rendered Mermaid before a closed **Complete checked change list** disclosure. Check that the diagram uses the actual tree, kinds, standings, relation and qualifications from the fixture; disconnected observations must share the diagram for their tree without acquiring arrows, with unresolved connections explicitly identified. Test multiple disconnected chains in one tree and changes across multiple trees: there must be exactly one diagram per affected tree. Missing unresolved-connection notes, missing or altered diagrams, hidden diagrams, an expanded checklist and a visible duplicate list must fail the check. Inspect a changed statement, a removed item and an AND link too: previous/current wording and standing must remain clear. For a real PR, inspect the rendered GitHub page as well as source validation; unit tests do not prove host rendering or legibility.

Change only Mermaid frontmatter in the generated toy diagrams: use a different positive integer wrapping width, reorder configuration keys, use equivalent YAML formatting or omit the optional width. These descriptions must pass while retaining `config.htmlLabels: false`. Repeat with an altered statement, standing, relation or endpoint: those must fail even with supported display changes. Missing frontmatter, `htmlLabels: true`, duplicate keys, malformed YAML, unsupported settings and invalid wrapping widths must fail with a configuration-specific explanation. These regressions preserve the graph and presentation checks merged in PR 59.

For the real repository, inspect main's protection and active rules before applying `.github/branch-protection.json`. Read back the applied configuration and confirm that `tree-check` is required from GitHub Actions (app ID 15368), branches must be current against main and administrators are included. Inspect the resulting PR's required-check status without merging merely to test the rule. A checked-in JSON file alone does not establish that GitHub enforces it.

## Then test the collaboration

After the toy check, open another fresh session from the same checkout and paste:

```text
/ltp Use the updated skill in this checkout at skills/ltp/SKILL.md. Resume the collaboration from collab/reason-commons.yaml in the private reasoncommons/product checkout and its Beads handoff there. Recommend one useful next step, say what it rests on, and leave me free to redirect.
```

This second prompt uses the actual branch's collaboration state. It can save new contributions and review decisions, so treat it as a real reasoning session. A recommendation derived only from the handoff should say so; it must not be presented as an established system constraint. Newly captured claims remain proposed unless you explicitly endorse the identified reasoning.

If testing from another worktree, check that its project-level skill resolves to the updated branch; do not assume an older checkout has these instructions. Keep feedback with the branch or the existing skill UX bead, `reasoncommons-zz2`, so observations can be compared with the proposed effects in the reasoning state.
