/* The clinic team alongside the story. Each beat reconstructs its exact
   knowledge state; no timed transcript and no duplicated inline scenes. */
(function () {
  'use strict';

  var D = {};
  if (!document.querySelector('.practice-scene')) return;

  var NS = 'http://www.w3.org/2000/svg';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* The Ashfield clinic, shared across the trilogy. A page can extend it. */
  var CAST = {
    sam:     { name: 'Sam Whitfield',    short: 'Sam',        role: 'Practice manager' },
    maria:   { name: 'Maria Costa',      short: 'Maria',      role: 'Front desk' },
    adeyemi: { name: 'Dr Funmi Adeyemi', short: 'Dr Adeyemi', role: 'Doctor' },
    tomasz:  { name: 'Tomasz Nowak',     short: 'Tomasz',     role: 'Triage nurse' },
    leila:   { name: 'Leila Haddad',     short: 'Leila',      role: 'Pharmacist' },
    skill:   { name: 'Reason Commons',   short: 'Reason Commons', role: 'The ltp skill' }
  };
  Object.keys(D.cast || {}).forEach(function (k) { CAST[k] = D.cast[k]; });

  /* How the team chat is invoked: `/reason` answers by default, records in
     capture mode, and `/reason-accept` endorses a displayed review. */
  var CMD = { capture: '/reason · capture', ask: '/reason · ask', review: '/reason · review',
              accept: '/reason-accept' };
  var MIC = '<svg viewBox="0 0 12 12" aria-hidden="true"><rect x="4" y="1" width="4" height="6.4" rx="2" ' +
    'fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M2.4 5.6 C2.4 9.6 9.6 9.6 9.6 5.6 M6 8.6 L6 11" ' +
    'fill="none" stroke="currentColor" stroke-width="1.2"/></svg>';

  /* ---------- avatars ----------
     Drawn in the series' line style, one marker of role each, and run
     through a gentler version of the pages' rough filter. */
  var SPRITE =
    '<svg xmlns="' + NS + '" width="0" height="0" style="position:absolute" aria-hidden="true"><defs>' +
    '<filter id="sm-rough" x="-10%" y="-10%" width="120%" height="120%">' +
      '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="5" result="n"/>' +
      '<feDisplacementMap in="SourceGraphic" in2="n" scale="1.3" xChannelSelector="R" yChannelSelector="G"/></filter>' +
    '<clipPath id="sm-clip"><circle cx="24" cy="24" r="22.4"/></clipPath>' +
    av('sam',
      '<path d="M16.4 19 C15.8 10.6 32.2 10.6 31.6 19 C29.4 15.2 18.6 15.2 16.4 19Z" fill="var(--ink-soft)"/>',
      '<circle cx="21.2" cy="20.2" r="2.3" fill="none" stroke="var(--ink)" stroke-width="1.1"/>' +
      '<circle cx="26.8" cy="20.2" r="2.3" fill="none" stroke="var(--ink)" stroke-width="1.1"/>' +
      '<path d="M23.5 20.2 L24.5 20.2" stroke="var(--ink)" stroke-width="1.1"/>',
      '<path d="M19.6 33.4 L24 40 L28.4 33.4" fill="none" stroke="var(--skill)" stroke-width="1.3"/>' +
      '<rect x="22" y="39.6" width="4" height="5.2" rx=".6" fill="var(--paper)" stroke="var(--ink)" stroke-width="1"/>') +
    av('maria',
      '<circle cx="31.4" cy="12" r="3.7" fill="var(--ink-soft)"/>' +
      '<path d="M16.4 19.6 C15.6 11 32.4 11 31.6 19.6 C29.6 15.6 18.4 15.6 16.4 19.6Z" fill="var(--ink-soft)"/>',
      '',
      '<path d="M15.6 21.4 C15.4 9.4 32.6 9.4 32.4 21.4" fill="none" stroke="var(--ink)" stroke-width="1.6"/>' +
      '<rect x="13.9" y="18.6" width="3.2" height="5.6" rx="1.3" fill="var(--ink)"/>' +
      '<path d="M15.6 24 Q16.4 27.4 21 26.6" fill="none" stroke="var(--ink)" stroke-width="1.3"/>' +
      '<circle cx="21.4" cy="26.5" r=".9" fill="var(--ink)"/>') +
    av('adeyemi',
      '<path d="M16.3 19.4 C15 12.2 18.8 10.6 20.8 11.5 C22.4 9.8 25.6 9.8 27.2 11.5 C29.2 10.6 33 12.2 31.7 19.4 C29.2 15.8 18.8 15.8 16.3 19.4Z" fill="var(--ink)"/>',
      '',
      '<path d="M18.6 32.6 C17.4 38.6 20.8 41.4 24 41.4 C27.2 41.4 30.6 38.6 29.4 32.6" fill="none" stroke="var(--ink)" stroke-width="1.4"/>' +
      '<circle cx="24" cy="42.6" r="1.9" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.2"/>') +
    av('tomasz',
      '<path d="M16.6 18.4 C16.4 12 31.6 12 31.4 18.4 C29.4 15.8 18.6 15.8 16.6 18.4Z" fill="var(--ink-faint)"/>',
      '<path d="M16.8 21.6 C17.2 29.4 30.8 29.4 31.2 21.6 C29.4 25.2 18.6 25.2 16.8 21.6Z" fill="var(--ink-soft)"/>',
      '<path d="M20 33.4 L24 38 L28 33.4" fill="none" stroke="var(--ink)" stroke-width="1.3"/>' +
      '<path d="M31 35.4 L31 37.6" stroke="var(--ink)" stroke-width="1"/>' +
      '<circle cx="31" cy="39.4" r="1.9" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.1"/>', true) +
    av('leila',
      '<path d="M14.6 23.4 C13.6 9 34.4 9 33.4 23.4 C33.8 29.4 30 33 24 33.4 C18 33 14.2 29.4 14.6 23.4Z" fill="var(--skill-soft)" stroke="var(--ink)" stroke-width="1.5"/>',
      '', '<rect x="28.6" y="37" width="5" height="7" rx="1" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.1"/>' +
      '<path d="M28.2 37 L34 37" stroke="var(--ink)" stroke-width="1.6"/>', false, 6.6) +
    '<symbol id="sm-av-skill" viewBox="0 0 48 48"><g filter="url(#sm-rough)">' +
      '<rect x="4.5" y="4.5" width="39" height="39" rx="10" fill="var(--skill-soft)" stroke="var(--skill)" stroke-width="1.6"/>' +
      '<path d="M24 18.4 L24 23.6 M16 29 L16 23.6 L32 23.6 L32 29" fill="none" stroke="var(--skill)" stroke-width="1.5"/>' +
      '<rect x="18.6" y="11" width="10.8" height="7.4" rx="1.2" fill="var(--paper)" stroke="var(--skill)" stroke-width="1.5"/>' +
      '<rect x="10.6" y="29" width="10.8" height="7.4" rx="1.2" fill="var(--paper)" stroke="var(--skill)" stroke-width="1.5"/>' +
      '<rect x="26.6" y="29" width="10.8" height="7.4" rx="1.2" fill="var(--paper)" stroke="var(--skill)" stroke-width="1.5"/>' +
    '</g></symbol>' +
    '</defs></svg>';

  /* One person: a circle, shoulders, a head, and whatever marks them out.
     `back` sits behind the head (hair, a bun, a scarf), `face` on it,
     `front` on the chest or over the head. */
  function av(id, back, face, front, noSmile, headR) {
    var r = headR || 7.6;
    return '<symbol id="sm-av-' + id + '" viewBox="0 0 48 48"><g filter="url(#sm-rough)">' +
      '<circle cx="24" cy="24" r="22.4" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.4"/>' +
      '<g clip-path="url(#sm-clip)">' +
        '<path d="M8.6 47 C8.6 34.2 39.4 34.2 39.4 47Z" fill="var(--paper-2)" stroke="var(--ink)" stroke-width="1.5"/>' +
        '<path d="M21.4 27.4 L21.4 31 M26.6 27.4 L26.6 31" stroke="var(--ink)" stroke-width="1.4"/>' +
        back +
        '<circle cx="24" cy="20.4" r="' + r + '" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.5"/>' +
        '<circle cx="21.3" cy="20.2" r=".95" fill="var(--ink)"/><circle cx="26.7" cy="20.2" r=".95" fill="var(--ink)"/>' +
        (noSmile ? '' : '<path d="M21.9 23.6 Q24 25.1 26.1 23.6" fill="none" stroke="var(--ink)" stroke-width="1.1"/>') +
        face + front +
      '</g></g></symbol>';
  }

  function avatar(id, cls) {
    return '<svg class="sm-av' + (cls ? ' ' + cls : '') + '" viewBox="0 0 48 48" aria-hidden="true">' +
      '<use href="#sm-av-' + id + '"/></svg>';
  }

  /* Source HTML is the complete, accessible transcript. The device is an
     optional visual mirror, never the only place a contribution exists. */
  var scenes = [].slice.call(document.querySelectorAll('.practice-scene'));
  document.body.insertAdjacentHTML('afterbegin', SPRITE);
  [].forEach.call(document.querySelectorAll('.scene-message'), function (m) {
    m.querySelector('.scene-avatar').innerHTML = avatar(m.dataset.who);
  });
  var rail = document.createElement('aside');
  rail.className = 'sm-rail';
  rail.setAttribute('aria-label', 'Illustrated conversation companion');
  rail.innerHTML = '<div class="sm-tools"><span>Alongside the story</span><button type="button">Hide companion</button></div><div class="sm-visual" aria-hidden="true" inert></div>';
  document.body.appendChild(rail);
  var visual = rail.querySelector('.sm-visual');
  var show = document.createElement('button');
  show.type = 'button'; show.className = 'sm-show'; show.textContent = 'Show companion';
  document.body.appendChild(show);
  var media = window.matchMedia('(min-width:1200px) and (min-height:760px)');
  var hide = rail.querySelector('button');
  function collapse(on) {
    var anchor=readingAnchor;
    var before=anchor?anchor.getBoundingClientRect().top:null;
    document.body.classList.toggle('sm-collapsed', on);
    if(anchor&&before!==null) window.scrollBy({top:anchor.getBoundingClientRect().top-before,behavior:'auto'});
    try { localStorage.setItem('sm-collapsed', on ? '1' : '0'); } catch (e) {}
    schedule();
  }
  hide.addEventListener('click', function () { collapse(true); show.focus(); });
  show.addEventListener('click', function () { collapse(false); hide.focus(); });
  try { if (localStorage.getItem('sm-collapsed') === '1') document.body.classList.add('sm-collapsed'); } catch (e) {}
  document.body.classList.add('sm-ready');
  function roster(who) {
    return '<div class="sm-roster">' + ['sam','maria','tomasz','adeyemi','leila','skill'].map(function (id) {
      return '<span class="sm-person' + (id === who || id === 'skill' ? ' active' : '') + '">' + avatar(id) + CAST[id].short + '</span>';
    }).join('') + '</div>';
  }
  var current = -2;
  function render(index) {
    if (index === current) return;
    current = index;
    rail.dataset.scene = index < 0 ? 'introduction' : scenes[index].id;
    if (index < 0) {
      visual.innerHTML = roster('skill') + '<div class="sm-cover"><p class="scene-kicker">Illustrated story · actual record linked below</p><h2>The people bring a question.<br>The skill keeps the reasoning.</h2><p>Reason Commons is an installed package for an AI assistant. It keeps claims, authors, objections and the next check in a working file.</p><p>The clinic and these conversations are invented. Follow the story first; each complete exchange appears after its premises.</p><p class="sm-footnote">Sam manages · Maria handles reception · Tomasz triages · Dr Adeyemi consults · Leila dispenses.</p></div>';
    } else {
      var s = scenes[index];
      visual.innerHTML = roster(s.dataset.who) + '<p class="scene-kicker">' + s.querySelector('.scene-kicker').textContent + '</p><h2>' + s.querySelector('h2').textContent + '</h2><div class="sm-device" data-device="' + s.dataset.device + '"><p class="sm-surface">' + (s.dataset.device === 'phone' ? 'Team-chat prototype · explicit /reason capture' : 'AI assistant · ltp skill installed') + '</p><div class="scene-dialogue">' + s.querySelector('.scene-dialogue').innerHTML + '</div></div><p class="scene-consequence">' + s.querySelector('.scene-consequence').textContent + '</p><p class="sm-footnote">Latest exchange · the saved reasoning is in the story.</p>';
    }
    /* Larger fonts or unusual heights fall back to the complete inline source. */
    if (media.matches && rail.offsetHeight && rail.scrollHeight > rail.clientHeight + 2) document.body.classList.add('sm-inline');
  }

  /* Reconcile drawings from scroll geometry, preserving the existing art
     hooks while avoiding out-of-order observer callbacks on large jumps. */
  var steps = [].slice.call(document.querySelectorAll('.step'));
  var layers = [].slice.call(document.querySelectorAll('.layer'));
  var triggers = [].slice.call(document.querySelectorAll('.trigger'));
  var originalStep = window.onStep;
  var storyId = '';
  function syncStory(id) {
    if (!id || id === storyId) return;
    storyId = id;
    steps.forEach(function (e) { e.classList.toggle('on', e.dataset.step === id); });
    layers.forEach(function (e) { e.classList.toggle('on', e.dataset.layer.split(/\s+/).indexOf(id) !== -1); });
    [].forEach.call(document.querySelectorAll('.steps.stack'), function (g) {
      var seen = false;
      for (var i = g.children.length - 1; i >= 0; i--) {
        var e = g.children[i];
        if (e.dataset.step === id) seen = true;
        e.classList.toggle('on', seen); e.classList.toggle('cur', e.dataset.step === id);
      }
    });
    if (typeof originalStep === 'function') originalStep(id);
    if (typeof window.fitPortrait === 'function') window.fitPortrait();
  }
  var ticking = false;
  var readingAnchor = null;
  var lastWidth = innerWidth;
  var markers = [].slice.call(document.querySelectorAll('.trigger,[data-sm-beat],.practice-scene,.practice-intro,.practice-next'));
  function update() {
    ticking = false;
    var line = innerHeight * .52;
    var active = null;
    triggers.forEach(function (t) {
      var r = t.closest('.scroll-item').getBoundingClientRect();
      if (r.top <= line && r.bottom > line && t.getBoundingClientRect().top <= line) active = t;
    });
    if (active) syncStory(active.dataset.t);
    var picked = -1;
    scenes.forEach(function (s,i) { if (s.getBoundingClientRect().top <= line) picked = i; });
    render(picked);
    markers.forEach(function (m) { if(m.getBoundingClientRect().top <= line) readingAnchor=m; });
  }
  function schedule() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  function observedStep() { storyId = ''; schedule(); }
  window.onStep = observedStep;
  var portrait = window.matchMedia('(max-width:640px)').matches;
  window.addEventListener('scroll', schedule, {passive:true});
  window.addEventListener('resize', function () {
    var next = window.matchMedia('(max-width:640px)').matches;
    if (next !== portrait && typeof window.rebuildExplainerArtwork === 'function') {
      window.rebuildExplainerArtwork();
      layers = [].slice.call(document.querySelectorAll('.layer'));
      originalStep = window.onStep;
      window.onStep = observedStep;
      portrait = next;
    }
    document.body.classList.remove('sm-inline');
    if(lastWidth !== innerWidth && readingAnchor){
      var top=readingAnchor.getBoundingClientRect().top+scrollY-innerHeight*.52;
      window.scrollTo({top:Math.max(0,top),behavior:'auto'});
    }
    lastWidth=innerWidth;
    current = -2; storyId = ''; schedule();
  });
  window.addEventListener('load', schedule);
  if (document.fonts) document.fonts.ready.then(function () {current=-2;storyId='';schedule();});
  update();
})();
