# Gandhi 2.0 workspace (prototype)

Another way to read the [Gandhi 2.0 commons](../../../../website/demos/reason-commons-in-use/gandhi-2-0/index.html), published at [`/demos/gandhi-2-0-workspace/index.html`](../../../../website/demos/gandhi-2-0-workspace/index.html). It sits beside the commons pages as an alternative and changes none of them.

## What it tries

The commons pages give each of the six questions its own diagram. This prototype leads with one path instead: the goal, a problem, a change meant to address it, a first step and an action. Each stop can be swapped for any other the record links to the stop above it. From any statement you can trace what leads to it and what follows, one connection at a time. A side panel keeps the exact wording, who proposed and accepted it, its sources, its assumptions and its open questions in view. Notes drafted on a statement stay in the reader's browser and are labelled as not submitted.

It adds nothing to the record. Every card, connection and option comes from the published `reasoning.json`, and where the record has no connection the page says so.

## Files

| File | What it holds |
| --- | --- |
| `model.js` | Reads a release into statements, connections, references between questions and open questions. No DOM; runs in the page and under Node. |
| `app.js` | The views, the side panel, routing on the URL hash, search and local notes. |
| `style.css`, `template.html` | The page's look and shell. |
| `build.py` | Assembles one self-contained page with the release embedded. |
| `test.cjs` | Checks the model, and optionally rendered pages, against the release. |

## Build and check

From the repository root:

```sh
python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py
python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py --check
node apps/reasoning-demo/prototypes/gandhi-2-0-workspace/test.cjs
```

Rebuild after the Gandhi 2.0 release changes, or the page will show the earlier release; `--check` and the first test catch that. To check rendered views as well, dump them with headless Chrome and pass the files to the test:

```sh
chrome --headless=new --virtual-time-budget=3000 --dump-dom "file://$PWD/website/demos/gandhi-2-0-workspace/index.html#focus--g2-r-u03" > /tmp/focus.html
node apps/reasoning-demo/prototypes/gandhi-2-0-workspace/test.cjs /tmp/focus.html
```

Views are addressed by hash: `#start`, `#path--<problem>--<change>--<step>--<action>`, `#focus--<statement>`, `#q--goal|way|conflict|change|first|who`, `#open` and `#notes`.

## Not done

- No test with readers, so whether a newcomer grasps the argument faster is unknown.
- No screen-reader pass.
- No whole-map picture, no side-by-side comparison of two branches and no "what if" view.
- It reads only Gandhi 2.0. The model is general, but the page's opening copy and the build's source path are not.
- Fonts load from Google Fonts, unlike the rest of the demo site, which hosts its own.
