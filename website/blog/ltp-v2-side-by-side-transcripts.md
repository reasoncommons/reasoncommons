---
title: "Drafting first vs asking first: transcripts"
created: 2026-11-16
date: 2026-11-16
authors: ["rufus-pollock"]
---

# Drafting first vs asking first: transcripts

Full transcripts behind [the comparison](ltp-v2-side-by-side.md). Both runs used the same brief and the same four user turns. "Sam" and the garden are made up, and a model played the assistant in each run, following one skill each.

## The brief

> # Brief: community garden volunteers
> 
> Situation: A neighbourhood community garden has run for 4 years with about 30 members. Two founders do most of the organising.
> Complication: Volunteer turnout at work days has halved this year, the founders are burning out, and newer members say they don't know what needs doing or how decisions are made.
> Question: How do we get the garden to run well without depending on the two founders?

## ltp (the original)

### Turn 1
**User:** Hi, I'm Sam, one of the founders. Can you help me think this through? Brief is in brief.md.
**Assistant:**
**Type: Introduction**

Welcome, Sam. This is Reason Commons for **Community garden without founder dependence**: a shared record of the reasoning behind the work, such as goals, problems, proposed changes and what we expect them to do. I help you add to it, question it and act on it. Nothing you say counts as agreed until you say so.

| When you see | It asks of you |
| --- | --- |
| **Feedback request** | Your experience of a change: did the expected benefit happen, and did the possible harm? Answer either or both, or say "not yet". |
| **Change proposal** | A typed acceptance before any project file changes, or the revisions you want. |
| **Next step** | Nothing. One suggestion you can take, change or ignore. |
| **Change result**, **Answer**, **Tree view**, **Capture result** | Nothing. Information about what changed or what is recorded. |

**Feedback:** each request shows the expected benefit and the possible harm side by side, as they were written before the change. Silence is never taken as an answer, and answering doesn't mean you agree with the reasoning.

**Sharing:** not available, because this reasoning file is not in a Git checkout. Your answers stay on this computer.

**Waiting for you:** nothing right now.

Ask to see this introduction again at any time.

---

I've read the brief. **Saved** (all proposed, none accepted yet):

- Goal: the garden runs well without depending on the two founders.
- Three current problems: work-day turnout has halved, the founders are burning out, and newer members don't know what needs doing or how decisions are made.

Focus: keeping the garden going without the founders · Driver: Sam · Other participants: none.

**Next:** Tell me, in your own words, what you'd see happening at the garden when it is running well without you. What would a newer member be doing?

**Why:** The goal is still one sentence; what "running well" means decides which problems matter most.

You can accept the goal and the three problems for now, or revise them.

### Turn 2
**User:** Looks roughly right. I'd add that we need some money for seeds and tools — we're always short.
**Assistant:**
**Saved:** one condition and one link, both proposed.

```text
GOAL
+------------------------------+          +--------------------------+
| ADDED · [Proposed]           | -------> | [Proposed]               |
| Necessary condition          | necessary| Goal                     |
| Enough money for seeds       |   for    | Garden runs well without |
| and tools                    |          | depending on founders    |
+------------------------------+          +--------------------------+
```

Full statement: "The garden has enough money for seeds and tools." (Goal · Necessary condition · Proposed), from you.

I've kept the goal and three problems as proposed, since "roughly right" leaves open what to change. Do you want to accept them for now?

**Next:** Say what else would have to be true for the garden to run well without you, besides money.

### Turn 3
**User:** The real tension: I want to hand things over, but I also want the garden to keep its standards. If I let go, things slip.
**Assistant:**
**Saved:** a conflict, all proposed. The shared objective and the two links to it are my wording; the rest are yours.

```text
CONFLICT
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

Assumption on the right-hand link, from you: "If I let go, things slip." Not yet examined.

**Next:** Give one concrete example of a standard that slipped, or that you fear would. What did it look like?

**Why:** The conflict rests on that assumption. A specific example shows whether the standard can be written down and shared.

You can accept this conflict for now, or revise it.

### Turn 4
**User:** OK, what should we actually do?
**Assistant:**
**Type: Next step**

**Next:** List the three standards you would not let slip, each as something a newer member could check (for example, "tools are cleaned and put back").

**Why:** I can't yet recommend an action from the reasoning so far. The conflict (Proposed) turns on your assumption that things slip if you let go, and the answer changes what to do: if the standards can be written down, handing them over with a checklist is plausible. If they can't, you need a different handover.

**What this resolves:** Whether the assumption holds, and what to hand over first.

**State:** No change. Nothing has been carried out or accepted.

Or: view the reasoning so far. What are your three?

## ltp-v2

### Turn 1
**User:** Hi, I'm Sam, one of the founders. Can you help me think this through? Brief is in brief.md.
**Assistant:** `Goal [~] > Reality [ ] > Conflicts [ ] > Future [ ] > Actions [ ]`

TL;DR: I started from brief.md and drafted the goal with four things that must be true; tell me what's missing or wrong.

```
G  The garden runs well without depending on the two
   founders.

CSF1 Enough members turn up regularly to do the work
CSF2 Members can see what needs doing and who is doing it
CSF3 Members know how decisions are made and can take part
CSF4 Founders' load is sustainable; they can step back
     without things falling over
```

Critique (quick check before showing):

| Point | My recommendation |
|---|---|
| CSF4 overlaps CSF1 | Keep it; it is the burnout half of your brief |
| "Enough" turnout has no number | Leave open; set it with real work-day data |
| Nothing on keeping standards or what the garden is for | Add only if you want it (my guess, not from the brief) |

**You:**
1. Is anything missing, such as money or standards? I'd add only what you name.

**Decided:** saved to ltp/reason-commons.yaml with a summary in ltp/README.md; trees only, no conditions yet. No git here, so nothing committed.

`Saved · not committed`

### Turn 2
**User:** Looks roughly right. I'd add that we need some money for seeds and tools — we're always short.
**Assistant:** `Goal [x] > Reality [ ] > Conflicts [ ] > Future [ ] > Actions [ ]`

TL;DR: I added money as a fifth thing that must be true, and drafted the conditions under each.

Pushback first: you could run a garden on donated tools, so "money" may be a solution rather than a need. I've captured the need instead: running costs are reliably covered. Say if you disagree.

```
G  Garden runs well without depending on the two founders

CSF1 Enough members turn up regularly to do the work
 ~ Work days have a clear, light time commitment
 ✗ New members get welcomed and given a first task
CSF2 Members can see what needs doing and who is doing it
 ✗ Visible list of jobs with owners and dates
 ✗ Seasonal calendar written down, not in founders' heads
CSF3 Members know how decisions are made and can take part
 ✗ Decision rules written down and shared
 ✗ Any member can raise a proposal and see it decided
CSF4 Founders' load is sustainable
 ✗ Founder jobs are held by other members
 ✗ A founder can take a break without a crisis
CSF5 Seeds, tools and running costs reliably covered
 ~ Known annual budget and a way to raise it
```

All conditions and statuses are my assumptions from the brief until you confirm.

**You:**
1. Do the statuses look right? I'd leave them and fix them as we meet reality.

**Decided:** treated "roughly right" as OK for the five factors; saved and validated.

`Saved · not committed`

### Turn 3
**User:** The real tension: I want to hand things over, but I also want the garden to keep its standards. If I let go, things slip.
**Assistant:** `Goal [x] > Reality [~] > Conflicts [~] > Future [ ] > Actions [ ]`

TL;DR: that tension looks like the core driver, so I sketched current reality in brief and went straight to the conflict.

Pushback: maybe standards slip because they live in your head, not because you let go. I've drafted it that way; correct me if I'm wrong.

```
CURRENT REALITY
Effects:  turnout halved; founders burning out; newer
          members unsure what needs doing or how decisions
          are made; always short of money
Causes:   jobs and decisions live in the founders' heads
          (assumption)
          <- founders hold on to protect standards  (yours)
          <- no small, clear way in for members (assumption)
Core driver: holding on to protect standards
```

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

Critique:

| Point | My recommendation |
|---|---|
| Injection assumes standards can be written down | Test it on two jobs first |
| Money is not in this cloud | Treat as a separate possible conflict |
| Walk-round may just recreate founder control | Members rotate; founders join last |

**You:**
1. Does "what good looks like" match the standards you fear losing? I'd say yes until you object.

Other candidate conflicts: money (fees vs open access). Any more?

**Decided:** saved and validated.

`Saved · not committed`

### Turn 4
**User:** OK, what should we actually do?
**Assistant:** `Goal [x] > Reality [x] > Conflicts [x] > Future [x] > Actions [~]`

TL;DR: here are the actions to take, in order; the hand-over only works if the standards are written down first.

```
ACTIONS
1. This month: write "what good looks like" for two jobs
   and test it with a newer member.
2. Founders agree a rule: ask the member before changing
   their work.
3. Post a job list with owners and dates; ask five members
   by name to take one job each.
4. Write a one-page "how we decide" and share it.
5. First monthly walk-round, rotating members; founders
   join last.
6. Next meeting: agree an annual budget and how to cover
   seeds and tools.

If it works: members know what to do, work stops waiting on
founders, burnout eases (all assumptions until tried).

OBSTACLES
- writing takes time      -> start with two jobs
- founders step back in   -> action 2
- members wait to be asked -> ask by name (action 3)
```

Critique:

| Point | My recommendation |
|---|---|
| Money has no source chosen | Keep action 6 as a decision, not a plan |
| Turnout number still missing | Count the next work day as a baseline |
| Nothing says who owns each action | Name owners at your next meeting |

**You:**
1. Which two jobs are the pilot? I'd pick the ones that cost you most time.

**Decided:** no new conflict raised, so I moved on; saved and validated.

`Saved · not committed`

