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
