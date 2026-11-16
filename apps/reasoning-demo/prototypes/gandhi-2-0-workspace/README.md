# Gandhi 2.0 workspace (prototype)

Another way to read the [Gandhi 2.0 commons](../../../../website/demos/reason-commons-in-use/gandhi-2-0/index.html), published at [`/demos/gandhi-2-0-workspace/index.html`](../../../../website/demos/gandhi-2-0-workspace/index.html). It sits beside the commons pages as an alternative and changes none of them.

## What it tries

The commons pages give each of the six questions its own diagram. This prototype answers one question first: given the goal, where do we start, and why there? Its opening screen shows the goal, the action to start with and the reason that action comes first. Four lines beneath say how the action serves the goal: the step it puts into practice, the change that step serves, the problem the change is meant to address, and the predicted route from the change to the goal. Each line opens in place to show the full wording, the alternatives the record links there, and the obstacle, needs, risks or connections behind it. Any of them can be swapped for another the record links to the line above.

Every view follows the same rule: the answer in the first screen, the support one click away. The start page opens on the same goal-and-action block. Each question page lists its parts by title and opens them in place. The statement page shows the statement first, then what leads to it and what follows, one connection at a time. A side panel keeps the exact wording, who proposed and accepted it, its sources, its assumptions and its open questions in view. Notes drafted on a statement stay in the reader's browser and are labelled as not submitted.

It adds nothing to the record. Every card, connection and option comes from the published `reasoning.json`, and where the record has no connection the page says so.

## Which action comes first

The record holds no judgement of which action matters most, so the page does not claim one. It reads the order from recorded connections only (`actionOrder` in `model.js`). An action comes after another when it uses what the other produces, or follows it by a "comes before" connection. Where the action tree says nothing about two actions, the steps decide: an action comes after one whose step its own step needs. A pair the record orders both ways is left unordered. The starting action is one that nothing comes before; among several, the one the most others come after. With no order recorded, the first action listed stands in and the page says the record does not say which comes first.

On Gandhi 2.0 the action tree records no order, and the steps put "Select one willing host and one function" before the other seven. The path the release itself singles out ends at a later action; its link still opens, marked as a later action with a way back to the starting one.

## Files

| File | What it holds |
| --- | --- |
| `model.js` | Reads a release into statements, connections, references between questions and open questions. No DOM; runs in the page and under Node. |
| `app.js` | The views, the side panel, routing on the URL hash, search and local notes. |
| `style.css`, `template.html` | The page's look and shell. |
| `build.py` | Assembles the Gandhi 2.0 page with the release embedded, and refreshes the styles and browser code of each shared workspace page it lists. |
| `test.cjs` | Checks the model, and optionally rendered pages, against the release. |

## Build and check

From the repository root:

```sh
python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py
python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py --check
node apps/reasoning-demo/prototypes/gandhi-2-0-workspace/test.cjs
```

Rebuild after the Gandhi 2.0 release changes, or the page will show the earlier release; `--check` and the first test catch that. The build also refreshes the [TDI workspace](../../../../website/demos/tdi-cybernetic-futures-workspace/index.html), keeping its own shell and embedded record; a page with `"view": "shared"` reads like the private workspace and takes its "Full record" link from `record_href`. Then run `python3 scripts/export-skill-viewer.py` so the skill's private workspace gets the same code. To check rendered views as well, dump them with headless Chrome and pass the files to the test:

```sh
chrome --headless=new --virtual-time-budget=3000 --dump-dom "file://$PWD/website/demos/gandhi-2-0-workspace/index.html#focus--g2-r-u03" > /tmp/focus.html
node apps/reasoning-demo/prototypes/gandhi-2-0-workspace/test.cjs /tmp/focus.html
```

Views are addressed by hash: `#start`, `#path` (the starting action) or `#path--<problem>--<change>--<step>--<action>`, `#focus--<statement>`, `#q--goal|way|conflict|change|first|who`, `#open` and `#notes`.

## Not done

- No test with readers, so whether a newcomer grasps the argument faster is unknown.
- No screen-reader pass.
- No whole-map picture, no side-by-side comparison of two branches and no "what if" view.
- The public page reads only Gandhi 2.0. The model is general, and the skill's private workspace and the TDI page use it, but the public page's opening copy and the build's source path are not.
- Fonts load from Google Fonts, unlike the rest of the demo site, which hosts its own.
