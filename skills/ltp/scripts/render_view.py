#!/usr/bin/env python3
"""Render one tree at one standing as an in-chat view, straight from the YAML.

  render_view.py STATE --counts                         view-menu counts per tree
  render_view.py STATE --tree T --standing S            pan-and-zoom widget HTML
  render_view.py STATE --tree T --standing S --format markdown
                                                        complete native Mermaid response
  render_view.py STATE --tree T --standing S --format mermaid|text
  render_view.py --wrap --heading "LAST CHANGE: PROPOSED · …" < diagram.mmd
                                                        any Mermaid source in the frame

The widget output is complete: pass it unchanged to the host's widget tool.
Markdown output is complete too: return it unchanged on a native Mermaid surface.
Counts, topology, standing markers and the "Not shown" line come from the
state, so the conversation never has to count or lay out nodes by hand.
"""

import argparse
import html
import json
from pathlib import Path
import sys
import textwrap
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_views import load, validate  # noqa: E402

PEOPLE = {}
STANDINGS = ("accepted", "proposed", "disputed")
STANDING_NAME = {"accepted": "Accepted", "proposed": "Proposed", "disputed": "Disputed"}
# The Claude widget host neither wraps node or edge text nor widens labels past about 200px,
# so widget labels are broken into lines that fit; 28 characters fit in testing, 26 leaves margin.
WIDTH = 26
TREE_ORDER = ("goal", "current_reality", "conflict", "future_reality", "prerequisite", "transition")


def status(item):
    return item.get("status", "proposed")


def title(tree):
    return tree.replace("_", " ").capitalize()


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def ordered(trees):
    return sorted(trees, key=lambda t: TREE_ORDER.index(t) if t in TREE_ORDER else len(TREE_ORDER))


def counts(state):
    lines = []
    for name in ordered(state["trees"]):
        nodes = state["trees"][name]["nodes"]
        if not nodes:
            continue
        parts = [f"{sum(status(n) == s for n in nodes)} {s}" for s in STANDINGS]
        lines.append(f"{title(name)} ({' · '.join(p for p in parts if not p.startswith('0 '))})")
    return "\n".join(lines) or "There are no trees to view yet."


def default_standing(tree):
    return "accepted" if any(status(n) == "accepted" for n in tree["nodes"]) else "proposed"


def select(tree, standing):
    """Nodes and links of one standing, plus nodes of other standings as context."""
    nodes = {n["id"]: n for n in tree["nodes"]}
    shown = [n["id"] for n in tree["nodes"] if status(n) == standing]
    links = [l for l in tree["links"] if status(l) == standing]
    context = []
    for link in links:
        for ident in link["from"] + [link["to"]]:
            if status(nodes[ident]) != standing and ident not in context:
                context.append(ident)
    return nodes, shown, context, links


def label(node, standing, tree, multiline=True, width=None):
    # The view heading names the tree, so a node carries only its standing, kind and statement.
    head, kind = f"[{STANDING_NAME[status(node)]}]", title(node["kind"])
    parts = [node["text"].strip()]
    if standing == "disputed":
        parts += [f"Objection ({PEOPLE.get(c['by'], c['by'])}): {c['text'].strip()}" for c in node.get("challenges", [])]
    if not multiline:
        return f"{head} {kind}: " + "\n".join(parts)
    # Diagrams draw the one-sentence label when there is one; the text outline keeps the full statement.
    parts[0] = (node.get("label") or node["text"]).strip()
    lines = [head, kind]
    for part in parts:
        lines += textwrap.wrap(part, width, break_long_words=False, break_on_hyphens=False) if width else [part]
    return "\n".join(lines)


def escape(text):
    for raw, code in (("&", "#amp;"), ('"', "#quot;"), ("<", "#lt;"), (">", "#gt;")):
        text = text.replace(raw, code)
    return text.replace("\n", "<br/>")


def heading(name, standing, shown, links, context=()):
    extra = f"; {len(context)} nodes of other standings as context" if context else ""
    return f"{title(name).upper()} — {standing.upper()} ONLY ({plural(len(shown), 'node')}, {plural(len(links), 'link')}{extra})"


def not_shown(tree, standing):
    others = [(s, sum(status(n) == s for n in tree["nodes"])) for s in STANDINGS if s != standing]
    others = [(s, n) for s, n in others if n]
    if not others:
        return "Nothing else in this tree."
    return "Not shown: " + ", ".join(f"{n} {s}" for s, n in others) + ". Say " + " or ".join(f"“show {s}”" for s, _ in others) + "."


def relations(links):
    names = {l["relation"] for l in links}
    return names.pop().replace("_", " ") if len(names) == 1 else None


def mermaid(name, tree, standing, width=None):
    nodes, shown, context, links = select(tree, standing)
    common = relations(links)
    short = {ident: f"n{i}" for i, ident in enumerate(shown + context, 1)}
    linked = {i for l in links for i in l["from"] + [l["to"]]}
    loose = [i for i in shown if i not in linked]
    out = ["flowchart BT"]
    for ident in [i for i in shown + context if i not in loose]:
        out.append(f'  {short[ident]}["{escape(label(nodes[ident], standing, name, width=width))}"]')
    if loose and links:
        out.append('  subgraph loose["Not yet linked"]')
        out += [f'    {short[i]}["{escape(label(nodes[i], standing, name, width=width))}"]' for i in loose]
        out.append("  end")
    else:
        out += [f'  {short[i]}["{escape(label(nodes[i], standing, name, width=width))}"]' for i in loose]
    for j, link in enumerate(links, 1):
        tag = [] if common else [link["relation"].replace("_", " ")]
        if status(link) == "disputed":
            tag.insert(0, "disputed")
        solid = status(link) == "accepted"
        plain = "-->" if solid else "-.->"
        tagged = f"-- {' · '.join(tag)} -->" if solid else f"-. {' · '.join(tag)} .->"
        arrow = tagged if tag else plain
        target = short[link["to"]]
        if len(link["from"]) > 1:
            out.append(f'  j{j}(("AND"))')
            out += [f"  {short[s]} {plain} j{j}" for s in link["from"]]
            out.append(f"  j{j} {arrow} {target}")
        else:
            out.append(f"  {short[link['from'][0]]} {arrow} {target}")
    out += [
        "  classDef proposed stroke-dasharray:4 3,stroke:#BA7517",
        "  classDef accepted stroke:#1D9E75,stroke-width:2px",
        "  classDef disputed stroke:#E24B4A,stroke-width:2px",
        "  classDef context stroke-dasharray:2 2,opacity:0.6",
    ]
    if shown:
        out.append(f"  class {','.join(short[i] for i in shown)} {standing}")
    if context:
        out.append(f"  class {','.join(short[i] for i in context)} context")
    return "\n".join(out), shown, links, common, context


def text_outline(name, tree, standing):
    """Plain-text fallback: every link once, grouped by its effect; loose nodes last."""
    nodes, shown, context, links = select(tree, standing)
    common = relations(links)
    lines = [heading(name, standing, shown, links, context)]
    if common:
        lines.append(f"Each arrow reads “{common}”.")
    by_target = {}
    for link in links:
        by_target.setdefault(link["to"], []).append(link)
    for target, incoming in by_target.items():
        lines.append("")
        lines.append(label(nodes[target], standing, name, multiline=False).replace("\n", "\n    "))
        for link in incoming:
            causes = [label(nodes[s], standing, name, multiline=False).split("\nObjection (", 1)[0] for s in link["from"]]
            via = "" if common else f" ({link['relation'].replace('_', ' ')})"
            joined = causes[0] if len(causes) == 1 else "AND( " + " + ".join(causes) + " )"
            lines.append(f"  <-{via} {joined}")
    linked = {i for l in links for i in l["from"] + [l["to"]]}
    loose = [i for i in shown if i not in linked]
    if loose:
        lines += ["", "Not yet linked:"] + [f"  {label(nodes[i], standing, name, multiline=False)}" for i in loose]
    lines += ["", not_shown(tree, standing)]
    return "\n".join(lines)


WIDGET = """<style>
#rcv{position:relative;height:380px;border:0.5px solid var(--border);border-radius:12px;overflow:hidden;cursor:grab;touch-action:none;background:var(--surface-1)}
#rcv.drag{cursor:grabbing}
#rcv.tall{height:720px}
#rcv svg{width:100%;height:100%;max-width:none!important}
.rcb{position:absolute;top:8px;right:8px;display:flex;gap:4px}
.rcb button{width:30px;height:30px;border:0.5px solid var(--border-strong);border-radius:var(--radius);background:var(--surface-2);color:var(--text-primary);cursor:pointer;font-size:16px;line-height:1}
.rcb #ztall{width:auto;padding:0 8px;font-size:13px}
</style>
<h2 class="sr-only">__HEADING__, with pan and zoom</h2>
<p style="margin:0 0 8px;font-size:13px;color:var(--text-secondary)">__HEADING__ · drag to pan · pinch or ⌘/Ctrl+scroll to zoom</p>
<div id="rcv"><div id="rc" style="width:100%;height:100%"></div>
<div class="rcb"><button id="ztall" aria-pressed="false">Taller</button><button id="zin" aria-label="Zoom in"><i class="ti ti-plus" aria-hidden="true"></i></button><button id="zout" aria-label="Zoom out"><i class="ti ti-minus" aria-hidden="true"></i></button><button id="zfit" aria-label="Fit to view"><i class="ti ti-arrows-maximize" aria-hidden="true"></i></button></div></div>
<p style="margin:8px 0 0;font-size:13px;color:var(--text-secondary)">__NOT_SHOWN__</p>
<script type="module">
import mermaid from 'https://esm.sh/mermaid@11/dist/mermaid.esm.min.mjs';
const mode = document.documentElement.dataset.mode;
const dark = mode ? mode === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
await document.fonts.ready;
mermaid.initialize({startOnLoad: false, theme: 'base', fontFamily: '"anthropic-sans", sans-serif',
  themeVariables: {darkMode: dark, fontSize: '13px', fontFamily: '"anthropic-sans", sans-serif',
    lineColor: dark ? '#9c9a92' : '#73726c', textColor: dark ? '#c2c0b6' : '#3d3d3a',
    primaryColor: dark ? '#2C2C2A' : '#F1EFE8', primaryBorderColor: dark ? '#888780' : '#5F5E5A'}});
const { svg } = await mermaid.render('__RENDER_ID__', __SOURCE__);
const host = document.getElementById('rc'); host.innerHTML = svg;
const el = host.querySelector('svg'); el.removeAttribute('style'); el.setAttribute('width','100%'); el.setAttribute('height','100%');
const [fx,fy,fw,fh] = el.getAttribute('viewBox').split(/[\\s,]+/).map(Number);
const pad = 16, fit = {x:fx-pad,y:fy-pad,w:fw+2*pad,h:fh+2*pad};
let v = {...fit};
const set = () => el.setAttribute('viewBox', `${v.x} ${v.y} ${v.w} ${v.h}`);
const scale = () => { const r = el.getBoundingClientRect(); return Math.max(v.w/r.width, v.h/r.height); };
const zoom = (f, cx, cy) => { const r = el.getBoundingClientRect(); const s = scale();
  const px = cx==null ? v.x+v.w/2 : v.x + (cx-r.left)*s - (s*r.width-v.w)/2;
  const py = cy==null ? v.y+v.h/2 : v.y + (cy-r.top)*s - (s*r.height-v.h)/2;
  const nw = Math.min(Math.max(v.w*f, fit.w/8), fit.w*4); const k = nw/v.w;
  v = {x:px-(px-v.x)*k, y:py-(py-v.y)*k, w:v.w*k, h:v.h*k}; set(); };
set();
const box = document.getElementById('rcv');
document.getElementById('zin').onclick = () => zoom(0.8);
document.getElementById('zout').onclick = () => zoom(1.25);
document.getElementById('zfit').onclick = () => { v = {...fit}; set(); };
const tall = document.getElementById('ztall');
tall.onclick = () => { const on = box.classList.toggle('tall'); tall.textContent = on ? 'Shorter' : 'Taller'; tall.setAttribute('aria-pressed', on); };
box.addEventListener('wheel', e => { if (!(e.ctrlKey || e.metaKey)) return; e.preventDefault(); zoom(Math.exp(e.deltaY*0.01), e.clientX, e.clientY); }, {passive:false});
let last = null;
box.addEventListener('pointerdown', e => { if (e.target.closest('button')) return; last = [e.clientX,e.clientY]; box.setPointerCapture(e.pointerId); box.classList.add('drag'); });
box.addEventListener('pointermove', e => { if (!last) return; const s = scale(); v.x -= (e.clientX-last[0])*s; v.y -= (e.clientY-last[1])*s; last = [e.clientX,e.clientY]; set(); });
const end = () => { last = null; box.classList.remove('drag'); };
box.addEventListener('pointerup', end); box.addEventListener('pointercancel', end);
</script>
"""


def markdown(name, tree, standing):
    """Complete native Mermaid response, with the same scope and context as a widget."""
    source, shown, links, common, context = mermaid(name, tree, standing)
    lines = [heading(name, standing, shown, links, context)]
    if common:
        lines.append(f"Each arrow reads “{common}”.")
    lines += ["", "```mermaid", source, "```", "", not_shown(tree, standing)]
    return "\n".join(lines)


def widget(name, tree, standing):
    source, shown, links, common, context = mermaid(name, tree, standing, width=WIDTH)
    relation = f" · each arrow reads “{common}”" if common else ""
    return frame(source, heading(name, standing, shown, links, context) + relation, not_shown(tree, standing))


def frame(source, head, footer=""):
    page = WIDGET if footer else WIDGET.replace('<p style="margin:8px 0 0;font-size:13px;color:var(--text-secondary)">__NOT_SHOWN__</p>\n', "")
    for key, value in (
        ("__HEADING__", html.escape(head, quote=False)),
        ("__NOT_SHOWN__", html.escape(footer, quote=False)),
        ("__RENDER_ID__", f"rc-{uuid.uuid4().hex[:8]}"),
        ("__SOURCE__", json.dumps(source).replace("</", "<\\/")),
    ):
        page = page.replace(key, value)
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state", type=Path, nargs="?")
    parser.add_argument("--wrap", action="store_true", help="wrap Mermaid source from stdin in the pan-and-zoom frame")
    parser.add_argument("--heading", help="with --wrap: the label line above the diagram")
    parser.add_argument("--footer", default="", help="with --wrap: an optional line below the diagram")
    parser.add_argument("--counts", action="store_true", help="print per-tree node counts by standing for the view menu")
    parser.add_argument("--tree", help="tree key, such as current_reality")
    parser.add_argument("--standing", choices=STANDINGS, help="default: accepted, or proposed when nothing is accepted")
    parser.add_argument("--format", choices=("widget", "markdown", "mermaid", "text"), default="widget")
    args = parser.parse_args()
    if args.wrap:
        if not args.heading:
            parser.error("--wrap needs --heading")
        print(frame(sys.stdin.read().strip(), args.heading, args.footer))
        return
    if args.state is None:
        parser.error("give a state file, or use --wrap")
    try:
        state = load(args.state)
        validate(state)
    except (OSError, ValueError) as error:
        sys.exit(f"Cannot read {args.state}: {error}")
    PEOPLE.update(state["participants"], assistant="assistant")
    if args.counts:
        print(counts(state))
        return
    if args.tree not in state["trees"]:
        sys.exit(f"--tree must be one of: {', '.join(ordered(state['trees']))}")
    tree = state["trees"][args.tree]
    standing = args.standing or default_standing(tree)
    if not any(status(n) == standing for n in tree["nodes"]):
        sys.exit(f"{title(args.tree)} has no {standing} nodes. {not_shown(tree, standing)}")
    if args.format == "text":
        print(text_outline(args.tree, tree, standing))
    elif args.format == "markdown":
        print(markdown(args.tree, tree, standing))
    elif args.format == "mermaid":
        print(mermaid(args.tree, tree, standing)[0])
    else:
        print(widget(args.tree, tree, standing))


if __name__ == "__main__":
    main()
