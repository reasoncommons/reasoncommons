(function () {
  'use strict';
  var RC = window.RC;
  var D = JSON.parse(document.getElementById('rc-data').textContent);
  var local = D.view === 'private';
  var M = RC.build(D);
  var S = RC.stats(M);
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var main = $('#main'), insp = $('#insp'), rail = $('#rail');

  var GLYPH = { aim: '◎', problem: '▲', change: '◆', predict: '○', risk: '▽', step: '■', action: '▶', now: '●', need: '◐' };
  var NOTE_TYPES = ['Observation', 'Objection', 'Counterexample', 'Request for evidence', 'Correction to a paraphrase', 'Question'];

  // ---------- state
  var store = {};
  var storageKey = local ? 'reason-commons-workspace:' + D.storage_key : 'rc-g2-workspace';
  try { store = JSON.parse(localStorage.getItem(storageKey) || '{}') || {}; } catch (e) { store = {}; }
  function save() {
    try { localStorage.setItem(storageKey, JSON.stringify(store)); return true; }
    catch (e) { return false; }
  }
  var st = {
    view: 'start', arg: null, sel: null,
    path: RC.normalizePath(M, store.path || RC.defaultPath(M)),
    trail: [], expand: Object.create(null), openWork: 'all', openTree: 'all', notes: Array.isArray(store.notes) ? store.notes : []
  };

  // ---------- small helpers
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function plural(n, one, many) { return n + ' ' + (n === 1 ? one : (many || one + 's')); }
  function openCount(id) { return (M.backlog[id] || []).length; }
  function day(s) { var p = String(s).slice(0, 10).split('-'); var m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+p[1] - 1]; return +p[2] + ' ' + m + ' ' + p[0]; }
  function hashFor(view) {
    var args = [].slice.call(arguments, 1).map(function (part) {
      if (part == null) return '';
      var encoded = encodeURIComponent(part).replace(/'/g, '%27');
      return /(^-|--|-$)/.test(encoded) ? encoded.replace(/-/g, '%2D') : encoded;
    });
    while (args.length && !args[args.length - 1]) args.pop();
    return '#' + [view].concat(args).join('--');
  }
  function readHash() {
    return (location.hash || '#start').slice(1).split('--').map(function (part) {
      try { return decodeURIComponent(part); } catch (e) { return ''; }
    });
  }
  function taskLabel(task) {
    return task.label || RC.WORK[task.work] || task.work.replace(/_/g, ' ');
  }
  function availablePath(path) {
    return RC.goalNode(M) || path.problem || path.change || path.step || path.action;
  }
  function acceptedNames(x) {
    return (x.accepted_by || []).map(function (a) { return a.name || a; });
  }
  function pathHash(p) { return hashFor('path', p.problem, p.change, p.step, p.action); }
  function standingWord(x) {
    var who = (x.contributors || []).map(function (c) { return c.name; }).join(', ') || 'not recorded';
    var standing = RC.STANDING[x.status] || x.status;
    return x.status === 'proposed' ? standing + ' by ' + who : standing;
  }

  // A statement as a card. `act` decides what a click does: inspect (default) or refocus the trace.
  function card(id, opt) {
    opt = opt || {};
    var n = M.nodes[id]; if (!n) return '<span class="missing">Statement ' + esc(id) + ' is not in this release.</span>';
    var r = RC.role(n), oc = openCount(id);
    var attr = opt.focus ? 'data-go="' + hashFor('focus', id) + '"' : 'data-sel="' + esc(id) + '"';
    var text = opt.full ? n.text : n.label;
    return '<button type="button" class="st st-' + r + ' is-' + n.status + (opt.big ? ' st-big' : '') + (opt.small ? ' st-small' : '') + (st.sel === id ? ' sel' : '') + '" ' + attr + ' data-id="' + esc(id) + '">' +
      '<span class="st-kind"><span class="gl" aria-hidden="true">' + GLYPH[r] + '</span>' + esc(RC.kindLabel(n)) +
      (opt.tag ? ' <span class="st-tag">' + esc(opt.tag) + '</span>' : '') +
      (oc ? ' <span class="st-open" title="Open questions on this statement">' + plural(oc, 'open question') + '</span>' : '') +
      (n.status !== 'proposed' ? ' <span class="st-standing">' + esc(RC.STANDING[n.status] || n.status) + '</span>' : '') + '</span>' +
      '<span class="st-text">' + esc(text) + '</span>' +
      (n.proposed_role ? '<span class="st-who">Who: unassigned · proposed role: ' + esc(n.proposed_role) + '</span>' : '') +
      '</button>';
  }
  // The relation of one connection, as a control that opens the connection itself.
  function relButton(lid, opt) {
    opt = opt || {};
    var l = M.links[lid], marks = [];
    if ((l.assumptions || []).length) marks.push(plural(l.assumptions.length, 'assumption') + ' recorded');
    if (openCount(lid)) marks.push(plural(openCount(lid), 'open question'));
    var loop = RC.isLoop(l);
    marks.unshift(RC.STANDING[l.status] || l.status);
    return '<button type="button" class="rel' + (loop ? ' rel-loop' : '') + (l.relation === 'prevents' ? ' rel-prevents' : '') + (st.sel === lid ? ' sel' : '') + '" data-sel="' + esc(lid) + '" data-id="' + esc(lid) + '">' +
      '<span class="rel-arrow" aria-hidden="true">' + (loop ? '↺' : '↓') + '</span><span class="rel-word">' + esc(opt.phrase || RC.relPhrase(l)) + '</span>' +
      (marks.length ? '<span class="rel-marks">' + esc(marks.join(' · ')) + '</span>' : '') +
      '<span class="rel-inspect">Inspect this connection</span></button>';
  }
  function jointNote(l) {
    return RC.isJoint(l) ? '<p class="joint-note"><span aria-hidden="true">⦚</span> One connection from ' + l.from.length + ' statements together. The record does not say any one of them is enough alone.</p>' : '';
  }

  // ---------- views
  function pathPreview(goal, path) {
    var stops = [['In the way', path.problem], ['A change', path.change], ['A first step', path.step], ['An action', path.action]];
    if (goal && !local) stops.unshift(['Goal', goal.id]);
    return '<ol class="teaser">' + stops.map(function (stop) {
      var n = M.nodes[stop[1]];
      return n ? '<li class="tz tz-' + RC.role(n) + '"><span class="tz-k"><span class="gl" aria-hidden="true">' + GLYPH[RC.role(n)] +
        '</span>' + esc(stop[0]) + '</span><span class="tz-t">' + esc(n.label) + '</span></li>' : '';
    }).join('') + '</ol><p><a class="btn btn-primary" href="' + pathHash(path) + '">Follow this path</a></p>';
  }
  function questionList() {
    return '<section aria-labelledby="six-h"><h2 id="six-h">Browse by question</h2><ol class="six">' +
      M.trees.map(function (T) {
        var t = D.trees[T.key];
        return '<li><a href="' + hashFor('q', T.slug) + '"><span class="six-q">' + esc(T.q) + '</span><span class="six-n">' +
          plural(t.nodes.length, 'statement') + ' · ' + plural(t.backlog.length, 'open question') + '</span></a></li>';
      }).join('') + '</ol></section>';
  }
  function viewPrivateStart() {
    var goal = RC.goalNode(M), path = st.path;
    var h = '<header class="hero"><h1 tabindex="-1">' + esc(D.title) + '</h1><p class="lede">From ' + esc(D.source_file) + '</p></header>';
    if (!S.total) return h + '<p class="empty">No reasoning has been recorded yet.</p>';
    if (goal) {
      h += '<section class="goal-block" aria-label="The goal"><p class="eyebrow">The goal</p>' +
        card(goal.id, { full: true, big: true }) + '</section>';
    }
    if (path.problem || path.change || path.step || path.action) {
      h += '<section aria-labelledby="pt-h"><h2 id="pt-h">One path through the reasoning</h2>' +
        '<p class="sub">Follow the recorded connections and see where the path ends.</p>' + pathPreview(goal, path) + '</section>';
    }
    return h + questionList();
  }
  function viewStart() {
    if (local) return viewPrivateStart();
    var gn = RC.goalNode(M), p = RC.defaultPath(M);
    var allProposed = S.proposed === S.total;
    var unassigned = D.trees.transition.nodes.filter(function (n) { return n.kind === 'action'; });
    var h = '<header class="hero"><p class="eyebrow">Source reconstruction · release ' + esc(D.release_id) + ' · ' + day(D.snapshot_date) + ' · read-only</p>' +
      '<h1 tabindex="-1">' + esc(D.title) + '</h1>' +
      '<p class="lede">A map of the reasoning in one public forum thread, the essays shared in it and two analyses of it. Follow it from the goal to a first action, and check every step for yourself.</p></header>';
    h += '<section class="goal-block" aria-label="The proposed goal"><p class="eyebrow">The proposed goal</p>' + card(gn.id, { full: true, big: true }) + '</section>';
    h += '<section class="standing-box" aria-labelledby="sb-h"><h2 id="sb-h">What you are looking at</h2><dl class="facts">' +
      '<div><dt>' + S.statements + ' statements, ' + S.connections + ' connections</dt><dd>' + (allProposed ? 'All ' + S.total + ' are proposed.' : S.proposed + ' proposed, ' + (S.accepted || 0) + ' accepted for now, ' + (S.disputed || 0) + ' disputed.') + ' ' + (S.acceptedByAnyone ? S.acceptedByAnyone + ' have been accepted by a named person.' : 'Nobody has accepted any of them.') + '</dd></div>' +
      '<div><dt>Who wrote them</dt><dd>' + esc(Object.keys(S.proposers).map(function (k) { return k + ' (' + S.proposers[k] + ')'; }).join(', ')) + '. The wording is the AI’s, built from the sources below.</dd></div>' +
      '<div><dt>Whose ideas</dt><dd>' + esc(Object.keys(D.authors).map(function (k) { return D.authors[k].name; }).join(', ')) + ' took part in the thread. A credit says where an idea comes from. It does not mean its author agrees with the wording, and none of them has reviewed it.</dd></div>' +
      D.people.map(function (x) { return '<div><dt>' + esc(x.name) + '</dt><dd>' + esc(x.role) + '.</dd></div>'; }).join('') +
      '<div><dt>What is open</dt><dd>' + S.open + ' open questions are recorded. ' + unassigned.length + ' actions are proposed and none has an owner.</dd></div></dl></section>';

    h += '<section aria-labelledby="pt-h"><p class="eyebrow">Start here</p><h2 id="pt-h">One path, from the goal to a first action</h2>' +
      '<p class="sub">This is the path the release itself singles out. Each stop is one statement.</p>' + pathPreview(gn, p) + '</section>';

    h += '<section aria-labelledby="ways-h"><h2 id="ways-h">Three ways in</h2><div class="ways">' +
      '<a class="way" href="' + pathHash(p) + '"><span class="way-k">New here</span><span class="way-t">Read the argument as one path</span><span class="way-d">Five stops. Swap any stop to see a different problem, change or step.</span></a>' +
      '<a class="way" href="' + hashFor('focus', p.problem) + '"><span class="way-k">Sceptical</span><span class="way-t">Take one claim apart</span><span class="way-d">See what is said to cause this problem, which causes act together, the assumption behind each connection and its source.</span></a>' +
      '<a class="way" href="#open"><span class="way-k">Taking part</span><span class="way-t">Find something to check or settle</span><span class="way-d">' + S.open + ' open questions, each tied to one statement or connection. Draft a note on any of them.</span></a></div></section>';

    h += '<section aria-labelledby="six-h"><h2 id="six-h">Six questions the map answers</h2><ol class="six">' +
      RC.TREES.map(function (T) {
        var t = D.trees[T.key];
        return '<li><a href="' + hashFor('q', T.slug) + '"><span class="six-q">' + esc(T.q) + '</span><span class="six-n">' + plural(t.nodes.length, 'statement') + ' · ' + plural(t.backlog.length, 'open question') + '</span></a></li>';
      }).join('') + '</ol></section>';

    h += '<section aria-labelledby="src-h"><h2 id="src-h">Sources</h2><ul class="sources">' + D.sources.map(function (s) {
      return '<li><span class="src-t">' + (s.url ? '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.title) + '</a>' : esc(s.title)) + '</span><span class="src-d">' + esc(s.description) + '</span></li>';
    }).join('') + '</ul></section>';
    h += '<section aria-labelledby="hist-h"><h2 id="hist-h">How this record has changed</h2><ol class="hist">' + D.history.map(function (r) {
      return '<li><span class="mono">' + esc(r.release_id) + '</span><strong>' + esc(r.title) + '</strong><span>' + esc(r.summary) + '</span></li>';
    }).join('') + '</ol></section>';
    return h;
  }

  function swap(slot, list, current, lead) {
    if (local && list.length < 2) return '';
    if (list.length < 2) return '<p class="swap-none">' + esc(lead(list.length)) + '</p>';
    var compare = slot === 'change';
    var rows = list.map(function (id) {
      var n = M.nodes[id], on = id === current, extra = '';
      if (compare) {
        var addr = M.xout[id].filter(function (x) { return x.via === 'addresses'; }).length;
        extra = '<span class="cmp">' + plural(addr, 'problem') + ' addressed</span><span class="cmp">' + plural(RC.risksOf(M, id).length, 'risk') + ' recorded</span><span class="cmp">' + plural(RC.stepsFor(M, id).length, 'first step') + '</span><span class="cmp">' + plural(openCount(id), 'open question') + '</span>';
      } else if (slot === 'step') {
        extra = '<span class="cmp">' + (RC.actionsFor(M, id).length ? plural(RC.actionsFor(M, id).length, 'action') : 'no action recorded') + '</span>';
      } else if (slot === 'problem') {
        extra = '<span class="cmp">' + plural(RC.changesFor(M, id).length, 'change') + ' meant to address it</span>';
      }
      return '<li><button type="button" class="opt' + (on ? ' on' : '') + '" aria-pressed="' + on + '" data-pick="' + slot + '" data-id="' + esc(id) + '"><span class="opt-t">' + esc(n.label) + '</span>' + extra + '</button></li>';
    }).join('');
    return '<details class="swap"' + (st.expand['swap-' + slot] ? ' open' : '') + ' data-keep="swap-' + slot + '"><summary>' + esc(lead(list.length)) + ' <span class="swap-cta">Compare and swap</span></summary>' +
      (compare ? '<p class="swap-note">The counts are what the record holds. They are not scores.</p>' : '') + '<ul class="opts">' + rows + '</ul></details>';
  }

  function viewPath() {
    var p = st.path, gn = RC.goalNode(M);
    if (!availablePath(p)) return '<header class="vh"><h1 tabindex="-1">No path recorded yet</h1><p><a href="#start">Back to the commons</a></p></header>';
    var heading = local ? 'Follow the recorded path' : 'From the goal to a first action';
    var h = '<header class="vh"><h1 tabindex="-1">' + heading + '</h1><p class="lede">' +
      'Select a statement to see its exact wording, standing and open questions.</p></header><ol class="stops">';
    var number = 0;
    function stopTitle(question) {
      number += 1;
      return '<li class="stop"><p class="stop-q"><span class="num">' + number + '</span>' + question + '</p>';
    }

    // 1 goal
    if (gn) {
      var csf = M.inc[gn.id].filter(function (id) { return M.links[id].relation === 'necessary_for'; }).length;
      h += stopTitle('What are we trying to achieve?') + card(gn.id, { full: true, big: true }) +
        '<p class="stop-more">' + plural(csf, 'connection') + ' ' + (csf === 1 ? 'is' : 'are') + ' recorded as needed for it. <a href="#q--goal">See the goal tree</a></p></li>';
    }

    var first = p.problem || p.change || p.step || p.action;
    if (gn && first) {
      var direct = RC.hasDirect(M, gn.id, first);
      var throughChange = p.change && RC.routeToGoal(M, p.change);
      h += '<li class="join join-gap"><span class="join-line" aria-hidden="true"></span><p>' +
        (direct ? 'There is a recorded reference between this statement and the goal.' :
          'No direct connection is recorded between the goal and the next statement.' +
          (throughChange ? ' See the predicted route from the change to the goal below.' : '')) + '</p></li>';
    }

    // 2 problem
    if (p.problem || !local) {
      var pin = p.problem ? M.inc[p.problem] : [];
      h += stopTitle('What stands in the way?') + (p.problem ? card(p.problem, { full: true, big: true }) : '<p class="empty">No problem is recorded.</p>') +
        swap('problem', RC.problems(M), p.problem, function (n) { return plural(n, 'problem') + ' ' + (n === 1 ? 'is' : 'are') + ' recorded.'; }) +
        (p.problem ? '<p class="stop-more">' + (pin.length ? plural(pin.length, 'connection') + ' lead' + (pin.length === 1 ? 's' : '') + ' into this problem' + (pin.some(function (i) { return RC.isJoint(M.links[i]); }) ? ', some from several causes acting together' : '') + '.' : 'No cause is recorded for this problem.') + ' <a href="' + hashFor('focus', p.problem) + '">Why? Trace what leads to it</a></p>' : '') + '</li>';
    }

    // join problem - change
    if (p.change && p.problem) h += '<li class="join"><span class="join-line" aria-hidden="true"></span><p><span class="join-arrow" aria-hidden="true">↑</span> The change below <strong>' + RC.XREF.addresses.fwd + '</strong> this problem. <span class="join-kind">A reference between two questions, recorded on the change.</span></p></li>';

    // 3 change
    if (p.change || p.problem || !local) {
      h += stopTitle('What will we change?');
      if (p.change) {
        h += card(p.change, { full: true, big: true });
        h += swap('change', RC.pathOptions(M, p, 'change'), p.change, function (n) { return plural(n, 'change') + (p.problem ? ' linked to this problem.' : ' recorded.'); });
        var from = M.xout[p.change].filter(function (ref) {
          var node = M.nodes[ref.to];
          return ref.via === 'derived_from' && node.tree === 'conflict' && node.kind === 'prerequisite';
        });
        if (from.length) h += '<div class="sub-block"><p class="sub-h">Developed from ' + plural(from.length, 'position') + ' in a conflict</p><div class="minis">' + from.map(function (x) { return card(x.to, { small: true }); }).join('') + '</div></div>';
        var route = RC.routeToGoal(M, p.change);
        if (route) {
          h += '<details class="sub-block"' + (st.expand.route !== false ? ' open' : '') + ' data-keep="route"><summary class="sub-h">Predicted route to the goal · ' + plural(route.length, 'connection') + '</summary>' +
            '<p class="sub-note">The shortest recorded chain from this change to an effect linked to the goal.</p><ol class="route">' + route.map(function (lid, index) {
            var l = M.links[lid];
            var prev = index === 0 ? p.change : M.links[route[index - 1]].to;
            var others = l.from.filter(function (f) { return f !== prev; });
            return '<li>' + (others.length ? '<div class="with"><span class="with-h">Together with</span>' + others.map(function (o) { return card(o, { small: true }); }).join('') + '</div>' : '') + relButton(lid) + card(l.to, { small: true }) + '</li>';
          }).join('') + '</ol>';
          h += '<p class="sub-note">The last effect ' + RC.XREF.implements.fwd + ' the goal at stop 1.</p></details>';
        } else if (gn) {
          h += '<p class="stop-more">No route from this change to the goal is recorded.</p>';
        }
        var risks = RC.risksOf(M, p.change);
        if (risks.length) {
          h += '<details class="sub-block"' + (st.expand.risks ? ' open' : '') + ' data-keep="risks"><summary class="sub-h">' + plural(risks.length, 'predicted risk') + ' of this change</summary>' +
            '<ul class="risks">' + risks.map(function (r) {
              return '<li>' + relButton(r.link) + card(r.risk, { small: true }) + (r.remedies.length ? r.remedies.map(function (rl) { return '<div class="remedy">' + M.links[rl].from.map(function (f) { return card(f, { small: true }); }).join('') + relButton(rl) + '</div>'; }).join('') : '<p class="sub-note">No remedy is recorded for this risk.</p>') + '</li>';
            }).join('') + '</ul></details>';
        }
      } else h += '<p class="empty">' + (p.problem ? 'No change is linked to this problem.' : 'No change is recorded.') + '</p>';
      h += '</li>';
    }

    // join change - step
    if (p.step && p.change) h += '<li class="join"><span class="join-line" aria-hidden="true"></span><p><span class="join-arrow" aria-hidden="true">↑</span> The step below <strong>' + RC.XREF.implements.fwd + '</strong> this change. <span class="join-kind">A reference between two questions, recorded on the step.</span></p></li>';

    // 4 step
    if (p.step || p.change || !local) {
      h += stopTitle('What has to happen first?');
      if (p.step) {
        h += card(p.step, { full: true, big: true });
        h += swap('step', RC.pathOptions(M, p, 'step'), p.step, function (n) { return plural(n, 'first step') + (p.change ? ' linked to this change.' : ' recorded.'); });
        var over = M.out[p.step].filter(function (i) { return M.links[i].relation === 'overcomes'; });
        h += '<div class="sub-block"><p class="sub-h">' + (over.length ? 'The obstacle it gets past' : 'No obstacle is recorded for this step') + '</p>' + over.map(function (i) { return relButton(i) + card(M.links[i].to, { small: true }); }).join('') + '</div>';
        var needs = M.inc[p.step].filter(function (i) { return M.links[i].relation === 'necessary_for'; });
        h += '<div class="sub-block"><p class="sub-h">' + (needs.length ? 'What it needs first' : 'Nothing is recorded as needed before this step') + '</p>' + needs.map(function (i) {
          var l = M.links[i];
          return '<div class="grp' + (RC.isJoint(l) ? ' grp-joint' : '') + '">' + jointNote(l) + '<div class="grp-nodes">' + l.from.map(function (f) { return card(f, { small: true }); }).join('') + '</div>' + relButton(i) + '</div>';
        }).join('') + '</div>';
        var chk = M.backlog[p.step] || [];
        if (chk.length) h += '<div class="sub-block"><p class="sub-h">Open on this step</p><ul class="oq-mini">' + chk.map(function (b) { return '<li><span class="oq-w">' + esc(RC.WORK[b.work] || b.work) + '</span>' + esc(taskLabel(b)) + '</li>'; }).join('') + '</ul></div>';
      } else h += '<p class="empty">' + (p.change ? 'No first step is linked to this change.' : 'No first step is shown on this path.') + '</p>';
      h += '</li>';
    }

    // join step - action
    if (p.action && p.step) h += '<li class="join"><span class="join-line" aria-hidden="true"></span><p><span class="join-arrow" aria-hidden="true">↑</span> The action below <strong>' + RC.XREF.implements.fwd + '</strong> this step. <span class="join-kind">A reference between two questions, recorded on the action.</span></p></li>';

    // 5 action
    if (p.action || p.step || !local) {
      h += stopTitle('Who does what?');
      if (p.action) {
        var a = M.nodes[p.action];
        h += card(p.action, { full: true, big: true });
        h += swap('action', RC.pathOptions(M, p, 'action'), p.action, function (n) { return plural(n, 'action') + (p.step ? ' linked to this step.' : ' recorded.'); });
        h += '<div class="who"><p class="who-h">Who</p><p class="who-v">' + esc(a.owner || 'Unassigned') + '</p>' +
          (a.proposed_role ? '<p class="who-n">Suggested role: <strong>' + esc(a.proposed_role) + '</strong></p>' : '') + '</div>';
        M.out[p.action].forEach(function (i) {
          var l = M.links[i], others = l.from.filter(function (f) { return f !== p.action; });
          h += '<div class="sub-block"><p class="sub-h">What it starts from, and what it is meant to produce</p>' + (others.length ? '<div class="with"><span class="with-h">Together with</span>' + others.map(function (o) { return card(o, { small: true }); }).join('') + '</div>' : '') + relButton(i) + card(l.to, { small: true }) + '</div>';
        });
      } else h += '<p class="empty">' + (p.step ? 'No action is linked to this step.' : 'No action is shown on this path.') + '</p>';
      h += '</li>';
    }
    return h + '</ol>';
  }

  // Incoming connections of a statement, each as one group so joint sources stay one connection.
  function incoming(id, seen, depth) {
    var links = M.inc[id];
    if (!links.length) return '<p class="empty">Nothing is recorded as leading to this. It is a starting point of this part of the map.</p>';
    return '<ul class="grps">' + links.map(function (lid) {
      var l = M.links[lid];
      return '<li class="grp' + (RC.isJoint(l) ? ' grp-joint' : '') + '">' + jointNote(l) + '<div class="grp-nodes">' + l.from.map(function (f) {
        var key = 'why-' + JSON.stringify(seen.concat([id, lid, f])), looped = seen.indexOf(f) >= 0 || f === id, has = M.inc[f].length;
        var open = !!st.expand[key];
        return '<div class="src-node">' + card(f, { focus: true, small: depth > 0 }) +
          (looped ? '<p class="loop-note"><span aria-hidden="true">↺</span> This is already on the chain above: a loop in the record.</p>' :
            has ? '<button type="button" class="why" aria-expanded="' + open + '" data-toggle="' + esc(key) + '">' + (open ? 'Hide' : 'Why?') + ' <span class="why-n">' + plural(has, 'connection') + ' lead' + (has === 1 ? 's' : '') + ' here</span></button>' + (open ? '<div class="nest">' + incoming(f, seen.concat([id]), depth + 1) + '</div>' : '') :
              '<p class="root-note">Nothing is recorded behind this.</p>') + '</div>';
      }).join('') + '</div>' + relButton(lid) + '</li>';
    }).join('') + '</ul>';
  }

  function viewFocus() {
    var id = st.arg, n = M.nodes[id];
    if (!n) return '<header class="vh"><h1 tabindex="-1">Statement unavailable</h1><p class="lede">This link may point to an earlier version of the record. <a href="#start">Go to the start</a>.</p></header>';
    var T = RC.tree(n.tree);
    var h = '<header class="vh"><p class="eyebrow"><a href="' + hashFor('q', T.slug) + '">' + esc(T.q) + '</a></p><h1 tabindex="-1" class="h-quiet">Tracing one statement</h1>';
    if (st.trail.length > 1) h += '<nav class="trail" aria-label="Statements you came through"><span>You came through</span><ol>' + st.trail.slice(-5, -1).map(function (t) { return '<li><a href="' + hashFor('focus', t) + '">' + esc(M.nodes[t].label) + '</a></li>'; }).join('') + '</ol></nav>';
    h += '</header>';
    h += '<section class="dir" aria-labelledby="in-h"><h2 id="in-h">What leads to this</h2><p class="sub">Each group is one recorded connection.</p>' + incoming(id, [], 0) + '</section>';
    h += '<section class="focus-card" aria-label="The statement in focus">' + card(id, { full: true, big: true }) + '<p class="claim-type">' + esc(RC.claimType(n)) + ' · ' + esc(standingWord(n)) + (acceptedNames(n).length ? ' · ' + (n.status === 'disputed' ? 'earlier accepted by ' : 'accepted by ') + esc(acceptedNames(n).join(', ')) : '') + '</p></section>';
    var outs = M.out[id];
    h += '<section class="dir" aria-labelledby="out-h"><h2 id="out-h">What this leads to</h2>' + (outs.length ? '<ul class="grps">' + outs.map(function (lid) {
      var l = M.links[lid], others = l.from.filter(function (f) { return f !== id; });
      return '<li class="grp' + (RC.isJoint(l) ? ' grp-joint' : '') + '">' + (others.length ? jointNote(l) + '<div class="with"><span class="with-h">Together with</span>' + others.map(function (o) { return card(o, { focus: true, small: true }); }).join('') + '</div>' : '') + relButton(lid) + card(l.to, { focus: true }) + '</li>';
    }).join('') + '</ul>' : '<p class="empty">Nothing is recorded as following from this within this question.</p>') + '</section>';

    var xo = M.xout[id], xi = M.xin[id];
    if (xo.length || xi.length) {
      h += '<section class="dir" aria-labelledby="x-h"><h2 id="x-h">Connections across questions</h2><p class="sub">References from a statement under one question to a statement under another.</p>';
      Object.keys(RC.XREF).forEach(function (via) {
        var o = xo.filter(function (x) { return x.via === via; }), i = xi.filter(function (x) { return x.via === via; });
        function xg(head, ids, key) {
          var cards = '<div class="minis">' + ids.map(function (c) { return card(c, { focus: true, small: true }); }).join('') + '</div>';
          return ids.length > 4 ? '<details class="xgroup"' + (st.expand[key] ? ' open' : '') + ' data-keep="' + key + '"><summary class="sub-h">' + head + ' · ' + plural(ids.length, 'statement') + '</summary>' + cards + '</details>' : '<div class="xgroup"><p class="sub-h">' + head + '</p>' + cards + '</div>';
        }
        if (o.length) h += xg(RC.XREF[via].head, o.map(function (x) { return x.to; }), 'xo-' + via);
        if (i.length) h += xg(RC.XREF[via].back, i.map(function (x) { return x.from; }), 'xi-' + via);
      });
      h += '</section>';
    }
    return h;
  }

  function cloud(v) {
    var ids = v.nodes, links = D.trees.conflict.links.filter(function (l) { return ids.indexOf(l.to) >= 0 && l.from.every(function (f) { return ids.indexOf(f) >= 0; }); });
    var obj = ids.filter(function (i) { return M.nodes[i].kind === 'objective'; })[0];
    var clash = links.filter(function (l) { return l.relation === 'conflicts_with'; })[0];
    var needs = links.filter(function (l) { return l.relation === 'necessary_for' && l.to === obj; });
    var h = '<div class="cloud">' + (obj ? '<div class="cloud-obj"><p class="sub-h">Both sides want</p>' + card(obj) + '</div>' : '') + '<div class="cloud-sides">';
    needs.forEach(function (nl, k) {
      var need = nl.from[0], pos = links.filter(function (l) { return l.relation === 'necessary_for' && l.to === need; });
      h += '<div class="cloud-side"><p class="sub-h">Side ' + 'AB'.charAt(k) + '</p>' + pos.map(function (pl) { return card(pl.from[0]) + relButton(pl.id); }).join('') + card(need) + relButton(nl.id) + '</div>';
    });
    h += '</div>' + (clash ? '<div class="cloud-clash"><span aria-hidden="true">⇄</span> The two positions are recorded as conflicting. ' + '<button type="button" class="linklike" data-sel="' + esc(clash.id) + '">Inspect the conflict</button></div>' : '') + '</div>';
    return h;
  }

  function viewQuestion() {
    var T = RC.tree(st.arg);
    if (!T || !D.trees[T.key]) return '<header class="vh"><h1 tabindex="-1">No reasoning recorded for this question</h1><p><a href="#start">Back to the commons</a></p></header>';
    var t = D.trees[T.key], parts = (D.views || {})[T.key] || [];
    if (local) {
      return '<header class="vh"><h1 tabindex="-1">' + esc(T.q) + '</h1><p class="lede">' +
        plural(t.nodes.length, 'statement') + ' · ' + plural(t.links.length, 'connection') + '</p></header>' +
        '<section class="list" aria-label="Statements">' + t.nodes.map(function (n) { return card(n.id); }).join('') + '</section>';
    }
    var kinds = {};
    t.nodes.forEach(function (n) { var k = RC.kindLabel(M.nodes[n.id]); kinds[k] = (kinds[k] || 0) + 1; });
    var h = '<header class="vh"><p class="eyebrow">Question ' + (RC.TREES.indexOf(T) + 1) + ' of 6 · ' + esc(T.formal) + '</p><h1 tabindex="-1">' + esc(T.q) + '</h1>' +
      '<p class="lede">' + Object.keys(kinds).map(function (k) { return k === 'Already true' ? kinds[k] + ' already true' : plural(kinds[k], k.toLowerCase()); }).join(', ') + '. ' + plural(t.links.length, 'connection') + '. Select a statement to inspect it, then trace it.</p></header>';
    if (T.key === 'goal') {
      var gn = RC.goalNode(M);
      h += '<section class="part">' + card(gn.id, { full: true, big: true }) + '<p class="sub-h">Needed for it</p><ul class="outline">' + M.inc[gn.id].map(function (lid) {
        return M.links[lid].from.map(function (f) {
          return '<li>' + card(f) + (M.inc[f].length ? '<ul class="outline">' + M.inc[f].map(function (l2) { return M.links[l2].from.map(function (g2) { return '<li>' + card(g2, { small: true }) + '</li>'; }).join(''); }).join('') + '</ul>' : '') + '</li>';
        }).join('');
      }).join('') + '</ul></section>';
    } else if (T.key === 'conflict') {
      parts.forEach(function (v) { h += '<section class="part"><h2>' + esc(v.title) + '</h2><p class="sub">' + esc(v.summary) + '</p>' + cloud(v) + '</section>'; });
    } else {
      parts.forEach(function (v, i) {
        h += '<section class="part"><p class="eyebrow">Part ' + (i + 1) + ' of ' + parts.length + '</p><h2>' + esc(v.title) + '</h2><p class="sub">' + esc(v.summary) + '</p><div class="list">' + v.nodes.map(function (id) { return card(id); }).join('') + '</div></section>';
      });
      var placed = {}; parts.forEach(function (v) { v.nodes.forEach(function (i) { placed[i] = 1; }); });
      var loose = t.nodes.filter(function (n) { return !placed[n.id]; });
      if (loose.length) h += '<section class="part"><h2>Not placed in a part</h2><div class="list">' + loose.map(function (n) { return card(n.id); }).join('') + '</div></section>';
    }
    return h;
  }

  function refLine(id) {
    var x = RC.item(M, id);
    if (!x) return esc(id);
    if (!x.isLink) return '“' + esc(x.label) + '”';
    return x.from.map(function (f) { return '“' + esc(M.nodes[f].label) + '”'; }).join(' + ') + ' <em>' + esc(RC.relPhrase(x)) + '</em> “' + esc(M.nodes[x.to].label) + '”';
  }

  function viewOpen() {
    var all = [];
    Object.keys(M.backlog).forEach(function (r) { M.backlog[r].forEach(function (b) { all.push(b); }); });
    var works = Object.create(null); all.forEach(function (b) { var w = RC.WORK[b.work] || b.work; works[w] = (works[w] || 0) + 1; });
    var list = all.filter(function (b) { return (st.openWork === 'all' || (RC.WORK[b.work] || b.work) === st.openWork) && (st.openTree === 'all' || b.tree === st.openTree); });
    var h = '<header class="vh"><p class="eyebrow">Unsettled, by the record’s own account</p><h1 tabindex="-1">Open questions</h1><p class="lede">' + all.length + ' questions, each tied to one statement or one connection. They are the most useful places to add something.</p></header>';
    h += '<div class="filters" role="group" aria-label="Kind of work"><button type="button" class="chip' + (st.openWork === 'all' ? ' on' : '') + '" aria-pressed="' + (st.openWork === 'all') + '" data-ow="all">All ' + all.length + '</button>' + Object.keys(works).map(function (w) { return '<button type="button" class="chip' + (st.openWork === w ? ' on' : '') + '" aria-pressed="' + (st.openWork === w) + '" data-ow="' + esc(w) + '">' + esc(w) + ' ' + works[w] + '</button>'; }).join('') + '</div>';
    h += '<div class="filters" role="group" aria-label="Question"><button type="button" class="chip' + (st.openTree === 'all' ? ' on' : '') + '" aria-pressed="' + (st.openTree === 'all') + '" data-ot="all">Any question</button>' + M.trees.map(function (T) { return '<button type="button" class="chip' + (st.openTree === T.key ? ' on' : '') + '" aria-pressed="' + (st.openTree === T.key) + '" data-ot="' + T.key + '">' + esc(T.short) + ' ' + D.trees[T.key].backlog.length + '</button>'; }).join('') + '</div>';
    h += list.length ? '<ul class="oq">' + list.map(function (b) {
      var x = RC.item(M, b.ref);
      return '<li><p class="oq-w">' + esc(RC.WORK[b.work] || b.work) + ' · ' + esc(RC.tree(b.tree).short) + '</p><p class="oq-l">' + esc(taskLabel(b)) + '</p>' + (b.note ? '<p class="oq-n">' + esc(b.note) + '</p>' : '') +
        '<p class="oq-on">About the ' + (x && x.isLink ? 'connection' : 'statement') + ': ' + refLine(b.ref) + '</p><p class="oq-a"><button type="button" class="btn" data-sel="' + esc(b.ref) + '" data-id="' + esc(b.ref) + '">Inspect it</button> <button type="button" class="btn" data-sel="' + esc(b.ref) + '" data-note="1">Draft a note on it</button></p></li>';
    }).join('') + '</ul>' : '<p class="empty">No open question matches these filters.</p>';
    return h;
  }

  function noteText(n) {
    var x = RC.item(M, n.ref);
    return 'Draft contribution (not submitted)\nRecord: ' + D.title + (local ? ' · ' + D.source_file : ', release ' + D.release_id) + '\nAbout the ' + (x && x.isLink ? 'connection' : 'statement') + ' ' + n.ref + ': ' + (x ? (x.isLink ? x.from.join(' + ') + ' ' + x.relation + ' ' + x.to : '"' + x.text + '"') : '(not in this release)') + '\nType: ' + n.type + '\n\n' + n.text;
  }
  function noteItem(n) {
    return '<li class="note"><p class="oq-w">' + esc(n.type) + ' · local draft · ' + esc(n.at) + '</p><p class="note-t">' + esc(n.text) + '</p><p class="oq-on">About: ' + refLine(n.ref) + '</p>' +
      '<p class="oq-a"><button type="button" class="btn" data-copy="' + esc(n.id) + '">Copy with its reference</button> <button type="button" class="btn" data-sel="' + esc(n.ref) + '">Inspect what it is about</button> <button type="button" class="btn btn-quiet" data-del="' + esc(n.id) + '">Delete</button></p></li>';
  }
  function viewNotes() {
    return '<header class="vh"><p class="eyebrow">Only in this browser</p><h1 tabindex="-1">Your draft notes</h1><p class="lede">Drafts stay in this browser. Copy a draft to bring it back to the conversation.</p></header>' +
      (st.notes.length ? '<ul class="oq">' + st.notes.map(noteItem).join('') + '</ul>' : '<p class="empty">No notes yet. Select any statement or connection and choose “Draft a note”.</p>');
  }

  // ---------- inspector
  function sourceList(refs) {
    if (!refs || !refs.length) return '<p class="empty">No source is recorded.</p>';
    var forum = D.sources.filter(function (s) { return s.posts; })[0];
    return '<ul class="refs">' + refs.map(function (r) {
      var s = D.sources.filter(function (x) { return x.id === r.source_id; })[0] || { title: r.source_id }, where;
      if (r.post != null) {
        var post = forum && forum.posts[String(r.post)], who = r.author && D.authors[r.author] ? D.authors[r.author].name : 'Unknown author';
        where = '<a href="' + esc(s.url + '/' + r.post) + '" target="_blank" rel="noopener">' + esc(who) + ', post ' + r.post + '</a>' + (post && post.date ? ' · ' + day(post.date) : '');
      } else where = esc(s.title.split(' · ')[0]) + (r.locator ? ', ' + esc(r.locator) : '');
      return '<li class="ref ref-' + esc(r.basis) + '"><span class="ref-w">' + where + '</span><span class="ref-b">' + esc(RC.BASIS[r.basis] || r.basis) + '</span></li>';
    }).join('') + '</ul>';
  }
  function inspector() {
    var x = st.sel && RC.item(M, st.sel);
    if (!x) {
      return '<div class="insp-empty"><h2>Inspect</h2><p>Select any statement or connection to see its exact wording, who proposed it, who has accepted it, where it comes from and what is still open.</p>' +
        '<dl class="key"><dt><span class="sw sw-proposed"></span>Dashed edge</dt><dd>Proposed</dd><dt><span class="sw sw-accepted"></span>Solid edge</dt><dd>Accepted for now</dd><dt><span class="sw sw-disputed"></span>Double edge</dt><dd>Disputed</dd></dl>' +
        '<dl class="key">' + [['aim', 'An aim'], ['problem', 'A claim about what is wrong now'], ['change', 'A proposed change'], ['predict', 'A prediction, not observed'], ['risk', 'A predicted risk'], ['step', 'A condition to reach first'], ['action', 'A proposed action'], ['need', 'A need or position in a conflict'], ['now', 'Claimed to hold now']].map(function (k) { return '<dt><span class="gl gl-' + k[0] + '" aria-hidden="true">' + GLYPH[k[0]] + '</span></dt><dd>' + k[1] + '</dd>'; }).join('') + '</dl></div>';
    }
    var T = RC.tree(x.tree), h = '<div class="insp-head"><p class="eyebrow">' + (x.isLink ? 'Connection' : esc(RC.kindLabel(x))) + ' · ' + esc(T.q) + '</p><button type="button" class="close" data-close="1" aria-label="Close details">Close</button></div>';
    if (x.isLink) {
      h += '<div class="link-sent">' + x.from.map(function (f) { return card(f, { small: true, full: true }); }).join('') + '<p class="link-rel"><span aria-hidden="true">' + (RC.isLoop(x) ? '↺' : '↓') + '</span> ' + esc(RC.relPhrase(x)) + '</p>' + card(x.to, { small: true, full: true }) + '</div>';
      h += jointNote(x);
      if (RC.isLoop(x)) h += '<p class="joint-note"><span aria-hidden="true">↺</span> This connection loops back in the record.</p>';
      h += '<p class="raw">Recorded as <span class="mono">' + esc(x.relation) + '</span>, from ' + plural(x.from.length, 'statement') + ' to 1.</p>';
    } else {
      h += '<blockquote class="canon"><p>' + esc(x.text) + '</p></blockquote>';
      if (x.label !== x.text) h += '<p class="raw">Above is the full wording in the record. Short form used on cards: “' + esc(x.label) + '”</p>';
      h += '<p class="claim-type">' + esc(RC.claimType(x)) + '</p>';
    }
    h += '<dl class="facts facts-tight"><div><dt>Standing</dt><dd><span class="standing standing-' + esc(x.status) + '">' + esc(RC.STANDING[x.status] || x.status) + '</span></dd></div>' +
      '<div><dt>Proposed by</dt><dd>' + esc((x.contributors || []).map(function (c) { return c.name + (c.role === 'assistant' ? ' (AI)' : ''); }).join(', ') || 'Not recorded') + '</dd></div>' +
      '<div><dt>' + (x.status === 'disputed' ? 'Earlier accepted by' : 'Accepted by') + '</dt><dd>' +
      (acceptedNames(x).length ? esc(acceptedNames(x).join(', ')) : 'Nobody recorded') + '</dd></div>' +
      (x.owner ? '<div><dt>Who</dt><dd>' + esc(x.owner) + '</dd></div>' : x.proposed_role ? '<div><dt>Who</dt><dd>Unassigned. Suggested role: ' + esc(x.proposed_role) + '</dd></div>' : '') + '</dl>';

    if (!x.isLink) {
      var onPath = RC.pathThrough(M, st.path, x.id);
      h += '<div class="asks"><a class="btn btn-primary" href="' + hashFor('focus', x.id) + '">Why? Trace it</a>' + (onPath ? '<button type="button" class="btn" data-onpath="' + esc(x.id) + '">Put it on the path</button>' : '') + '<button type="button" class="btn" data-note="1">Draft a note</button></div>';
    } else h += '<div class="asks"><a class="btn btn-primary" href="' + hashFor('focus', x.to, x.id) + '">Show it in context</a><button type="button" class="btn" data-note="1">Draft a note</button></div>';

    [['assumptions', 'Assumptions'], ['challenges', 'Challenges']].forEach(function (entry) {
      var notes = x[entry[0]] || [];
      if (notes.length) h += '<section><h3>' + entry[1] + '</h3><ul class="assume">' + notes.map(function (note) {
        return '<li><p>' + esc(note.text) + '</p><p class="by">Recorded by ' + esc(note.by || 'unknown') + '</p></li>';
      }).join('') + '</ul></section>';
    });
    var oq = M.backlog[x.id] || [];
    h += '<section><h3>What is open here</h3>' + (oq.length ? '<ul class="oq-mini">' + oq.map(function (b) { return '<li><span class="oq-w">' + esc(RC.WORK[b.work] || b.work) + '</span><strong>' + esc(taskLabel(b)) + '</strong>' + (b.note ? '<span class="oq-n">' + esc(b.note) + '</span>' : '') + '</li>'; }).join('') + '</ul>' : '<p class="empty">No open question is recorded on this ' + (x.isLink ? 'connection' : 'statement') + '. That is not the same as it being settled.</p>') + '</section>';
    if (!local || (x.source_refs || []).length) h += '<section><h3>Where it comes from</h3>' + sourceList(x.source_refs) + '<p class="by">A credit says where an idea comes from, not that its author agrees with this wording.</p></section>';

    if (!x.isLink) {
      var inc = M.inc[x.id], out = M.out[x.id];
      h += '<section><h3>Connections</h3>' + (inc.length + out.length ? '<ul class="conn">' + inc.map(function (i) { return '<li><button type="button" class="linklike" data-sel="' + esc(i) + '">' + refLine(i) + '</button></li>'; }).join('') + out.map(function (i) { return '<li><button type="button" class="linklike" data-sel="' + esc(i) + '">' + refLine(i) + '</button></li>'; }).join('') + '</ul>' : '<p class="empty">No connection is recorded.</p>') + '</section>';
      var parts = M.part[x.id] || [];
      if (parts.length) h += '<section><h3>Appears in</h3><p class="by">' + parts.map(function (p) { return '<a href="' + hashFor('q', RC.tree(p.tree).slug) + '">' + esc(p.title) + '</a>'; }).join(' · ') + '</p></section>';
    }
    var hist = M.history[x.id] || [];
    if (!local || hist.length) h += '<section><h3>History</h3>' + (hist.length ? '<ul class="hist-mini">' + hist.map(function (r) { return '<li><span class="mono">' + esc(r.release) + '</span> ' + esc(r.type) + (r.note ? ': ' + esc(r.note) : '') + '</li>'; }).join('') + '</ul>' : '<p class="empty">No change to this item is recorded in the release history.</p>') + '</section>';

    var mine = st.notes.filter(function (n) { return n.ref === x.id; });
    h += '<section id="note-sec"><h3>Your draft notes</h3><p class="by">Stored only in this browser. Not submitted to anyone.</p>' + (mine.length ? '<ul class="oq oq-tight">' + mine.map(noteItem).join('') + '</ul>' : '') +
      '<form id="note-form" class="note-form"><label for="note-type">Kind of note</label><select id="note-type">' + NOTE_TYPES.map(function (t) { return '<option>' + t + '</option>'; }).join('') + '</select>' +
      '<label for="note-text">Your note on this ' + (x.isLink ? 'connection' : 'statement') + '</label><textarea id="note-text" rows="4" placeholder="What did you see, doubt or want checked?"></textarea><button type="submit" class="btn">Save draft in this browser</button><p id="note-msg" class="by" role="status"></p></form></section>';
    h += '<p class="idline"><span class="mono">' + esc(x.id) + '</span>' + (local ? '' : ' · release ' + esc(D.release_id)) + '</p>';
    return h;
  }

  // ---------- rendering and routing
  function renderRail() {
    var cur = st.view === 'q' ? st.arg : null;
    function a(hash, label, on, n) { return '<li><a href="' + hash + '"' + (on ? ' aria-current="page"' : '') + '><span>' + label + '</span>' + (n != null ? '<span class="n">' + n + '</span>' : '') + '</a></li>'; }
    var questions = M.trees.map(function (T) { return a(hashFor('q', T.slug), esc(T.q), cur === T.slug, D.trees[T.key].nodes.length); }).join('');
    rail.innerHTML = '<ul>' + a('#start', 'Start', st.view === 'start') +
      (availablePath(st.path) ? a(pathHash(st.path), 'Follow the path', st.view === 'path') : '') + '</ul>' +
      (questions ? '<p class="rail-h">Questions</p><ol>' + questions + '</ol>' : '') +
      '<p class="rail-h">Work on it</p><ul>' +
      (S.open ? a('#open', 'Open questions', st.view === 'open', S.open) : '') +
      (S.total || st.notes.length ? a('#notes', 'Your draft notes', st.view === 'notes', st.notes.length) : '') +
      (local && S.total ? a('items.html', 'Full record', false) : '') +
      (D.has_reports ? a('learning.html', 'Outcome reports', false) : '') + '</ul>';
  }
  function renderMain(keepScroll) {
    var v = { start: viewStart, path: viewPath, focus: viewFocus, q: viewQuestion, open: viewOpen, notes: viewNotes }[st.view] || viewStart;
    main.innerHTML = v();
    renderRail();
    if (!keepScroll) { window.scrollTo(0, 0); var h1 = $('h1', main); if (h1 && st.ready) h1.focus({ preventScroll: true }); }
  }
  function renderInsp(openSheet) {
    insp.innerHTML = inspector();
    document.body.classList.toggle('insp-open', !!openSheet && !!st.sel);
    [].forEach.call(document.querySelectorAll('[data-id]'), function (el) { el.classList.toggle('sel', el.getAttribute('data-id') === st.sel); });
  }
  function select(id, opts) {
    if (!RC.item(M, id)) return;
    st.sel = id; renderInsp(true);
    insp.scrollTop = 0;
    if (opts && opts.note) { var t = $('#note-text'); if (t) { t.scrollIntoView({ block: 'center' }); t.focus(); } }
    else if (window.matchMedia('(max-width: 1040px)').matches) { var c = $('.close', insp); if (c) c.focus(); }
  }
  function route(keep) {
    var parts = readHash();
    var view = parts[0];
    if (view === 'main') {
      main.focus();
      return;
    }
    st.sel = null;
    if (view === 'path') {
      st.path = RC.normalizePath(M, { problem: parts[1], change: parts[2], step: parts[3], action: parts[4] });
      store.path = st.path; save();
    } else if (view === 'focus') {
      st.arg = parts[1];
      if (M.nodes[st.arg]) {
        if (st.trail[st.trail.length - 1] !== st.arg) st.trail.push(st.arg);
        var link = M.links[parts[2]];
        st.sel = link && link.to === st.arg ? link.id : st.arg;
      }
    } else if (view === 'q') st.arg = parts[1];
    else if (['start', 'open', 'notes'].indexOf(view) < 0) view = 'start';
    st.view = view;
    document.body.classList.remove('insp-open');
    renderMain(!!keep); renderInsp(view === 'focus' && st.sel && M.links[st.sel]);
  }

  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-go],[data-sel],[data-pick],[data-toggle],[data-ow],[data-ot],[data-close],[data-onpath],[data-note],[data-copy],[data-del]');
    if (!t) return;
    if (t.hasAttribute('data-go')) { location.hash = t.getAttribute('data-go'); return; }
    if (t.hasAttribute('data-pick')) {
      var p = Object.assign({}, st.path); p[t.getAttribute('data-pick')] = t.getAttribute('data-id');
      st.path = RC.normalizePath(M, p); st.expand['swap-' + t.getAttribute('data-pick')] = false;
      var hsh = pathHash(st.path);
      if (location.hash === hsh) renderMain(true); else { st.keep = true; location.hash = hsh; }
      return;
    }
    if (t.hasAttribute('data-toggle')) { var k = t.getAttribute('data-toggle'); st.expand[k] = !st.expand[k]; renderMain(true); var again = main.querySelector('[data-toggle="' + CSS.escape(k) + '"]'); if (again) again.focus(); return; }
    if (t.hasAttribute('data-ow')) { st.openWork = t.getAttribute('data-ow'); renderMain(true); return; }
    if (t.hasAttribute('data-ot')) { st.openTree = t.getAttribute('data-ot'); renderMain(true); return; }
    if (t.hasAttribute('data-close')) { document.body.classList.remove('insp-open'); var back = st.sel && main.querySelector('[data-id="' + CSS.escape(st.sel) + '"]'); if (back) back.focus(); return; }
    if (t.hasAttribute('data-onpath')) { var np = RC.pathThrough(M, st.path, t.getAttribute('data-onpath')); if (np) location.hash = pathHash(np); return; }
    if (t.hasAttribute('data-copy')) {
      var n = st.notes.filter(function (x) { return x.id === t.getAttribute('data-copy'); })[0]; if (!n) return;
      var txt = noteText(n), done = function (ok) { t.textContent = ok ? 'Copied' : 'Copy failed. Select the text instead.'; };
      try { navigator.clipboard.writeText(txt).then(function () { done(true); }, function () { done(false); }); } catch (err) { done(false); }
      return;
    }
    if (t.hasAttribute('data-del')) {
      st.notes = st.notes.filter(function (x) { return x.id !== t.getAttribute('data-del'); });
      store.notes = st.notes; save(); renderMain(true); renderInsp(document.body.classList.contains('insp-open'));
      return;
    }
    if (t.hasAttribute('data-sel')) { select(t.getAttribute('data-sel'), { note: t.hasAttribute('data-note') }); return; }
    if (t.hasAttribute('data-note')) { var ta = $('#note-text'); if (ta) { ta.scrollIntoView({ block: 'center' }); ta.focus(); } }
  });
  document.addEventListener('toggle', function (e) { var k = e.target.getAttribute && e.target.getAttribute('data-keep'); if (k) st.expand[k] = e.target.open; }, true);
  document.addEventListener('submit', function (e) {
    if (e.target.id !== 'note-form') return;
    e.preventDefault();
    var text = $('#note-text').value.trim(), msg = $('#note-msg');
    if (!text) { msg.textContent = 'Write the note first.'; return; }
    st.notes.unshift({ id: 'n' + Date.now().toString(36), ref: st.sel, type: $('#note-type').value, text: text, at: new Date().toISOString().slice(0, 10) });
    store.notes = st.notes; var saved = save(); renderInsp(document.body.classList.contains('insp-open')); renderRail();
    if (st.view === 'notes') renderMain(true);
    var m = $('#note-msg'); if (m) m.textContent = saved ? 'Saved as a local draft.' : 'This browser could not save the draft. Copy it before closing the page.';
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && document.body.classList.contains('insp-open')) { var c = $('.close', insp); if (c) c.click(); } });

  // search
  var q = $('#q'), res = $('#q-res');
  function showResults() {
    var ids = RC.search(M, q.value, 10);
    if (q.value.trim().length < 2) { res.hidden = true; res.innerHTML = ''; return; }
    res.hidden = false;
    res.innerHTML = ids.length ? ids.map(function (id) { var n = M.nodes[id]; return '<li><a href="' + hashFor('focus', id) + '"><span class="st-kind"><span class="gl gl-' + RC.role(n) + '" aria-hidden="true">' + GLYPH[RC.role(n)] + '</span>' + esc(RC.kindLabel(n)) + ' · ' + esc(RC.tree(n.tree).short) + '</span>' + esc(n.label) + '</a></li>'; }).join('') : '<li class="empty">No statement matches. Try a word from the claim, a person’s name or a kind such as “obstacle”.</li>';
  }
  q.addEventListener('input', showResults);
  q.addEventListener('focus', showResults);
  document.addEventListener('click', function (e) { if (!e.target.closest('.search')) res.hidden = true; else if (e.target.closest('#q-res a')) { res.hidden = true; q.value = ''; } });

  // header standing line
  if (!local) $('#standing').innerHTML = (S.proposed === S.total ? '<strong>Everything here is proposed.</strong> ' : '') + S.statements + ' statements and ' + S.connections + ' connections, written by an AI from the sources. ' + (S.acceptedByAnyone ? S.acceptedByAnyone + ' accepted by a named person.' : 'Nobody has accepted any of it.') + ' Read-only release ' + esc(D.release_id) + '.';

  window.addEventListener('hashchange', function () { var keep = st.keep; st.keep = false; route(keep); });
  route(); st.ready = true;
  window.RCApp = { M: M, st: st };
})();
