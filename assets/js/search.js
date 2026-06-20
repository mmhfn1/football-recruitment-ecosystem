/* ════════════════════════════════════════════════════════════════
   search.js — Club search box in the nav bar.
   Builds an index of every club that ever appears in the network,
   filters as you type, and jumps the network to that club on select.
   ════════════════════════════════════════════════════════════════ */

(function () {
  let allClubs = [];   // [{ name, topology, lastYear }]
  let input, dropdown;

  function buildIndex(D) {
    const seen = new Map();
    Object.entries(D.network).forEach(([yr, payload]) => {
      payload.nodes.forEach((n) => {
        seen.set(n.id, { name: n.id, topology: n.topology, lastYear: yr });
      });
    });
    allClubs = Array.from(seen.values()).sort((a, b) => a.name.localeCompare(b.name));
  }

  function renderResults(query) {
    const q = query.trim().toLowerCase();
    if (!q) { dropdown.classList.remove('visible'); dropdown.innerHTML = ''; return; }

    const matches = allClubs
      .filter((c) => c.name.toLowerCase().includes(q))
      .slice(0, 8);

    if (matches.length === 0) {
      dropdown.innerHTML = `<div class="search-result"><span class="search-result-meta">No clubs match "${escapeHtml(query)}"</span></div>`;
      dropdown.classList.add('visible');
      return;
    }

    dropdown.innerHTML = matches.map((c) => `
      <div class="search-result" data-club="${escapeHtml(c.name)}">
        <span class="search-result-name">${escapeHtml(c.name)}</span>
        <span class="search-result-meta">${c.topology}</span>
      </div>
    `).join('');
    dropdown.classList.add('visible');

    dropdown.querySelectorAll('.search-result[data-club]').forEach((el) => {
      el.addEventListener('click', () => {
        const club = el.getAttribute('data-club');
        selectClub(club);
      });
    });
  }

  function selectClub(name) {
    dropdown.classList.remove('visible');
    input.value = '';
    document.getElementById('ecosystem').scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => window.FRE_Network.focusClub(name), 400);
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function init(D) {
    buildIndex(D);
    input = document.getElementById('club-search-input');
    dropdown = document.getElementById('search-dropdown');

    input.addEventListener('input', () => renderResults(input.value));
    input.addEventListener('focus', () => { if (input.value) renderResults(input.value); });
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.nav-search') && !e.target.closest('#search-dropdown')) {
        dropdown.classList.remove('visible');
      }
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const first = dropdown.querySelector('.search-result[data-club]');
        if (first) selectClub(first.getAttribute('data-club'));
      } else if (e.key === 'Escape') {
        dropdown.classList.remove('visible');
        input.blur();
      }
    });
  }

  window.FRE_Search = { init };
})();
