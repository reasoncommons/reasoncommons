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
    let detail = target.closest('details');
    while (detail) {
      detail.open = true;
      detail = detail.parentElement?.closest('details');
    }
  };
  addEventListener('hashchange', openLinkedDisclosure);
  openLinkedDisclosure();
})();
