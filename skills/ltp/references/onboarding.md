# First-session introduction

A participant opening Reason Commons for the first time needs to know what the skill is for and what each type of message asks of them, especially before their first **Feedback request**. Show this introduction once per participant per repository, before the feedback queue and the ordinary agenda.

## When to show it

Once the driver is known, run `python3 <skill-directory>/scripts/onboarding.py <state.yaml> --participant <driver>`. If it prints an **Introduction**, show it unchanged as the first substantive response, then continue to the driver's feedback queue. It prints nothing for someone who has already seen it in this repository's main checkout or any of its worktrees. When someone asks to see the introduction again, run it with `--again`.

The script records who has seen it only in the local, gitignored folder beside the main checkout's copy of the state file (`.reason-commons/onboarding.json` for `reason-commons.yaml`), so it never changes the shared reasoning, a new worktree session doesn't repeat it and the record outlives deleted worktrees. Records left in individual worktrees still count. A reasoning file that exists only in a worktree keeps its record beside it, creating nothing in the main checkout. It reads whether feedback sharing is configured but never configures it: a participant turns sharing on by running the printed command with their own words of authorisation. The command names the remote's default branch, the one other participants read, rather than the checkout's current branch. In a linked worktree, the printed command configures the main checkout's copy of the file, so later worktree sessions inherit it; when the main checkout already authorised sharing for this file, the introduction reports sharing as on and names that checkout; see [feedback-sync.md](feedback-sync.md).

## Introduction

Edit the wording here; the script fills the placeholders. Keep it short: it stands between a busy person and their first useful step.

```markdown
**Type: Introduction**

Welcome, {name}. This is Reason Commons for **{project}**: a shared record of the reasoning behind the work, such as goals, problems, proposed changes and what we expect them to do.{others} I help you add to it, question it and act on it. Nothing you say counts as agreed until you say so.

| When you see | It asks of you |
| --- | --- |
| **Feedback request** | Your experience of a change: did the expected benefit happen, and did the possible harm? Answer either or both, or say "not yet". |
| **Change proposal** | A typed acceptance before any project file changes, or the revisions you want. |
| **Next step** | Nothing. One suggestion you can take, change or ignore. |
| **Change result**, **Answer**, **Tree view**, **Capture result** | Nothing. Information about what changed or what is recorded. |

**Feedback:** each request shows the expected benefit and the possible harm side by side, as they were written before the change. Silence is never taken as an answer, and answering doesn't mean you agree with the reasoning.

**Sharing:** {sharing}

**Waiting for you:** {waiting}

Ask to see this introduction again at any time.
```
