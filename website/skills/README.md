<!-- Generated from skills/README.md; edit that canonical source and run python3 scripts/export-website.py. -->

# LTP skill

A skill that helps people and groups work out what they are trying to achieve and what to do about it, in conversation with an AI agent, and keeps that reasoning so it builds up. It works in Claude Code, Codex and other agents that support `SKILL.md` skills.

<div class="rc-cards">
<a class="rc-card" href="#start-here"><span class="rc-card-title">1 · Install</span><p>One command puts the skill in your agent.</p></a>
<a class="rc-card" href="#start-a-reasoning-conversation"><span class="rc-card-title">2 · Think together</span><p>Work a goal, problem or plan through in conversation.</p></a>
<a class="rc-card" href="#send-this-to-a-colleague"><span class="rc-card-title">Pass it on</span><p>A short message to send a colleague.</p></a>
</div>

## Start here

Install the LTP (Logical Thinking Process) skill:

```sh
npx skills add reasoncommons/reasoncommons -s ltp
```

That selects the conversational skill and asks which agents to install it into.

To install it for one agent in every project:

```sh
npx skills add reasoncommons/reasoncommons -s ltp -a claude-code -g
```

Replace `claude-code` with the agent you use. Run `npx skills add reasoncommons/reasoncommons --list` to see the available skills without installing them.

Don't want to install anything? Print a skill as a ready-to-paste prompt, or give your agent the raw file:

```sh
npx skills use reasoncommons/reasoncommons@ltp
```

```text
https://raw.githubusercontent.com/reasoncommons/reasoncommons/main/skills/ltp/SKILL.md
```

An installed copy includes the skill's helper script and references, so installation is the best option.

Previously installed `reason-commons`? Install `ltp` and remove the old skill from your agent to avoid duplicate discovery. Existing `reason-commons.yaml` working files and their history remain compatible.

## The skill

| Skill | What it does | Use it when |
|-------|--------------|-------------|
| [`ltp`](https://github.com/reasoncommons/reasoncommons/blob/main/skills/ltp/SKILL.md) | Helps people work through a goal or problem in conversation and turn it into agreed next steps, keeping who said what, what is still unfinished, what was accepted and diagrams of it | You want to think through a goal, problem, conflict, proposed change, obstacle or action with one person or a group |

## Start a reasoning conversation

After installing, open your agent in the folder where you want the working state to live and paste a prompt like this:

```text
Use the ltp skill to help me think through why customer quotes are late. My name is Alice. Keep the working state in reason-commons.yaml.
```

You can begin with a goal, a problem, a conflict, a proposed change, an obstacle or a sequence of actions. You do not need to know the method underneath or prepare a document. The agent will capture useful statements, keep contributors' names attached to their ideas, and ask one focused question at a time.

To resume later, open the same folder and say:

```text
Use the ltp skill and resume from reason-commons.yaml. Show me the most useful unfinished reasoning to work on next.
```

For a group, name people as they contribute. If speaker labels come from a transcript or voice system, give those labels to the agent; the skill does not guess who spoke.

### What the backlog is for

The backlog is the reasoning that still needs attention: an observation that has not been connected or explained, a causal link that needs testing, an assumption to examine, or an objection to resolve. It is not a second task manager and it is not a list of every possible question. The agent keeps a small active subset, preserves the rest, and prefers working through existing reasoning before asking the group for more material.

Acceptance and backlog are separate. A person can accept a useful statement or connection while leaving a question about it in the backlog. Drawing an arrow does not by itself finish the reasoning.

### How accepted reasoning becomes diagrams

New statements and connections begin as proposals. They become accepted only when a person explicitly endorses the identified item or fragment; silence and moving on do not count. A substantive objection marks the item disputed until it is resolved.

After an accepted change, the helper validates the working YAML and saves one numbered snapshot of that turn's accepted state. It then updates two SVG diagrams for each affected tree:

- The full view shows all currently accepted statements and accepted connections.
- The latest-change view highlights what was added, changed or removed, with enough neighboring context to review the change.

Proposals, disputes and backlog-only edits stay in the working YAML but do not create a new accepted snapshot. The YAML is the source of truth; the diagrams are derived views. The skill normally runs the helper and links both diagrams when accepted reasoning changes. Python with PyYAML is required; the current helper draws its SVG directly without Graphviz or a JavaScript renderer; see [`ltp/references/views.md`](https://github.com/reasoncommons/reasoncommons/blob/main/skills/ltp/references/views.md) for details.

### See your commons in the browser

To read the whole thing at once, ask:

```text
Show me our commons in the browser.
```

The agent turns the working file into pages like the [demonstration commons](/demos/reason-commons-in-use/index.html): an overview, a map, a page for each question and every statement with who contributed it, who accepted it and what is still open. Accepted, proposed and disputed reasoning are all there, each marked. The pages stay on your computer, next to the working file; nothing is published or sent anywhere. Ask again after the reasoning changes to see the new version.

## Send this to a colleague

```text
Try the LTP skill from Reason Commons to think through a goal, problem, conflict or plan together. Install it with `npx skills add reasoncommons/reasoncommons -s ltp`, then ask your agent: "Use the ltp skill to help me think through [topic]. My name is [name]." The agent keeps unfinished reasoning in a backlog and turns explicitly accepted reasoning into full and latest-change diagrams. More: https://reasoncommons.com/skills
```

## For contributors

The explainer-writing skill has moved to its own repository: [Scrollable Explainer](https://github.com/rufuspollock/scrollable-explainer). Its research, worked examples and installation instructions live there. It is installed separately and is not bundled with the Reason Commons skill.

## For maintainers

- Skills live at top level so they work outside one agent runtime. Link the skills you use into `.claude/skills/` for Claude Code or `.agents/skills/` for Codex. This repository tracks the Codex link for `ltp`.
- `ltp-project` and `ltp-visualize` were retired on 2026-10-21 with the Reason Commons app whose import format they served. `tree-gen`, `annotation-mapping`, `contribution-proposals`, `goal-alignment` and `project-ltp` were retired earlier. All remain in Git history.

## Canonical packages and public guide

Installable packages and their helpers/tests remain under `skills/`. The public `/skills` guide is exported from this file by `python3 scripts/export-website.py`; its package links point to canonical repository sources. Finished website content lives under `website/`.
