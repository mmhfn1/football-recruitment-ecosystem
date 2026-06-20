/* ════════════════════════════════════════════════════════════════
   club-panel.js — Side panel showing a club's full multi-year history
   Opens when a network node is clicked. Draws a small SVG sparkline
   of revenue across all seasons the club appears in.
   ════════════════════════════════════════════════════════════════ */

(function () {
  const COLORS = window.FRE_COLORS;
  const TOPO_COLOR = window.FRE_TOPO_COLOR;
  let D = null;

  function buildHistory(clubId) {
    const years = window.FRE_Network.getYears();
    const points = [];
    years.forEach((yr) => {
      const raw = D.network[yr];
      if (!raw) return;
      const node = raw.nodes.find((n) => n.id === clubId);
      if (node) points.push({ year: yr, ...node });
    });
    return points;
  }

  function sparklineSVG(points, key, color) {
    if (points.length < 2) return '';
    const w = 300, h = 56, pad = 4;
    const vals = points.map((p) => p[key]);
    const min = Math.min(...vals), max = Math.max(...vals);
    const range = max - min || 1;
    const stepX = (w - pad * 2) / (points.length - 1);

    const coords = points.map((p, i) => {
      const x = pad + i * stepX;
      const y = h - pad - ((p[key] - min) / range) * (h - pad * 2);
      return [x, y];
    });

    const linePath = coords.map((c, i) => (i === 0 ? `M${c[0]},${c[1]}` : `L${c[0]},${c[1]}`)).join(' ');
    const areaPath = `${linePath} L${coords[coords.length - 1][0]},${h - pad} L${coords[0][0]},${h - pad} Z`;

    const dots = coords.map((c, i) =>
      `<circle cx="${c[0]}" cy="${c[1]}" r="2.5" fill="${color}">
         <title>${points[i].year}: ${points[i][key].toFixed(0)}</title>
       </circle>`
    ).join('');

    return `
      <svg class="club-sparkline" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
        <path d="${areaPath}" fill="${color}" opacity="0.10"></path>
        <path d="${linePath}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path>
        ${dots}
      </svg>
    `;
  }

  function open(clubId) {
    const panel = document.getElementById('club-panel');
    const history = buildHistory(clubId);
    if (history.length === 0) return;

    const latest = history[history.length - 1];
    const first = history[0];
    const col = TOPO_COLOR[latest.topology] || '#fff';
    const roleDesc = {
      Incubator: 'Develops & sells young talent',
      Refinery: 'Buys young, sells prime',
      Aggregator: 'Trophy-hunting superclub',
    }[latest.topology] || '';

    const revChange = first.revenue > 0 ? ((latest.revenue - first.revenue) / first.revenue * 100) : 0;
    const revChangeStr = (revChange >= 0 ? '+' : '') + revChange.toFixed(0) + '%';
    const revChangeColor = revChange >= 0 ? COLORS.green : '#FF4466';

    panel.innerHTML = `
      <button class="club-panel-close" onclick="FRE_closeClubPanel()">✕</button>
      <div class="club-panel-name">${clubId}</div>
      <div class="club-panel-role" style="background:rgba(${hexToRgbStr(col)},0.1);color:${col};border:1px solid rgba(${hexToRgbStr(col)},0.3)">
        ${latest.topology} · ${roleDesc}
      </div>

      <div class="club-panel-section">
        <div class="club-panel-label">REVENUE HISTORY — ${first.year} TO ${latest.year}</div>
        ${sparklineSVG(history, 'revenue', col)}
        <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:11px;color:var(--sub)">
          <span>€${first.revenue.toFixed(0)}M (${first.year})</span>
          <span style="color:${revChangeColor};font-weight:600">${revChangeStr}</span>
          <span>€${latest.revenue.toFixed(0)}M (${latest.year})</span>
        </div>
      </div>

      <div class="club-panel-section">
        <div class="club-panel-label">LATEST SEASON SNAPSHOT (${latest.year})</div>
        <div class="club-stat-grid">
          <div class="club-stat">
            <div class="club-stat-val">€${latest.revenue.toFixed(0)}M</div>
            <div class="club-stat-label">REVENUE</div>
          </div>
          <div class="club-stat">
            <div class="club-stat-val">€${latest.wages.toFixed(0)}M</div>
            <div class="club-stat-label">WAGE BILL</div>
          </div>
          <div class="club-stat">
            <div class="club-stat-val">${latest.w2r.toFixed(0)}%</div>
            <div class="club-stat-label">WAGES / REV</div>
          </div>
          <div class="club-stat">
            <div class="club-stat-val" style="color:${latest.op >= 0 ? COLORS.green : '#FF4466'}">
              ${latest.op >= 0 ? '+' : ''}€${latest.op.toFixed(0)}M
            </div>
            <div class="club-stat-label">OP. PROFIT</div>
          </div>
        </div>
      </div>

      <div class="club-panel-section">
        <div class="club-panel-label">SEASONS TRACKED</div>
        <div style="font-size:13px;color:var(--sub)">
          Appears in <strong style="color:var(--text)">${history.length}</strong> of
          ${window.FRE_Network.getYears().length} seasons in this dataset
          (${first.year}–${latest.year}).
        </div>
      </div>

      <div class="club-panel-section" style="margin-bottom:0">
        <div class="club-panel-label">KEYBOARD TIP</div>
        <div style="font-size:12px;color:var(--dim);line-height:1.7">
          Press <kbd style="background:var(--panel);border:1px solid var(--border);border-radius:3px;padding:1px 5px">Esc</kbd>
          to unpin, or click another node to switch clubs.
        </div>
      </div>
    `;
    panel.classList.add('open');
  }

  function hexToRgbStr(hex) {
    const h = hex.replace('#', '');
    return `${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)}`;
  }

  function close() {
    document.getElementById('club-panel').classList.remove('open');
    window.FRE_Network.unpinClub();
  }

  window.FRE_initClubPanel = function (data) { D = data; };
  window.FRE_openClubPanel = open;
  window.FRE_closeClubPanel = close;
})();
