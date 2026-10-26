/* Progressive enhancement only: every page is complete and readable without this file. */
(() => {
  'use strict';
  const store = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* Private windows may refuse storage. */ } }
  };

  // Diagram or outline. Narrow screens start with the outline unless the reader chose otherwise.
  for (const toggle of document.querySelectorAll('.view-toggle')) {
    const views = toggle.nextElementSibling;
    const show = view => {
      views.dataset.show = view;
      for (const button of toggle.querySelectorAll('button')) button.setAttribute('aria-pressed', String(button.dataset.view === view));
    };
    show(store.get('rc-view') || (matchMedia('(max-width: 640px)').matches ? 'outline' : 'diagram'));
    toggle.hidden = false;
    toggle.addEventListener('click', event => {
      const button = event.target.closest('button[data-view]');
      if (!button) return;
      show(button.dataset.view);
      store.set('rc-view', button.dataset.view);
    });
  }

  // Light up a statement or connection together with everything it touches.
  for (const svg of document.querySelectorAll('svg.rc-diagram')) {
    const edges = [...svg.querySelectorAll('a.e')];
    const clear = () => {
      svg.classList.remove('is-lit');
      for (const lit of svg.querySelectorAll('.lit')) lit.classList.remove('lit');
    };
    const light = target => {
      clear();
      const id = target.dataset.id;
      const touched = new Set([id]);
      for (const edge of edges) {
        const ends = edge.dataset.ends.split(' ');
        if (edge.dataset.id === id || ends.includes(id)) {
          edge.classList.add('lit');
          ends.forEach(end => touched.add(end));
          touched.add(edge.dataset.id);
        }
      }
      for (const element of svg.querySelectorAll('a[data-id]')) if (touched.has(element.dataset.id)) element.classList.add('lit');
      svg.classList.add('is-lit');
    };
    svg.addEventListener('mouseover', event => { const target = event.target.closest('a[data-id]'); if (target) light(target); });
    svg.addEventListener('focusin', event => { const target = event.target.closest('a[data-id]'); if (target) light(target); });
    svg.addEventListener('mouseleave', clear);
    svg.addEventListener('focusout', event => { if (!svg.contains(event.relatedTarget)) clear(); });
  }

  // Step through an indented tree: start from its root and open one level at a time.
  // Rows are drawn in reading order, so a folded branch only closes the gap it leaves.
  const calm = matchMedia('(prefers-reduced-motion: reduce)');
  for (const svg of document.querySelectorAll('svg.rc-diagram[data-hierarchy]')) {
    const bar = svg.closest('figure')?.querySelector('.step-bar');
    if (!bar) continue;
    const { pad, rowGap, rail, stem } = Object.fromEntries(['pad', 'rowGap', 'rail', 'stem'].map(key => [key, Number(svg.dataset[key])]));
    const width = svg.viewBox.baseVal.width;
    const rows = [...svg.querySelectorAll('a.n[data-depth]')];
    const byId = new Map(rows.map(row => [row.dataset.id, row]));
    const ancestors = row => {
      const result = [];
      for (let id = row.dataset.parent; id; id = byId.get(id).dataset.parent) result.push(id);
      return result;
    };
    const edges = [...svg.querySelectorAll('a.e')].map(edge => {
      const [child, parent] = edge.dataset.ends.split(' ');
      return { edge, child: byId.get(child), parent: byId.get(parent) };
    });
    const [toggle, count, all, reset] = ['.step-toggle', '.step-count', '.step-all', '.step-reset'].map(s => bar.querySelector(s));
    const open = new Set();
    let on = false;

    const layout = (entering = new Set()) => {
      const top = new Map();
      let y = pad;
      for (const row of rows) {
        const shown = !on || ancestors(row).every(id => open.has(id));
        row.classList.toggle('is-folded', !shown);
        if (!shown) continue;
        top.set(row, y);
        row.style.transform = `translate(0px,${y - Number(row.dataset.y)}px)`;
        row.classList.toggle('is-open', open.has(row.dataset.id));
        if (on && row.dataset.kids) {
          row.setAttribute('role', 'button');
          row.setAttribute('aria-expanded', String(open.has(row.dataset.id)));
        } else {
          row.removeAttribute('role');
          row.removeAttribute('aria-expanded');
        }
        y += Number(row.dataset.h) + rowGap;
      }
      for (const { edge, child, parent } of edges) {
        edge.classList.toggle('is-folded', !top.has(child));
        if (!top.has(child)) continue;
        const cx = Number(child.dataset.x), cy = top.get(child) + stem;
        const rx = Number(parent.dataset.x) + rail, end = top.get(parent) + Number(parent.dataset.h);
        const r = Math.min(7, (cx - rx) / 2, (cy - end) / 2);
        const d = `M${cx},${cy}L${rx + r},${cy}Q${rx},${cy} ${rx},${cy - r}L${rx},${end}`;
        for (const path of edge.querySelectorAll('.e-hit, .e-line')) path.setAttribute('d', d);
        edge.querySelector('.e-head').style.transform = `translate(0px,${top.get(parent) - Number(parent.dataset.y)}px)`;
        if (entering.has(child)) entering.add(edge);
      }
      if (!calm.matches) {
        for (const element of entering) {
          element.classList.add('is-entering');
          element.addEventListener('animationend', () => element.classList.remove('is-entering'), { once: true });
        }
      }
      const height = Math.round(y - rowGap + pad);
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.setAttribute('height', height);
      count.textContent = on ? `${top.size} of ${rows.length} shown` : '';
      all.hidden = !on || top.size === rows.length;
      reset.hidden = !on || top.size === 1;
    };

    // Keep the opened box and what it revealed on screen, or the box itself when they can't all fit.
    const reveal = (row, kids) => {
      requestAnimationFrame(() => {
        const first = row.getBoundingClientRect(), last = kids[kids.length - 1].getBoundingClientRect();
        const room = innerHeight - 24;
        let by = 0;
        if (last.bottom - first.top > room - 24) by = first.top - 24;
        else if (last.bottom > room) by = last.bottom - room;
        else if (first.top < 24) by = first.top - 24;
        if (by) scrollBy({ top: by, behavior: calm.matches ? 'auto' : 'smooth' });
      });
    };

    const flip = row => {
      const id = row.dataset.id;
      svg.classList.remove('is-lit');  // Focus lighting would dim the branches the reader is stepping through.
      if (open.has(id)) {
        open.delete(id);
        for (const other of rows) if (ancestors(other).includes(id)) open.delete(other.dataset.id);
        layout();
        return;
      }
      open.add(id);
      const kids = rows.filter(other => other.dataset.parent === id);
      layout(new Set(kids));
      reveal(row, kids);
    };

    const set = (value, remember) => {
      on = value;
      open.clear();
      toggle.setAttribute('aria-pressed', String(on));
      svg.classList.toggle('is-stepping', on);
      bar.classList.toggle('is-on', on);
      layout();
      if (remember) store.set('rc-steps', on ? 'on' : 'off');
    };

    svg.addEventListener('click', event => {
      const row = on && event.target.closest('a.n[data-kids]');
      if (!row) return;
      event.preventDefault();
      flip(row);
    });
    svg.addEventListener('keydown', event => {
      const row = on && event.key === ' ' && event.target.closest('a.n[data-kids]');
      if (!row) return;
      event.preventDefault();
      flip(row);
    });
    toggle.addEventListener('click', () => set(!on, true));
    all.addEventListener('click', () => {
      for (const row of rows) if (row.dataset.kids) open.add(row.dataset.id);
      layout();
    });
    reset.addEventListener('click', () => {
      open.clear();
      layout();
      rows[0].focus();
    });
    bar.hidden = false;
    const saved = store.get('rc-steps');
    set(saved ? saved === 'on' : rows.length > 10, false);  // Large trees start stepped unless the reader chose otherwise.
  }

  // Plans: lines between stages, tracing what a step needs and makes possible, a read-only panel,
  // the objective filter and stage jumps. Without this, cards link to their records and list what they need.
  const planCards = document.querySelectorAll('.pv-card');
  if (planCards.length) {
    const map = document.querySelector('.pv-map');
    const drawer = document.createElement('aside');
    drawer.className = 'pv-drawer';
    drawer.setAttribute('aria-label', 'Details');
    drawer.tabIndex = -1;
    document.body.append(drawer);
    const shut = document.createElement('button');
    shut.type = 'button';
    shut.className = 'pv-x';
    shut.setAttribute('aria-label', 'Close details');
    shut.textContent = '×';
    let opener = null;
    let pinned = null;
    let trace = () => {};

    const close = () => {
      if (!drawer.classList.contains('is-open')) return;
      drawer.classList.remove('is-open');
      document.body.classList.remove('pv-open');
      for (const card of document.querySelectorAll('.pv-focus')) card.classList.remove('pv-focus');
      if (opener && document.contains(opener)) opener.focus({ preventScroll: true });
      opener = null;
      pinned = null;
      trace(null);
    };
    const open = (id, from) => {
      const template = document.getElementById(`pv-d-${id}`);
      if (!template) return false;
      drawer.replaceChildren(shut, template.content.cloneNode(true));
      drawer.classList.add('is-open');
      document.body.classList.add('pv-open');
      drawer.scrollTop = 0;
      opener = from || opener;
      drawer.querySelector('.pv-d-title')?.focus({ preventScroll: true });
      return true;
    };
    const select = (id, card) => {
      for (const other of document.querySelectorAll('.pv-focus')) other.classList.remove('pv-focus');
      if (map && map.contains(card)) {
        if (pinned === id) { close(); return; }
        pinned = id;
        trace(id);
      }
      card.classList.add('pv-focus');
      open(id, card.querySelector('.pv-hit'));
      // Keep the selected step clear of the panel on a wide screen.
      requestAnimationFrame(() => {
        const scroller = card.closest('.pv-scroll');
        if (!scroller || getComputedStyle(drawer).position !== 'fixed' || innerWidth <= 760) return;
        const over = card.getBoundingClientRect().right - (innerWidth - drawer.offsetWidth - 24);
        if (over > 0) scroller.scrollBy({ left: over, behavior: calm.matches ? 'auto' : 'smooth' });
      });
    };
    const show = card => card.scrollIntoView({ behavior: calm.matches ? 'auto' : 'smooth', block: 'center', inline: 'center' });

    document.addEventListener('click', event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (event.target.closest('.pv-x')) { close(); return; }
      const hit = event.target.closest('.pv-hit');
      const goto = event.target.closest('[data-goto]');
      if (hit && document.getElementById(`pv-d-${hit.dataset.id}`)) {
        event.preventDefault();
        select(hit.dataset.id, hit.closest('.pv-card'));
      } else if (goto) {
        const card = [...document.querySelectorAll(`.pv-card[data-node="${CSS.escape(goto.dataset.goto)}"]`)].find(c => !c.classList.contains('pv-out'));
        if (!card) return;  // Not on this page: follow the link to the full record.
        event.preventDefault();
        show(card);
        if (pinned !== goto.dataset.goto) select(goto.dataset.goto, card);
      } else if (map && pinned && event.target.closest('.pv-scroll') && !event.target.closest('.pv-card')) {
        close();
      }
    });
    addEventListener('keydown', event => { if (event.key === 'Escape') close(); });

    if (map) {
      const data = JSON.parse(document.querySelector('.pv-data').textContent);
      const pre = new Map(), post = new Map();
      const add = (index, key, value) => { if (!index.has(key)) index.set(key, []); index.get(key).push(value); };
      for (const link of data.links) for (const from of link.from) { add(pre, link.to, from); add(post, from, link.to); }
      const reach = (id, index) => {
        const seen = new Set(), todo = [id];
        while (todo.length) for (const next of index.get(todo.pop()) || []) if (!seen.has(next)) { seen.add(next); todo.push(next); }
        return seen;
      };
      const path = (nodes, edges) => ({ nodes: new Set(nodes), edges: new Set(edges.map(pair => pair.join('>'))) });
      const everything = path(data.critical, data.edges);
      let critical = everything;
      const svg = map.querySelector('.pv-lines');
      const anchor = 34;  // Lines meet a card at its first line of text, so the critical path runs straight.
      const cardOf = id => map.querySelector(`.pv-card[data-node="${CSS.escape(id)}"]:not(.pv-out)`);
      const attr = value => String(value).replace(/[&"<>]/g, ch => ({ '&': '&amp;', '"': '&quot;', '<': '&lt;', '>': '&gt;' }[ch]));

      trace = id => {
        map.classList.toggle('is-traced', Boolean(id));
        for (const element of map.querySelectorAll('.pv-on')) element.classList.remove('pv-on', 'pv-up');
        if (!id) return;
        const up = reach(id, pre), down = reach(id, post);
        const above = x => up.has(x) || x === id, below = x => down.has(x) || x === id;
        for (const card of map.querySelectorAll('.pv-card')) if (card.dataset.node === id || up.has(card.dataset.node) || down.has(card.dataset.node)) card.classList.add('pv-on');
        const lit = new Map();
        for (const line of svg.querySelectorAll('[data-from]')) {
          const { from, to } = line.dataset;
          const isUp = up.has(from) && above(to), isDown = below(from) && down.has(to);
          if (!isUp && !isDown) continue;
          line.classList.add('pv-on');
          if (isUp) line.classList.add('pv-up');
          if (!lit.has(to) || isUp) lit.set(to, isUp);
        }
        for (const part of svg.querySelectorAll('[data-to]:not([data-from])')) {
          if (!lit.has(part.dataset.to)) continue;
          part.classList.add('pv-on');
          if (lit.get(part.dataset.to)) part.classList.add('pv-up');
        }
      };

      const draw = () => {
        if (getComputedStyle(svg).display === 'none') { map.classList.remove('has-lines'); return; }
        map.classList.add('has-lines');  // Lines replace each card's "Needs" list; measure after it is hidden.
        const box = map.getBoundingClientRect();
        svg.setAttribute('width', map.offsetWidth);
        svg.setAttribute('height', map.offsetHeight);
        const at = (id, side) => {
          const card = cardOf(id);
          if (!card) return null;
          const r = card.getBoundingClientRect();
          return { x: (side === 'out' ? r.right : r.left) - box.left, y: r.top - box.top + anchor };
        };
        const curve = (a, b) => {
          const k = Math.max(22, Math.min(110, (b.x - a.x) * 0.45));
          return `M${a.x},${a.y} C${a.x + k},${a.y} ${b.x - k},${b.y} ${b.x},${b.y}`;
        };
        const lines = [];
        for (const link of data.links) {
          const target = at(link.to, 'in');
          const sources = link.from.map(from => [from, at(from, 'out')]).filter(([, point]) => point);
          if (!target || !sources.length) continue;
          const meet = link.from.length > 1 ? { x: target.x - 16, y: target.y } : target;  // Joint conditions meet before one arrow.
          let onPath = false;
          for (const [from, point] of sources) {
            const crit = critical.edges.has(`${from}>${link.to}`);
            onPath = onPath || crit;
            lines.push(`<path class="pv-e pv-${link.status}${crit ? ' pv-crit' : ''}" data-from="${attr(from)}" data-to="${attr(link.to)}" d="${curve(point, meet)}"/>`);
          }
          const style = `pv-e pv-${link.status}${onPath ? ' pv-crit' : ''}`;
          if (meet !== target) {
            lines.push(`<path class="${style}" data-to="${attr(link.to)}" d="M${meet.x},${meet.y}L${target.x},${target.y}"/>`,
                       `<circle class="pv-j${onPath ? ' pv-crit' : ''}" data-to="${attr(link.to)}" cx="${meet.x}" cy="${meet.y}" r="3.2"/>`);
          }
          lines.push(`<path class="${style} pv-tip" data-to="${attr(link.to)}" d="M${target.x - 7},${target.y - 4.5}L${target.x - 1},${target.y}L${target.x - 7},${target.y + 4.5}"/>`);
        }
        svg.innerHTML = lines.join('');
        trace(pinned);
      };
      let frame = 0;
      const redraw = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(draw); };
      new ResizeObserver(redraw).observe(map);
      document.fonts?.ready.then(redraw);
      redraw();

      // Hovering or focusing a step previews its trace until one is selected.
      map.addEventListener('mouseover', event => { const card = event.target.closest('.pv-card'); if (card && !pinned) trace(card.dataset.node); });
      map.addEventListener('mouseleave', () => trace(pinned));
      map.addEventListener('focusin', event => { const card = event.target.closest('.pv-card'); if (card && !pinned) trace(card.dataset.node); });
      map.addEventListener('focusout', event => { if (!map.contains(event.relatedTarget)) trace(pinned); });

      const hint = document.querySelector('.pv-hint');
      if (hint) hint.hidden = false;
      const toward = document.querySelector('.pv-toward');
      if (toward) {
        toward.hidden = false;
        toward.querySelector('select').addEventListener('change', event => {
          const view = data.toward[event.target.value];
          close();
          for (const card of map.querySelectorAll('.pv-card')) {
            const id = card.dataset.node;
            const kept = !view || id in view.order;
            card.classList.toggle('pv-out', !kept);
            card.style.order = view && kept ? view.order[id] : '';
          }
          for (const column of map.querySelectorAll('.pv-col')) column.hidden = !column.querySelector('.pv-card:not(.pv-out)');
          critical = view ? path(view.critical, view.edges) : everything;
          for (const card of map.querySelectorAll('.pv-card')) card.classList.toggle('pv-crit', critical.nodes.has(card.dataset.node));
          redraw();
        });
      }
      const jump = document.querySelector('.pv-jump');
      if (jump) {
        jump.hidden = false;
        const scroller = map.closest('.pv-scroll');
        jump.addEventListener('click', event => {
          const button = event.target.closest('button[data-jump]');
          const column = button && map.querySelector(`.pv-col[data-stage="${button.dataset.jump}"]`);
          if (!column || column.hidden) return;
          const left = scroller.scrollLeft + column.getBoundingClientRect().left - scroller.getBoundingClientRect().left - parseFloat(getComputedStyle(scroller).paddingLeft);
          scroller.scrollTo({ left, behavior: calm.matches ? 'auto' : 'smooth' });
        });
      }
      // A link to one step (prerequisites.html#id) opens that step traced.
      let target;
      try { target = decodeURIComponent(location.hash.slice(1)); } catch { target = ''; }
      const linked = target && cardOf(target);
      if (linked) requestAnimationFrame(() => { show(linked); select(target, linked); });
    }
  }

  // Statements: a filter for the list, and a page title for the item in view.
  const list = document.querySelector('.items');
  if (list) {
    const base = document.title;
    const search = list.querySelector('.search');
    const input = search.querySelector('input');
    const status = search.querySelector('.search-status');
    search.hidden = false;
    input.addEventListener('input', () => {
      const words = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
      let shown = 0;
      for (const item of list.querySelectorAll('.item')) {
        const match = words.every(word => item.dataset.search.includes(word));
        item.hidden = !match;
        if (match) shown += 1;
      }
      for (const tree of list.querySelectorAll('.items-tree')) tree.hidden = !tree.querySelector('.item:not([hidden])');
      status.textContent = words.length ? `${shown} matching ${shown === 1 ? 'item' : 'items'}` : '';
    });
    const follow = () => {
      const id = decodeURIComponent(location.hash.slice(1));
      const item = id && document.getElementById(id);
      if (item && item.classList.contains('item')) {
        if (item.hidden) { input.value = ''; input.dispatchEvent(new Event('input')); }
        document.title = `${(item.querySelector('.item-statement') || item.querySelector('.card-text')).textContent.trim().slice(0, 70)} · ${base}`;
        const detail = item.querySelector('.item-detail');
        detail.setAttribute('tabindex', '-1');
        detail.focus({ preventScroll: true });
        scrollTo(0, 0);  // The item now stands alone under the commons header, like a page of its own.
      } else {
        document.title = base;
      }
    };
    addEventListener('hashchange', follow);
    // The browser jumps to the anchor while loading; settle on the item page after that jump.
    if (document.readyState === 'complete') follow(); else addEventListener('load', follow);
  }

  // Copy a brief. If the clipboard is unavailable, open the text so it can be copied by hand.
  for (const button of document.querySelectorAll('button[data-copy]')) {
    button.hidden = false;
    button.addEventListener('click', async () => {
      const pre = document.getElementById(button.dataset.copy);
      const status = button.parentElement.querySelector('.copy-status');
      try {
        if (!navigator.clipboard?.writeText) throw new Error('No clipboard');
        await navigator.clipboard.writeText(pre.textContent);
        status.textContent = 'Brief copied. Nothing has been sent.';
      } catch {
        pre.closest('details').open = true;
        const range = document.createRange();
        range.selectNodeContents(pre);
        getSelection().removeAllRanges();
        getSelection().addRange(range);
        status.textContent = 'Copying is blocked here. The brief is selected: copy it by hand.';
      }
    });
  }
  // A source card or bookmarked comparison opens only the disclosure it targets.
  const openLinkedDisclosure = () => {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = id && document.getElementById(id);
    if (!target) return;
    if (target.classList.contains('participation')) target.focus({ preventScroll: true });
    let detail = target.closest('details');
    while (detail) {
      detail.open = true;
      detail = detail.parentElement?.closest('details');
    }
  };
  addEventListener('hashchange', openLinkedDisclosure);
  openLinkedDisclosure();
})();
