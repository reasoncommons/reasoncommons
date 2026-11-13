/* Pure reading of a Reason Commons release. No DOM. Runs in the page and under node for the checks. */
(function (g) {
  'use strict';

  var TREES = [
    { key: 'goal', slug: 'goal', q: 'What are we trying to achieve?', short: 'The goal', formal: 'Goal tree' },
    { key: 'current_reality', slug: 'way', q: 'What stands in the way?', short: 'In the way', formal: 'Current reality tree' },
    { key: 'conflict', slug: 'conflict', q: 'Where do needs pull two ways?', short: 'Conflicts', formal: 'Conflict cloud' },
    { key: 'future_reality', slug: 'change', q: 'What will we change?', short: 'Changes', formal: 'Future reality tree' },
    { key: 'prerequisite', slug: 'first', q: 'What has to happen first?', short: 'First steps', formal: 'Prerequisite tree' },
    { key: 'transition', slug: 'who', q: 'Who does what?', short: 'Actions', formal: 'Transition tree' }
  ];

  // Wording follows the published viewer (skills/ltp/viewer) so the two read alike.
  var KIND = {
    goal: 'Goal', critical_success_factor: 'Success factor', necessary_condition: 'Condition',
    undesirable_effect: 'Problem', cause: 'Cause', observation: 'Observation', objective: 'Objective',
    need: 'Need', prerequisite: 'Position', injection: 'Change', existing_condition: 'Already true',
    predicted_effect: 'Predicted effect', desirable_effect: 'Desired effect', obstacle: 'Obstacle',
    intermediate_objective: 'Step', action: 'Action', expected_effect: 'Expected effect'
  };
  var SPECIAL = { 'future_reality|undesirable_effect': 'Possible harm', 'conflict|objective': 'Shared objective' };

  // The relation types exactly as recorded, with the phrase that reads from the source statement(s) to the target.
  var REL = {
    necessary_for: 'is needed for', contributes_to: 'contributes to', feeds_back_to: 'feeds back to',
    prevents: 'is meant to prevent', overcomes: 'overcomes', conflicts_with: 'conflicts with',
    produces: 'is meant to produce', causes: 'causes', precedes: 'comes before'
  };
  var REL_JOINT = {
    necessary_for: 'are together needed for', contributes_to: 'together contribute to', feeds_back_to: 'together feed back to',
    prevents: 'are together meant to prevent', overcomes: 'together overcome', produces: 'are together meant to produce',
    causes: 'together cause', precedes: 'together come before', conflicts_with: 'conflict with'
  };
  // References from a statement in one question to a statement in another. They are fields on the statement, not connections with their own identity.
  var XREF = {
    addresses: { fwd: 'is meant to address', back: 'Addressed by', head: 'Meant to address' },
    derived_from: { fwd: 'was developed from', back: 'Developed into', head: 'Developed from' },
    implements: { fwd: 'puts into practice', back: 'Put into practice by', head: 'Puts into practice' }
  };
  var BASIS = {
    paraphrase: 'Paraphrased by the AI from this post',
    related: 'Makes a related point; the statement goes beyond it',
    cited: 'Cited by the supplied analysis; the original was not checked here',
    reconstruction: 'Reconstructed by the supplied analysis',
    inference: 'Inferred by the AI; the sources do not state it'
  };
  var WORK = {
    connect_or_explain: 'Explain or connect', examine_assumption: 'Check an assumption',
    resolve_challenge: 'Examine a challenge', test_causality: 'Find out what happens',
    review_feedback: 'Find out what happens', check_locally: 'Check at the host'
  };
  var STANDING = { accepted: 'Accepted for now', proposed: 'Proposed', disputed: 'Disputed' };

  function build(d) {
    var trees = TREES.filter(function (T) { return Object.hasOwn(d.trees, T.key); });
    var M = { d: d, trees: trees };
    ['nodes', 'links', 'inc', 'out', 'xout', 'xin', 'backlog', 'history', 'part'].forEach(function (key) {
      M[key] = Object.create(null);
    });
    trees.forEach(function (T) {
      (d.trees[T.key].nodes || []).forEach(function (n) {
        var c = Object.assign({}, n, { label: n.label || n.text }); c.tree = T.key; c.isLink = false;
        M.nodes[n.id] = c; M.inc[n.id] = []; M.out[n.id] = []; M.xout[n.id] = []; M.xin[n.id] = [];
      });
    });
    trees.forEach(function (T) {
      (d.trees[T.key].links || []).forEach(function (l) {
        var c = Object.assign({}, l); c.tree = T.key; c.isLink = true;
        M.links[l.id] = c;
        if (M.inc[l.to]) M.inc[l.to].push(l.id);
        l.from.forEach(function (f) { if (M.out[f]) M.out[f].push(l.id); });
      });
      (d.trees[T.key].backlog || []).forEach(function (b) {
        var c = Object.assign({}, b); c.tree = T.key;
        (M.backlog[b.ref] = M.backlog[b.ref] || []).push(c);
      });
      ((d.views || {})[T.key] || []).forEach(function (v) {
        v.nodes.forEach(function (id) { (M.part[id] = M.part[id] || []).push({ tree: T.key, id: v.id, title: v.title }); });
      });
    });
    Object.keys(M.nodes).forEach(function (id) {
      Object.keys(XREF).forEach(function (via) {
        (M.nodes[id][via] || []).forEach(function (to) {
          M.xout[id].push({ via: via, to: to });
          if (M.xin[to]) M.xin[to].push({ via: via, from: id });
        });
      });
    });
    (d.history || []).forEach(function (h) {
      (h.changes || []).forEach(function (c) {
        (c.refs || []).forEach(function (r) {
          (M.history[r] = M.history[r] || []).push({ release: h.release_id, date: h.date, title: h.title, type: c.type, note: c.note });
        });
      });
    });
    return M;
  }

  function item(M, id) { return M.nodes[id] || M.links[id] || null; }
  function tree(key) { return TREES.filter(function (t) { return t.key === key || t.slug === key; })[0]; }
  function kindLabel(n) { return SPECIAL[n.tree + '|' + n.kind] || KIND[n.kind] || n.kind; }

  // A visual family for the statement. Derived from its recorded role only.
  function role(n) {
    var k = n.kind, t = n.tree;
    if (k === 'goal' || k === 'critical_success_factor' || k === 'necessary_condition') return 'aim';
    if (k === 'objective') return 'aim';
    if (k === 'need' || (k === 'prerequisite' && t === 'conflict')) return 'need';
    if (k === 'undesirable_effect') return t === 'future_reality' ? 'risk' : 'problem';
    if (k === 'cause' || k === 'obstacle') return 'problem';
    if (k === 'injection') return 'change';
    if (k === 'desirable_effect' || k === 'predicted_effect' || k === 'expected_effect') return 'predict';
    if (k === 'intermediate_objective') return 'step';
    if (k === 'action') return 'action';
    return 'now';
  }

  // What sort of claim this is, so a prediction is never read as an observation. Derived from the recorded role.
  function claimType(n) {
    var k = n.kind, t = n.tree;
    if (k === 'goal' || k === 'critical_success_factor' || k === 'necessary_condition') return 'An aim: something wanted, not a report of fact';
    if (k === 'objective') return t === 'conflict' ? 'An aim both sides are taken to share' : 'An aim: a state to reach, not yet reached';
    if (k === 'need') return 'A need: something required for the shared objective';
    if (k === 'prerequisite') return 'A position: one way of meeting a need';
    if (k === 'undesirable_effect') return t === 'future_reality' ? 'A predicted risk of a change: not observed' : 'A claim about how things are now';
    if (k === 'cause') return 'A claim about how things are now';
    if (k === 'observation') return 'An observation reported in the sources';
    if (k === 'obstacle') return 'A claimed obstacle: to be checked where the work would happen';
    if (k === 'injection') return 'A proposed change: nothing has been done';
    if (k === 'desirable_effect' || k === 'predicted_effect' || k === 'expected_effect') return 'A prediction: not observed';
    if (k === 'intermediate_objective') return 'A condition to reach first: not yet reached';
    if (k === 'action') return 'A proposed action: nobody has committed to it';
    if (k === 'existing_condition') return 'A starting condition: claimed to hold now';
    return 'A statement';
  }

  function relPhrase(l) { return (l.from.length > 1 ? REL_JOINT[l.relation] : REL[l.relation]) || l.relation; }
  function isJoint(l) { return l.from.length > 1; }
  function isLoop(l) { return l.loop || l.relation === 'feeds_back_to'; }

  // ---- The path: goal, problem, change, step, action. Every option comes from a recorded reference.
  function goalNode(M) { return Object.keys(M.nodes).map(function (i) { return M.nodes[i]; }).filter(function (n) { return n.tree === 'goal' && n.kind === 'goal'; })[0]; }
  function statementsOf(M, treeKey, kind) {
    var t = M.d.trees[treeKey];
    return t ? t.nodes.filter(function (n) { return n.kind === kind; }).map(function (n) { return n.id; }) : [];
  }
  function problems(M) { return statementsOf(M, 'current_reality', 'undesirable_effect'); }
  function back(M, id, via, test) {
    return M.xin[id].filter(function (x) { return x.via === via && test(M.nodes[x.from]); }).map(function (x) { return x.from; });
  }
  function changesFor(M, problem) { return back(M, problem, 'addresses', function (n) { return n.tree === 'future_reality' && n.kind === 'injection'; }); }
  function stepsFor(M, change) { return back(M, change, 'implements', function (n) { return n.tree === 'prerequisite' && n.kind === 'intermediate_objective'; }); }
  function actionsFor(M, step) { return back(M, step, 'implements', function (n) { return n.tree === 'transition' && n.kind === 'action'; }); }

  function goalAnchors(M) {
    var gn = goalNode(M);
    return gn ? back(M, gn.id, 'implements', function (n) { return n.tree === 'future_reality'; }) : [];
  }
  // Shortest recorded chain of "contributes to" connections from a change to the effect that stands for the goal.
  function routeToGoal(M, change) {
    var anchors = goalAnchors(M), seen = Object.create(null), queue = [[change, []]];
    seen[change] = true;
    while (queue.length) {
      var cur = queue.shift(), id = cur[0], path = cur[1];
      if (anchors.indexOf(id) >= 0 && path.length) return path;
      var outs = M.out[id] || [];
      for (var i = 0; i < outs.length; i++) {
        var l = M.links[outs[i]];
        if (l.relation !== 'contributes_to' || seen[l.to]) continue;
        if (role(M.nodes[l.to]) === 'risk') continue;
        seen[l.to] = true; queue.push([l.to, path.concat([l.id])]);
      }
    }
    return null;
  }
  function risksOf(M, change) {
    return (M.out[change] || []).map(function (i) { return M.links[i]; }).filter(function (l) {
      return l.relation === 'contributes_to' && role(M.nodes[l.to]) === 'risk';
    }).map(function (l) {
      return { link: l.id, risk: l.to, remedies: M.inc[l.to].filter(function (i) { return M.links[i].relation === 'prevents'; }) };
    });
  }
  function hasDirect(M, a, b) {
    var viaLink = Object.keys(M.links).some(function (i) {
      var l = M.links[i];
      return (l.to === a && l.from.indexOf(b) >= 0) || (l.to === b && l.from.indexOf(a) >= 0);
    });
    var viaRef = (M.xout[a] || []).some(function (x) { return x.to === b; }) || (M.xout[b] || []).some(function (x) { return x.to === a; });
    return viaLink || viaRef;
  }
  function firstWithNext(list, next) {
    for (var i = 0; i < list.length; i++) if (next(list[i]).length) return list[i];
    return list[0] || null;
  }
  // Begin at the first available stop and extend it only through recorded references.
  function pathOptions(M, path, slot) {
    if (slot === 'problem') return problems(M);
    if (slot === 'change') {
      return path.problem ? changesFor(M, path.problem) : statementsOf(M, 'future_reality', 'injection');
    }
    if (slot === 'step') {
      if (path.change) return stepsFor(M, path.change);
      return path.problem ? [] : statementsOf(M, 'prerequisite', 'intermediate_objective');
    }
    if (path.step) return actionsFor(M, path.step);
    return path.problem || path.change ? [] : statementsOf(M, 'transition', 'action');
  }
  function normalizePath(M, p) {
    p = p || {};
    var r = {};
    ['problem', 'change', 'step', 'action'].forEach(function (slot) {
      var options = pathOptions(M, r, slot);
      r[slot] = options.indexOf(p[slot]) >= 0 ? p[slot] : firstWithNext(options, function (id) {
        if (slot === 'problem') return changesFor(M, id);
        if (slot === 'change') return stepsFor(M, id);
        if (slot === 'step') return actionsFor(M, id);
        return [];
      });
    });
    return r;
  }
  // The path the release's own overview singles out.
  function defaultPath(M) {
    var spine = (M.d.overview || []).filter(function (b) { return b.type === 'spine'; })[0], p = {};
    if (spine) {
      spine.hops.forEach(function (h) { if (h.via === 'addresses' && M.nodes[h.to] && M.nodes[h.to].tree === 'current_reality') { p.problem = h.to; p.change = h.from; } });
      spine.hops.forEach(function (h) { if (h.via === 'implements' && h.to === p.change) p.step = h.from; });
      spine.hops.forEach(function (h) { if (h.via === 'implements' && h.to === p.step) p.action = h.from; });
    }
    return normalizePath(M, p);
  }
  // Put a chosen statement on the path, keeping whatever else still fits.
  function pathThrough(M, cur, id) {
    var n = M.nodes[id], p = Object.assign({}, cur || {});
    if (!n) return normalizePath(M, p);
    function refs(via, treeKey, kind) {
      return M.xout[id].filter(function (x) {
        var target = M.nodes[x.to];
        return x.via === via && target.tree === treeKey && target.kind === kind;
      }).map(function (x) { return x.to; });
    }
    var slot, parent, options;
    if (n.tree === 'current_reality' && n.kind === 'undesirable_effect') {
      slot = 'problem';
    } else if (n.tree === 'future_reality' && n.kind === 'injection') {
      slot = 'change'; parent = 'problem'; options = refs('addresses', 'current_reality', 'undesirable_effect');
    } else if (n.tree === 'prerequisite' && n.kind === 'intermediate_objective') {
      slot = 'step'; parent = 'change'; options = refs('implements', 'future_reality', 'injection');
    } else if (n.tree === 'transition' && n.kind === 'action') {
      slot = 'action'; parent = 'step'; options = refs('implements', 'prerequisite', 'intermediate_objective');
    } else return null;
    if (parent && options.length) {
      var previous = options.indexOf(p[parent]) >= 0 ? p[parent] : options[0];
      p = pathThrough(M, p, previous);
      if (!p) return null;
    }
    p[slot] = id;
    var result = normalizePath(M, p);
    return result[slot] === id ? result : null;
  }

  function stats(M) {
    var all = Object.keys(M.nodes).map(function (i) { return M.nodes[i]; }).concat(Object.keys(M.links).map(function (i) { return M.links[i]; }));
    var s = { statements: Object.keys(M.nodes).length, connections: Object.keys(M.links).length, proposed: 0, accepted: 0, disputed: 0, acceptedByAnyone: 0, byAI: 0, joint: 0, loops: 0, open: 0, proposers: Object.create(null) };
    all.forEach(function (x) {
      s[x.status] = (s[x.status] || 0) + 1;
      if ((x.accepted_by || []).length) s.acceptedByAnyone++;
      var ai = (x.contributors || []).length && x.contributors.every(function (c) { return c.role === 'assistant'; });
      if (ai) s.byAI++;
      (x.contributors || []).forEach(function (c) { s.proposers[c.name] = (s.proposers[c.name] || 0) + 1; });
      if (x.isLink && x.from.length > 1) s.joint++;
      if (x.isLink && isLoop(x)) s.loops++;
    });
    Object.keys(M.backlog).forEach(function (k) { s.open += M.backlog[k].length; });
    s.total = all.length;
    return s;
  }

  function search(M, q, limit) {
    q = (q || '').trim().toLowerCase(); if (q.length < 2) return [];
    var words = q.split(/\s+/), hits = [];
    Object.keys(M.nodes).forEach(function (id) {
      var n = M.nodes[id];
      var authors = M.d.authors || {};
      var people = (n.source_refs || []).map(function (r) { return r.author && authors[r.author] ? authors[r.author].name : ''; })
        .concat((n.contributors || []).map(function (c) { return c.name; }), n.accepted_by || []).join(' ');
      var hay = (n.text + ' ' + n.label + ' ' + kindLabel(n) + ' ' + n.status + ' ' + people + ' ' + id).toLowerCase();
      if (words.every(function (w) { return hay.indexOf(w) >= 0; })) hits.push({ id: id, rank: n.text.toLowerCase().indexOf(words[0]) >= 0 ? 0 : 1 });
    });
    hits.sort(function (a, b) { return a.rank - b.rank; });
    return hits.slice(0, limit || 12).map(function (h) { return h.id; });
  }

  g.RC = {
    TREES: TREES, KIND: KIND, REL: REL, REL_JOINT: REL_JOINT, XREF: XREF, BASIS: BASIS, WORK: WORK, STANDING: STANDING,
    build: build, item: item, tree: tree, kindLabel: kindLabel, role: role, claimType: claimType, relPhrase: relPhrase, isJoint: isJoint, isLoop: isLoop,
    goalNode: goalNode, problems: problems, changesFor: changesFor, stepsFor: stepsFor, actionsFor: actionsFor, goalAnchors: goalAnchors,
    routeToGoal: routeToGoal, risksOf: risksOf, hasDirect: hasDirect, normalizePath: normalizePath, pathOptions: pathOptions, defaultPath: defaultPath,
    pathThrough: pathThrough, stats: stats, search: search
  };
})(typeof window !== 'undefined' ? window : globalThis);
