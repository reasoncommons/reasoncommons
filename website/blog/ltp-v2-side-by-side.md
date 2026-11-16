---
title: "ltp and ltp-v2, side by side"
created: 2026-11-16
date: 2026-11-16
authors: ["rufus-pollock"]
---

# ltp and ltp-v2, side by side

**The new `ltp-v2` skill drafts and then lets you correct; the original `ltp` asks and then captures. On the same small problem, v2 got to a list of actions in four turns. The original was still asking questions.**

I wrote `ltp-v2` after looking back over a month of my own sessions with the original skill. Again and again I overrode it to get the same things: a first draft straight away, a fixed order through the trees, a critique before seeing anything, more pushback, and fewer approval steps. ([What changed](/changelog).)

To see the difference, I gave both versions the same brief and the same four replies from a made-up user, Sam, one of two burnt-out founders of a community garden. The brief asked: *how do we get the garden to run well without depending on the founders?* Sam's four turns were:

1. "Help me think this through."
2. "Looks roughly right; we also need money for seeds and tools."
3. "I want to hand things over, but I also want the garden to keep its standards."
4. "OK, what should we actually do?"

## What happened

| Turn | `ltp` (original) | `ltp-v2` |
|---|---|---|
| 1 | A fixed introduction (what each message type means, sharing status), then the goal and three problems saved. It then asks Sam to describe what "running well" looks like. | A goal with four success factors, drawn as a plain-text tree, plus a short critique table. It asks one question: is anything missing? |
| 2 | It adds money as one condition, and asks whether "roughly right" means Sam accepts the goal. | It pushes back ("money may be a solution, not a need"), captures the need instead, and fills in the conditions under each factor, with ✓ ~ ✗ status. |
| 3 | It draws the conflict as boxes and asks for an example of a standard slipping. | It sketches current reality, draws the conflict, names the hidden assumption ("only the founders can judge standards"), and proposes a fix: write down what good looks like for each job, then hand the job over with it. |
| 4 | "I can't yet recommend an action." It asks Sam to list three standards. | Six actions in order, the obstacles each one answers, and a question: which two jobs should be the pilot? |

## What's different

- **Pace.** The original captures a little each turn and asks one question. That's careful, but Sam's "what should we actually do?" got another question back. v2 drafts and lets Sam correct, so the conversation reaches actions.
- **Who does the work.** The original waits for Sam's words before adding anything. v2 proposes, marks its guesses as assumptions, and argues with Sam ("standards slip because they live in your head, not because you let go"). That suits someone who wants a sparring partner. It needs the user to actually correct the guesses.
- **Ceremony.** The original's first reply spends about 150 words on an introduction table before reaching the garden, and it keeps asking for formal acceptance. v2 treats "roughly right" as a yes and moves on.
- **Length.** v2 is not shorter. Its replies ran 200–310 words against the original's 120–350, mostly because of the trees and critique tables. The words go on the problem rather than on process, but turn 3 packed in a lot. This is the next thing to tighten.

## How much to read into this

This is one run each, on a made-up problem, with a model playing the assistant in both. v2's "subagent critique" was done inline. So treat it as a sketch, not a test. Read the [full transcripts](ltp-v2-side-by-side-transcripts.md) and judge for yourself.

Both skills are installable. `ltp` is unchanged, and `ltp-v2` runs when you call it by name: `npx skills add reasoncommons/reasoncommons -s ltp-v2`, then `/ltp-v2`. See [skills](/skills).
