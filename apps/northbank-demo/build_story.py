#!/usr/bin/env python3
"""Build the illustrated AP walkthrough from the dated case and reviewed story source."""
from pathlib import Path
from html import escape as e
import argparse
import json
import build

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'website/explainers/northbank-print/index.html'
SOURCE=ROOT/'ltp/examples/northbank-print/story.json'
TEMPLATE=Path(__file__).with_name('story-template.html')

def small(text): return f'<span class="small">{text}</span>'
def note(text): return f'<p class="drawing-note">{text}</p>'
def stamp(text): return f'<span class="stamp">{text}</span>'
def arrow(text='may contribute to'): return f'<div class="arrow"><span>{text}</span><i aria-hidden="true">↓</i></div>'
def node(text,kind,ref,issue=False):
    return f'<div class="claim {"issue" if issue else ""}" data-ref="{ref}"><span class="standing">[Proposed]</span><span class="kind">{kind}</span><strong>{text}</strong></div>'
def chain(nodes,label='may contribute to',horizontal=False):
    return '<div class="chain '+('horizontal' if horizontal else '')+'">'+arrow(label).join(nodes)+'</div>'
def joint(nodes,target,link):
    return f'<div class="joint" data-link="{link}"><div class="joint-sources">'+''.join(nodes)+f'</div><div class="join-lines" aria-hidden="true"></div><div class="and">AND</div><div class="joint-relation">Together, may contribute to</div><div class="joint-stem" aria-hidden="true">↓</div>{target}</div>'
def dots(n,total,unit='order',issue=True):
    return f'<div class="marks" style="--cols:{10 if total>=40 else 5}" role="img" aria-label="{n} highlighted {unit}s out of {total}">'+''.join(f'<span class="mark {"selected" if i<n else ""} {"neutral" if not issue else ""}" aria-hidden="true"></span>' for i in range(total))+'</div>'
def count(n,d,label,sub='',issue=False):
    return f'<div class="count {"issue-text" if issue else ""}"><div><b>{n}</b><span> / {d}</span></div><strong>{label}</strong>{small(sub) if sub else ""}</div>'
def metric(label,value,sub=''): return f'<div class="metric"><span>{label}</span><strong>{value}</strong>{small(sub) if sub else ""}</div>'
def panel(content,cls=''): return f'<div class="paper-panel {cls}">{content}</div>'
def eyebrow(t): return f'<p class="diagram-kicker">{t}</p>'
def ticket(status='ORIGINAL PROMISE',bottom='Standard repeat order'):
    return f'<div class="order-ticket"><span class="ticket-label">NORTHBANK PRINT</span><div class="ticket-rule"></div><strong>One order.<br>One promise.</strong><span class="ticket-bottom">{bottom}</span>{stamp(status)}</div>'
def person(name,role,letter=None):
    return f'<div class="person"><span class="portrait" aria-hidden="true">{letter or name[0]}</span><span><strong>{name}</strong><small>{role}</small></span></div>'
def voice(yes,responses,eligible=20):
    return '<div class="voice-marks" role="img" aria-label="'+f'{yes} yes, {responses-yes} no and {eligible-responses} missing of {eligible} eligible'+ '">'+''.join(f'<span class="voice-person {"yes" if i<yes else "no" if i<responses else "missing"}" aria-hidden="true">'+('●' if i<yes else '×' if i<responses else '?')+'</span>' for i in range(eligible))+'</div>'+f'<div class="voice-key"><span><b>{yes}</b> yes</span><span><b>{responses-yes}</b> no</span><span><b>{eligible-responses}</b> missing</span></div>'

def legacy_art(key):
    if key=='opening':
        return eyebrow('A print business · 22 people · two sites')+ '<div class="workshop" aria-hidden="true"><svg viewBox="0 0 600 190"><g filter="url(#rough)" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 158V72l74-40 74 40v86M15 72h163M216 158V68l73-35v35l73-35v35l73-35v125M10 159h570"/><path d="M58 158v-53h47v53M122 101h24v29h-24zM246 100h36v31h-36zM306 100h36v31h-36zM367 100h36v31h-36zM460 158V99h90v59M475 119h60"/></g><g fill="currentColor" font-size="13" font-family="system-ui"><text x="55" y="184">CUSTOMER OFFICE</text><text x="272" y="184">WORKSHOP</text></g></svg></div>'+ticket('LATE')+'<div class="people-row">'+person('Maya','Managing director')+person('Imani','Operator · staff representative')+'</div>'
    if key=='question':
        return eyebrow('11 January · Stephen opens the inquiry')+'<div class="question-sheet"><span class="quote-mark" aria-hidden="true">“</span><p>What would a customer notice if this worked<span class="issue-text">?</span></p><div class="question-rule"></div><p>What must employees be able to rely on<span class="issue-text">?</span></p></div>'+person('Stephen','Facilitator')
    if key=='goal':
        return eyebrow('Goal · agreed within the fiction')+node('Dispatch reliably within paid time;<br>hear concerns.','Goal','nb-g-goal')+'<div class="goal-parts"><div><span aria-hidden="true">↗</span><strong>Keep the date</strong></div><div><span aria-hidden="true">◷</span><strong>Pay for the time</strong></div><div><span aria-hidden="true">“</span><strong>Hear the concern</strong></div></div>'+note('Standard repeat orders only. The representatives check this goal with their teams.')
    if key=='baseline':
        return eyebrow('Baseline · 4–15 January')+count(20,80,'orders dispatched late','Each mark is one order.',True)+dots(20,80)+ '<div class="baseline-second">'+metric('Prompt decisions','12 / 40','30% · authorized and communicated')+'</div>'+note('Late means after the original promised date. Renegotiating a date does not erase a miss.')
    if key=='finish':
        return eyebrow('Agreed during Orient · before the trial')+'<div class="window-pair">'+''.join(panel(f'<span class="sheet-top">FORTNIGHT {i}</span><div class="blank-check">○</div><p><b>≤10%</b> late</p><p><b>≥80%</b> prompt decisions</p>','window-sheet') for i in [1,2])+'</div>'+note('Two consecutive, nonoverlapping windows. At least 60 orders in each; all safeguards must also pass.')
    if key=='safeguards':
        return eyebrow('The original safeguards')+'<div class="guardrails">'+panel('<div class="large-symbol" aria-hidden="true">◷</div><h3>Paid time</h3><p><b>≤18 hours</b> overtime in each week, across all 22 employees.</p><p><b>Zero</b> unpaid work.</p>')+panel('<div class="large-symbol" aria-hidden="true">“</div><h3>Speaking up</h3><p><b>≥16 yes</b> answers out of 20 eligible employees.</p><p><b>≥18 responses</b> required.</p>')+'</div>'+note('The pulse asks whether an unrealistic commitment can be raised without penalty. Missing answers stay missing.')
    if key=='assessment':
        return eyebrow('Assess · different positions, shared orders')+'<div class="two-sides">'+panel(person('Ben','Customer services lead')+'<h3>Customer office</h3><p>Urgent deadlines.<br>Changed specifications.</p>')+panel(person('Rosa','Production lead')+'<h3>Workshop</h3><p>Materials.<br>Workable production slots.</p>')+'</div><div class="environment">Changing customer demands &amp; supplier dependence</div>'+note('Coordination · adaptability · robustness. The assessment considers all three before the group selects an adjustment.')
    if key=='first-cause':
        return eyebrow('Current Reality · initial explanation, 18 January')+chain([node('Sales shares<br>changes slowly.','Cause','nb-r-authority',True),node('Some instructions<br>are incomplete.','Undesirable effect','nb-r-incomplete')], 'proposed contribution')+'<div class="evidence-slip"><b>Ben’s check</b><span>“On these orders I passed the change on immediately.”</span></div>'+note('The challenged arrow sets the next task: trace three changed orders. Late dispatches are not yet connected in this draft.')
    if key=='trace':
        return eyebrow('Order trace · two of three inspected orders')+'<div class="order-trace"><div><span class="trace-dot">1</span><strong>Change shared promptly</strong><small>Ben’s timestamped email</small></div><span class="sequence">then ↓</span><div class="waiting"><span class="trace-dot">2</span><strong>Delivery approval waits</strong><small>Only Maya can authorize it</small></div><span class="sequence">then ↓</span><div><span class="trace-dot">3</span><strong>Job enters production</strong><small>The decision is still unresolved</small></div></div>'+note('The sequence locates a different wait. It does not establish the cause of every late order.')
    if key=='causal-and':
        return eyebrow('Current Reality · revised explanation, 22 January')+joint([node('Changed orders can wait<br>for authorized decisions.','Cause','nb-r-authority',True),node('Some jobs are released<br>before decisions are resolved.','Cause','nb-r-release')],node('Some jobs enter production<br>with incomplete instructions.','Undesirable effect','nb-r-incomplete'),'nb-r-l1')+note('AND matters: the recorded explanation needs both conditions. Neither arrow is being treated as proved.')
    if key=='causal-next':
        return eyebrow('Current Reality · the next connection')+chain([node('Some jobs enter production<br>with incomplete instructions.','Undesirable effect','nb-r-incomplete'),node('Some dispatches miss<br>their original promises.','Undesirable effect','nb-r-late',True)])+note('This is one mechanism to test. Materials, machine capacity and peak demand remain live questions.')
    if key=='capacity':
        return eyebrow('The group chooses its first adjustment')+'<div class="capacity-list"><div class="chosen"><span>01</span><div><b>Coordination</b><p>Who can settle a changed commitment?</p></div>'+stamp('START HERE')+'</div><div><span>02</span><div><b>Adaptability</b><p>Review results and revise the approach.</p></div></div><div><span>03</span><div><b>Robustness</b><p>Keep decisions moving during absence.</p></div></div></div>'+note('Choose a bounded test, then trace ten more orders before trial readiness.')
    if key=='values':
        return eyebrow('An ACT-informed conversation · Ben’s example')+'<div class="values-sheet"><div><span>WHAT MATTERS</span><strong>“Dependability.”</strong></div><div><span>A DIFFICULT THOUGHT</span><strong>“If I ask for time,<br>we’ll lose the customer.”</strong></div><div class="habit"><span>A HABIT TO EXAMINE</span><strong>Promise immediately.</strong></div></div>'+note('The shared implication: acknowledge urgency while checking whether the promise is feasible.')
    if key=='limits':
        return eyebrow('The same discussion · Imani’s check')+'<div class="limit-sheet"><div class="calendar-date"><span>REQUESTED DATE</span><b>?</b><small>May be infeasible</small></div><blockquote>“Some dates really<br>are impossible.”</blockquote></div>'+panel('<span class="private-lock" aria-hidden="true">▱</span><strong>Private personal sheets</strong><p>Voluntary disclosure.<br>Shared practical implications only.</p>','private-sheet')+note('A real workload constraint remains a real constraint. It is not evidence that someone resists change.')
    if key=='first-future':
        return eyebrow('Future Reality · the first working prediction')+chain([node('Representatives meet<br>each morning.','Injection','nb-f-adjustment'),node('Changed orders receive<br>prompt authorized decisions.','Predicted effect','nb-f-decisions')])+'<div class="assumption"><span>ASSUMPTION TO CHECK</span><strong>Maya attends and can authorize answers.</strong></div>'+note('A proposed arrow makes the assumption discussable before the trial.')
    if key=='harm-branch':
        return eyebrow('Future Reality · a separate harmful branch')+chain([node('Representatives meet<br>each morning.','Injection','nb-f-adjustment'),node('Coordination work can extend<br>beyond paid hours.','Undesirable effect','nb-f-overwork',True)])+note('The intended chain is decisions → ready instructions → fewer late dispatches. This separate branch keeps the possible cost visible, too.')
    if key=='readiness':
        return eyebrow('29 January · preparation is reviewed')+'<div class="trace-count">'+count(6,10,'additional changed jobs','had unresolved decisions')+dots(6,10,'job')+'</div><div class="readiness-list"><div><span>✓</span>Shared change list</div><div><span>✓</span>Paid meeting time</div><div class="issue-text"><span>○</span>Named deputy still missing</div></div>'+note('The plan relies on Maya attending. Unfinished cover remains visible rather than becoming assumed readiness.')
    if key=='prediction-one':
        return prediction('29 JANUARY','1–12 FEBRUARY','32 / 40','12 / 80','Expectation 1 · recorded before starting')
    if key=='target-distinction':
        return eyebrow('Two different standards · same 80-order example')+'<div class="target-pair">'+panel('<span>FIRST-TRIAL EXPECTATION</span><strong>≤12 <small>/ 80 late</small></strong><p>An initial improvement to test.</p>')+panel('<span>COMPLETION CRITERION</span><strong>≤8 <small>/ 80 late</small></strong><p>Equivalent to the original 10% ceiling.</p>')+'</div>'+note('Release 1 shares the reviewed baseline and trial. It does not relax the finish line.')
    if key=='early':
        return eyebrow('5 February · preliminary, not yet fully checked')+'<div class="result-twins">'+count(17,20,'reported prompt decisions','First-week report')+count(6,40,'late dispatches','First week',True)+'</div>'+panel('<span class="decision-label">DECISION</span><strong>Continue the same trial.</strong><p>Check the count before expanding.</p>','decision-sheet')+note('A promising first week earns another week of checking, not a wider rollout.')
    if key=='correction':
        return eyebrow('12 February · correction appended to the report')+'<div class="correction-pair"><div class="old-count"><span>ORIGINAL REPORT</span><b>17 <small>/ 20</small></b><p>Some acknowledgments counted.</p></div><span class="correct-arrow" aria-hidden="true">→</span><div class="new-count"><span>CORRECTED REPORT</span><b>11 <small>/ 20</small></b><p>Authorized answer communicated in time.</p></div></div><div class="definition"><b>A prompt decision needs all three:</b><span>Authority · customer communication · by next working day</span></div>'+note('Both versions remain. The first week’s report changes; the definition does not.')
    if key=='trial-result':
        return eyebrow('1–12 February · first complete trial window')+'<div class="comparison"><div class="compare-head"><span></span><span>Expected</span><span>Observed</span></div><div><strong>Prompt decisions</strong><span>≥32 / 40</span><b class="issue-text">21 / 40</b></div><div><strong>Late dispatches</strong><span>≤12 / 80</span><b class="issue-text">16 / 80</b></div></div>'+note('Only 8/10 meetings occurred; Maya missed two. Worsening paper supply affected four late jobs. These observations guide inquiry without identifying one cause.')
    if key=='harm-observed':
        return eyebrow('12 February · benefit and burden reviewed together')+'<div class="harm-summary"><div class="hours-correction"><span>TWO UNPAID HOURS FOUND, THEN PAID</span><strong>17 <i>→</i> <b>19</b><small>hours overtime · week two</small></strong><p>Original weekly ceiling: 18 hours</p></div><div class="voice-mini"><span>SPEAKING UP · 20 ELIGIBLE</span>'+voice(10,16)+'</div></div>'+stamp('PAUSE EXPANSION')+note('The work is paid and the report corrected. Four missing pulse answers remain unknown.')
    if key=='missing-authority':
        return eyebrow('Future Reality · return to the first arrow')+chain([node('Representatives meet<br>each morning.','Injection','nb-f-adjustment'),node('Changed orders receive<br>prompt authorized decisions.','Predicted effect','nb-f-decisions',True)],'does a meeting ensure authority?')+'<div class="evidence-slip"><b>Imani’s correction</b><span>“People used the process. Nobody in the room could authorize the answer.”</span></div>'+note('Stephen withdraws the AI brief’s “reluctant staff” interpretation. The next revision concerns authority and paid time.')
    if key=='revised-and':
        return eyebrow('Future Reality · revised joint condition')+joint([node('Delegate routine replans;<br>review exceptions.','Injection','nb-f-adjustment'),node('Provide authorized cover<br>and paid preparation.','Existing condition','nb-f-cover',True)],node('Decide and communicate<br>by the next working day.','Predicted effect','nb-f-decisions'),'nb-f-l1')+note('The changed arrangement receives fresh fictional agreement. Its effects still need to be tested.')
    if key=='actions':
        return eyebrow('Transition · preparations before 22 February')+'<div class="action-tree"><div class="action-sources">'+node('Maya defines authority<br>and names a deputy.','Action','nb-t-authority')+node('Maya and Rosa allocate<br>paid preparation time.','Action','nb-t-time')+'</div><div class="precedes-lines"><span>comes before ↘</span><span>↙ comes before</span></div>'+node('Representatives review<br>results fortnightly.','Action','nb-t-review')+'</div>'+note('These lines specify order. Finishing the preparation does not prove that the trial will succeed.')
    if key=='prepared':
        return eyebrow('22 February · action and effect are different claims')+'<div class="prepared-sheet"><div><span>PREPARATION</span><strong>Authority, deputy<br>and paid time.</strong><b>In place before restart</b></div><div class="unknown-effect"><span>EFFECT</span><strong>Better decisions?<br>Fewer late orders?</strong><b>Still to be observed</b></div></div>'+note('Two preparation hours move from nonurgent quotations. Imani checks the burden; quote delays stay on the watch list.')
    if key=='mixed':
        return eyebrow('15–26 February · a mixed observation window')+'<div class="mixed-calendar">'+''.join(f'<div class="day {"revised" if day>=22 else ""}"><span>{day}</span><i></i></div>' for day in range(15,27))+'</div><div class="calendar-key"><span>Earlier arrangement</span><span>Revision starts 22 Feb</span></div><div class="result-twins compact">'+count(14,80,'late dispatches')+count(24,40,'prompt decisions')+'</div>'+note('Most days preceded the revision. Retain the report; use a fresh full window to assess the new approach.')
    if key=='prediction-two':
        return prediction('26 FEBRUARY','1–12 MARCH','32 / 40','8 / 80','Expectation 2 · revised approach, unchanged safeguards')
    if key=='authority-result':
        return eyebrow('1–12 March · first full revised window')+count(34,40,'prompt decisions','Original expectation: at least 32/40')+dots(34,40,'decision',False)+'<div class="absence-slip"><span>MAYA AWAY FOR TWO DAYS</span><strong>5 / 6</strong><p>requests still get prompt decisions<br>within the delegated limits</p></div>'+note('This is evidence about authority being available during absence, rather than a count of meetings held.')
    if key=='no-baseline':
        return eyebrow('Ready instructions · the comparison is missing')+'<div class="missing-comparison"><div><span>BEFORE</span><strong>?</strong><p>No comparable<br>readiness baseline.</p></div><div><span>1–12 MARCH</span><strong>75 <small>/ 80</small></strong><p>Jobs ready at<br>their agreed slot.</p></div></div><div class="environment">Paper supply normalizes · job mix is slightly easier</div>'+note('The count is useful. How much readiness improved, and how much caused the delivery result, remain unknown.')
    if key=='march-one':
        return eyebrow('1–12 March · first qualifying fortnight')+count(8,80,'late dispatches','10% · original completion ceiling')+dots(8,80)+'<div class="safeguard-strip">'+metric('Overtime by week','16 / 15 h')+metric('Speaking up','16 yes','19 of 20 respond')+metric('Unpaid work','0 reported')+'</div>'+note('One qualifying window. Continue unchanged; two are needed before active support closes.')
    if key=='march-two':
        return eyebrow('Two consecutive windows · original rules')+'<div class="march-table"><div><span>OBSERVATION WINDOW</span><b>1–12 Mar</b><b>15–26 Mar</b></div><div><span>Late dispatches ≤10%</span><strong>8 / 80</strong><strong>7 / 80</strong></div><div><span>Prompt decisions ≥80%</span><strong>34 / 40</strong><strong>35 / 40</strong></div><div><span>Overtime ≤18 h each week</span><strong>16 / 15 h</strong><strong>14 / 15 h</strong></div><div><span>Speaking up ≥16 yes</span><strong>16 yes<small>19/20 respond</small></strong><strong>17 yes<small>19/20 respond</small></strong></div><div><span>Unpaid work</span><strong>0 reported</strong><strong>0 reported</strong></div></div>'+note('Both windows qualify. Easier work, supply, peak capacity and quotation delays remain open questions; meeting the criteria does not prove a unique cause.')
    if key=='record':
        return eyebrow('2 April · Rosa takes over the same commons')+'<div class="record-folder"><span class="folder-tab">NORTHBANK · MAINTAINED RECORD</span><div><span>WHY</span><strong>The goal and original criteria</strong></div><div><span>WHAT CHANGED</span><strong>Earlier wording and corrections</strong></div><div><span>WHAT HAPPENED</span><strong>Predictions beside reports</strong></div><div><span>WHAT IS OPEN</span><strong>Questions and review triggers</strong></div></div>'+note('Rosa inherits the reason behind the arrangement, not just an instruction to keep holding a meeting.')
    if key=='stewards':
        return eyebrow('After handover · people keep the record useful')+'<div class="steward-grid">'+panel(person('Rosa','Record steward')+'<p>Maintains reviewed updates<br>and fortnightly review.</p>')+panel(person('Ben','Order figures')+'<p>Dispatch dates and<br>changed-order decisions.</p>')+panel(person('Maya','Paid working time')+'<p>Checks hours, authority<br>and available cover.</p>')+panel(person('Imani','Staff voice')+'<p>Anonymous pulse and<br>private concern route.</p>')+'</div>'+note('Release 3 is the reviewed handover reference. Human updates continue; no automated monitoring is promised.')
    if key=='triggers':
        return eyebrow('Agreed reopening rules · human monitoring')+'<div class="trigger-rules"><div class="urgent"><b>Immediately</b><p>Unpaid work or reprisal concern:<br>review and offer independent facilitation.</p></div><div><b>Two failed windows</b><p>Delivery or speaking-up criteria fail twice consecutively:<br>invite Stephen back.</p></div><div><b>Sooner, if useful</b><p>The team can ask for help before that trigger.</p></div></div>'+note('These rules are retained at handover. A safeguard concern need not wait for two reporting windows.')
    if key=='may-delivery':
        return eyebrow('3–14 May · follow-up window')+count(9,80,'late dispatches','11.25% · above the unchanged 10% ceiling',True)+dots(9,80)+'<div class="baseline-second">'+metric('Prompt decisions still qualify','33 / 40','82.5% · overtime 15 and 16 hours')+'</div>'+note('Delivery is better than the January baseline, yet this window fails the agreed completion threshold.')
    if key=='may-voice':
        return eyebrow('3–14 May · speaking up also misses its threshold')+voice(15,18)+'<div class="pulse-result"><b>15 yes</b><span>16 needed · 18 of 20 responded</span></div><div class="evidence-slip"><b>A concern to explore</b><span>Questioning dates feels like “holding everyone up.”</span></div>'+note('Deputy cover was diverted twice; a new customer sends more late changes. Keep these observations in play without claiming one caused all the drift.')
    if key=='next':
        return eyebrow('14 May · choose the next review')+'<div class="next-review"><span class="sheet-top">NEXT REVIEW · 28 MAY</span><strong>Restore deputy cover.</strong><strong>Offer a voluntary conversation.</strong><div class="pending-line"><span>Result</span><b>Pending</b></div></div>'+note('This is one failed delivery-and-voice window. Restore and review internally; the agreed two-window invitation has not yet been reached.')
    if key=='pending':
        return eyebrow('28 May · the next review is pending')+'<div class="empty-report"><span>NEXT REVIEW</span><strong>28 May</strong><div class="empty-lines" aria-hidden="true"><i></i><i></i><i></i></div>'+stamp('PENDING')+'</div>'+note('March’s qualifying results and May’s warning both remain in the record.')
    raise ValueError(key)

def prediction(recorded,window,decisions,late,heading):
    return eyebrow(heading)+f'<div class="prediction-sheet"><span class="sheet-top">RECORDED {recorded} · BEFORE THE WINDOW</span><h3>{window}</h3><div class="prediction-metrics"><div><span>PROMPT DECISIONS</span><strong>≥{decisions}</strong></div><div><span>LATE DISPATCHES</span><strong>≤{late}</strong></div></div><div class="prediction-footer">Same safeguards · actual denominators retained</div></div>'+note('Keep this prediction beside its later report. A revised expectation does not overwrite an earlier one.')

def load():
    state,data=build.load()
    return state,data,json.loads(SOURCE.read_text())

def validate_story(state,data,story):
    build.validate(state,data)
    require=build.require
    require(story['format_version']==1 and story['fictional'] is True,'Story must retain its version and fiction label.')
    scenes=story['scenes'];records={r['id']:r for r in data['ap']['records']}
    require(50<=len(scenes)<=55,'The reviewed story needs approximately 50–55 short views.')
    require([s['date'] for s in scenes]==sorted(s['date'] for s in scenes),'Story scenes must remain chronological.')
    require(list(dict.fromkeys(s['date'] for s in scenes))==[ev['date'] for ev in data['events']],'Every original event must appear in order.')
    ids=[ref for s in scenes for ref in [s['id']]+s.get('aliases',[])]
    require(len(ids)==len(set(ids)),'Story bookmarks must be unique.')
    require({f'beat-{i:02}' for i in range(1,41)}<=set(ids),'Published story bookmarks must be retained.')
    for s in scenes:
        require(s['ap_ref'] in records and records[s['ap_ref']]['date']==s['date'],'A story scene reveals an unavailable AP record.')
        require(s['ap_stage'] in data['ap']['stages'],'Every scene needs a source-defined AP stage.')
        require(s['title'].strip() and s['text'].strip() and len(s['text'].split())<=45,'Story narration must remain a short complete thought.')
    require([s['art'] for s in scenes if s['art'] in {'matrix-'+x for x in build.AP_MATRIX_ORDER}]==['matrix-'+x for x in build.AP_MATRIX_ORDER],'The main story must show the full ACT pass, in order.')
    required={'environment-volatility','environment-hazards','capacity-profile','mismatch','capacity-choice','method-choice','reassessment','reassessment-profile','reassessment-may','closure'}
    require(required<={s['art'] for s in scenes},'The visible story omits a required AP explanation.')
    require(story['script']=='docs/marketing/explainers/northbank-print/08-ap-script-v2.md','Unexpected reviewed script path.')
    script=(ROOT/story['script']).read_text().strip().split('\n\n')[1:]
    require([s['text'] for s in scenes]==script,'The built narration differs from the reviewed narrative.')

def ap_figure(scene,data):
    """One source-backed question/comparison per view; full working records remain linked."""
    key=scene['art'];r=next(r for r in data['ap']['records'] if r['id']==scene['ap_ref'])
    people={p['id']:p for p in data['people']}
    def who(id):return people[id]['name']
    def cards(rows,cls=''):
        return '<div class="ap-cards '+cls+'">'+''.join(panel(f'<span class="ap-label">{e(label)}</span><strong>{e(text)}</strong>') for label,text in rows)+'</div>'
    if key=='orient-choice':
        rows=[('Maya · director','Reliable delivery'),('Ben · customer services','Feasible promises'),('Rosa · production','Workable instructions'),('Imani · staff representative','Paid time and voice')]
        return eyebrow('Orient · whose concerns must the goal serve?')+cards(rows,'four')+note('Stephen helps them find shared positive wording. Representatives check with their teams; agreement follows that check.')
    if key=='assessment-method':
        return eyebrow('Assess · two connected sources of understanding')+panel('<span class="ap-label">INPUT</span><strong>People’s accounts<br>+ existing records</strong>','ap-input')+cards([('Outside the group','Volatility · hazardousness'),('Inside the group','Coordination · adaptability · robustness')])+note('Twenty of twenty-two people provide some input. Interviews, an optional questionnaire and records inform the working assessment; unknowns stay unknown.')
    if key=='environment-volatility':
        return eyebrow('Assess · volatility')+'<div class="horizons">'+''.join(f'<div><b>{e(x["horizon"])}</b><p>{e(x["finding"])}</p><span>{e(x["interpretation"])}</span></div>' for x in r['outlook'])+'</div>'+note('The group distinguishes a current operating demand from possibilities it should monitor. No future outcome or probability is invented.')
    if key=='environment-hazards':
        return eyebrow('Assess · hazardousness')+cards([('Short-term survival','Supplier dependence creates disruption exposure.'),('Employee safety','Machine safeguards remain mandatory.')])+panel('<strong>A limited screening</strong><p>No immediate survival crisis is identified. A full safety or continuity audit is not claimed.</p>','ap-input')+note(e(r['heterogeneity']))
    if key=='capacity-profile':
        return eyebrow('Assess · three different capacities')+profile_rows(r,capacities=True)+note('These are working judgments, with strengths, concerns and unknowns. The full twenty-four-principle record follows the story and is available in the linked case.')
    if key=='mismatch':
        return eyebrow('Analyze · compare environment with capacity')+cards([('What the environment demands',r['mismatch']['demand']),('What the group can currently supply',r['mismatch']['capacity'])])+note(e(r['mismatch']['consequence']))
    if key=='capacity-choice':
        return eyebrow('Analyze · a choice made by the group')+'<div class="capacity-list"><div class="chosen"><span>01</span><div><b>Coordination</b><p>Decision-making is the immediate gap.</p></div>'+stamp('CHOSEN FIRST')+'</div><div><span>02</span><div><b>Adaptability</b><p>Watch change; review and learn.</p></div></div><div><span>03</span><div><b>Robustness</b><p>Keep safeguards; provide decision cover.</p></div></div></div>'+note('The choice serves this bounded issue. An acute threat, changed demands or different evidence would reopen it; this is not an automatic score.')
    if key=='method-choice':
        return eyebrow('Adjust · method and format are choices, too')+panel('<span class="ap-label">CHOSEN METHOD</span><strong>ACT group matrix</strong><span class="ap-label spaced">CHOSEN FORMAT</span><p>Facilitated in-person discussion<br>Private reflection · voluntary sharing</p>','method-sheet')+note('The representatives can meet together in this scenario. A written/email route remains available. Personal sheets stay private; the shared record contains practical implications.')
    if key.startswith('matrix-') and key!='matrix-revisit':
        token=key[7:];step=next(s for s in r['matrix'] if s['key']==token)
        steps='<div class="matrix-steps" aria-label="ACT sequence">'+''.join(f'<span class="{"current" if x==token else ""}">{x}</span>' for x in build.AP_MATRIX_ORDER)+'</div>'
        head=eyebrow('Adjust · ACT group matrix')+steps+'<p class="matrix-context">Working on decision-making across office and workshop</p>'
        if token=='A':body=panel('<span class="ap-label">SELECTED CAPACITY</span><strong>Decision-making</strong><p>Across the customer office<br>and production workshop.</p>','matrix-answer')
        elif token=='B':body=cards([('For customers','A feasible, authorized answer in time.'),('For employees','Ready jobs, paid time and room to challenge.')])
        elif token=='1':body=cards([(who(x['by']),x['value']) for x in step['contributions']],'four')
        elif token=='2':body='<div class="helpful-actions">'+''.join(f'<div><span aria-hidden="true">↗</span><strong>{e(action)}</strong></div>' for action in step['helpful_actions'])+'</div>'
        elif token=='3':body='<div class="thoughts">'+''.join(f'<div><span>{e(who(x["by"]))}</span><p>“{e(x["thought"])}”</p></div>' for x in step['examples'])+'</div>'
        elif token=='4':body='<div class="patterns">'+''.join(f'<div><span>{e(who(x["by"]))}</span><p>{e(x["thought"])}</p><i aria-hidden="true">↓</i><strong>{e(x["response"])}</strong></div>' for x in step['patterns'])+'</div>'
        else:body=panel(f'<span class="ap-label">A COMMITMENT TO TRY</span><p class="commitment-quote">“{e(step["example_utterance"])}”</p><div class="question-rule"></div><p>Acknowledge urgency and fear.<br>Check a workable promise.<br>Use the authorized morning review.</p>','matrix-answer')
        captions={'A':'A shared capacity, not an instruction for one department to work harder.','B':'The desired result connects the chosen capacity to the original goal and safeguards.','1':'The team agrees these values should guide its promises together. These are fictional contributions, not real participant endorsements.','2':'Name helpful behaviours before exploring what makes them difficult. Maya agrees to make time for authorized answers.','3':'Voluntary fictional examples. A difficult thought is not a diagnosis, and real constraints still matter.','4':'The group recognizes conditional patterns. Some requested dates really are infeasible; the response cannot be reduced to discomfort.','C':'Maya will attend a bounded morning review; preparation is planned inside paid shifts. These are chosen commitments and assumptions to test.'}
        return head+body+note(captions[token])
    if key in ('reassessment','reassessment-profile','reassessment-may'):
        return eyebrow('Repeat · reassess both environment and capacities')+profile_rows(r)+note({'reassessment':'Paper delay, authority and workload point to different questions. The group checks the whole profile before revising its arrangement.','reassessment-profile':'The short-absence check supports decision cover; severe-shock robustness remains untested. One qualifying window justifies continuing unchanged.','reassessment-may':'Changed customer demands, diverted cover and staff concerns remain live observations. None alone establishes the cause of drift.'}[key])
    if key=='matrix-revisit':
        return eyebrow('Repeat · revisit the ACT way forward')+cards([('Values and desired result retained','Dependability · craftsmanship · fairness · reliable commitments'),('Helpful action made feasible','Routine authority + cover + paid preparation')])+note(e(r['decision']))
    if key=='closure':
        return eyebrow('Repeat · the agreed endpoint is checked')+panel('<span class="ap-label">ORIGINAL CRITERIA</span><strong>Two qualifying<br>March windows.</strong><p>Delivery · decisions · paid time · speaking up</p>','closure-sheet')+cards([('Active AP support','Closes because the criteria are met.'),('Ongoing monitoring','The group chooses to continue it.')])+note('Open causal questions remain. The thresholds and two-window rule belong to this fictional agreement; they are not universal AP requirements.')
    rendered=legacy_art(key)
    if key in ('first-cause','causal-and','causal-next','first-future','harm-branch','missing-authority','revised-and','actions','goal'):
        rendered=rendered.replace('<p class="diagram-kicker">','<p class="diagram-kicker">Reason Commons tool · ',1)
    if key=='prediction-one':
        rendered+=note('The first trial allows ≤12/80 late. Completion still requires ≤10% — equivalent to ≤8/80 with eighty orders. Release 1 preserves the reviewed plan.')
    if key=='record':
        rendered=rendered.replace('Earlier wording and corrections','Assessment, capacity choice and ACT commitments').replace('The goal and original criteria','The goal and original criteria').replace('Predictions beside reports','Earlier wording, predictions and reports')
    return rendered

def profile_rows(record,capacities=False):
    keys=('coordination','adaptability','robustness') if capacities else build.AP_FACTORS
    return '<div class="profile-rows">'+''.join(f'<div><span>{e(k.capitalize())}</span><strong>{e(record["visual_factors"][k])}</strong></div>' for k in keys)+'</div>'

AP_STYLES=r'''
.ap-progress{position:fixed;top:62px;left:0;right:0;height:28px;z-index:9;display:flex;align-items:center;justify-content:center;gap:22px;background:var(--paper);border-bottom:1px solid var(--line);font:11px var(--sans)}.ap-progress a{color:var(--muted);text-decoration:none;padding:5px 0}.ap-progress a[aria-current="step"]{color:var(--ink);font-weight:700;border-bottom:2px solid var(--ink)}.ap-progress .return-symbol{font:18px var(--serif);color:var(--muted)}.scene-inner{padding-top:130px}.hero{padding-top:130px}.scene-date{flex-wrap:wrap;row-gap:3px}.anchor-alias{position:absolute;top:0}.ap-cards{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}.ap-cards .paper-panel{padding:22px}.ap-label{display:block;font:10px/1.5 var(--sans);letter-spacing:.06em;color:var(--muted);margin-bottom:14px;text-transform:uppercase}.ap-cards strong{display:block;font:25px/1.3 var(--serif)}.ap-cards.four strong{font-size:25px}.ap-cards.four .ap-label{font-size:11px;text-transform:none;letter-spacing:0}.ap-input{padding:20px;margin:20px 0}.ap-input>strong{display:block;font:25px/1.3 var(--serif)}.ap-input p{font:16px/1.6 var(--sans);color:var(--muted)}.horizons{display:grid;gap:0}.horizons>div{display:grid;grid-template-columns:110px 1fr;gap:8px 20px;padding:20px 0;border-bottom:1px solid var(--line)}.horizons b{font:24px var(--serif);grid-row:1/3}.horizons p{font:22px/1.4 var(--serif)}.horizons span{font:11px/1.5 var(--sans);color:var(--muted)}.profile-rows>div{display:grid;grid-template-columns:115px 1fr;gap:18px;border-bottom:1px solid var(--line);padding:18px 0;align-items:start}.profile-rows span{font:12px/1.5 var(--sans);color:var(--muted)}.profile-rows strong{font:22px/1.35 var(--serif)}.method-sheet>strong{font:38px/1.2 var(--serif);display:block}.method-sheet p{font:21px/1.5 var(--serif)}.spaced{margin-top:30px}.matrix-steps{display:flex;justify-content:space-between;gap:10px;max-width:450px;margin:0 auto 17px}.matrix-steps>span{border:1px solid var(--line);width:34px;height:30px;display:grid;place-items:center;font:12px var(--sans);color:var(--muted)}.matrix-steps .current{border-color:var(--mark);color:var(--mark);font-weight:700}.matrix-context{font:12px/1.5 var(--sans);text-align:center;color:var(--muted);margin:15px 0 24px}.matrix-answer{padding:30px}.matrix-answer>strong{display:block;font:38px/1.2 var(--serif)}.matrix-answer>p{font:23px/1.5 var(--serif)}.matrix-answer .question-rule{margin-left:0}.matrix-answer .commitment-quote{font:italic 29px/1.4 var(--serif);max-width:28ch}.helpful-actions{display:grid;gap:0}.helpful-actions>div{display:flex;align-items:center;gap:20px;padding:20px 15px;border-bottom:1px solid var(--line)}.helpful-actions span{font:30px var(--serif);color:var(--muted)}.helpful-actions strong{font:25px/1.3 var(--serif)}.thoughts{display:grid;gap:20px}.thoughts>div{padding:20px 24px;border-left:2px solid var(--ink);background:var(--sheet)}.thoughts span,.patterns>div>span{display:block;font:12px var(--sans);color:var(--muted);margin-bottom:12px}.thoughts p{font:italic 27px/1.4 var(--serif)}.patterns{display:grid;grid-template-columns:1fr 1fr;gap:20px}.patterns>div{padding:22px 19px;border:1px solid var(--line);background:var(--sheet)}.patterns p{font:21px/1.4 var(--serif)}.patterns i{display:block;font:26px var(--serif);color:var(--muted);text-align:center;margin:15px 0}.patterns strong{font:23px/1.3 var(--serif);display:block}.closure-sheet>strong{display:block;font:40px/1.2 var(--serif)}.closure-sheet p{font:15px/1.6 var(--sans)}.principle-records{display:grid;grid-template-columns:1fr 1fr;gap:20px}.principle-records article{padding:20px;border:1px solid var(--line);background:var(--sheet)}.principle-records h4{font:22px/1.2 var(--serif);font-weight:400;margin:0 0 10px}.principle-records p{font-size:13px}.principle-records .assessment-judgment{font:10px var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:13px}.notes .source-contract{margin:25px 0}.source-contract a{display:flex;gap:20px;padding:14px 0;border-bottom:1px solid var(--line);font:14px var(--sans);text-decoration:none}.source-contract span{color:var(--muted);min-width:65px}.notes h4{font:24px var(--serif);margin-top:30px}
@media(max-width:1150px){.ap-cards strong,.ap-cards.four strong{font-size:23px}.horizons p{font-size:21px}.profile-rows strong{font-size:20px}.matrix-answer .commitment-quote{font-size:27px}}
@media(min-width:801px) and (max-height:800px){.scene-inner{padding-top:110px;padding-bottom:54px}.hero{padding-top:112px}.diagram-kicker{margin-bottom:14px;padding-bottom:8px}.marks{gap:5px 8px;margin:18px 0}.mark{height:10px}.count b{font-size:68px}.profile-rows>div{padding:14px 0}.horizons>div{padding:16px 0}.ap-cards .paper-panel{padding:20px}.helpful-actions>div{padding:16px 12px}.matrix-answer{padding:24px}}
@media(max-width:800px){.ap-progress{top:52px;gap:17px;font-size:10px;height:27px}.scene-inner{padding-top:107px}.hero{padding-top:112px}.ap-cards{gap:15px}.ap-cards strong,.ap-cards.four strong{font-size:23px}.horizons p{font-size:21px}.profile-rows strong{font-size:21px}.profile-rows>div{grid-template-columns:100px 1fr;padding:16px 0;gap:15px}.matrix-answer .commitment-quote{font-size:27px}.matrix-answer>strong{font-size:34px}.helpful-actions strong{font-size:23px}.thoughts p{font-size:25px}.patterns strong{font-size:22px}.closure-sheet>strong{font-size:35px}}
@media(max-width:450px){.ap-progress{gap:13px;font-size:9px}.scene-inner{padding-top:104px}.hero{padding-top:109px}.ap-cards{gap:12px}.ap-cards .paper-panel{padding:18px 14px}.ap-cards strong,.ap-cards.four strong{font-size:21px}.ap-label{font-size:9px;margin-bottom:11px}.ap-cards.four .ap-label{font-size:10px}.ap-input>strong{font-size:22px}.ap-input p{font-size:14px}.horizons>div{grid-template-columns:85px 1fr;padding:17px 0;gap:7px 14px}.horizons b{font-size:22px}.horizons p{font-size:19px}.horizons span{font-size:10px}.profile-rows>div{grid-template-columns:88px 1fr;gap:13px;padding:15px 0}.profile-rows span{font-size:11px}.profile-rows strong{font-size:19px}.method-sheet>strong{font-size:32px}.method-sheet p{font-size:19px}.spaced{margin-top:23px}.matrix-steps{gap:8px}.matrix-steps>span{font-size:11px;width:31px;height:27px}.matrix-context{font-size:10px;margin-bottom:20px}.matrix-answer{padding:23px 20px}.matrix-answer>strong{font-size:31px}.matrix-answer>p{font-size:20px}.matrix-answer .commitment-quote{font-size:25px}.helpful-actions>div{padding:17px 9px;gap:14px}.helpful-actions strong{font-size:21px}.thoughts>div{padding:18px 19px}.thoughts p{font-size:23px}.patterns{gap:13px}.patterns>div{padding:18px 13px}.patterns p{font-size:19px}.patterns strong{font-size:20px}.closure-sheet>strong{font-size:32px}.principle-records{grid-template-columns:1fr}.notes .source-contract a{font-size:13px;gap:12px}}
@media(max-width:450px){.scene-inner{min-width:0}.ap-cards.four .paper-panel{padding-inline:10px}.ap-cards.four strong{font-size:20px}.profile-rows>div{padding:12px 0}#ap-act-C .matrix-answer{padding:20px 18px}#ap-act-C .matrix-answer .commitment-quote{font-size:23px}#ap-act-C .matrix-answer>p:not(.commitment-quote){font-size:18px}#ap-act-C .matrix-context{margin-bottom:16px}#ap-act-C .drawing-note{margin-top:16px}}
@media print{.ap-progress{display:none}.scene-inner{padding:35px}.hero{padding:35px}}
'''

ORIENTATION_SCRIPT=r'''
(() => {
  const scenes = [...document.querySelectorAll('.scene')];
  const label = document.querySelector('#rail-label');
  const count = document.querySelector('#rail-count');
  const progress = document.querySelector('.read-progress');
  const stages = [...document.querySelectorAll('[data-ap-jump]')];
  let scheduled = false;
  function update() {
    scheduled = false;
    const y = innerHeight * .45;
    const active = scenes.find(scene => {const r=scene.getBoundingClientRect();return r.top<=y&&r.bottom>y;});
    if (active) {
      label.textContent = active.dataset.stage + ' · ' + active.dataset.dateLabel;
      count.textContent = active.dataset.number + ' / ' + scenes.length;
      document.body.dataset.active = active.id;
    } else {
      const end = document.querySelector('#notes').getBoundingClientRect().top <= y;
      label.textContent = end ? 'Sources, assessment and limits' : 'A fictional AP engagement · January–May 2027';
      count.textContent = end ? scenes.length+' / '+scenes.length : 'Scroll to follow the story ↓';
      document.body.dataset.active = end ? 'notes' : 'hero';
    }
    stages.forEach(link=>{if(active&&link.dataset.apJump===active.dataset.apStage)link.setAttribute('aria-current','step');else link.removeAttribute('aria-current');});
    progress.style.width = Math.max(0,Math.min(100,scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight)*100))+'%';
  }
  function request(){if(!scheduled){scheduled=true;requestAnimationFrame(update);}}
  addEventListener('scroll',request,{passive:true});
  addEventListener('resize',request);
  addEventListener('pageshow',request);
  document.fonts?.ready.then(request);
  update();
})();
'''

def date_label(day):
    return build.date.fromisoformat(day).strftime('%-d %B')

def notes_view(data,story):
    baseline=next(r for r in data['ap']['records'] if r['id']=='assess-2027-01-18')
    principles=''
    for capacity in ('coordination','adaptability','robustness'):
        principles+=f'<h3>{e(capacity.capitalize())}: eight working principle notes</h3><div class="principle-records">'
        for p in baseline['principles']:
            if p['capacity']!=capacity:continue
            principles+=f'<article><p class="assessment-judgment">Working judgment · {e(p["assessment"])}</p><h4>{e(p["name"])}</h4><p>{e(p["finding"])}</p><p><b>Open question:</b> {e(p["open_question"])}</p></article>'
        principles+='</div>'
    contracts=''.join(f'<a href="#{next(s["id"] for s in story["scenes"] if s["ap_stage"]==phase)}"><span>{e(phase)}</span>{e(text)}</a>' for phase,text in [('Orient','Agree a workable issue and original criteria'),('Assess','Examine environment and capacities, including unknowns'),('Analyze','Compare demands with capacities and choose a priority'),('Adjust','Use the selected group method to choose feasible action'),('Repeat','Reassess, revise and check the agreed endpoint')])
    chronology=''.join(f'<a href="#{next(s["id"] for s in story["scenes"] if s["date"]==ev["date"])}"><time datetime="{ev["date"]}">{date_label(ev["date"])}</time><span>{e(ev["title"])}</span></a>' for ev in data['events'])
    metrics=''.join(f'<div><h3>{e(m["name"])}</h3><p>{e(m["definition"])}</p><p>{e(m["threshold"])}</p></div>' for m in data['metrics'])
    return f'''<section class="notes" id="notes" aria-labelledby="notes-title"><div class="notes-inner"><p class="eyebrow">The record behind the AP walkthrough</p><h2 id="notes-title">Sources, working judgments and limits.</h2><p>The people, interviews, dialogue, agreements and results in Northbank are deliberate fiction. The expanded AP assessment and matrix records are authored scenario content added to make the process inspectable, not recovered real consultations. Stephen Le has not endorsed this case. All formal reasoning remains proposed.</p><div class="source-links"><a href="../../demos/northbank-print/index.html">Full dated case ↗</a><a href="../../demos/northbank-print/commons.json">Case, AP records and history · JSON</a><a href="../../demos/northbank-print/reason-commons.yaml">Proposed reasoning · YAML</a></div><h3>The process illustrated here</h3><nav class="source-contract" aria-label="AP process coverage">{contracts}</nav><p>The October summary is the procedural reference: Orient and Assess on pages 4–6; Analyze on page 6; Adjust and the ACT group matrix on pages 6–8; Repeat and termination on page 8. AP is a flexible meta-protocol. This group chooses ACT; other engagements may choose another suitable method. The typical ACT order shown is A, B, 1, 2, 3, 4 and C. Its sequence can vary with the group.</p><p>Northbank uses a facilitated in-person discussion with private reflection and voluntary contributions. The source notes that ACT and EFT require training and practice; these scenes do not establish facilitation competence. The source provides no universal requirement for Northbank’s numerical thresholds, two-window endpoint or later monitoring cadence.</p><h3>AP and the supporting Reason Commons tools</h3><p>The environment-capacity comparison and group choice organize the work. The causal and future-reality fragments help question explanations and expected consequences. Preserved predictions, corrected reports, wording history and action dependencies support review. These are supporting Reason Commons practices; AP does not require every group to use these trees or records.</p><h3>Source versions</h3><ul><li><a href="{e(data['ap']['sources'][0]['url'])}">Adaptive Persistence: A Meta-Protocol for Cooperation</a> — internally dated 11 October 2026, despite the Oct 16 filename. The opening permits sufficient capacity improvement; the final Repeat section specifies all Orient criteria. This case retains its original all-criteria endpoint.</li><li><a href="{e(data['ap']['sources'][1]['url'])}">Adaptive Persistence v1</a> — internally dated 30 September 2026. It includes geographic heterogeneity, suggests considering omission of collaboration assessment under high hazardousness or volatility, and loops to analysis. The October summary loops back to Assess and broadens method choice.</li></ul><p>The case retains useful cross-site context and does not turn typical priority guidance into an automatic score. Source file fingerprints and the complete source-to-scene crosswalk are recorded with the maintained project sources.</p><h3>The baseline principle record</h3><p>This is a qualitative pass through all twenty-four principles. A recorded unknown is an assessment limit, not a healthy score. The main story uses the relevant findings; these notes retain the rest. Every entry is authored fiction. Later dated records revisit all five factors and retain unresolved questions.</p>{principles}<h3>The original measures</h3><div class="metric-notes">{metrics}</div><h3>What the results do and do not establish</h3><p>The original definitions, six observation windows, two prospective predictions, seven reports and three releases are preserved. The first-week correction retains 17/20 beside 11/20. Readiness has no invented baseline. Two March windows meet the original criteria without identifying a unique cause. A short absence supports decision cover, not severe-shock robustness. May is one failed window; 28 May remains pending.</p><p>The page illustrates an entire source-defined AP pass and subsequent review. It does not establish actual client benefit, real audience comprehension or Stephen’s methodological approval. People carry out the reviews and maintain the record; no autonomous monitoring is provided.</p><h3>Return to a moment</h3><nav class="chronology" aria-label="The thirteen events">{chronology}</nav></div></section>'''

def render(state,data,story):
    validate_story(state,data,story)
    sections=[]
    for n,s in enumerate(story['scenes'],1):
        phase=s['ap_stage'] if s['ap_stage']==s['ap_step'] else s['ap_stage']+' · '+s['ap_step']
        aliases=''.join(f'<span class="anchor-alias" id="{e(a)}" aria-hidden="true"></span>' for a in s.get('aliases',[]))
        sections.append(f'''<section class="scene" id="{e(s['id'])}" data-number="{n:02}" data-event="{s['date']}" data-stage="{e(phase)}" data-ap-stage="{s['ap_stage']}" data-ap-record="{s['ap_ref']}" data-date-label="{date_label(s['date'])} 2027" aria-labelledby="{s['id']}-title">{aliases}<div class="scene-inner"><div class="narration"><p class="scene-date"><span class="scene-number">{n:02}</span><time datetime="{s['date']}">{date_label(s['date'])} 2027</time><span>{e(phase)}</span></p><h2 id="{s['id']}-title">{e(s['title'])}</h2><p class="narrative">{e(s['text'])}</p><a class="source-link" href="../../demos/northbank-print/index.html#ap-{s['ap_ref']}">Inspect this AP working record ↗</a></div><figure class="visual" aria-label="{e(s['title'])}">{ap_figure(s,data)}</figure></div></section>''')
    progress='<nav class="ap-progress" aria-label="AP stages">'+''.join(f'<a data-ap-jump="{phase}" href="#{next(s["id"] for s in story["scenes"] if s["ap_stage"]==phase)}">{phase}</a>' for phase in data['ap']['stages'])+'<span class="return-symbol" aria-hidden="true">↺</span></nav>'
    trace={k:data[k] for k in ['fictional','metrics','windows','predictions','reports','releases','ap']}
    trace['events']=[{k:ev[k] for k in ['date','stage','title']} for ev in data['events']]
    raw=json.dumps(trace,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    output=TEMPLATE.read_text()
    for marker,value in {'STORY_SECTIONS':''.join(sections),'NOTES':notes_view(data,story),'SOURCE_DATA':raw,'ORIENTATION_SCRIPT':ORIENTATION_SCRIPT,'AP_STYLES':AP_STYLES,'AP_PROGRESS':progress}.items():
        build.require('{{'+marker+'}}' in output,'Missing story template marker: '+marker)
        output=output.replace('{{'+marker+'}}',value)
    return output.rstrip()+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    state,data,story=load();output=render(state,data,story)
    if args.check:
        build.require(TARGET.exists() and TARGET.read_text()==output,'Generated AP story differs from its source.')
        print('The 54-view AP story, reviewed script, dated working records and generated HTML agree.')
    else:
        TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(output)
        print(f'Built {len(story["scenes"])} AP story views in {TARGET}')

if __name__=='__main__':main()

