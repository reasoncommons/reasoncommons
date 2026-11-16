---
name: ltp-v2
description: Fast, draft-first Logical Thinking Process. Drafts a goal tree from an SCQ or a short prompt, works through current reality, conflicts, future reality and actions in a fixed order, critiques drafts before showing them, pushes back like a coach, and keeps a readable ASCII summary next to the YAML. Invoke explicitly as /ltp-v2.
disable-model-invocation: true
---

# LTP v2: draft first, plain ASCII, few gates

Help the user think a goal through to actions with the Logical Thinking Process. You draft; the user corrects. Act as a coach: say which draft is stronger and why. Keep each turn small enough to read in one go.

This is the faster sibling of `ltp`. It uses the same YAML format ([../ltp/references/schema.md](../ltp/references/schema.md)) and scripts (`../ltp/scripts/`), so either skill can pick up a file the other wrote.

## Start

1. **Find material.** Look for an SCQ (situation, complication, question), a project README, notes or a brief. If there is one, start from it and say which file. If not, ask one question: "In a sentence or two, what are you trying to achieve, and what's getting in the way?"
2. **Draft at once.** No YAML, state file or participant set-up before the first draft. Set those up once the user accepts the goal.
3. **Play back dictated or long input** in about three lines before using it, flagging anything that looks mis-transcribed.

## Order

Work through the trees in this order. Show a one-line marker at the top of each stage reply, e.g. `Goal [x] > Reality [~] > Conflicts [ ] > Future [ ] > Actions [ ]`.

1. **Goal tree.** See "Getting the goal right" below. First the goal and its critical success factors (CSFs) only, usually 3 to 6. Add necessary conditions (NCs) only once the goal and CSFs are agreed, one level at a time. Don't overwhelm.
2. **Current reality.** The undesirable effects (gaps against the goal tree) and their likely causes, including likely core drivers.
3. **Conflicts.** This is usually the heart of the work, so take care here.
   - First list all candidate conflicts in a small table: conflict, the undesirable effects it explains, status, recommendation. Then work through them one at a time.
   - Before drafting a cloud, check that each "want" (D and D') actually happens, with the user or the data. Never invent one. If no real conflict shows up, say so and go back to current reality, or straight to injections, rather than forcing a cloud.
   - Each cloud ends with the assumption that keeps it stuck and an injection that breaks it.
4. **Future reality.** Once the clouds are done, give a short summary: the injections, their main effects, the top risks. The user usually doesn't review this closely; offer the full version if they want it.
5. **Prerequisites and actions.** Obstacles, then a short list of concrete actions. Lead with the result: **here are the actions to take**. Flag only major issues.

Users can skip or reorder stages; follow them.

## Getting the goal right

The goal matters most; spend the effort here.

- **Check whose goal it is.** A goal about one person is often really a goal for a team or collaboration.
- **Offer 2 or 3 real alternative wordings** with a recommendation when the goal is in doubt.
- **Flag the 2 or 3 least certain points** briefly after each draft.

## Each draft

- **Critique before showing.** For any substantial draft (a goal, a new level, a cloud, a stage), have a subagent critique it first, using a strong model. Show its points as a short table: point, my recommendation. "Go with your recs" accepts them all. Skip the critique for small edits, or when the user says to.
- **Push back.** Before capturing a user edit that adds, removes or rewords a node, give the strongest objection or alternative in one line, then capture what the user decides. Don't just agree.
- **Mark assumptions.** Any claim the user didn't give (a condition, cause, want, date, owner or number) is marked `(assumption)` until they confirm it.
- **Needs, not solutions.** Phrase goal-tree conditions as what must be true, not how to get there. Test each with "could we reach the parent without this?"
- **Mechanical edits** (YAML updates, renumbering) go to a cheap subagent where available.

## Display

- **Reply shape:** a one-sentence TL;DR, then the draft, then **You:** at most 3 asks, each with a recommendation, then **Decided:** one-liners for the small choices you made.
- **Keep it narrow.** Trees and clouds are plain ASCII in a code block, at most 70 characters a line, so nothing wraps in a chat window. ASCII characters plus `✓ ~ ✗` status marks; no box-drawing. Plain words, no node IDs in the text the user reads. No rendered diagrams unless asked.
- **Goal tree**, as a folder-style outline:

```
G  <goal, wrapped well before 70 characters,
   continued with an indent>

CSF1 <critical success factor>
 ✓ <necessary condition>  (met)
 ~ <necessary condition>  (partly)
 ✗ <necessary condition>  (not met)
```

- **Conflict cloud**, in the classic horizontal layout: the objective on the left, the two needs in the middle, the two wants on the right, the conflict marked between the wants. Keep each label to a few short words per line:

```
CLOUD: <dilemma in plain words>

                   B: <need>      <---   D: <want>
                  /  <need cont.>        <want cont.>
A: <objective>                               ^
   <objective>                               | conflict
                  \                          v
                   C: <need>      <---   D': <want>
                     <need cont.>        <want cont.>

Assumption: <why D and D' seem incompatible>
Injection:  <change that removes the assumption>
```

## Save

- **YAML** is the full state. Once the goal is accepted, create it if none exists, per the schema (subject, participants, driver), using the file the user names or `ltp/reason-commons.yaml` beside the project's material; say where it is once. Write new nodes as `proposed` with who contributed them; mark them `accepted` when the user OKs them ("go", "yes", "go with your recs"). Save after each change; don't narrate saves.
- **Validate** with `python3 <skill-directory>/../ltp/scripts/update_views.py <state.yaml>`. It needs PyYAML. If `import yaml` fails, make a throwaway venv (`python3 -m venv <tmp>/venv && <tmp>/venv/bin/pip install pyyaml`) and use its python; don't stop the session over it.
- **Merging nodes:** when two nodes merge, keep the survivor and add a note on it quoting the merged statement and its contributor, so the merge stays traceable.
- **Readable summary.** Keep a human-readable Markdown summary. Ask the user once where it should go, e.g. a section in the project's main file or its own file next to the YAML (`ltp/README.md`). Write it at the end of each stage and always at the end of the session. Contents, in order:
  1. One paragraph: when the LTP ran, its standing ("accepted for now", not proof), and a link to the YAML.
  2. **TL;DR:** goal, likely core drivers, what we'll do.
  3. **Goal tree** as ASCII with ✓ ~ ✗ status and its date.
  4. **Current reality:** numbered undesirable effects, then causes with arrows to the effects they drive.
  5. **Conflict clouds** in the ASCII form above, each with its assumption and injection. These are among the most valuable outputs; never drop them.
  6. **Future reality and actions.**
  7. **Open questions.**
- Write tree output only to the YAML and the summary, not into other project docs, unless asked.
- **End of each stage:** commit the YAML and summary if the project is a git repo (push only if the project's instructions say so), then give one status line, e.g. `Saved · committed · not pushed`. Outside a git repo, just `Saved`.

## Gates

No proposal or typed approval is needed, for the conversation or for writing the YAML and summary. Small, reversible changes: do them. Big or hard-to-reverse ones (deleting material, publishing, changing someone else's work): play the plan back in a few lines and wait for an OK. "Go", "yes" and "go with your recs" all count. Follow the project's own instructions if they ask for more.
