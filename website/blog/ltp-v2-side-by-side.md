---
title: "Drafting first vs asking first: two versions of one thinking skill"
created: 2026-11-16
date: 2026-11-16
authors: ["rufus-pollock"]
---

# Drafting first vs asking first: two versions of one thinking skill

**The new `ltp-v2` skill drafts and lets you correct; the original `ltp` asks and then records your answer. On the same small problem, v2 reached a list of actions in four turns. The original was still checking the assumption those actions depend on.**

Both are skills for AI agents such as Claude Code and Codex. They help you work out what you are trying to achieve, what is getting in the way, and what to do about it. Underneath they use the Logical Thinking Process: a goal and what must be true to reach it, what's going wrong and why, the conflicts that keep a problem stuck (two needs that pull against each other), and the changes and actions that resolve them.

I wrote `ltp-v2` after looking back over a month of my own sessions with the original. Again and again I overrode it to get the same things: a first draft straight away, a fixed order, a critique before I saw anything, more pushback, and fewer approval steps. ([What changed](/changelog/2026-11-16-ltp-v2).)

To compare them, I gave both the same brief and the same four replies from a made-up user, Sam. Sam is one of two burnt-out founders of a community garden, and asks: *how do we get the garden to run well without depending on the founders?* Sam's four turns were:

1. "Help me think this through."
2. "Looks roughly right; we also need money for seeds and tools."
3. "I want to hand things over, but I also want the garden to keep its standards."
4. "OK, what should we actually do?"

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

## What happened

| Turn | `ltp` (original) | `ltp-v2` |
|---|---|---|
| 1 | A fixed introduction (what each kind of message means, whether sharing is on), then the goal and three problems saved. It asks Sam to describe what "running well" looks like. | A goal with four success factors as a plain-text tree, plus a short critique table. It asks one question: is anything missing, such as money or standards? |
| 2 | It adds money as a condition, in Sam's words, and offers to accept the goal "for now". | It pushes back ("money may be a solution, not a need"), records "running costs reliably covered" instead, and fills in conditions under each factor with ✓ ~ ✗ status. |
| 3 | It draws the conflict, marks Sam's "if I let go, things slip" as an assumption not yet examined, and asks for an example of a standard slipping. | It sketches what's going wrong, draws the conflict, names a deeper assumption ("only the founders can judge standards") and proposes a fix: write down what good looks like for each job, and hand the job over with it. |
| 4 | It declines to recommend an action yet, because everything turns on that assumption, and asks Sam to list three standards. | Six actions in order, the obstacles each answers, and a question: which two jobs should be the pilot? |

## Turn 3 up close

The two skills draw the same conflict differently. The original draws boxes side by side, which needs a wide screen and breaks when a label doesn't fit (see the bottom row):

```
                 +--------------------------------+
                 | [Proposed] Objective           |
                 | Garden runs well, standards    |
                 | kept, founders stepping back   |
                 +--------------------------------+
                    ^                        ^
          necessary for                necessary for
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

In the Claude desktop app the original draws a rendered diagram instead, which is easier on the eye but packs a lot into small boxes. v2 stacks the two sides, keeps lines short enough not to wrap in a chat window, and puts the way out underneath:

```
CLOUD: hand over vs keep standards

Goal: the garden runs well, keeps its standards, no founders

A want: the garden keeps its standards
  so we: founders keep checking and deciding
        <-- conflicts with -->
B want: founders step back, members own the work
  so we: hand jobs and decisions over fully

Assumption under D vs D': only the founders can judge
  standards, and their judgment is not written down.
Injection: write each job's "what good looks like" as a
  short checklist, hand the job over with it, and swap
  founder sign-off for a monthly rotating member walk-round.
```

## What's different

- **Pace.** The original records a little each turn and asks one question. v2 drafts and lets Sam correct, so the conversation reaches actions sooner.
- **They agree more than it looks.** Both spot that everything hangs on whether standards can be written down. The original won't recommend actions until that is checked. v2 recommends them anyway, and makes checking it the first action ("write what good looks like for two jobs and test it"). One is careful, the other is quick; neither is wrong.
- **Who does the work.** v2 proposes, marks its guesses as assumptions, and argues ("standards slip because they live in your head, not because you let go"). That suits someone who wants a sparring partner, but only if they actually correct the guesses.
- **Ceremony.** The original's first reply spends about 220 words on an introduction before reaching the garden, and keeps offering formal acceptance. v2 treats "roughly right" as a yes.
- **Length.** v2 is not shorter: 200–310 words a reply against the original's 120–350, mostly trees and critique tables. Tightening this is next.

## Where the original is stronger

- It keeps your words. Money stayed "money"; v2 rewrote it as "running costs".
- It records who said what, and never takes silence as agreement.
- It is built for groups, with participants, feedback on changes, and sharing, which a one-person test like this can't show.

## How much to read into this

One run each, on a made-up problem, with a model playing the assistant in both. v2's "critique" was done inline rather than by a separate agent. And v2's first question happened to ask about money and standards, which Sam's scripted replies then raised, so it looks more perceptive here than it may be. Treat this as a sketch, not a test, and read the [full transcripts](ltp-v2-side-by-side-transcripts.md).

Both skills are installable. `ltp` is unchanged. `ltp-v2` runs when you call it by name: `npx skills add reasoncommons/reasoncommons -s ltp-v2`, then `/ltp-v2`. See [skills](/skills).
