/* ════════════════════════════════════════════════════════════════
   app.js — Main orchestration
   Loads dashboard_data.json, wires up nav, scroll progress, reveal
   animations, hero count-up, glossary filter, and back-to-top.
   ════════════════════════════════════════════════════════════════ */

window.FRE_COLORS = {
  cyan: '#00F5FF', amber: '#FFB800', magenta: '#FF2D78',
  blue: '#3A7FFF', green: '#44FF99', text: '#E0E8FF',
  sub: '#6A7BAA', bg: '#05060F', panel: '#0A0E1F',
  border: '#161C35', grid: '#0D1120',
};
window.FRE_TOPO_COLOR = {
  Incubator: window.FRE_COLORS.cyan,
  Refinery: window.FRE_COLORS.amber,
  Aggregator: window.FRE_COLORS.magenta,
};

(function () {
  const DATA_URL = 'assets/data/dashboard_data.json';

  function initScrollProgress() {
    const bar = document.getElementById('scroll-progress');
    function update() {
      const h = document.documentElement;
      const scrolled = h.scrollTop;
      const height = h.scrollHeight - h.clientHeight;
      bar.style.width = (height > 0 ? (scrolled / height) * 100 : 0) + '%';
    }
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  function initNavTracking() {
    const sections = ['ecosystem', 'intelligence', 'analysis', 'glossary'];
    const links = Array.from(document.querySelectorAll('.nav-link'));
    function update() {
      const y = window.scrollY + 140;
      let activeIdx = 0;
      sections.forEach((id, i) => {
        const el = document.getElementById(id);
        if (el && el.offsetTop <= y) activeIdx = i;
      });
      links.forEach((l, i) => l.classList.toggle('active', i === activeIdx));
    }
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  function initRevealAnimations() {
    const targets = document.querySelectorAll(
      '.section-header, #network-wrap, .chart-card, .analysis-block, .gloss-card'
    );
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    targets.forEach((t) => obs.observe(t));
  }

  function animateCountUp(el, target, opts) {
    opts = opts || {};
    const prefix = opts.prefix || '';
    const suffix = opts.suffix || '';
    const decimals = opts.decimals || 0;
    const duration = opts.duration || 1400;
    const start = performance.now();

    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const val = target * eased;
      el.textContent = prefix + val.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;
      if (t < 1) requestAnimationFrame(frame);
      else el.textContent = prefix + target.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;
    }
    requestAnimationFrame(frame);
  }

  function initHeroCountUp(D) {
    const s = D.summary;
    const targets = [
      { id: 'stat-transfers', val: s.total_transfers, opts: { decimals: 0 } },
      { id: 'stat-fees', val: s.total_fees / 1000, opts: { prefix: '€', suffix: 'B', decimals: 1 } },
      { id: 'stat-clubs', val: s.n_clubs, opts: { decimals: 0 } },
      { id: 'stat-genjumps', val: s.gen_jumps, opts: { decimals: 0 } },
      { id: 'stat-avgfee', val: s.avg_fee, opts: { prefix: '€', suffix: 'M', decimals: 1 } },
    ];
    const heroEl = document.querySelector('.hero-stats');
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          targets.forEach((t) => {
            const el = document.getElementById(t.id);
            if (el) animateCountUp(el, t.val, t.opts);
          });
          obs.disconnect();
        }
      });
    }, { threshold: 0.4 });
    if (heroEl) obs.observe(heroEl);
  }

  function initBackToTop() {
    const btn = document.getElementById('back-to-top');
    window.addEventListener('scroll', () => {
      btn.classList.toggle('visible', window.scrollY > 600);
    }, { passive: true });
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  function initGlossaryFilter() {
    const buttons = document.querySelectorAll('.gloss-filter-btn');
    const cards = document.querySelectorAll('.gloss-card');
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        buttons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.getAttribute('data-filter');
        cards.forEach((card) => {
          const matches = filter === 'all' || card.getAttribute('data-category') === filter;
          card.style.display = matches ? '' : 'none';
        });
      });
    });
  }

  window.FRE_scrollTo = function (id, evt) {
    document.querySelector(id).scrollIntoView({ behavior: 'smooth', block: 'start' });
    if (evt) {
      document.querySelectorAll('.nav-link').forEach((b) => b.classList.remove('active'));
      evt.target.classList.add('active');
    }
  };

  async function boot() {
    let D;
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      D = await res.json();
    } catch (err) {
      document.body.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;height:100vh;
                    flex-direction:column;gap:16px;color:#E0E8FF;font-family:Inter,sans-serif;
                    text-align:center;padding:24px">
          <div style="font-family:Rajdhani,sans-serif;font-size:24px;color:#FF2D78;font-weight:700">
            COULDN'T LOAD DASHBOARD DATA
          </div>
          <div style="color:#6A7BAA;max-width:480px;font-size:14px;line-height:1.7">
            ${escapeHtml(String(err.message))}<br><br>
            If you opened this file directly (file://), most browsers block local
            JSON fetches for security. Serve the folder with a local web server instead, e.g.:
            <br><code style="color:#FFB800">python3 -m http.server 8000</code>
            <br>then open <code style="color:#FFB800">http://localhost:8000</code>.
            <br><br>This works automatically once hosted on GitHub Pages.
          </div>
        </div>`;
      console.error('Failed to load dashboard data:', err);
      return;
    }

    initScrollProgress();
    initNavTracking();
    initRevealAnimations();
    initBackToTop();
    initGlossaryFilter();
    initHeroCountUp(D);

    window.FRE_Network.init(D);
    window.FRE_initClubPanel(D);
    window.FRE_Search.init(D);
    window.FRE_Charts.renderAll(D);
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  document.addEventListener('DOMContentLoaded', boot);
})();
