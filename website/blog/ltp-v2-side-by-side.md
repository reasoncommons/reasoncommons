---
title: "Drafting first vs asking first: two versions of one thinking skill"
created: 2026-11-16
date: 2026-11-16
authors: ["rufus-pollock"]
---

# Drafting first vs asking first: two versions of one thinking skill

**The new `ltp-v2` skill drafts and lets you correct; the original `ltp` asks and then records your answer. On the same small problem, v2 reached a list of actions in four turns. The original was still checking the assumption those actions depend on.**

![The same brief, first reply: the original ltp opens with an introduction and a question; ltp-v2 opens with a draft goal tree and a short critique](/changelog/images/2026-11-16-ltp-v2-first-reply.png)

Both are skills for AI agents such as Claude Code and Codex. They help you work out what you are trying to achieve, what is getting in the way, and what to do about it. Underneath they use the Logical Thinking Process: a goal and what must be true to reach it, what's going wrong and why, the conflicts that keep a problem stuck (two needs that pull against each other), and the changes and actions that resolve them.

## What changed in v2

I looked back over a month of my own sessions with the original skill. Again and again I overrode it to get the same things, so v2 does them by default:

1. **It drafts first.** It starts from whatever you already have (a brief, notes, or one sentence) and shows a draft goal straight away, one level at a time, rather than building it up question by question.
2. **It follows a fixed order** (goal, what's going wrong, conflicts, the fix, actions) and shows where you are. It takes most care over the conflicts. After them it moves fast and ends on actions to take.
3. **It critiques its own drafts before showing them**, and lists the critic's points with a recommendation on each. "Go with your recs" accepts them all.
4. **It pushes back** on your edits, and marks anything it guessed as an assumption.
5. **It shows trees as plain text** narrow enough not to wrap in a chat window, and keeps a readable summary next to its saved state.
6. **It has fewer approval steps.** No introduction screen, and "roughly right" counts as a yes.

The original `ltp` is unchanged and still the default. ([Changelog entry](/changelog/2026-11-16-ltp-v2); [the skill](https://github.com/reasoncommons/reasoncommons/blob/main/skills/ltp-v2/SKILL.md); [how to install it](/skills#try-the-faster-version-ltp-v2).)

## How each runs

```
ltp (original)

  Sam's first message
        |
        v
  Introduction: message types, sharing status
        |
        v
  +-> Capture what Sam said, a node at a time
  |         |
  |         v
  |   Ask ONE question  ("accept for now?")
  |         |
  +---------+   repeat; Sam picks which tree next
        |
        v
  Next step: one recommendation, when the
  reasoning supports it
```

```
ltp-v2

  Brief, SCQ or a one-line prompt
        |
        v
  Draft goal + top-level success factors
        |   (critique first, then show)
        v
  Sam corrects  ("go with your recs" = yes)
        |
        v
  Goal -> Reality -> Conflicts -> Future -> Actions
                     ^ most care   ^ drafted together
        |
        v
  Actions to take, plus a readable summary
  saved next to the state file
```

## The test

I gave both skills the same short brief and the same four replies from a made-up user, Sam. Sam is one of two founders of a community garden with about 30 members. Turnout at work days has halved, the founders are burning out, and newer members don't know what needs doing or how decisions get made. Sam's question: *how do we get the garden to run well without depending on the founders?*

Here is what each skill did at the four moments that mattered.

### 1. The first reply

Sam says: "Help me think this through. The brief is in brief.md."

**Original.** It opens with a fixed introduction of about 220 words: what each kind of message means, and whether sharing is on. Then it saves the goal and three problems, and asks a question:

> **Next:** Tell me, in your own words, what you'd see happening at the garden when it is running well without you. What would a newer member be doing?

**v2.** It shows a draft goal at one level, with a check of its weak spots, and asks whether anything is missing:

```
G  The garden runs well without depending on the two
   founders.

CSF1 Enough members turn up regularly to do the work
CSF2 Members can see what needs doing and who is doing it
CSF3 Members know how decisions are made and can take part
CSF4 Founders' load is sustainable; they can step back
     without things falling over
```

*The difference:* Sam has something to react to in the first reply rather than a question to answer.

### 2. Sam adds money

Sam says: "Looks roughly right. We also need some money for seeds and tools."

**Original.** It records money as a condition, in Sam's words, and checks what "roughly right" means:

> I've kept the goal and three problems as proposed, since "roughly right" leaves open what to change. Do you want to accept them for now?

**v2.** It argues first, then takes "roughly right" as a yes and fills in the next level:

> Pushback first: you could run a garden on donated tools, so "money" may be a solution rather than a need. I've captured the need instead: running costs are reliably covered.

*The difference:* the original keeps Sam's words and asks before assuming. v2 challenges and moves on. Which is better depends on whether Sam wants a careful note-taker or a sparring partner.

### 3. The conflict

Sam says: "I want to hand things over, but I also want the garden to keep its standards. If I let go, things slip."

Both skills spot this as the heart of the problem, and both draw it as a conflict. The original draws boxes side by side. That needs a wide screen and breaks when a label doesn't fit (see the bottom row):

```
+---------------------------+      +---------------------------+
| [Proposed] Need           |      | [Proposed] Need           |
| Sam wants to hand things  |      | Sam wants the garden to   |
| over                      |      | keep its standards        |
+---------------------------+      +---------------------------+
          ^                                  ^
    necessary for                      necessary for
+---------------------------+      +---------------------------+
| [Proposed] Prerequisite   | <--> | [Proposed] Prerequisite   |
| Sam lets go of tasks and  |  conflicts  | Sam keeps hold of how the |
| decisions he handles      |  with | work is done              |
+---------------------------+      +---------------------------+
```

It then marks "if I let go, things slip" as an assumption not yet examined, and asks for an example of a standard slipping. (In the Claude desktop app the original draws a rendered diagram instead, which is easier on the eye but packs a lot into small boxes.)

v2 stacks the two sides so the lines stay short, names a deeper assumption, and proposes a way out (both diagrams trimmed slightly; full versions in the transcripts):

```
A want: the garden keeps its standards
  so we: founders keep checking and deciding
        <-- conflicts with -->
B want: founders step back, members own the work
  so we: hand jobs and decisions over fully

Assumption: only the founders can judge standards,
  and their judgment is not written down.
Fix: write each job's "what good looks like" as a
  short checklist, and hand the job over with it.
```

*The difference:* both find the same hinge. v2 also offers a fix to try.

### 4. "What should we actually do?"

**Original.** It declines to recommend anything yet:

> I can't yet recommend an action from the reasoning so far. The conflict (Proposed) turns on your assumption that things slip if you let go …

It asks Sam to list three standards a newer member could check.

**v2.** It gives six actions in order, and the first is a test of that same assumption:

```
1. This month: write "what good looks like" for two jobs
   and test it with a newer member.
2. Founders agree a rule: ask the member before changing
   their work.
3. Post a job list with owners and dates; ask five members
   by name to take one job each.
...
```

*The difference:* they agree more than it looks. Both see that everything hangs on whether standards can be written down. The original won't recommend until that is checked. v2 recommends anyway and makes checking it step one. One is careful, the other is quick.

## Where the original is stronger

- It keeps your words. Money stayed "money"; v2 rewrote it as "running costs".
- It records who said what, and never takes silence as agreement.
- It is built for groups, with participants, feedback on changes, and sharing, none of which a one-person test like this can show.
- It doesn't claim more than the reasoning supports, as turn 4 shows.

v2's weak spot is length. Its replies ran 200–310 words against the original's 120–350, mostly trees and critique tables. Tightening that is next.

## How much to read into this

This is one run each, on a made-up problem, with a model playing the assistant in both. v2's critique was done inline rather than by a separate agent. And v2's first question happened to ask about money and standards, which Sam's scripted replies then raised, so v2 looks more perceptive here than it may be. Treat this as a sketch, not a test. The [full transcripts](ltp-v2-side-by-side-transcripts.md) are there to check.

Both skills are installable. `ltp-v2` runs when you call it by name: `npx skills add reasoncommons/reasoncommons -s ltp-v2`, then `/ltp-v2`. See [skills](/skills).

## Appendix: turn by turn

Sam is a founder of a community garden whose volunteers are drifting away. Sam's four messages were scripted and the same for both skills.

| Sam says | `ltp` (original) | `ltp-v2` |
|---|---|---|
| "Help me think this through." | Introduction, then the goal and three problems saved; asks what "running well" looks like | A draft goal with four success factors and a critique; asks what's missing |
| "Roughly right; we also need money." | Adds money in Sam's words; offers to accept "for now" | Pushes back on "money", records "running costs" instead, fills in the next level with ✓ ~ ✗ status |
| "Hand over vs keep standards." | Draws the conflict; marks Sam's assumption; asks for an example | Draws the conflict; names a deeper assumption; proposes a fix |
| "What should we actually do?" | Declines to recommend yet; asks for three standards | Six actions in order, the first a test of the assumption |
