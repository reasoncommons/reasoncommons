---
title: "AI and the problem of proliferating plausible reasoning"
created: 2026-10-25
date: 2026-10-25
authors: [ "Rufus Pollock", "David Joseph" ]
image: /blog/images/proliferating-plausible-reasoning-babel.jpg
---

# AI and the problem of proliferating plausible reasoning

![Pieter Bruegel the Elder, The Tower of Babel, 1563](/blog/images/proliferating-plausible-reasoning-babel.jpg)

*Pieter Bruegel the Elder, The Tower of Babel, 1563. Public domain, via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Pieter_Bruegel_the_Elder_-_The_Tower_of_Babel_(Vienna)_-_Google_Art_Project_-_edited.jpg).*

Ask an AI whether your organisation should expand into a new market and you will get a good answer: clear, structured, alert to risks, better written than most strategy memos. Ask a different model and you will get another good answer that points the other way. Rephrase the question and the first model may change its mind. Each answer is plausible. None of them tells you which one to rely on, or why.

We tried it. Two managers at a remote company asked GPT whether to bring staff back to the office three days a week: one sure it was right, one sure it was a mistake. It told the first to "run a 12-week January pilot with coordinated office days", and the second to "Keep remote as the default".[^test]

We call this **proliferating plausible reasoning**. AI has made good-looking arguments almost free to produce. What it has not made cheaper, and may have made harder, is knowing which reasoning a group is actually relying on, and why it accepts it. That second thing is what we mean by *warrant*: being able to say "this is what we're choosing, this is the reasoning we rely on, and this is why we accept it."

## The problem we already had

AI has made an old problem worse.

Any group with a goal faces many plausible directions. A company could chase this customer or that one, build this feature or fix that process. A charity could scale up or go deep. For most real choices there is a respectable case for several options, and usually someone in the room who can make it well.

Groups have never been good at choosing between plausible options in a way they can stand behind. The reasoning is scattered: in people's heads, meeting notes, chat threads, slide decks and half-remembered conversations. Decisions get made, but the *why* is rarely written down in a form anyone can inspect later. Even the slide deck may not be it: organisations routinely commission analysis they then don't use, less to make a decision than to show it was made properly.[^feldman] So the choice often goes to whoever argued most fluently, spoke last, or has the most authority. Months later, when the plan isn't working, nobody can say which assumption failed, because nobody wrote the assumptions down.

## What AI changes

AI makes this worse in three ways.

**It inflates plausibility.** A good-sounding argument used to cost someone time and skill, and that cost was a rough signal: someone had cared enough to argue this carefully. Now an argument costs a prompt. Every option on the table can arrive with a polished case for it, and so can options nobody had thought of. The supply of plausible reasoning has exploded; a group's ability to evaluate it hasn't, and the old signal no longer separates a considered position from a hunch.

**It invites trust on authority.** AI reasoning is often as good as ours, and usually too long and too quick to check line by line. The natural response is to trust it. But trust what, exactly? Different models give different answers; the same model gives different answers to differently worded questions; and models tend to argue for whatever the person asking seems to want. "The AI said so" is not a warrant. It is an appeal to an authority that disagrees with itself.

**It adds to the scatter.** AI-generated reasoning now sits alongside everything else: in someone's chat history, pasted into a doc, summarised in a message. Each person on a team may have had their own conversations with their own AI and come away with different, equally confident conclusions. The reasoning behind a group's decisions gets more fragmented, not less.

The upshot: plausible arguments are no longer scarce. Warrant is.

## What helps: reasoning you can see and agree on

The answer isn't to generate less reasoning or to stop using AI. It is to change where the reasoning lives and what a group does with it.

**Lay the reasoning out as a tree.** Rather than a wall of prose, break an argument into claims, each with the claims that support it, connected explicitly. A goal at the top; what it needs; what stands in the way; what we'll do about it. A tree is slower to write than a paragraph but much faster to *check*, because you can see exactly what rests on what.

**Make disagreement local.** Go back to the market question. Lay both AI answers out as trees and they share most of their structure: the market is growing, our product fits it, we have the people to sell into it. They split on one claim. The first assumes customers there will pay our current prices; the second assumes they won't. That turns "which AI do we trust?" into "will customers there pay our prices?", which someone can go and find out. Not every disagreement shrinks this neatly. Some come down to values or goals, and a tree won't make those go away. But it makes them visible, so the group argues about the real difference rather than about whose answer sounds better.

**Record what is accepted, and by whom.** Each claim carries its standing: proposed, accepted or disputed. Acceptance is a deliberate act by named people, not a side effect of an AI producing text. This doesn't settle who gets to decide; groups still have to agree how they agree. What it does is make the answer explicit, so a group can point to exactly what it has accepted, who accepted it, and what is still open.

**Let AI be the clerk, not the judge.** AI is very good at the part that has always made structured reasoning impractical: turning a messy conversation into a clean tree, keeping it up to date, spotting a missing step or a contradiction. That is where we want it. The judgement about which claims to accept stays with the people who have to live with the decision.

**Let it accumulate.** Because the tree persists, the next decision builds on the last one instead of starting again. When a plan fails, you can go back and see which accepted claim turned out to be wrong, and fix that, rather than relitigating everything.

## Won't AI just produce plausible trees instead?

It will, and that's fine. A polished tree for every option is still proliferating plausible reasoning, so the tree alone isn't the fix. The difference is that a tree breaks an argument into claims small enough to check one at a time, and puts acceptance in human hands claim by claim. A persuasive essay asks you to accept it whole. A tree lets you accept most of it, dispute one claim, and see exactly what follows from that. Plausibility persuades at the level of the whole; checking happens at the level of the parts.

## The opportunity

There is a hopeful version of this story. The same technology that floods us with plausible reasoning may also make structured reasoning cheap enough to use every day. Methods for laying out reasoning explicitly, from argument maps to the Theory of Constraints' Thinking Processes, have existed for decades and been used by very few. Our working hypothesis is that this is because maintaining them was too much work for the people whose reasoning most needed it. AI can do that work.

So the choice isn't between trusting AI and ignoring it. It is between letting plausible reasoning pile up in a hundred chat windows and putting it somewhere a group can examine it, argue about specific claims, and agree on what it relies on. As AI gets better at sounding right, we think the second is how groups keep making decisions they can stand behind.

We are testing this on ourselves first; [Making work add up](/blog/making-work-add-up) shows one example. If you face the same problem, [try the skill](/skills).

[^test]: GPT-6.1 Sol, 25 October 2026. Claude Sonnet 5.5 gave both managers the same verdict. Prompts and all answers, unedited: [the transcripts](/blog/proliferating-plausible-reasoning-transcripts).

[^feldman]: Martha S. Feldman and James G. March, "Information in Organizations as Signal and Symbol", *Administrative Science Quarterly* 26(2), 1981. On how such decisions fare, see Paul C. Nutt, *Why Decisions Fail* (Berrett-Koehler, 2002): of 400+ decisions by top managers, about half were not fully used two years on.
