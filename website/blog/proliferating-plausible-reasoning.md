---
title: "AI and the problem of proliferating plausible reasoning"
created: 2026-10-25
date: 2026-10-25
authors: [ "Rufus Pollock", "David Joseph" ]
---

# AI and the problem of proliferating plausible reasoning

Picture a 30-person software company, fully remote since 2020. Some of the leadership want everyone back in an office three days a week. One manager is sure it's the right call: junior staff aren't learning, the culture is thinning out. Another is sure it's a mistake: people joined for remote work, and the best of them will leave. Before the leadership meeting, each of them asks an AI.

We ran exactly this test with two leading models, OpenAI's GPT and Anthropic's Claude.[^test] GPT told the office advocate to "run a 12-week January pilot with coordinated office days". It told the remote advocate to "Keep remote as the default". Claude gave both managers the same verdict, but not the same treatment: the remote advocate heard "Your reasoning is sound", while the office advocate was told that mentoring having "clearly suffered" was "a belief until you test it". Ask a different model, get a different answer; ask the same model from the other side, and the answer bends toward you.

Every one of those answers is careful, balanced and sensible. That is the problem. Each manager walks into the meeting with a thoughtful, independent-sounding second opinion, and nobody in the room can see how much of it came from the question.

We call this **proliferating plausible reasoning**. AI has made good arguments for almost anything nearly free to produce. Plausible arguments are no longer scarce. What is scarce is *warrant*: being able to say, as a group, "this is what we're choosing, this is the reasoning we rely on, and this is why we accept it."

## The problem we already had

Any group with a goal faces many plausible directions. A company could chase this customer or that one, build this feature or fix that process. A charity could scale up or go deep. For most real choices there is a respectable case for several options, and someone in the room who can make it well.

Groups have never been good at choosing between plausible options in a way they can stand behind. More than forty years ago, Martha Feldman and James March noticed something odd about organisations: they gather far more information than they use, ask for analysis and then ignore it, and assemble the justification after the decision is taken. The analysis is real, but its job is often to show that the decision was made properly and to defend it later, not to make it.[^feldman] The reasons in the deck are not necessarily the reasons for the decision.

Paul Nutt collected more than 400 major decisions made by top managers over two decades. About half were not fully used two years later, and a third were never used at all. In 60% of cases managers carried the decision by persuasion or power, which worked about one time in three. Involving the people affected, so they could see and shape the reasoning, worked more than 80% of the time.[^nutt]

Put those together and you get the familiar picture. The official reasoning lives in the slides; the real reasoning lives in people's heads, corridor conversations and chat threads; and decisions are carried by whoever pushes hardest. When the plan fails, nobody can say which assumption was wrong, because the assumptions that mattered were never written down.

## What AI changes

AI pours fuel on all of this, in three ways.

**It inflates plausibility.** A good argument used to cost time and skill, and that cost was a signal: someone cared enough to make the case properly. Now a case costs a prompt. Every option arrives with a polished rationale, and so do options nobody had considered. The supply of plausible reasoning has exploded. Our ability to evaluate it has not.

**It launders preference into authority.** AI reasoning is often as good as ours, and too long to check line by line, so we trust it. But it bends toward whoever is asking, different models answer differently, and the same model answers differently to a reworded question. "The AI agrees with me" sounds like independent support. It is an echo with a confident voice.

**It multiplies the scatter.** Every person on a team now has private conversations with their own AI and comes away with their own well-argued conclusions. The reasoning behind a group's decisions becomes more fragmented, not less, and each fragment is more persuasive than before.

The arguments got cheaper. The warrant didn't.

## What helps: reasoning you can see and agree on

The answer isn't to generate less reasoning or to stop using AI. It is to change where the reasoning lives and what a group does with it.

**Lay the reasoning out as a tree.** Instead of a wall of prose, break an argument into claims, each with the claims that support it, connected explicitly: a goal at the top, what it needs, what stands in the way, what we'll do about it. A tree is slower to write than a paragraph but much faster to *check*, because you can see exactly what rests on what.

**Make disagreement local.** Go back to the two managers. Lay their positions out as trees and most of the structure is shared: both want junior staff to grow, both want to keep good people, both care about the culture. They split on two claims. One: mentoring has suffered *because* we are remote. Two: a mandate would cost us our best people. Both can be checked. Ask the juniors; look at how long new hires take to get up to speed; ask staff, confidentially, what they would do. "Whose AI do we believe?" becomes "what do our juniors and our senior engineers actually say?" Not every disagreement shrinks this neatly; some are about values, and a tree won't dissolve those. But it shows them for what they are, so the group argues about the real difference instead of about whose answer sounds better.

**Record what is accepted, and by whom.** Each claim carries its standing: proposed, accepted or disputed. Acceptance is a deliberate act by named people, never a side effect of an AI producing text. The group can point to exactly what it has accepted, who accepted it, and what is still open. And because the record persists, the next decision builds on the last one; when a plan fails, you can see which accepted claim turned out to be wrong and fix that, rather than relitigating everything.

**Let AI be the clerk, not the judge.** AI is very good at the part that has always made structured reasoning impractical: turning a messy conversation into a clean tree, keeping it current, spotting a missing step or a contradiction. That is where we want it. The judgement about which claims to accept stays with the people who have to live with the decision.

## Won't AI just produce plausible trees instead?

It will, and that's fine. A polished tree for every option is still proliferating plausible reasoning, so the tree alone isn't the fix. The difference is what a tree lets you do with it. A persuasive essay asks you to accept it whole. A tree lets you accept most of it, dispute one claim, and see exactly what follows. Plausibility works on the whole. Checking works on the parts.

## The opportunity

There is a hopeful twist. The same technology that floods us with plausible reasoning may also make structured reasoning cheap enough to use every day. Ways of laying out reasoning explicitly, from argument maps to the Theory of Constraints' Thinking Processes, have existed for decades and been used by very few. We think that is because keeping them up was too much work for the people whose reasoning most needed it. AI can do that work.

So the choice isn't between trusting AI and ignoring it. It is between letting plausible reasoning pile up in a hundred private chat windows, and putting it somewhere a group can see it, argue about specific claims, and agree on what it relies on. As AI gets better at sounding right, only the second lets a group make decisions it can stand behind.

*We are testing this on ourselves first: [Making work add up](/blog/making-work-add-up) shows how. To try it on a decision of your own, [get the skill](/skills).*

[^test]: Claude Sonnet 5.5 and GPT-6.1 Sol, run on 25 October 2026 with no personal instructions or project files, two runs per framing per model; each prompt asked for a recommendation in under 120 words. Prompts and all eight answers, unedited: [the transcripts](/blog/proliferating-plausible-reasoning-transcripts).

[^feldman]: Martha S. Feldman and James G. March, "Information in Organizations as Signal and Symbol", *Administrative Science Quarterly* 26(2), 1981.

[^nutt]: Paul C. Nutt, *Why Decisions Fail: Avoiding the Blunders and Traps That Lead to Debacles* (Berrett-Koehler, 2002). Figures from Ohio State University's [summary of the study](https://news.osu.edu/half-of-business-decisions-fail-because-of-managements-blunders-new-study-finds/).
