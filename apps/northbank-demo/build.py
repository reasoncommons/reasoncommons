#!/usr/bin/env python3
"""Generate the Northbank worked commons from its canonical reasoning and history."""
from copy import deepcopy
from datetime import date
from html import escape as esc
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'ltp/examples/northbank-print'
DEST = ROOT / 'website/demos/northbank-print'
TREE_NAMES = {'goal':'The agreed goal', 'current_reality':'The working explanation', 'future_reality':'The adjustment and its consequences', 'transition':'Who does what'}
KINDS = {'goal':'Goal', 'cause':'Possible cause', 'undesirable_effect':'Problem / possible harm', 'injection':'Adjustment', 'existing_condition':'Enabling condition', 'predicted_effect':'Expected effect', 'desirable_effect':'Desired outcome', 'action':'Action'}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def load():
    return yaml.safe_load((SOURCE/'reason-commons.yaml').read_text()), json.loads((SOURCE/'engagement.json').read_text())

def index(state):
    return {item['id']:dict(item, tree=tree) for tree, content in state['trees'].items() for key in ('nodes','links') for item in content[key]}

def historical(state, engagement, when):
    """Reconstruct one dated view; it is not a separately maintained commons."""
    result = {}
    current = index(state)
    for event in engagement['events']:
        if event['date'] > when:
            break
        for change in event['updates']:
            ref = change['ref']
            result[ref] = {**deepcopy(current[ref]), **deepcopy(change['after'])}
            if 'text' in change['after'] and change['after']['text'] != current[ref].get('text'):
                result[ref]['label'] = change['after']['text']
    return result

def validate(state, data):
    helper = ROOT / 'skills/ltp/scripts/update_views.py'
    if not helper.exists():
        helper = ROOT / 'skills/reason-commons/scripts/update_views.py'
    spec = importlib.util.spec_from_file_location('northbank_views', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate(state)
    require(data['fictional'] is True, 'The fiction label is mandatory.')
    items = index(state)
    require(all(x['status']=='proposed' and not x.get('accepted_by') for x in items.values()), 'Fictional endorsements must not become real acceptance.')
    dates = [x['date'] for x in data['events']]
    require(len(dates)==13 and dates==sorted(set(dates)), 'Expected thirteen unique chronological entries.')
    for group, key in [('reports','id'),('predictions','id'),('windows','id'),('releases','id')]:
        ids=[x[key] for x in data[group]]
        require(len(ids)==len(set(ids)), f'Duplicate {group} ID.')
    reports={x['id']:x for x in data['reports']}
    predictions={x['id']:x for x in data['predictions']}
    windows={x['id']:x for x in data['windows']}
    releases={x['id']:x for x in data['releases']}
    previous={}
    for event in data['events']:
        for change in event['updates']:
            ref=change['ref']; require(ref in items, f'Unknown change reference: {ref}')
            if 'before' in change:
                require(ref in previous and change['before']==previous[ref], f'Broken before/after chain: {ref}')
            else:
                require(ref not in previous, f'Repeated addition without before wording: {ref}')
            previous[ref]=change['after']
        if event.get('report'): require(event['report'] in reports, 'Unknown report')
        for ref in event.get('additional_reports',[]): require(ref in reports, 'Unknown correction')
        if event.get('prediction'): require(event['prediction'] in predictions, 'Unknown prediction')
        if event.get('release'): require(releases[event['release']]['date']==event['date'], 'Release date differs from event')
    require(set(previous)==set(items), 'Every current item must have a historical origin.')
    for ref, after in previous.items():
        require(all(items[ref][k]==v for k,v in after.items()), f'Latest version differs from current YAML: {ref}')
    for prediction in predictions.values():
        window=windows[prediction['window']]
        require(prediction['recorded_on']<window['start'], 'A prospective prediction must precede its observation window.')
        at_capture=historical(state,data,prediction['recorded_on'])
        about=prediction['about']
        require(at_capture[about['ref']]['text']==about['text'], 'Prediction intervention differs from wording at capture.')
        for ref in prediction['benefits']+prediction['reservations']:
            require(ref in at_capture, 'Prediction outcome did not yet exist.')
    for report in reports.values():
        if report.get('prediction'):
            require(report['date']>=predictions[report['prediction']]['recorded_on'], 'Report precedes prediction.')
        if report.get('window'):
            require(report['date']>=windows[report['window']]['end'], 'Report precedes observation window end.')
        if report.get('corrects'):
            require(reports[report['corrects']].get('correction')==report['id'], 'Correction must link in both directions.')
    for window in windows.values():
        require(window['start']<=window['end'], 'Invalid window')
        for key in ('late','decisions'):
            n,d=window[key]; require(0<=n<=d and d>0, 'Invalid denominator')
        yes,responses,eligible=window['voice']
        require(0<=yes<=responses<=eligible==20,'Invalid voice denominator')
    require(windows['march1']['end']<windows['march2']['start'],'Closure windows must not overlap.')
    require(qualifies(windows['march1']) and qualifies(windows['march2']), 'Closure needs two qualifying windows.')
    require(not qualifies(windows['followup']), 'The May deterioration must remain visible.')
    validate_tree_uses(state,data)
    require({x['ref'] for x in data['actions']}=={n['id'] for n in state['trees']['transition']['nodes']}, 'Actions and current reasoning differ.')

def qualifies(window):
    late,total=window['late']; decisions,requests=window['decisions']; yes,responses,_=window['voice']
    return total>=60 and late/total<=.1 and decisions/requests>=.8 and max(window['overtime'])<=18 and window['unpaid']==0 and yes>=16 and responses>=18

def fmt_date(value):
    return date.fromisoformat(value).strftime('%-d %B %Y')

def short_date(value):
    return date.fromisoformat(value).strftime('%-d %b')

def a(ref, text, cls=''):
    return f'<a class="{cls}" href="#item-{esc(ref)}">{esc(text)}</a>'

def paragraphs(texts):
    if isinstance(texts,str): texts=[texts]
    return ''.join(f'<p>{esc(x)}</p>' for x in texts)

def relation(shape,items):
    if 'text' in shape: return esc(shape['text'])
    sources=' <strong>AND</strong> '.join(a(ref,items[ref].get('label',items[ref].get('text',ref))) for ref in shape['from'])
    target=shape['to']
    return f'{sources} <span class="relation">{esc(shape["relation"].replace("_"," "))} →</span> {a(target,items[target].get("label",items[target].get("text",target)))}'

def change_card(change,items,before_items=None,after_items=None):
    ref=change['ref']
    old=f'<div class="before"><span class="small-label">Earlier wording / connection</span>{relation(change["before"],before_items or items)}</div>' if change.get('before') else ''
    return f'<article class="change"><div class="change-head"><span class="tag">{esc(change["operation"])}</span>{a(ref,"Inspect this item →")}</div>{old}<div class="after"><span class="small-label">Recorded at this point</span>{relation(change["after"],after_items or items)}</div>{paragraphs(change["note"]) if change.get("note") else ""}</article>'

def metric_definitions(data,baseline_known=True):
    out='<details class="definitions"><summary>What counts as progress? Four definitions agreed during Orient</summary>'
    for m in data['metrics']:
        baseline = m['baseline'] + ' · ' + m['baseline_period'] + ' (recorded 18 January)' if baseline_known else 'Pending: collect 4–15 January; review completed baseline on 18 January.'
        out+=f'<article><h3>{esc(m["name"])}</h3>{paragraphs(m["definition"])}<dl><dt>Baseline</dt><dd>{esc(baseline)}</dd><dt>Units</dt><dd>{esc(m["units"])}</dd><dt>Source</dt><dd>{esc(m["source"])}</dd><dt>Owner / cadence</dt><dd>{esc(m["owner"])} · {esc(m["frequency"])}</dd><dt>Decision rule</dt><dd>{esc(m["threshold"])}</dd></dl></article>'
    return out+'</details>'

def prediction_card(p):
    judges=', '.join(p['judges']).title()
    return f'<article class="prediction"><span class="eyebrow">Prospective prediction · {esc(fmt_date(p["recorded_on"]))}</span><h3>{esc(p["title"])}</h3><blockquote>{esc(p["about"]["text"])}</blockquote><h4>Expected benefit</h4>{paragraphs(p["expected"])}<h4>Possible harm and safeguards</h4>{paragraphs(p["guardrails"])}<p class="meta">Who judges: {esc(judges)} · Review {esc(fmt_date(p["review_on"]))}</p><a href="#prediction-{p["id"]}">Inspect this prediction and its reports →</a></article>'

def report_card(r,compact=False):
    link=f'<a href="#report-{r["id"]}">Read report and context →</a>' if compact else ''
    correction=f'<p>{"Corrects" if r.get("corrects") else "Later correction"}: <a href="#report-{r.get("corrects",r.get("correction"))}">inspect the linked report →</a></p>' if r.get('corrects') or r.get('correction') else ''
    return f'<article class="report"><span class="eyebrow">Fictional report · {esc(short_date(r["date"]))} · {esc(r["by"])}</span><h3>{esc(r["title"])}</h3><span class="tag neutral">{esc(r["verdict"])}</span>{paragraphs(r["text"])}{correction}{link}</article>'

TREE_TITLES = {'goal':'Goal', 'current_reality':'Current Reality tree', 'future_reality':'Future Reality tree', 'transition':'Action dependencies'}
TREE_KINDS = {'goal':'Goal', 'cause':'Cause', 'undesirable_effect':'Undesirable effect', 'injection':'Injection', 'existing_condition':'Existing condition', 'predicted_effect':'Predicted effect', 'desirable_effect':'Desirable effect', 'action':'Action'}

def tree_model(state, data, tree, when):
    """Only statements and connections actually captured by this fictional date."""
    at = historical(state, data, when)
    nodes = {n['id']:at[n['id']] for n in state['trees'][tree]['nodes'] if n['id'] in at}
    links = [at[l['id']] for l in state['trees'][tree]['links'] if l['id'] in at]
    require(all(set(l['from']+[l['to']]) <= set(nodes) for l in links), 'A dated tree has a missing endpoint.')
    return {'tree':tree, 'when':when, 'nodes':nodes, 'links':links}

def label_lines(text):
    import textwrap
    return '<br>'.join(esc(line) for line in textwrap.wrap(text, width=22, break_long_words=False))

def tree_diagram(state, data, tree, when, focus=(), evidence=(), fragment=False):
    model=tree_model(state,data,tree,when)
    nodes,links=model['nodes'],model['links']
    if fragment:
        links=[link for link in links if link['id'] in focus]
        require(links,'A connection fragment needs a recorded focused link.')
        ids={ref for link in links for ref in link['from']+[link['to']]}
        nodes={ref:node for ref,node in nodes.items() if ref in ids}
    if not nodes:return ''
    focus=set(focus)
    incoming={n:[] for n in nodes}
    outgoing={n:[] for n in nodes}
    neighbors={n:set() for n in nodes}
    for link in links:
        incoming[link['to']].append(link)
        for source in link['from']:
            outgoing[source].append(link)
            neighbors[source].add(link['to']);neighbors[link['to']].add(source)
    notes={}
    for note in evidence:notes.setdefault(note['ref'],[]).append(note)
    def annotations(ref):
        out=''
        for note in notes.get(ref,[]):
            report=f' · <a href="#report-{esc(note["report"])}">Inspect report →</a>' if note.get('report') else ''
            out+=f'<aside class="rt-evidence"><span class="small-label">At this point</span><p>{esc(note["text"])}</p><small>{esc(note["source"])}{report}</small></aside>'
        return out
    def node_box(ref):
        n=nodes[ref];selected=ref in focus
        flag='<span class="rt-focus-label">In discussion</span>' if selected else ''
        return f'<article class="rt-node{" rt-focused" if selected else ""}" data-tree-node="{esc(ref)}"><a href="#item-{esc(ref)}"><span class="rt-standing">[{esc(n["status"].capitalize())}]</span><span class="rt-kind">{esc(TREE_KINDS[n["kind"]])}</span><strong>{label_lines(n.get("label",n["text"]))}</strong>{flag}</a>{annotations(ref)}</article>'
    def edge(link):
        selected=link['id'] in focus
        label='comes before' if link['relation']=='precedes' else 'may contribute to'
        flag='<span class="rt-focus-label">In discussion</span>' if selected else ''
        return f'<div class="rt-edge{" rt-focused" if selected else ""}" data-tree-link="{esc(link["id"])}"><span aria-hidden="true">↓</span><a href="#item-{esc(link["id"])}">{esc(label)}</a>{flag}{annotations(link["id"])}</div>'
    def path(ref,seen=frozenset()):
        require(ref not in seen,'A cycle cannot be shown as an action or causal tree.')
        branches=[]
        for link in incoming[ref]:
            sources=''.join(path(source,seen|{ref}) for source in link['from'])
            if len(link['from'])>1:
                sources=f'<div class="rt-joint">{sources}</div><div class="rt-and">AND <small>both conditions together</small></div>'
            branches.append(f'<div class="rt-input">{sources}{edge(link)}</div>')
        upstream=''.join(branches)
        if len(branches)>1:upstream=f'<div class="rt-inputs">{upstream}</div>'
        return f'<div class="rt-path">{upstream}{node_box(ref)}</div>'
    components=[];remaining=set(nodes)
    for start in nodes:
        if start not in remaining:continue
        component=set();pending=[start]
        while pending:
            ref=pending.pop()
            if ref in component:continue
            component.add(ref);pending.extend(neighbors[ref]-component)
        remaining-=component;components.append(component)
    forests=[]
    for component in components:
        sinks=[ref for ref in nodes if ref in component and not outgoing[ref]]
        require(sinks,'A tree component must have an endpoint.')
        body=''
        if len(components)>1 and len(component)==1:
            condition=nodes[next(iter(component))]['kind']=='existing_condition'
            question='Recorded condition, not yet connected. Which arrow depends on it?' if condition else 'No explanation connected yet. What would explain this?'
            body+='<p class="rt-unconnected">'+question+'</p>'
        for ref in sinks:
            harm=tree=='future_reality' and nodes[ref]['kind']=='undesirable_effect'
            if harm:body+='<p class="rt-branch-label">The same adjustment has a possible harmful branch</p>'
            body+=f'<div class="rt-branch{" rt-harm" if harm else ""}">{path(ref)}</div>'
        forests.append(f'<div class="rt-component">{body}</div>')
    caption=f'{TREE_TITLES[tree]} · '+('connection under review · ' if fragment else '')+fmt_date(when)
    return f'<figure class="reasoning-tree" data-reasoning-tree="{esc(tree)}" data-tree-date="{esc(when)}"><figcaption>{esc(caption)}</figcaption><p class="rt-legend">Follow the arrows downward. Gold marks the question in discussion; the recorded standing remains Proposed.</p>{"".join(forests)}</figure>'

def tree_use_view(use,event,state,data):
    tree=use['tree'];focus=use['focus']
    response=f'<div class="rt-response"><span class="small-label">Client check · {esc(use["response_by"])}</span><p>{esc(use["response"])}</p></div>'
    if use.get('compare_with'):
        when=use['compare_with']
        earlier=f'<div class="rt-before"><h4>Earlier connection · {esc(fmt_date(when))}</h4>{tree_diagram(state,data,tree,when,focus,fragment=True)}<details class="record-details"><summary>Show the complete earlier tree</summary>{tree_diagram(state,data,tree,when,focus)}</details></div>'
        diagram=earlier+response+'<p class="rt-revision">The connection the group revises ↓</p>'+tree_diagram(state,data,tree,event['date'],focus,use['evidence'],fragment=True)
        diagram+='<details class="record-details"><summary>Show the complete revised tree</summary>'+tree_diagram(state,data,tree,event['date'],focus)+'</details>'
    else:
        diagram=tree_diagram(state,data,tree,event['date'],focus,use['evidence'])+response
    return f'<section class="tree-use"><span class="eyebrow">Using the tree in this meeting</span><h3>{esc(use["question"])}</h3><div class="rt-question"><span class="small-label">Stephen asks</span><p>{esc(use["prompt"])}</p></div>{diagram}<div class="rt-decision"><span class="small-label">The next move this leads to</span><p>{esc(use["decision"])}</p></div></section>'

def validate_tree_uses(state,data):
    reports={r['id']:r for r in data['reports']}
    for event in data['events']:
        for use in event.get('tree_uses',[]):
            require(use['tree'] in state['trees'],'Unknown tree in a facilitation scene.')
            for field in ('question','prompt','response_by','response','decision'):
                require(isinstance(use.get(field),str) and use[field].strip(),f'Tree use needs a concrete {field}.')
            at=tree_model(state,data,use['tree'],event['date'])
            ids=set(at['nodes'])|{l['id'] for l in at['links']}
            require(use.get('focus') and set(use['focus'])<=ids,'A tree focus must exist at this date in this tree.')
            if use.get('compare_with'):
                require(use['compare_with']<event['date'],'A comparison must use an earlier tree.')
            for note in use['evidence']:
                require(note['ref'] in ids,'Evidence is attached to a future or different-tree item.')
                if note.get('report'):
                    require(note['report'] in reports,'Unknown tree evidence report.')
                    require(reports[note['report']]['date']<=event['date'],'A tree scene reveals a future report.')


def event_view(event,state,data):
    items=index(state); reports={x['id']:x for x in data['reports']}; predictions={x['id']:x for x in data['predictions']}; releases={x['id']:x for x in data['releases']}
    i=data['events'].index(event)
    dialogue=''.join(f'<p><strong>{esc(who)}</strong> “{esc(words)}”</p>' for who,words in event.get('dialogue',[]))
    dialogue=f'<aside class="dialogue" aria-label="Fictional dialogue">{dialogue}</aside>' if dialogue else ''
    before_items={**items,**historical(state,data,data['events'][i-1]['date'])} if i else items
    after_items={**items,**historical(state,data,event['date'])}
    changes=''.join(change_card(x,items,before_items,after_items) for x in event['updates'])
    if not changes:
        refs=event.get('reviewed_refs',[])
        changes='<div class="no-change"><strong>Reviewed without changing the wording.</strong><p>The report changes the next decision; it does not automatically change the standing or explanation.</p>'+' · '.join(a(ref,items[ref]['label']) for ref in refs)+'</div>'
    prediction=prediction_card(predictions[event['prediction']]) if event.get('prediction') else ''
    report=''.join(report_card(reports[ref],compact=True) for ref in ([event['report']] if event.get('report') else [])+event.get('additional_reports',[]))
    release=''
    if event.get('release'):
        r=releases[event['release']]
        release=f'<aside class="release"><strong>Deliberate internal release · {esc(r["title"])}</strong>{paragraphs(r["note"])}</aside>'
    prev=f'<a href="#entry-{data["events"][i-1]["date"]}">← Previous entry</a>' if i else '<span>Beginning of the engagement</span>'
    nxt=f'<a class="button" href="#entry-{data["events"][i+1]["date"]}">Continue the engagement →</a>' if i+1<len(data['events']) else '<a class="button" href="#progress">Review the progress →</a>'
    if i==0:
        nxt=nxt.replace('Continue the engagement →','Build the first tree →')
    tree_work=''.join(tree_use_view(use,event,state,data) for use in event.get('tree_uses',[]))
    if tree_work:
        changes='<details class="record-details"><summary>Inspect the exact recorded changes and review references</summary>'+changes+'</details>'
    measures=metric_definitions(data,event['date']>='2027-01-18') if event.get('show_metrics') else ''
    return f'<section class="view" id="entry-{event["date"]}" data-view><div class="entry-meta"><span>Entry {i+1:02} / 13</span><span>{esc(fmt_date(event["date"]))}</span><span class="tag">{esc(event["stage"])}</span></div><h2 tabindex="-1">{esc(event["title"])}</h2><p class="lede">{esc(event["summary"])}</p>{paragraphs(event["scene"])}{tree_work}{dialogue}<h3>Stephen’s facilitation</h3>{paragraphs(event["facilitation"])}<h3>What enters the record</h3>{changes}{measures}{prediction}{report}<h3>Why this changed</h3>{paragraphs(event["evidence"])}<div class="next"><span class="small-label">Decision, owner and next review</span>{paragraphs(event["next"])}</div>{("" if tree_work else "<h3>What keeping the record makes possible</h3>"+paragraphs(event["difference"]))}{release}<nav class="entry-nav" aria-label="Previous and next entry">{prev}{nxt}</nav></section>'

def item_view(ref,item,state,data):
    items=index(state)
    kind=KINDS.get(item.get('kind'), 'Connection')
    body=paragraphs(item['text']) if 'text'in item else f'<p>{relation(item,items)}</p>'
    history=''
    for event in data['events']:
        changes=[x for x in event['updates'] if x['ref']==ref]
        if changes or ref in event.get('reviewed_refs',[]):
            history+=f'<article class="history-event"><a href="#entry-{event["date"]}">{esc(fmt_date(event["date"]))} · {esc(event["title"])}</a>'
            i=data['events'].index(event)
            before_items={**items,**historical(state,data,data['events'][i-1]['date'])} if i else items
            after_items={**items,**historical(state,data,event['date'])}
            history+=''.join(change_card(x,items,before_items,after_items) for x in changes) if changes else '<p>Reviewed; wording retained. See the report and next decision in this entry.</p>'
            history+='</article>'
    neighbors=[]
    if 'from'in item:
        neighbors.append('<li>The sources and target above are the recorded connection. Its wording and source conditions are retained below.</li>')
    if 'text'in item:
        for link in items.values():
            if 'from'in link and ref in link['from']+[link['to']]:
                neighbors.append(f'<li>{relation(link,items)} · {a(link["id"],"Inspect connection")}</li>')
    for trace in ('addresses','implements'):
        if item.get(trace): neighbors.append('<li>'+esc(trace.title())+': '+', '.join(a(i,items[i]['label']) for i in item[trace])+'</li>')
    action=next((x for x in data['actions'] if x['ref']==ref),None)
    heading=item.get('label') or 'Connection into: '+items[item['to']].get('label',items[item['to']].get('text','the effect'))
    owner=f'<aside class="next"><strong>{esc(action["owner"])} · {esc(action["state"])}</strong><p>{esc(action["due"])}</p>{paragraphs(action["detail"])}</aside>' if action else ''
    work=[b for t in state['trees'].values() for b in t['backlog'] if b['ref']==ref]
    backlog='<h3>Still open</h3><ul>'+''.join('<li>'+esc(x['label'])+'</li>' for x in work)+'</ul>' if work else ''
    return f'<section class="view" id="item-{ref}" data-view><a href="#current">← Current commons</a><div class="entry-meta"><span>{esc(TREE_NAMES[item["tree"]])}</span><span>{esc(kind)}</span><span class="tag">Proposed</span></div><h2 tabindex="-1">{esc(heading)}</h2><div class="statement">{body}</div><p class="meta">Illustrative stable ID: <code>{esc(ref)}</code> · Authored by the AI. Fictional agreement is not real endorsement.</p>{owner}<h3>How it connects</h3><ul class="connections">{"".join(neighbors) or "<li>No reasoning connection is recorded here. Its role in the client’s goal is described in the change log.</li>"}</ul>{backlog}<h3>Wording and review history</h3>{history or "<p>No separate review recorded.</p>"}</section>'

def current_view(state,data):
    out='<section class="view" id="current" data-view><span class="eyebrow">One current commons · working update 14 May 2027</span><h2 tabindex="-1">The trees the group is working with</h2><p class="lede">Use the causal tree to question an explanation, the future tree to test an adjustment, and the action dependencies to prepare it. Select a statement or arrow to inspect its history.</p><p class="notice">All authored reasoning remains proposed. Reports and client agreements belong to the fictional story.</p>'
    purposes={'current_reality':'Which proposed connection would we check before choosing a fix?', 'future_reality':'Which condition or expected effect should we check now?', 'transition':'What comes before the next meaningful review?'}
    for tree,content in state['trees'].items():
        out+=f'<h3>{esc(TREE_NAMES[tree])}</h3>'
        if tree!='goal':
            out+=f'<p class="rt-purpose">{esc(purposes[tree])}</p>'+tree_diagram(state,data,tree,'2027-05-14')
            out+='<details class="record-details"><summary>Read the full statements and action ownership</summary>'
        out+='<div class="item-grid">'
        for n in content['nodes']:
            action=next((x for x in data['actions'] if x['ref']==n['id']),None)
            owner=f'<span class="meta">{esc(action["owner"])} · {esc(action["state"])}</span>' if action else ''
            out+=f'<a class="item-card" href="#item-{n["id"]}"><span class="small-label">{esc(KINDS[n["kind"]])} · Proposed</span><strong>{esc(n["text"])}</strong>{owner}<span class="item-open">Wording, connections and history →</span></a>'
        out+='</div>'
        if tree!='goal':out+='</details>'
    out+='<h3>Unfinished work</h3><ul>'
    out+=''.join(f'<li>{a(b["ref"],b["label"])}</li>' for t in state['trees'].values() for b in t['backlog'])
    return out+'</ul><h3>Monitoring after Stephen steps back</h3>'+paragraphs(data['handover'])+'<h3>The upkeep</h3>'+paragraphs(data['upkeep'])+'</section>'

def progress_view(state,data):
    rows=''
    for w in data['windows']:
        n,d=w['late'];dn,dd=w['decisions'];yes,responses,eligible=w['voice']; status='Baseline' if w['id']=='baseline' else ('Meets all criteria' if qualifies(w) else ('Mixed period' if w['id']=='mixed' else 'Review needed'))
        report=next((r for r in data['reports'] if r.get('window')==w['id']),None)
        title=esc(w['label']); title=f'<a href="#report-{report["id"]}">{title}</a>' if report else title
        rows+=f'<tr><th scope="row">{title}<small>{short_date(w["start"])}–{short_date(w["end"])}</small></th><td data-label="Late dispatches">{n}/{d}<strong>{100*n/d:g}%</strong><span class="bar"><i style="width:{min(100,100*n/d/.3):g}%"></i></span></td><td data-label="Prompt decisions">{dn}/{dd}<strong>{100*dn/dd:g}%</strong></td><td data-label="Overtime, week 1 / 2">{w["overtime"][0]} / {w["overtime"][1]} h<small>{"Not assessed" if w["unpaid"] is None else str(w["unpaid"])+" unpaid hours identified"}</small></td><td data-label="Speaking up">{yes} yes<small>{responses}/{eligible} responded</small></td><td data-label="Decision signal"><span class="tag neutral">{status}</span></td></tr>'
    return f'<section class="view" id="progress" data-view><span class="eyebrow">Predictions, reports and decisions</span><h2 tabindex="-1">Did the client’s problem improve?</h2><p class="lede">First the trial disappointed. Two later windows met the original criteria. Follow-up then detected drift. The record keeps all three findings.</p><div class="table-scroll" tabindex="0" role="region" aria-label="Progress over six observation windows"><table><caption>Original completion rules: ≤10% late; ≥80% prompt decisions; ≤18 overtime hours each week; zero unpaid work; ≥16 positive voice answers and ≥18 responses.</caption><thead><tr><th>Window</th><th>Late dispatches</th><th>Prompt decisions</th><th>Overtime, week 1 / 2</th><th>Speaking up</th><th>Decision signal</th></tr></thead><tbody>{rows}</tbody></table></div><p class="meta">The table shows reported values, including the corrected first trial. A complete action, an improved capacity and a better delivery outcome are different claims.</p>{metric_definitions(data)}<h3>What was expected beforehand</h3>{"".join(prediction_card(p) for p in data["predictions"])}<h3>The reports, including the correction</h3>{"".join(report_card(r,compact=True) for r in data["reports"])}<h3>Closure and handover</h3>{paragraphs(data["handover"])}</section>'

def source_view(data):
    sources=''.join(f'<li><a href="{esc(s["url"])}">{esc(s["title"])}</a><p class="meta">{esc(s["locator"])}</p>{paragraphs(s["note"])}</li>' for s in data['sources'])
    return '<section class="view" id="sources" data-view><span class="eyebrow">Sources and limits</span><h2 tabindex="-1">A fictional client; a grounded method</h2>'+paragraphs(data['standing_note'])+'<h3>Adaptive Persistence</h3>'+paragraphs(data['source_note'])+'<ul class="source-list">'+sources+'</ul><h3>What works here, and what is proposed practice</h3>'+paragraphs(data['capabilities'])+'<h3>What the case does not establish</h3>'+paragraphs('Improvement does not establish a unique cause. Agreement that a map represents a view is not validation of its explanation. Dates identify the fictional sequence; timestamps are not tamper-proof audit evidence.')+paragraphs(data['ap_learning'])+'<h3>One maintained record</h3>'+paragraphs(data['record_note'])+'<p><a href="reason-commons.yaml" download>Download current proposed reasoning (YAML)</a> · <a href="commons.json" download>Download the public case, history and reports (JSON)</a></p></section>'

CSS=r'''
:root{--paper:#f7f5ef;--ink:#222c35;--muted:#66716f;--line:#dcded5;--white:#fffefa;--green:#245e4a;--pale:#e8eee7;--amber:#9b5b25;--blue:#314e69;--serif:Georgia,'Times New Roman',serif}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}a{color:var(--green);text-underline-offset:4px}a:hover{color:#123b2c}button,a{-webkit-tap-highlight-color:transparent}a:focus-visible,button:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:3px solid #b07330;outline-offset:5px}h1,h2,h3,h4,p{overflow-wrap:anywhere}h1,h2{font-family:var(--serif);font-weight:400;line-height:1.12;letter-spacing:-.035em}h1{font-size:clamp(2.5rem,5vw,4.7rem);max-width:900px;margin:.5rem 0 1rem}h2{font-size:clamp(2rem,3.2vw,3rem);margin:1rem 0 1.25rem;max-width:850px}h3{font-size:1.15rem;line-height:1.35;margin:2rem 0 .7rem}h4{font-size:.9rem;margin:1.25rem 0 .3rem}p{margin:.75rem 0 1rem}ul{padding-left:1.2rem}code{font-size:.8rem;overflow-wrap:anywhere}.fiction{background:#253d35;color:#edf2e8;padding:10px 24px;text-align:center;font-size:.8rem;letter-spacing:.025em}.fiction strong{font-weight:600}.topbar{max-width:1280px;margin:auto;padding:24px 36px;display:flex;justify-content:space-between;gap:20px;align-items:center}.brand{font-family:var(--serif);color:var(--ink);font-size:1.3rem;text-decoration:none}.toplinks{display:flex;gap:20px;font-size:.8rem}.hero{max-width:1208px;margin:auto;padding:26px 0 28px}.eyebrow,.small-label{text-transform:uppercase;letter-spacing:.1em;font-size:.7rem;font-weight:700;color:var(--muted)}.hero .intro{font-size:1.07rem;max-width:790px;color:#52605e}.people{display:flex;flex-wrap:wrap;gap:22px;margin:26px 0 10px}.person{display:flex;align-items:center;gap:9px;font-size:.8rem;line-height:1.4}.person small{display:block;color:var(--muted);max-width:180px}.avatar{display:grid;place-items:center;background:#e8e5dc;border:1px solid #d5d7ce;width:35px;height:35px;border-radius:50%;font-size:.65rem;font-weight:700}.tabs{max-width:1208px;margin:auto;display:flex;align-items:center;gap:28px;border-bottom:1px solid var(--line);padding-bottom:0}.tabs a{text-decoration:none;padding:14px 0;border-bottom:3px solid transparent;font-size:.9rem;color:var(--muted)}.tabs a.active{color:var(--green);border-color:var(--green);font-weight:650}.workspace{max-width:1208px;margin:0 auto;display:grid;grid-template-columns:245px minmax(0,1fr);gap:52px;padding:35px 0 70px}.timeline{align-self:start;position:sticky;top:24px}.timeline ol{list-style:none;margin:15px 0;padding:0}.timeline li{border-left:1px solid var(--line)}.timeline a{display:block;padding:8px 13px 10px;margin-left:-1px;text-decoration:none;font-size:.8rem;color:var(--muted);line-height:1.4;border-left:3px solid transparent}.timeline a strong{display:block;font-weight:500;color:var(--ink)}.timeline a.active{background:var(--pale);border-color:var(--green)}.timeline a.active strong{font-weight:650}.timeline small{display:block;font-size:.7rem;margin-bottom:3px}.timeline .record-caption{font-size:.74rem;line-height:1.5;color:var(--muted);border-top:1px solid var(--line);padding-top:15px}.view{max-width:900px;scroll-margin-top:20px}.view+.view{margin-top:70px;padding-top:30px;border-top:1px solid var(--line)}.js .view[hidden]{display:none}.js .view+.view{margin-top:0;border:0;padding-top:0}.entry-meta{display:flex;flex-wrap:wrap;align-items:center;gap:12px;font-size:.74rem;color:var(--muted)}.tag{display:inline-block;border:1px solid #cbd6c9;border-radius:30px;padding:3px 10px;background:var(--pale);color:var(--green);font-size:.68rem;line-height:1.5}.tag.neutral{background:#efeee7;border-color:#deddd4;color:#5e6258}.lede{font-size:1.13rem;line-height:1.6;color:#596460;margin-bottom:1.6rem}.dialogue{border-left:3px solid var(--green);background:#eeeee5;padding:12px 23px;margin:25px 0;font-family:var(--serif);font-size:1.15rem}.dialogue p{margin:.4rem 0}.dialogue strong{font:600 .72rem system-ui;display:block;color:var(--green);letter-spacing:.04em}.change,.report,.prediction,.no-change,.definitions,.statement{background:var(--white);border:1px solid var(--line);border-radius:6px;margin:16px 0;padding:22px}.change-head{display:flex;gap:12px;align-items:center;justify-content:space-between;font-size:.75rem;margin-bottom:14px}.before,.after{padding:13px 15px;line-height:1.6}.before{background:#f3ede5;border-left:3px solid #b88b65;color:#695547}.after{background:#edf2e9;border-left:3px solid #5d8067}.small-label{display:block;margin-bottom:6px}.change p,.meta{font-size:.79rem;line-height:1.6;color:var(--muted)}.next{background:#e7ece3;border-left:3px solid var(--green);padding:18px 22px;margin:28px 0}.next p:last-child{margin-bottom:0}.release{border:1px solid #b8c5ba;padding:16px 20px;font-size:.82rem;margin-top:24px}.release p{margin-bottom:0}.entry-nav{margin-top:40px;padding-top:22px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:16px;align-items:center;font-size:.8rem}.entry-nav>span{color:var(--muted)}.button{display:inline-block;background:var(--green);color:white;padding:11px 16px;text-decoration:none;border-radius:4px}.button:hover{background:#163e2e;color:white}.report h3,.prediction h3{margin:.5rem 0 1rem}.report .tag{margin-bottom:7px}.prediction{border-top:3px solid var(--blue)}blockquote{font-family:var(--serif);font-size:1.1rem;margin:15px 0;padding-left:16px;border-left:2px solid #c5cccb}.definitions{padding:0}.definitions summary{padding:18px 20px;cursor:pointer;font-size:.85rem;font-weight:600}.definitions article{padding:0 20px 20px;border-top:1px solid var(--line)}dl{display:grid;grid-template-columns:100px minmax(0,1fr);gap:9px 15px;font-size:.78rem}dt{font-weight:650}dd{margin:0;color:#58635f}.item-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.item-card{padding:18px;background:var(--white);border:1px solid var(--line);border-radius:5px;text-decoration:none;color:var(--ink);display:flex;flex-direction:column;gap:10px;font-size:.87rem;line-height:1.55}.item-card strong{font-weight:500}.item-card:hover{border-color:var(--green)}.item-open{font-size:.72rem;color:var(--green)}.notice{font-size:.8rem;color:var(--muted);padding:12px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.connections li{margin:14px 0;font-size:.86rem}.relation{color:var(--muted);font-size:.8rem}.history-event{padding:18px 0;border-top:1px solid var(--line)}.history-event>a{font-size:.8rem}.mechanism{margin:30px 0;padding:20px;background:#eeeee7;border-radius:6px}.mechanism figcaption{font-size:.72rem;color:var(--muted);margin-bottom:18px}.flow{max-width:560px;margin:auto}.map-node{display:block;border:1px dashed #7d9383;border-radius:4px;background:var(--white);padding:12px 16px;text-align:center;text-decoration:none;font-size:.82rem;color:var(--ink)}.map-node:hover{background:#e1eadf}.joint-sources{display:grid;grid-template-columns:1fr 1fr;gap:12px}.and{text-align:center;font-size:.7rem;font-weight:700;margin:8px 0}.flow-arrow{text-align:center;font-size:.68rem;color:var(--muted);padding:7px}.harm-branch{border-top:1px solid var(--line);margin-top:20px;padding-top:15px;font-size:.78rem}.harm-branch .map-node{display:inline-block;margin-top:8px;border-color:#ae8055;background:#f5efe5}.table-scroll{overflow:auto;max-width:100%;margin:25px 0;border:1px solid var(--line);border-radius:5px}table{border-collapse:collapse;width:100%;font-size:.75rem;background:var(--white)}caption{text-align:left;padding:15px;background:#e8ede5;color:#4d5c53;font-size:.72rem}th,td{text-align:left;padding:14px 10px;border-bottom:1px solid var(--line);vertical-align:top;min-width:95px}thead th{font-size:.67rem;line-height:1.5;color:var(--muted)}tbody th{min-width:132px;font-weight:600}td strong{display:block;font-size:1rem;font-weight:500}td small,th small{display:block;color:var(--muted);font-size:.63rem;font-weight:400;margin-top:3px;line-height:1.45}.bar{display:block;background:#e4e8dd;height:4px;width:64px;margin-top:9px}.bar i{display:block;height:4px;background:#78927a}.source-list{list-style:none;padding:0}.source-list li{border-top:1px solid var(--line);padding:18px 0}.source-list p{font-size:.85rem;margin:.4rem 0}.footer{border-top:1px solid var(--line);max-width:1208px;margin:auto;padding:25px 0 45px;display:flex;justify-content:space-between;gap:25px;font-size:.75rem;color:var(--muted)}.skip{position:absolute;left:-9999px}.skip:focus{left:20px;top:10px;background:white;padding:12px;z-index:10}.mobile-entries{display:none}.js .fallback{display:none}.scope{font-size:.8rem;color:var(--muted);max-width:850px}.progress-summary{padding:18px;background:var(--pale);border-radius:6px}.sources-short{color:var(--muted);font-size:.75rem}
@media(min-width:1400px){.hero,.tabs,.workspace,.footer{max-width:1250px}.workspace{gap:65px}}
@media(max-width:1250px){.hero,.tabs,.workspace,.footer{margin-left:32px;margin-right:32px}.workspace{gap:35px;grid-template-columns:220px minmax(0,1fr)}}
@media(max-width:850px){.workspace{grid-template-columns:1fr}.timeline{position:static}.timeline ol,.timeline .record-caption{display:none}.timeline{padding-bottom:15px;border-bottom:1px solid var(--line)}.mobile-entries{display:block;width:100%;padding:12px;background:var(--white);border:1px solid var(--line);border-radius:4px;color:var(--ink);font-size:.8rem}.timeline>.eyebrow{display:none}.workspace{gap:25px}.hero{padding-top:10px}.hero .intro{font-size:.96rem}.people{gap:14px}.person small{max-width:130px}.tabs{gap:22px}.topbar{padding:20px 25px}.footer{flex-wrap:wrap}}
@media(max-width:520px){.hero,.tabs,.workspace,.footer{margin-left:20px;margin-right:20px}.fiction{font-size:.65rem;padding:9px 15px}.topbar{padding:18px 20px}.toplinks{gap:12px;font-size:.7rem}.brand{font-size:1.1rem}h1{font-size:2.65rem}h2{font-size:2.05rem}.people{display:grid;grid-template-columns:1fr 1fr;gap:13px}.person{font-size:.72rem;align-items:flex-start}.avatar{width:28px;height:28px;min-width:28px;font-size:.55rem}.person small{font-size:.64rem;max-width:120px}.tabs{gap:22px}.tabs a{font-size:.8rem}.workspace{padding-top:20px}.item-grid{grid-template-columns:1fr}.change,.report,.prediction,.statement{padding:16px}.change-head{align-items:flex-start}.change-head a{max-width:115px;text-align:right}.joint-sources{grid-template-columns:1fr}.entry-nav{align-items:flex-start}.entry-nav>a,.entry-nav>span{max-width:55%}.button{padding:10px 12px}.entry-meta{gap:8px;font-size:.67rem}.dialogue{padding:12px 16px}dl{grid-template-columns:1fr;gap:2px}dd{margin-bottom:12px}.mechanism{padding:15px}.table-scroll{max-width:calc(100vw - 40px)}.table-scroll table{min-width:710px}.footer{font-size:.7rem}.toplinks a:first-child{display:none}}
@media(max-width:520px){.table-scroll{overflow:visible;border:0}.table-scroll table{min-width:0}.table-scroll thead{display:none}.table-scroll table,.table-scroll tbody{display:block}.table-scroll tr{display:grid;grid-template-columns:1fr 1fr;border:1px solid var(--line);border-radius:4px;margin-bottom:12px;overflow:hidden}.table-scroll th,.table-scroll td{display:block;min-width:0;padding:12px}.table-scroll tbody th,.table-scroll td:last-child{grid-column:1/-1}.table-scroll td::before{content:attr(data-label);display:block;font-size:.62rem;color:var(--muted);margin-bottom:5px}.table-scroll caption{display:block}.table-scroll th small{display:inline;margin-left:8px}.table-scroll td:last-child{border-bottom:0}.hero h1{margin-bottom:.6rem}.hero .intro{font-size:.91rem}.hero{padding-bottom:15px}.people{margin:18px 0 8px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{.timeline,.tabs,.toplinks,.entry-nav,.footer,.mobile-entries{display:none!important}.workspace{display:block;margin:0;padding:0}.js .view[hidden],.view{display:block!important;border-top:1px solid #bbb!important;margin:25px 0!important;padding-top:20px!important}.hero{margin:0}.table-scroll{overflow:visible}table{min-width:0!important}.change,.report,.prediction{break-inside:avoid}a{color:inherit}}
.tree-use{margin:28px 0 32px;padding:24px;border:1px solid #bac9b9;border-top:4px solid var(--green);border-radius:6px;background:#f1f3eb}.tree-use>h3{font-family:var(--serif);font-size:1.6rem;font-weight:400;line-height:1.25;margin:.5rem 0 20px;letter-spacing:-.02em}.rt-question{border-left:3px solid #6e8c78;padding:4px 16px;margin:15px 0 22px}.rt-question p{font-size:.95rem;margin:.3rem 0}.reasoning-tree{margin:22px 0;background:var(--white);padding:20px 16px;border:1px solid var(--line);border-radius:5px}.reasoning-tree>figcaption{font-size:.8rem;font-weight:650;color:var(--green)}.rt-legend{font-size:.69rem;color:var(--muted);line-height:1.5;margin:7px 0 22px}.rt-component+.rt-component{margin-top:20px;padding-top:18px;border-top:1px solid var(--line)}.rt-path{min-width:0;display:flex;flex-direction:column;align-items:stretch}.rt-node{max-width:350px;width:100%;margin:0 auto;background:#fcfdf8;border:1px dashed #879a87;border-radius:4px;min-width:0}.rt-node>a{display:block;padding:13px 12px;text-align:center;text-decoration:none;color:var(--ink)}.rt-node>a:hover{background:#edf2e7}.rt-standing,.rt-kind{display:block;font-size:.6rem;line-height:1.5;color:var(--muted);letter-spacing:.04em}.rt-kind{text-transform:uppercase;margin:2px 0 7px}.rt-node strong{display:block;font-size:.83rem;line-height:1.5;font-weight:550;overflow-wrap:anywhere}.rt-joint,.rt-inputs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;align-items:end}.rt-joint{padding-bottom:13px;border-bottom:1px dashed #879a87;position:relative}.rt-joint>.rt-path::after{content:'';display:block;height:13px;margin:0 auto -13px;border-left:1px dashed #879a87}.rt-and{align-self:center;text-align:center;margin:9px auto 0;padding:4px 12px;border:1px solid #a6b8a1;border-radius:6px;background:#e8eee3;font-size:.72rem;font-weight:700}.rt-and small{display:block;color:var(--muted);font-weight:400;font-size:.58rem}.rt-edge{max-width:350px;margin:8px auto;display:flex;flex-direction:column;align-items:center;gap:3px;text-align:center;color:var(--muted);font-size:.69rem;padding:5px 8px;min-width:0;width:100%;border-radius:4px}.rt-edge>span[aria-hidden]{font-size:1.1rem;line-height:1.1}.rt-edge>a{font-size:.7rem}.rt-input{min-width:0}.rt-inputs{margin-bottom:8px}.rt-focused{border:2px solid #b37835;background:#fff9ed}.rt-focus-label{display:block;width:max-content;max-width:100%;margin:7px auto 0;padding:2px 6px;background:#f2dfbc;color:#744c1c;font-size:.54rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;border-radius:3px}.rt-edge .rt-focus-label{margin:0 auto 3px}.rt-evidence{border-top:1px solid #dce0d1;padding:11px 13px;background:#f0f3e9;text-align:left}.rt-evidence p{font-size:.75rem;line-height:1.6;margin:5px 0 8px}.rt-evidence small{display:block;font-size:.62rem;line-height:1.5;color:var(--muted)}.rt-evidence .small-label{font-size:.54rem}.rt-edge .rt-evidence{border:1px solid #dce0d1;width:100%}.rt-branch-label{border-top:1px solid #d8ddce;padding-top:20px;margin:25px 0 15px;font-size:.75rem;font-weight:600;color:#895b2e}.rt-harm>.rt-path>.rt-node{border-color:#b18b63;background:#fcf6ec}.rt-unconnected{font-size:.7rem;padding:10px 13px;border:1px dotted #9d9c8e;color:#6f7066;background:#f4f2e9}.rt-response,.rt-decision{padding:18px 20px;margin:18px 0 0;background:var(--white);border-left:3px solid #9eaf9b}.rt-response p,.rt-decision p{font-size:.9rem;margin:.4rem 0 0}.rt-decision{background:#e1eadd;border-color:var(--green)}.rt-before{margin:18px 0;border:1px solid var(--line);border-radius:5px;background:#f8f6ef}.rt-before>summary{padding:12px 16px;font-size:.78rem;font-weight:650;cursor:pointer}.rt-before>.reasoning-tree{margin:0;border:0;border-top:1px solid var(--line);border-radius:0;background:#faf8f1}.rt-revision{text-align:center;margin:25px 0 12px;color:var(--green);font-weight:650;font-size:.8rem}.record-details{margin:20px 0;padding:0 16px 12px;border:1px solid var(--line);border-radius:5px;background:#fdfcf7}.record-details>summary{padding:14px 0;font-size:.8rem;cursor:pointer;font-weight:600}.record-details .change{margin-top:10px}.rt-purpose{font-size:1rem;color:#4c6456;margin:0 0 15px}.record-details .item-grid{padding-top:12px}.rt-before[open]>summary{border-bottom:0}
@media(max-width:520px){.tree-use{padding:17px 12px;margin:24px 0}.tree-use>h3{font-size:1.4rem}.reasoning-tree{padding:15px 9px}.rt-joint,.rt-inputs{gap:8px}.rt-node>a{padding:10px 7px}.rt-node strong{font-size:.76rem;line-height:1.5}.rt-kind,.rt-standing{font-size:.53rem}.rt-node strong{white-space:normal}.rt-joint .rt-node strong,.rt-inputs .rt-node strong{font-size:.73rem}.rt-question{padding:3px 11px}.rt-question p{font-size:.87rem}.rt-evidence{padding:10px 9px}.rt-evidence p{font-size:.7rem}.rt-evidence small{font-size:.58rem}.rt-response,.rt-decision{padding:15px}.rt-response p,.rt-decision p{font-size:.84rem}.rt-legend{font-size:.63rem}.rt-before>summary{font-size:.7rem;padding:11px 12px}.rt-edge{padding:5px 4px}.rt-inputs .rt-edge>a{font-size:.62rem}.rt-inputs .rt-focus-label{font-size:.47rem;letter-spacing:0}.rt-before>.reasoning-tree{padding:14px 8px}}
@media print{.tree-use{break-inside:auto}.rt-node,.rt-evidence{break-inside:avoid}.record-details{display:block}.record-details>*{display:block!important}.reasoning-tree{break-inside:auto}}

.rt-before>h4{padding:12px 16px;margin:0;font-size:.78rem}.rt-before>.record-details{margin:0 10px 12px}

'''

JS=r'''
document.documentElement.classList.add('js');
const views=[...document.querySelectorAll('[data-view]')];
const entries=[...document.querySelectorAll('[data-entry-link]')];
const picker=document.querySelector('#entry-picker');
let initial=true;
function route(){
  let id=decodeURIComponent(location.hash.slice(1))||'entry-2027-01-11';
  if(id==='changes')id='entry-2027-01-11';
  if(id==='main'){if(!initial){document.querySelector('#main').focus();return;}id='entry-2027-01-11';}
  let selected=views.find(v=>v.id===id);
  if(!selected){id='entry-2027-01-11';selected=views.find(v=>v.id===id);}
  views.forEach(v=>v.hidden=v!==selected);
  const isEntry=id.startsWith('entry-');
  entries.forEach(a=>{const active=a.hash==='#'+id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','step');else a.removeAttribute('aria-current');});
  if(isEntry)picker.value=id;
  document.querySelectorAll('[data-tab]').forEach(a=>{const active=(a.dataset.tab==='changes'&&isEntry)||(a.dataset.tab==='current'&&(id==='current'||id.startsWith('item-')))||(a.dataset.tab==='progress'&&(id==='progress'||id.startsWith('report-')||id.startsWith('prediction-')));a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  document.title=(selected.querySelector('h2')?.textContent||'Northbank Print')+' · Northbank Print · Reason Commons';
  if(!initial){selected.scrollIntoView({block:'start',behavior:'instant'});selected.querySelector('h2')?.focus({preventScroll:true});}
  initial=false;
}
picker.addEventListener('change',()=>{location.hash=picker.value;});
window.addEventListener('hashchange',route);
route();
'''

def render(state,data):
    public=deepcopy(state);public.pop('change_acceptances',None)
    payload={'reasoning':public,'engagement':data}
    raw=json.dumps(payload,ensure_ascii=False,indent=2)
    people=''.join(f'<div class="person" title="Fictional stakeholder: {esc(p["concern"])}"><span class="avatar" aria-hidden="true">{p["initials"]}</span><span><strong>{esc(p["name"])}</strong><small>{esc(p["role"])}</small></span></div>' for p in data['people'])
    timeline=''.join(f'<li><a data-entry-link href="#entry-{e["date"]}"><small>{short_date(e["date"])} · {esc(e["stage"])}</small><strong>{esc(e["title"])}</strong></a></li>' for e in data['events'])
    options=''.join(f'<option value="entry-{e["date"]}">{short_date(e["date"])} · {esc(e["title"])}</option>' for e in data['events'])
    sections=''.join(event_view(e,state,data) for e in data['events'])+current_view(state,data)+progress_view(state,data)
    for ref,item in index(state).items():sections+=item_view(ref,item,state,data)
    for p in data['predictions']:
        reports=[r for r in data['reports'] if r.get('prediction')==p['id']]
        sections+=f'<section class="view" id="prediction-{p["id"]}" data-view><a href="#progress">← Progress and learning</a><h2 tabindex="-1">{esc(p["title"])}</h2>{prediction_card(p)}<h3>Reports against this original expectation</h3>'+''.join(report_card(r,compact=True) for r in reports)+'</section>'
    for r in data['reports']:
        prediction=next((p for p in data['predictions'] if p['id']==r.get('prediction')),None)
        event=next((e for e in data['events'] if r['id']==e.get('report') or r['id'] in e.get('additional_reports',[])),None)
        sections+=f'<section class="view" id="report-{r["id"]}" data-view><a href="#progress">← Progress and learning</a><h2 tabindex="-1">{esc(r["title"])}</h2>{report_card(r)}'+(f'<p><a href="#entry-{event["date"]}">Read the meeting, interpretation and next decision →</a></p>' if event else '')+(prediction_card(prediction) if prediction else '<p class="meta">This report reviews the retained success criteria; it is not attached retrospectively to a new prediction.</p>')+'</section>'
    sections+=source_view(data)
    html=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Northbank Print · Reason Commons</title><meta name="description" content="Follow one fictional Adaptive Persistence engagement through its maintained commons, decisions, change history and outcome reports."><style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to the commons</a><div class="fiction"><strong>Fictional worked commons</strong> · People, dialogue, dates and outcomes are invented · Read-only</div>
<header class="topbar"><a class="brand" href="/">Reason Commons</a><nav class="toplinks" aria-label="About this demonstration"><a href="/demos/reason-commons-in-use/index.html">Other commons ↗</a><a href="#sources">Sources &amp; limits</a></nav></header>
<div class="hero"><span class="eyebrow">A client engagement, from intake to follow-up</span><h1>Northbank Print</h1><p class="intro">Twenty-two people. Two sites. A shared goal: keep delivery promises without hidden overtime.</p><div class="people">{people}</div><p class="scope">Northbank Print · 11 January–2 April 2027 · Follow-up 14 May · One maintained commons</p></div>
<nav class="tabs" aria-label="Views of the same commons"><a data-tab="changes" href="#entry-2027-01-11">Change log</a><a data-tab="current" href="#current">Current commons</a><a data-tab="progress" href="#progress">Progress &amp; learning</a></nav>
<div class="workspace"><aside class="timeline"><span class="eyebrow">Follow the engagement</span><label class="skip" for="entry-picker">Choose an engagement entry</label><select class="mobile-entries" id="entry-picker">{options}</select><ol>{timeline}</ol><p class="record-caption">Follow the highlighted statement or arrow. What does Stephen ask? What do clients check? What decision follows?<br><br>Working updates are separate from the three deliberate internal releases.</p></aside><main id="main" tabindex="-1"><p class="fallback notice">Without JavaScript, all entries, statements and reports remain readable below. Links lead to the corresponding section.</p>{sections}</main></div>
<footer class="footer"><span>A fictional instantiation of AP, prepared for Stephen Le’s consideration.</span><span><a href="reason-commons.yaml" download>Current YAML</a> · <a href="commons.json" download>Case + history JSON</a> · <a href="#sources">Sources</a></span></footer>
<script id="commons-data" type="application/json">{raw.replace('<',chr(92)+'u003c')}</script><script>{JS}</script></body></html>'''
    return {'index.html':html+'\n','commons.json':raw+'\n','reason-commons.yaml':'# Fictional worked case. All reasoning is assistant-proposed; story endorsements are fictional.\n'+yaml.safe_dump(public,sort_keys=False,allow_unicode=True,width=100000)}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    state,data=load();validate(state,data);outputs=render(state,data)
    if args.check:
        drift=[name for name,text in outputs.items() if not (DEST/name).exists() or (DEST/name).read_text()!=text]
        require(not drift,'Generated output drift: '+', '.join(drift))
        print('Canonical reasoning, history, prospective predictions and all three exports agree.')
    else:
        DEST.mkdir(parents=True,exist_ok=True)
        for name,text in outputs.items():(DEST/name).write_text(text)
        print(f'Built {len(outputs)} files in {DEST}')

if __name__=='__main__':main()
