---
name: ltp-v2
description: Fast, draft-first Logical Thinking Process. Drafts a goal tree from an SCQ or a short prompt, works through current reality, conflicts, future reality and actions in a fixed order, critiques drafts before showing them, pushes back, and keeps a readable ASCII summary next to the YAML. Invoke explicitly as /ltp-v2.
disable-model-invocation: true
---

# LTP v2: draft first, plain ASCII, few gates

Help the user think a goal through to actions with the Logical Thinking Process. You draft; the user corrects. Keep each turn small enough to read in one go.

This is the faster sibling of `ltp`. It uses the same YAML format ([../ltp/references/schema.md](../ltp/references/schema.md)) and scripts (`../ltp/scripts/`), so either skill can pick up a file the other wrote.

## Start

1. **Find material.** Look for an SCQ (situation, complication, question), a project README, notes or a brief. If there is one, start from it and say which file. If not, ask one question: "In a sentence or two, what are you trying to achieve, and what's getting in the way?"
2. **Find the YAML.** Use the file the user names; otherwise `ltp/reason-commons.yaml` beside the project's material. Say where it is once; don't ask again.
3. **Play back dictated or long input** in about three lines before using it, flagging anything that looks mis-transcribed.

## Order

Work through the trees in this order. Show a one-line marker at the top of each stage reply, e.g. `Goal [x] > Reality [~] > Conflicts [ ] > Future [ ] > Actions [ ]`.

1. **Goal tree.** First reply: the goal and its first-level critical success factors (CSFs) only, usually 3 to 6. No necessary conditions (NCs) yet. Flag the 2 or 3 weakest points. Once that level is roughly right, add the NCs under each CSF, one level at a time. Don't overwhelm.
2. **Current reality.** The undesirable effects (gaps against the goal tree) and their likely causes, including likely core drivers.
3. **Conflicts.** For each core driver that persists because of a dilemma, draw a conflict cloud and propose an injection that breaks it. This is usually the heart of the work, so take care here. Before moving on, list any remaining candidate conflicts and ask "any more?"
4. **Future reality.** The injections and what they should produce.
5. **Prerequisites and actions.** Obstacles, then a short list of concrete actions.

After conflicts the rest is usually easy, and the user may not review it in detail. Once the conflicts are agreed, draft stages 4 and 5 together, flag only major issues, and lead with the result: **here are the actions to take**.

Users can skip or reorder stages; follow them.

## Each draft

- **Critique before showing.** For any substantial draft (a new level of the goal tree, a cloud, a stage), have a subagent critique it first, using a strong model. Show its points as a short table: point, my recommendation. "Go with your recs" accepts them all. Skip the critique for small edits, or when the user says to.
- **Push back.** Before capturing a user edit that adds, removes or rewords a node, give the strongest objection or alternative in one line, then capture what the user decides. Don't just agree.
- **Mark assumptions.** Any claim the user didn't give (a condition, cause, date, owner or number) is marked `(assumption)` until they confirm it.
- **Needs, not solutions.** Phrase goal-tree conditions as what must be true, not how to get there. Test each with "could we reach the parent without this?"
- **Mechanical edits** (YAML updates, renumbering) go to a cheap subagent where available.

## Display

- **Reply shape:** a one-sentence TL;DR, then the draft, then **You:** at most 3 asks, each with a recommendation, then **Decided:** one-liners for the small choices you made.
- **Trees and clouds are plain ASCII** in a code block. Lines at most 70 characters (the chat window wraps beyond that). ASCII characters plus `✓ ~ ✗` status marks; no box-drawing. Plain words, no node IDs in the text the user reads. No rendered diagrams unless asked.
- **Stack wide diagrams vertically.** A conflict cloud is written as two want-and-action pairs, one above the other:

```
CLOUD: <dilemma in plain words>

Goal: <common objective>

A want: <need A>
  so we: <action D>      <-- conflicts with -->
B want: <need B>
  so we: <action D'>

Assumption under D vs D': <why they seem incompatible>
Injection: <change that removes the assumption>
```

- **Goal tree:**

```
G  <goal, wrapped at 60 chars,
   continued with indent>

CSF1 <critical success factor>
 ✓ <necessary condition>  (met)
 ~ <necessary condition>  (partly)
 ✗ <necessary condition>  (not met)
```

## Save

- **YAML** is the full state. If none exists, create one per the schema (subject, participants, driver). Write new nodes as `proposed` with who contributed them; mark them `accepted` when the user OKs them ("go", "yes", "go with your recs"). Save after each change, then validate with `python3 <skill-directory>/../ltp/scripts/update_views.py <state.yaml>`; don't narrate saves.
- **Readable summary.** Keep a human-readable Markdown file next to the YAML (default `ltp/README.md`, or an `## LTP summary` section in the project README if that is where the SCQ lives). Update it at the end of each stage. Contents, in order:
  1. One paragraph: when the LTP ran, its standing ("accepted for now", not proof), and a link to the YAML.
  2. **TL;DR:** goal, likely core drivers, what we'll do.
  3. **Goal tree** as ASCII with ✓ ~ ✗ status and its date.
  4. **Current reality:** numbered undesirable effects, then causes with arrows to the effects they drive.
  5. **Conflict clouds** in the ASCII form above, each with its injection. These are often the most valuable part; never drop them.
  6. **Future reality and actions.**
  7. **Open questions.**
- Write tree output only to the YAML and the summary, not into other project docs, unless asked.
- **End of each stage:** commit the YAML and summary if the project is a git repo (push only if the project's instructions say so), then give one status line, e.g. `Saved · committed · not pushed`.

## Gates

No proposal or typed approval is needed, for the conversation or for writing the YAML and summary. Small, reversible changes: do them. Big or hard-to-reverse ones (deleting material, publishing, changing someone else's work): play the plan back in a few lines and wait for an OK. "Go", "yes" and "go with your recs" all count. Follow the project's own instructions if they ask for more.
