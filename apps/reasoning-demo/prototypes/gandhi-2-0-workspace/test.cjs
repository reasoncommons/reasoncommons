// Checks the reading model, and optionally rendered pages, against the published Gandhi 2.0 release.
//   node apps/reasoning-demo/prototypes/gandhi-2-0-workspace/test.cjs [rendered-dom.html ...]
// A rendered-dom file is a headless Chrome --dump-dom of the published page at one of its #views.
const fs = require('fs'), path = require('path'), assert = require('assert');
require('./model.js'); const RC = globalThis.RC;
const root = path.resolve(__dirname, '../../../..');
const src = JSON.parse(fs.readFileSync(path.join(root, 'website/demos/reason-commons-in-use/gandhi-2-0/reasoning.json'), 'utf8'));
const html = fs.readFileSync(path.join(root, 'website/demos/gandhi-2-0-workspace/index.html'), 'utf8');
const emb = JSON.parse(html.match(/<script type="application\/json" id="rc-data">([\s\S]*?)<\/script>/)[1]);
let n = 0; const t = (name, f) => { f(); n++; console.log('ok  ' + name); };
const M = RC.build(emb);
const srcNodes = Object.values(src.trees).flatMap(x => x.nodes), srcLinks = Object.values(src.trees).flatMap(x => x.links);

t('embedded data equals the published release', () => assert.deepStrictEqual(emb, src));
t('241 statements and 246 connections, ids unique and preserved', () => {
  assert.strictEqual(Object.keys(M.nodes).length, 241); assert.strictEqual(Object.keys(M.links).length, 246);
  assert.deepStrictEqual(Object.keys(M.nodes).sort(), srcNodes.map(x => x.id).sort());
  assert.deepStrictEqual(Object.keys(M.links).sort(), srcLinks.map(x => x.id).sort());
});
t('every connection keeps its relation, direction and full source list', () => srcLinks.forEach(l => {
  const m = M.links[l.id]; assert.strictEqual(m.relation, l.relation); assert.strictEqual(m.to, l.to); assert.deepStrictEqual(m.from, l.from);
  assert.ok(M.inc[l.to].includes(l.id)); l.from.forEach(f => assert.ok(M.out[f].includes(l.id)));
}));
t('incoming/outgoing indexes hold no connection the release lacks', () => {
  const inc = Object.values(M.inc).flat(), out = new Set(Object.values(M.out).flat());
  assert.strictEqual(inc.length, 246); assert.strictEqual(out.size, 246);
});
t('joint connections stay single connections (86 with several sources)', () => {
  const joint = srcLinks.filter(l => l.from.length > 1);
  assert.strictEqual(RC.stats(M).joint, joint.length);
  joint.forEach(l => { assert.ok(RC.isJoint(M.links[l.id])); assert.ok(/together/.test(RC.relPhrase(M.links[l.id])) || l.relation === 'conflicts_with'); });
  srcLinks.filter(l => l.from.length === 1).forEach(l => assert.ok(!/together/.test(RC.relPhrase(M.links[l.id]))));
});
t('three feedback loops are kept as loops', () => assert.strictEqual(RC.stats(M).loops, srcLinks.filter(l => l.relation === 'feeds_back_to').length));
t('standing, proposer and acceptance are reported as recorded', () => {
  const s = RC.stats(M); assert.strictEqual(s.proposed, 487); assert.strictEqual(s.acceptedByAnyone, 0); assert.strictEqual(s.byAI, 487);
  assert.deepStrictEqual({ ...s.proposers }, { 'AI assistant': 487 });
});
t('every relation and kind in the release has wording', () => {
  srcLinks.forEach(l => assert.ok(RC.REL[l.relation], l.relation));
  Object.values(M.nodes).forEach(x => { assert.ok(RC.kindLabel(x) !== x.kind || x.kind === 'goal', x.kind); assert.ok(RC.claimType(x) !== 'A statement', x.kind); });
  srcNodes.concat(srcLinks).forEach(x => x.source_refs.forEach(r => assert.ok(RC.BASIS[r.basis], r.basis)));
  Object.values(src.trees).flatMap(x => x.backlog).forEach(b => assert.ok(RC.WORK[b.work], b.work));
});
t('predictions and risks are never classed as observations', () => Object.values(M.nodes).forEach(x => {
  if (['desirable_effect', 'predicted_effect', 'expected_effect'].includes(x.kind)) assert.ok(/prediction: not observed/.test(RC.claimType(x)));
  if (x.tree === 'future_reality' && x.kind === 'undesirable_effect') assert.ok(/not observed/.test(RC.claimType(x)));
  if (x.kind === 'injection') assert.ok(/nothing has been done/.test(RC.claimType(x)));
}));
t('cross-question references match the release exactly', () => {
  let c = 0; srcNodes.forEach(x => ['addresses', 'derived_from', 'implements'].forEach(v => (x[v] || []).forEach(to => { c++; assert.ok(M.xout[x.id].some(r => r.via === v && r.to === to)); assert.ok(M.xin[to].some(r => r.via === v && r.from === x.id)); })));
  assert.strictEqual(Object.values(M.xout).flat().length, c); assert.strictEqual(Object.values(M.xin).flat().length, c);
});
t('all 70 open questions are attached to an existing statement or connection', () => {
  assert.strictEqual(RC.stats(M).open, 70); Object.keys(M.backlog).forEach(r => assert.ok(RC.item(M, r), r));
});
t('every path option is a recorded reference; every problem/change/step/action combination is valid', () => {
  let combos = 0;
  RC.problems(M).forEach(p => { assert.strictEqual(M.nodes[p].kind, 'undesirable_effect');
    RC.changesFor(M, p).forEach(c => { assert.ok(M.nodes[c].addresses.includes(p));
      RC.stepsFor(M, c).forEach(s => { assert.ok(M.nodes[s].implements.includes(c));
        RC.actionsFor(M, s).forEach(a => { assert.ok(M.nodes[a].implements.includes(s)); combos++;
          assert.deepStrictEqual(RC.normalizePath(M, { problem: p, change: c, step: s, action: a }), { problem: p, change: c, step: s, action: a }); }); }); }); });
  assert.ok(combos > 50);
});
t('the default path is the one the release singles out', () => assert.deepStrictEqual(RC.defaultPath(M), { problem: 'g2-r-u03', change: 'g2-f-guidance', step: 'g2-p-p07', action: 'g2-t-a4-action' }));
t('a broken or foreign path id is replaced by a recorded option, never kept', () => {
  const p = RC.normalizePath(M, { problem: 'nope', change: 'g2-t-select', step: 'x', action: 'y' });
  assert.ok(RC.problems(M).includes(p.problem)); assert.ok(RC.changesFor(M, p.problem).includes(p.change)); assert.ok(RC.stepsFor(M, p.change).includes(p.step));
});
t('a step with no action yields no action (missing owner stays missing)', () => {
  const lone = Object.values(M.nodes).find(x => x.tree === 'prerequisite' && (x.implements || []).length && !RC.actionsFor(M, x.id).length);
  assert.ok(lone); const p = RC.pathThrough(M, {}, lone.id); assert.strictEqual(p.step, lone.id); assert.strictEqual(p.action, null);
});
t('route to the goal uses only recorded contributes_to connections, in order, ending at the effect that implements the goal', () => {
  let found = 0;
  Object.values(M.nodes).filter(x => x.kind === 'injection').forEach(c => {
    const r = RC.routeToGoal(M, c.id); if (!r) return; found++; let at = c.id;
    r.forEach(id => { const l = M.links[id]; assert.strictEqual(l.relation, 'contributes_to'); assert.ok(l.from.includes(at)); at = l.to; });
    assert.ok(M.nodes[at].implements.includes('g2-g-goal'));
  });
  assert.ok(found > 0); assert.strictEqual(RC.routeToGoal(M, 'g2-f-n01-remedy'), null);
});
t('risks and remedies are recorded connections', () => Object.values(M.nodes).filter(x => x.kind === 'injection').forEach(c => RC.risksOf(M, c.id).forEach(r => {
  assert.strictEqual(M.links[r.link].to, r.risk); assert.ok(M.links[r.link].from.includes(c.id)); r.remedies.forEach(x => assert.strictEqual(M.links[x].relation, 'prevents'));
})));
t('goal and default problem have no direct recorded connection (so the page must say so)', () => assert.strictEqual(RC.hasDirect(M, 'g2-g-goal', 'g2-r-u03'), false));
t('search finds by wording, person and kind', () => {
  assert.ok(RC.search(M, 'conflict guidance').length); assert.ok(RC.search(M, 'Robert Bunge').length); assert.ok(RC.search(M, 'obstacle').every(id => M.nodes[id]));
  assert.deepStrictEqual(RC.search(M, 'zzzz'), []);
});

t('the workspace model accepts an empty commons', () => {
  const empty = RC.build({ trees: {} });
  assert.deepStrictEqual(empty.trees, []);
  assert.deepStrictEqual(RC.defaultPath(empty), { problem: null, change: null, step: null, action: null });
  assert.strictEqual(RC.stats(empty).total, 0);
  assert.deepStrictEqual(RC.search(empty, 'no match'), []);
});

t('a partial commons can start at a change and stops at a missing connection', () => {
  const change = { id: 'constructor', kind: 'injection', text: 'Review intake', status: 'accepted',
    contributors: [{ name: '__proto__', role: 'human' }], accepted_by: ['Nell'] };
  const step = { id: 'first-step', kind: 'intermediate_objective', text: 'Pick a reviewer',
    status: 'proposed', implements: [change.id] };
  const action = { id: 'action', kind: 'action', text: 'Ask for a volunteer', status: 'disputed' };
  const partial = RC.build({ trees: {
    future_reality: { nodes: [change], links: [] },
    prerequisite: { nodes: [step], links: [] },
    transition: { nodes: [action], links: [] }
  }});
  assert.deepStrictEqual(RC.defaultPath(partial), { problem: null, change: change.id, step: step.id, action: null });
  assert.strictEqual(RC.pathThrough(partial, {}, action.id), null);
  assert.strictEqual(RC.item(partial, change.id).label, change.text);
  assert.strictEqual(RC.stats(partial).proposers.__proto__, 1);
  assert.deepStrictEqual(RC.search(partial, 'nell'), [change.id]);
});

t('the goal outline follows recorded dependencies through every level', () => {
  const tree = {
    nodes: [
      { id: 'condition', kind: 'necessary_condition' },
      { id: 'loose', kind: 'necessary_condition' },
      { id: 'factor', kind: 'critical_success_factor' },
      { id: 'goal', kind: 'goal' },
      { id: 'detail', kind: 'necessary_condition' },
    ],
    links: [
      { id: 'a', from: ['factor'], to: 'goal', relation: 'necessary_for' },
      { id: 'b', from: ['condition'], to: 'factor', relation: 'necessary_for' },
      { id: 'c', from: ['detail'], to: 'condition', relation: 'necessary_for' },
    ],
  };
  const outline = RC.questionOutline(tree);
  assert.deepStrictEqual(outline.branches.map(n => n.id), ['goal']);
  const [goal] = outline.branches;
  const [factor] = goal.groups[0].children;
  const [condition] = factor.groups[0].children;
  assert.strictEqual(factor.id, 'factor');
  assert.strictEqual(condition.id, 'condition');
  assert.strictEqual(condition.groups[0].children[0].id, 'detail');
  assert.deepStrictEqual(outline.loose, ['loose']);
});

t('the outline shows shared sources in context and keeps joint causes and feedback intact', () => {
  const tree = {
    nodes: ['effect-a', 'effect-b', 'shared', 'joint'].map(id => ({ id })),
    links: [
      { id: 'together', from: ['shared', 'joint'], to: 'effect-a', relation: 'contributes_to' },
      { id: 'second', from: ['shared'], to: 'effect-b', relation: 'contributes_to' },
      { id: 'return', from: ['effect-b'], to: 'shared', relation: 'contributes_to', loop: true },
    ],
  };
  const { branches, references, loose } = RC.questionOutline(tree);
  assert.deepStrictEqual(branches.map(n => n.id), ['effect-a', 'effect-b']);
  assert.deepStrictEqual(branches[0].groups[0].children.map(n => n.id), ['shared', 'joint']);
  assert.strictEqual(branches[1].groups[0].children[0].repeated, true);
  assert.deepStrictEqual(references.map(l => l.id), ['return']);
  assert.deepStrictEqual(loose, []);
});

t('action stages follow produced effects and explicit order even when the file lists later steps first', () => {
  const tree = {
    nodes: ['a3', 'result', 'a2', 'effect', 'a1', 'condition'].map(id => ({ id })),
    links: [
      { id: 'later', from: ['effect', 'a2'], to: 'result', relation: 'produces' },
      { id: 'first', from: ['a1', 'condition'], to: 'effect', relation: 'produces' },
      { id: 'order', from: ['a2'], to: 'a3', relation: 'precedes' },
      { id: 'feedback', from: ['result'], to: 'a1', relation: 'feeds_back_to' },
    ],
  };
  const { stages, unordered, references } = RC.actionSequence(tree);
  assert.deepStrictEqual(stages.map(stage => stage.map(step => step.inputs)), [
    [['a1', 'condition']], [['effect', 'a2']], [['a3']],
  ]);
  assert.deepStrictEqual(unordered, []);
  assert.deepStrictEqual(references.map(l => l.id), ['order', 'feedback']);
});

// ---- rendered pages (headless Chrome dumps)
const ent = s => s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"');
for (const f of process.argv.slice(2)) {
  const dom = fs.readFileSync(f, 'utf8'), name = f.split('/').pop();
  const mainHtml = dom.slice(dom.indexOf('<main'), dom.indexOf('</main>'));
  t(name + ': every statement card names a real statement and shows its recorded wording', () => {
    const cards = [...mainHtml.matchAll(/<button type="button" class="st [^"]*"[^>]*data-id="([^"]+)"[^>]*>([\s\S]*?)<\/button>/g)];
    if (!/nope|notes|open/.test(name)) assert.ok(cards.length > 0, 'no cards');
    cards.forEach(c => { const x = M.nodes[c[1]]; assert.ok(x, c[1]); const txt = ent(c[2].match(/<span class="st-text">([\s\S]*?)<\/span>/)[1]); assert.ok(txt === x.text || txt === x.label, c[1]); assert.ok(c[0].includes('is-' + x.status)); });
  });
  t(name + ': every connection control names a real connection with its recorded relation wording', () => {
    [...mainHtml.matchAll(/<button type="button" class="rel[^"]*"[^>]*data-id="([^"]+)"[^>]*>[\s\S]*?<span class="rel-word">([^<]*)<\/span>/g)].forEach(c => { const l = M.links[c[1]]; assert.ok(l, c[1]); assert.strictEqual(ent(c[2]), RC.relPhrase(l)); });
  });
  t(name + ': no escaped markup or undefined leaked into the page', () => { assert.ok(!/&lt;(button|span|div|li)/.test(dom)); assert.ok(!/>undefined<|>null<|\[object Object\]/.test(dom)); });
}
console.log(n + ' checks passed');
