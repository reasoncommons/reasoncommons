---
title: Glossary
description: Plain-language definitions of the Logical Thinking Process terms and acronyms used across Reason Commons — the six trees, the kinds of statement in them, and the method's checks.
---

# Glossary

The [Logical Thinking Process](/ltp) comes with a lot of vocabulary and even more acronyms. You don't need any of it to use Reason Commons, but you will meet it in the guide, in the books, and in what the AI skills write. This page explains each term in a sentence or two. The six trees each come with a tiny sketch, all using the same example — a support team whose customers wait a week to hear back about refunds. Every term has its own heading, so you can link straight to it — `reasoncommons.com/glossary#current-reality-tree`.

## Acronyms

| Acronym | Stands for |
|---|---|
| CLR | [Categories of Legitimate Reservation](#categories-of-legitimate-reservation) |
| CRT | [Current Reality Tree](#current-reality-tree) |
| CSF | [Critical Success Factor](#critical-success-factor) |
| DE | [Desired Effect](#desired-effect) |
| EC | [Evaporating Cloud](#evaporating-cloud) |
| FRT | [Future Reality Tree](#future-reality-tree) |
| IO | [Intermediate Objective](#intermediate-objective) — or, in "IO Map", the [Goal Tree](#goal-tree) |
| LTP | [Logical Thinking Process](#logical-thinking-process) |
| NBR | [Negative Branch Reservation](#negative-branch) |
| NC | [Necessary Condition](#necessary-condition) |
| PRT | [Prerequisite Tree](#prerequisite-tree) |
| TOC | [Theory of Constraints](#theory-of-constraints) |
| TT, TRT | [Transition Tree](#transition-tree) |
| UDE | [Undesirable Effect](#undesirable-effect) |

## The method

### Theory of Constraints

TOC. A management approach developed by Eliyahu Goldratt from the 1980s. Its starting point: any system's performance is limited by a small number of constraints, so improving anything other than the constraint is mostly wasted effort. The Logical Thinking Process is its toolkit for finding and removing constraints that are policies and beliefs rather than machines.

### Logical Thinking Process

LTP. A set of six linked diagrams — the [trees](#the-six-trees) — for getting from "here is our goal and things are not going well" to "here is what we do on Monday", with every step argued in cause and effect. It began as Eliyahu Goldratt's *Thinking Processes* (five trees); H. William Dettmer codified it, added the [Goal Tree](#goal-tree) and gave it this name. See the [guide](/ltp) for an introduction.

### Constraint

The one thing that most limits a system from getting more of its goal. In the LTP it is usually a policy, habit or belief rather than a physical bottleneck, and the [Current Reality Tree](#current-reality-tree) is how you find it.

### Sufficiency logic

"If A, then B." Reading a link as *A is enough to cause B*. Used in the [Current Reality Tree](#current-reality-tree), [Future Reality Tree](#future-reality-tree) and [Transition Tree](#transition-tree). When one cause isn't enough on its own, several are joined with an **AND** (often drawn as an ellipse across the arrows).

### Necessity logic

"In order to have B, we must have A." Reading a link as *B cannot happen without A* — A is required, but not necessarily enough. Used in the [Goal Tree](#goal-tree), [Evaporating Cloud](#evaporating-cloud) and [Prerequisite Tree](#prerequisite-tree).

### Categories of Legitimate Reservation

CLR. The eight standard ways to challenge a link or a statement in a tree: clarity (do I understand it?), entity existence (is it actually true?), causality existence (does A really cause B?), cause insufficiency (is something else also needed?), additional cause (could something else cause B too?), cause–effect reversal (is it the other way round?), predicted effect existence (if A were true, what else would we see?), and tautology (is the effect being used as evidence of its own cause?). They are how a tree gets checked rather than just drawn. They were designed for the sufficiency trees and apply only loosely to the necessity ones.

### Negative branch

A chain of cause and effect showing that a proposed change also produces something bad. Raising one is a **Negative Branch Reservation** (NBR). It is built in the [Future Reality Tree](#future-reality-tree) and resolved with a further [injection](#injection) — the method's way of saying "yes, but…" constructively.

### Entity

Dettmer's word for one box in a tree — a single statement, written as a complete sentence.

### Sphere of influence

What you or your team can control directly (Dettmer's **span of control**) plus what you can persuade others to change (**sphere of influence**). It decides which [root causes](#root-cause) are worth acting on.

### Assumption

The unstated belief behind a link — why someone thinks A leads to B, or that B requires A. Surfacing assumptions is most of the work in an [Evaporating Cloud](#evaporating-cloud): a conflict breaks when one of them turns out to be false.

## The six trees

### Goal Tree

Also the **Intermediate Objectives Map** (IO Map). Shows what success is: the [goal](#goal) at the top, the [critical success factors](#critical-success-factor) beneath it, and the [necessary conditions](#necessary-condition) beneath those. Read with [necessity logic](#necessity-logic). It is the benchmark everything else is measured against. The app calls this view **goal**.

```text
               GOAL
          happy customers
            ▲         ▲
           CSF       CSF
     fast replies   right answers
       ▲      ▲
      NC      NC
   enough   clear
   staff    triage

 arrows point up; read down:
 "to have X we must have Y"
```

### Current Reality Tree

CRT. Explains why things are the way they are: starts from the [undesirable effects](#undesirable-effect) people can see and traces them back, through [intermediate causes](#intermediate-cause), to the [root causes](#root-cause). Read with [sufficiency logic](#sufficiency-logic). The app calls this view **problem**; files call it `current_reality`.

```text
 UDE                 UDE
 customers wait      customers
 a week for reply    chase or quit
     ▲                  ▲
     └────────┬─────────┘
     backlog keeps growing
              ▲
      ┌──────AND──────┐
  volume         every refund
  doubled        reply needs a
                 manager's OK
  root cause:    CRITICAL root
  can't change   cause: a policy
                 we can change

 arrows point up; read up:
 "if X, then Y"
```

### Evaporating Cloud

EC, also the **conflict cloud** or **conflict resolution diagram**. A five-box diagram of a dilemma: a shared [objective](#objective), two [requirements](#requirement) it depends on, and two [prerequisites](#prerequisite) — the actions each requirement seems to demand — which conflict. Each arrow hides [assumptions](#assumption); finding a false one and an [injection](#injection) that replaces it makes the conflict "evaporate". The app calls this view **conflict**.

```text
         ┌──── B ◄──── D
   A ◄───┤             ↕ conflict
         └──── C ◄──── D′

 A   objective     happy customers
 B   requirement   fast replies
 C   requirement   right answers
 D   prerequisite  skip sign-off
 D′  prerequisite  keep sign-off

 arrows point to A; read left to
 right: "to have A we need B;
 to have B we must do D"

 assumption under C ◄── D′: only a
 manager can catch a wrong answer
 (false for small refunds)

 injection: sign-off only for
 refunds over £100
```

Goldratt labels the boxes A–D′ as here; Dettmer uses O, R1, R2, P1, P2.

### Future Reality Tree

FRT. Tests a proposed change before you make it: starts from one or more [injections](#injection) and follows their effects forward to the [desired effects](#desired-effect), checking along the way for [negative branches](#negative-branch). Read with [sufficiency logic](#sufficiency-logic). The app calls this view **solution**; files call it `future_reality`.

```text
 DE                  negative
 replies within      branch: a
 a day               wrong refund
     ▲               slips through
 backlog shrinks          ▲
     ▲                    │
 INJECTION ───────────────┘
 sign-off only for refunds
 over £100

 arrows point up; read up:
 "if we do X, then Y"
 trim the branch with a second
 injection: spot-check 5% of replies
```

### Prerequisite Tree

PRT. Plans how to make the change real. Starting from the [objective](#objective) — usually an injection — it lists the [obstacles](#obstacle) in the way and, for each, an [intermediate objective](#intermediate-objective) that overcomes it, plus any plain steps that face no obstacle, and puts them all in order. Read with [necessity logic](#necessity-logic). The app calls this view **implement**; files call it `prerequisite`.

```text
 OBJECTIVE  sign-off only for
            refunds over £100
     ▲
 IO  managers agree the £100 rule
     ▲
 IO  spot-checks running
     [overcomes: managers
      fear mistakes]
     ▲
 IO  team lead frees 2 hours a week
     [overcomes: no time
      for checking]

 do it from the bottom up; an IO
 with no obstacle beside it is
 just a necessary step
```

### Transition Tree

TT, sometimes TRT. The step-by-step action plan. Each step joins the current reality, the need for change and an action, which together produce an expected effect; that effect becomes the reality for the next step up. Read with [sufficiency logic](#sufficiency-logic). Dettmer himself now suggests skipping it for a more detailed Prerequisite Tree plus ordinary project planning. The app calls this view **task**; files call it `transition`.

```text
       effect: small refunds go
       out the same day
                ▲
     ┌─────────AND─────────┐
 reality      need       ACTION
 every        replies    publish
 refund       out        the £100
 waits for    within     rule
 a manager    a day

 arrows point up; the next step
 sits above, starting from this
 step's effect
```

## What goes in the trees

### Goal

The single outcome the whole system exists to achieve — the top of the [Goal Tree](#goal-tree).

### Critical Success Factor

CSF. One of a handful of results that must all be true for the [goal](#goal) to hold. Remove any one and the goal fails.

### Necessary Condition

NC. Something a [critical success factor](#critical-success-factor) (or another necessary condition) depends on. The lower levels of the [Goal Tree](#goal-tree).

### Undesirable Effect

UDE (say "oody"). Something happening now that nobody wants, stated as a fact rather than a complaint — "customers wait more than a week for a reply", not "support is bad". A UDE is judged against the [Goal Tree](#goal-tree): it is the opposite of something success needs, and it is about the system, not one person's frustration. The visible symptoms a [Current Reality Tree](#current-reality-tree) sets out to explain. A [Future Reality Tree](#future-reality-tree) may also show new UDEs a change would cause.

### Intermediate cause

A link in the middle of a causal chain in the [Current Reality Tree](#current-reality-tree): it causes something, and is itself caused by something further down.

### Root cause

A cause at the bottom of the [Current Reality Tree](#current-reality-tree) — arrows go out of it, none come in. It isn't necessarily bad, and it may be something you can't change, like "volume doubled". The ones you can change are candidates for [critical root cause](#critical-root-cause).

### Critical root cause

A root cause that is a policy, practice or habit someone within your [sphere of influence](#sphere-of-influence) can change, and that drives a large share of the [undesirable effects](#undesirable-effect). Expect a few of them, not one. Fixing them is where the leverage is.

### Core problem

Goldratt's older idea that one root cause lies behind most of the undesirable effects. Dettmer found this rarely holds and talks about [critical root causes](#critical-root-cause) instead; you will still meet "core problem" in older books.

### Objective

The thing at the top that the rest serves. In an [Evaporating Cloud](#evaporating-cloud) it is box A, the aim both sides share. In a [Prerequisite Tree](#prerequisite-tree) it is what you are trying to achieve, usually an [injection](#injection).

### Requirement

In an [Evaporating Cloud](#evaporating-cloud), one of two needs that the shared objective depends on — often two of the [critical success factors](#critical-success-factor) from the Goal Tree. Both are legitimate; the conflict is not between them but between the actions they seem to demand.

### Prerequisite

In an [Evaporating Cloud](#evaporating-cloud), the action one side thinks its [requirement](#requirement) demands. The two prerequisites are what actually conflict — "skip manager sign-off" versus "keep manager sign-off". (Not to be confused with the [Prerequisite Tree](#prerequisite-tree).)

### Injection

A change you introduce into the system — a new policy, practice or condition — to break a conflict or produce a better future. Injections come out of the [Evaporating Cloud](#evaporating-cloud) and are tested in the [Future Reality Tree](#future-reality-tree).

### Desired Effect

DE. What becomes true once the [injections](#injection) are in place — usually the mirror image of an [undesirable effect](#undesirable-effect). The top of a [Future Reality Tree](#future-reality-tree).

### Obstacle

Something that currently stops you reaching an [objective](#objective) or an [intermediate objective](#intermediate-objective) in the [Prerequisite Tree](#prerequisite-tree). Word it as a condition that exists ("managers fear mistakes"), not as a need ("we need manager buy-in").

### Intermediate Objective

IO. A milestone in the [Prerequisite Tree](#prerequisite-tree), usually one that overcomes a specific [obstacle](#obstacle). (Confusingly, Dettmer also uses "intermediate objectives" for the whole [Goal Tree](#goal-tree) — the IO Map. Context usually tells you which.)

### Transition step

One step of a [Transition Tree](#transition-tree): the **existing reality**, the **need** to change it, the **action** someone takes, and the **expected effect**. Project files store them as four roles, one per part.

## Reason Commons terms

### Claim tree

A top-level claim or question broken down into sub-claims, which are broken down in turn. It is a stable scaffold: documents come and go, but the tree stays, and evidence accumulates against it.

```text
 Does remote work raise productivity?
 ├── For whom?
 │   ├── ICs vs managers?
 │   │   └── "quote from a study"
 │   │        → link to source
 │   └── Deep vs collaborative work?
 ├── For what tasks?
 └── Over what time horizon?

 "…" → source  =  an annotation
```

### Annotation

A fragment quoted from a source document — a paper, a post, a comment thread — attached to the node in a [claim tree](#claim-tree) it bears on, with a link back to where it came from.

### Observation

A statement about the system whose purpose in the argument isn't yet clear. The honest label for a sentence that is clearly relevant but that you can't yet place as a cause, effect or condition.

### Evidence

A measurement or source cited to back up or challenge a statement in a tree.

### View

What a Reason Commons project file calls each of the six trees. A project holds all six views over one shared set of statements, so the same statement can appear in more than one.

### Role

What a statement is doing in a given view — a [goal](#goal), an [undesirable effect](#undesirable-effect), an [injection](#injection), and so on. The full list the ltp skill uses is in [its schema](https://github.com/reasoncommons/reasoncommons/blob/main/skills/ltp/references/schema.md).

## Read more

The [guide](/ltp) walks through a complete worked example, and the [reading list](/library) has the books — Dettmer's *The Logical Thinking Process* is the reference most of these definitions follow.
