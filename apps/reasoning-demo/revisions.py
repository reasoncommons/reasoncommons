"""Reviewed public archives and the focused comparison. No Git or private state needed at build time."""
import hashlib
import html
import json
import re
import textwrap

E = html.escape


def items(snapshot):
    return {i["id"]: i for t in snapshot["trees"].values() for i in t["nodes"] + t["links"]}


def edges(snapshot, ids):
    return [l for l in snapshot["trees"]["future_reality"]["links"] if set(l["from"]) <= set(ids) and l["to"] in ids]


def validate(review, current, validate_snapshot):
    def require(ok, message):
        if not ok:
            raise ValueError(message)
    require(isinstance(review, dict) and set(review) == {"version", "releases", "source_cards", "comparison"} and review["version"] == 1, "Unreviewed review fields")
    archives = {}
    for release in review["releases"]:
        require(set(release) == {"commit", "snapshot_sha256", "snapshot"}, "Unreviewed archive fields")
        require(re.fullmatch(r"[0-9a-f]{40}", release["commit"]), "Invalid archive commit")
        snapshot = release["snapshot"]
        digest = hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        require(digest == release["snapshot_sha256"], "Archive fingerprint changed")
        # Apply the normal public projection allowlist to every historical snapshot too.
        registry = {k: snapshot[k] for k in ("publication_kind", "authors", "sources", "views", "overview", "retired")}
        registry.update(people={str(i): p["name"] for i,p in enumerate(snapshot["people"])}, feedback=[],
                        selection={name: {key: [i["id"] for i in tree[key]] for key in ("nodes", "links")} for name,tree in snapshot["trees"].items()})
        validate_snapshot(snapshot, registry)
        require(snapshot["release_id"] not in archives, "Duplicate historical release")
        archives[snapshot["release_id"]] = snapshot
    require(set(archives) == {h["release_id"] for h in current["history"]}, "Archive/history mismatch")
    require(archives.get(current["release_id"]) == current, "Latest archive differs from publication")
    source_ids = {s["id"] for s in current["sources"]}
    require(set(review["source_cards"]) <= source_ids, "Unknown source card")
    for card in review["source_cards"].values():
        require(set(card) == {"title", "pages", "style"} and isinstance(card["title"], str) and card["title"].strip()
                and type(card["pages"]) is int and card["pages"] > 0 and card["style"] in ART, "Invalid source card")
    comp = review["comparison"]
    require(set(comp) == {"before", "after", "ids"} and comp["before"] in archives and comp["after"] in archives, "Invalid comparison releases")
    require(comp["ids"] == ["rm-f-attune", "rm-f-variation", "rm-f-learning", "rm-f-coordination", "rm-f-capacities"], "Unreviewed comparison selection")
    old, new = archives[comp["before"]], archives[comp["after"]]
    require(comp["before"] == "2026-10-23.2" and comp["after"] == "2026-10-24.1", "Unreviewed comparison versions")
    for snapshot, count in ((old, 2), (new, 6)):
        selected = edges(snapshot, comp["ids"])
        require(len(selected) == count and all(len(l["from"]) == 1 and l["status"] == "proposed" for l in selected), "Comparison topology changed")
    return review


def archive(review, release_id):
    return next((r["snapshot"] for r in review.get("releases", []) if r["snapshot"]["release_id"] == release_id), None)


def compare(review):
    comp = review["comparison"]
    old, new = (archive(review, comp[k]) for k in ("before", "after"))
    result = COMPARISON
    for token, value in (("BEFORE_GRAPH", graph(old, "before", old, comp["ids"])), ("AFTER_GRAPH", graph(new, "after", old, comp["ids"])),
                         ("BEFORE_OUTLINE", outline(old, old, comp["ids"])), ("AFTER_OUTLINE", outline(new, old, comp["ids"]))):
        result = result.replace("{" + token + "}", value)
    result = re.sub(r"\{TEXT:([^:}]+):([^}]+)\}", lambda m: E(items(archive(review,m[1]))[m[2]]["text"]), result)
    return re.sub(r"\{ADDED:([^}]+)\}", lambda m: E(items(new)[m[1]]["text"]), result)


ART = {'slides': '<rect x="14" y="17" width="102" height="61" rx="3"/><path d="M26 30h48M26 40h75M26 66l21-15 18 10 17-21 21 26M65 78v10M45 88h40"/>', 'script': '<path d="M26 17h78v79H26zM39 33h51M39 44h51M39 55h40M39 66h51M39 77h33"/><circle cx="106" cy="80" r="12"/><path d="M101 78v6l9-3z"/>', 'passages': '<path d="M22 23h42v65H22zM70 23h37v65H70zM31 37h23M31 47h23M31 57h23M79 37h19M79 47h19M79 57h19M31 68h18M79 68h19"/>', 'glossary': '<path d="M24 20h82v76H24zM64 20v76M34 37h17M34 48h17M34 59h17M75 37h19M75 48h19M75 59h19M34 76h17M75 76h19"/>', 'bibliography': '<path d="M26 18h78v79H26zM46 34h43M46 47h43M46 60h43M46 73h43M46 85h30"/><circle cx="36" cy="33" r="1"/><circle cx="36" cy="46" r="1"/><circle cx="36" cy="59" r="1"/><circle cx="36" cy="72" r="1"/><circle cx="36" cy="85" r="1"/>'}

COMPARISON = '<section class="changes-section" id="changes" aria-labelledby="changes-title"><p class="eyebrow">Feedback, placed in context</p><h2 id="changes-title">See what actually changed</h2><p class="section-lead">Choose a section to see its before-and-after comparison. Details stay folded away until you open them.</p>\n<details class="comparison" id="agency-comparison"><summary><span class="summary-number">01</span><span><span class="summary-title">Agency emerging through interaction</span><span class="summary-subtitle">Open to compare the earlier and revised diagrams.</span></span><span class="toggle-icon" aria-hidden="true">+</span></summary><div class="comparison-body"><div class="concern"><p class="mini-label">The concern · paraphrase</p><p>Agency was represented too narrowly through permission and adjustment. The reciprocal process through which capacities emerge needed a clearer place.</p></div><div class="comparison-meta"><div><div class="legend" aria-label="Comparison legend"><span class="reworded-key"><i aria-hidden="true"></i>Reworded</span><span class="new"><i aria-hidden="true"></i>Added</span><span><i aria-hidden="true"></i>Proposed connection</span></div><p class="text-alternative">All statements and connections remain proposed. Phone layouts show the complete text outline.</p></div><label class="reading-option"><input id="text-reading" type="checkbox"> Read as text</label></div>\n<div class="comparison-panels"><section class="comparison-panel before-panel" aria-labelledby="before-title"><div class="panel-heading"><div><h3 id="before-title">Before</h3><p>The earlier published account</p></div><span class="version">23 Oct · 2026-10-23.2</span></div>{BEFORE_GRAPH} {BEFORE_OUTLINE}<p class="diagram-caption">A path from adjusting activity through surprise to learning. The coordination–capacity branch is absent.</p></section><section class="comparison-panel after-panel" aria-labelledby="after-title"><div class="panel-heading"><div><h3 id="after-title">After</h3><p>The revised published account</p></div><span class="version">24 Oct · 2026-10-24.1</span></div>{AFTER_GRAPH} {AFTER_OUTLINE}<p class="diagram-caption">The original path remains. A new branch connects activity, emerging coordination, changing capacities and feedback.</p></section></div><p class="graph-caption">Actual archived short labels and connections, with matching positions for shared statements. These are focused fragments of the Future Reality view, not the complete maps. Which release Margeret saw is unconfirmed.</p>\n<div class="interpretation"><div><h3>Why this changes the explanation</h3><p>The revised branch proposes that reciprocal adjustment may bring forth coordination that no participant specified alone. That coordination may reshape capacities and subsequent participation.</p><a class="detail-link" href="change.html#view-listen-and-adjust">Place this branch in the current full map ↗</a></div><div class="review-question"><h3>Still open to judgment</h3><p>Does this represent the agency Heath meant? The added connections are AI inferences from the spoken script, pp. 19–24 and 26. Their wording and interpretation await review.</p><a class="detail-link" href="about.html#source-spoken-script">Explore that source ↓</a></div></div>\n</div></details><details class="comparison" id="agency-wording"><summary><span class="summary-number">02</span><span><span class="summary-title">The exact statement changes</span><span class="summary-subtitle">Three revised statements and two added predictions, before and after.</span></span><span class="toggle-icon" aria-hidden="true">+</span></summary><div class="comparison-body"><h3 class="wording-title">The exact wording, before and after</h3><table class="wording-table"><caption class="sr-only">Three existing statements revised between the named releases</caption><thead><tr><th scope="col">Statement</th><th scope="col">Before · 2026-10-23.2</th><th scope="col">After · 2026-10-24.1</th></tr></thead><tbody><tr><th scope="row">Shared activity</th><td data-text-release="2026-10-23.2" data-ref="rm-f-attune">{TEXT:2026-10-23.2:rm-f-attune}</td><td data-text-release="2026-10-24.1" data-ref="rm-f-attune">{TEXT:2026-10-24.1:rm-f-attune}</td></tr><tr><th scope="row">Surprise</th><td data-text-release="2026-10-23.2" data-ref="rm-f-variation">{TEXT:2026-10-23.2:rm-f-variation}</td><td data-text-release="2026-10-24.1" data-ref="rm-f-variation">{TEXT:2026-10-24.1:rm-f-variation}</td></tr><tr><th scope="row">Learning</th><td data-text-release="2026-10-23.2" data-ref="rm-f-learning">{TEXT:2026-10-23.2:rm-f-learning}</td><td data-text-release="2026-10-24.1" data-ref="rm-f-learning">{TEXT:2026-10-24.1:rm-f-learning}</td></tr></tbody></table><ul class="added-statements"><li data-added-ref="rm-f-coordination"><span class="small-badge">Added · predicted effect</span><p>{ADDED:rm-f-coordination}</p><a href="items.html#rm-f-coordination">Inspect statement and source ↗</a></li><li data-added-ref="rm-f-capacities"><span class="small-badge">Added · predicted effect</span><p>{ADDED:rm-f-capacities}</p><a href="items.html#rm-f-capacities">Inspect statement and source ↗</a></li></ul><div class="comparison-bottom"><a href="#release-history">Read the detailed release history ↓</a><a href="#agency-wording">Link to these statement changes</a></div></div></details></section>'

STORY = '<section class="feedback-story" aria-labelledby="story-title"><div class="story-heading"><div><p class="eyebrow">How feedback changed this commons</p><h2 id="story-title">An objection becomes a visible revision.</h2></div><span class="status-tag">Revision awaits Margeret’s review</span></div><div class="story-steps"><article class="story-step"><h3><span class="step-number">01 / THE FEEDBACK</span>Margeret questions the emphasis</h3><p>The map gives too little weight to dynamical process, reciprocal agency, enmindment and uncertainty as poiesis.</p></article><article class="story-step"><h3><span class="step-number">02 / THE REVISION</span>The reasoning gains a process loop</h3><p>Shared activity may generate coordination; coordination may change capacities, which feed back into the activity.</p></article><article class="story-step"><h3><span class="step-number">03 / THE NEXT JUDGMENT</span>Does it capture her meaning?</h3><p>The revised interpretation is available to examine. Margeret has not endorsed this version.</p></article></div><div class="story-foot"><a href="changes.html#agency-comparison">See the agency comparison ↓</a><p>Author feedback paraphrased from comments relayed by David. The resulting AI-assisted revision of the shared reasoning remains open for review.</p></div></section>'

def svg_node(n, x,y, change):
    lines=textwrap.wrap(n.get('label') or n['text'],width=27,break_long_words=False)
    assert len(lines)<=5,(n['id'],lines)
    kind={'injection':'Proposed change','predicted_effect':'Predicted effect'}[n['kind']]
    badge={'earlier':'PROPOSED','reworded':'REWORDED · PROPOSED','added':'ADDED · PROPOSED'}[change]
    text=''.join(f'<tspan x="{x+18}" y="{y+72+i*21}">{E(line)}</tspan>' for i,line in enumerate(lines))
    return f'<g class="graph-node {change}" data-ref="{n["id"]}" data-label="{E(n.get("label") or n["text"],quote=True)}"><title>{E(n["text"])}</title><rect x="{x}" y="{y}" width="250" height="172" rx="9"/><text class="node-status" x="{x+18}" y="{y+24}">{badge}</text><text class="node-kind" x="{x+18}" y="{y+47}">{kind}</text><text class="node-label">{text}</text></g>'

def graph(s, which, old, ids):
    old_items = items(old)
    old_edges = edges(old, ids)
    ns=items(s)
    coords={'rm-f-attune':(20,75),'rm-f-variation':(20,330),'rm-f-learning':(20,585),'rm-f-coordination':(370,75),'rm-f-capacities':(370,330)}
    paths={'rm-fl-variation':'M145 247 V330','rm-fl-learning':'M145 502 V585','rm-fl-coordination':'M270 161 H370','rm-fl-capacities':'M495 247 V330','rm-fl-retuning':'M620 416 H638 V38 H145 V75','rm-fl-capacity-learning':'M495 502 V671 H270'}
    labels={'rm-fl-variation':(155,287),'rm-fl-learning':(155,542),'rm-fl-coordination':(320,137),'rm-fl-capacities':(505,287),'rm-fl-retuning':(402,22),'rm-fl-capacity-learning':(430,656)}
    old_links={l['id'] for l in old_edges}
    out=[]
    for l in edges(s, ids):
        added=l['id'] not in old_links
        cls='edge-added' if added else 'edge-existing'
        x,y=labels[l['id']]
        label='feeds back to' if l['relation']=='feeds_back_to' else 'contributes to'
        out.append(f'<g data-link-ref="{l["id"]}" data-from="{l["from"][0]}" data-to="{l["to"]}" data-relation="{l["relation"]}" class="{cls}"><title>Proposed: {E(label)}. {E(ns[l["from"][0]]["text"])} → {E(ns[l["to"]]["text"])}</title><path d="{paths[l["id"]]}" marker-end="url(#{which}-{cls})"/><text x="{x}" y="{y}" text-anchor="{"middle" if l["id"] in {"rm-fl-coordination","rm-fl-retuning","rm-fl-capacity-learning"} else "start"}">{E(label)}</text></g>')
    for ident in ids:
        if ident not in ns: continue
        change='earlier' if which=='before' else 'added' if ident not in old_items else 'reworded'
        out.append(svg_node(ns[ident],*coords[ident],change))
    if which=='before': out.append('<text class="absence" x="385" y="395">No coordination–capacity</text><text class="absence" x="385" y="418">branch recorded here.</text>')
    return f'<svg class="comparison-graph" viewBox="0 0 660 790" role="img" aria-labelledby="{which}-diagram-title {which}-diagram-desc"><title id="{which}-diagram-title">Agency reasoning in release {s["release_id"]}</title><desc id="{which}-diagram-desc">'+('Three proposed statements form the existing activity, surprise and learning path.' if which=='before' else 'The existing path is retained and reworded. Two new predicted effects describe coordination and capacities, with four added proposed links including feedback to shared activity.')+f'</desc><defs><marker id="{which}-edge-existing" markerWidth="8" markerHeight="8" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="none" stroke="#74796d" stroke-width="1.5"/></marker><marker id="{which}-edge-added" markerWidth="8" markerHeight="8" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="none" stroke="#2c6748" stroke-width="1.5"/></marker></defs>'+''.join(out)+'</svg>'

def outline(s, old, ids):
    old_items = items(old)
    ns=items(s)
    nodes=''.join(f'<li data-outline-ref="{i}"><span class="outline-kind">'+('Added predicted effect' if i not in old_items else 'Proposed change' if ns[i]['kind']=='injection' else 'Predicted effect')+f'</span>{E(ns[i].get("label") or ns[i]["text"])}</li>' for i in ids if i in ns)
    es=''.join(f'<li>{E(ns[l["from"][0]].get("label") or ns[l["from"][0]]["text"])} <b>{"feeds back to" if l["relation"]=="feeds_back_to" else "contributes to"}</b> {E(ns[l["to"]].get("label") or ns[l["to"]]["text"])}</li>' for l in edges(s, ids))
    return f'<div class="graph-outline"><ol>{nodes}</ol><p class="mini-label">The proposed connections</p><ul class="connection-outline">{es}</ul></div>'
