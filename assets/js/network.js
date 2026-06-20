/* ════════════════════════════════════════════════════════════════
   network.js — Force-directed club network rendered on Canvas
   No Plotly. No animation-frame bugs. Pure 2D context drawing,
   redrawn on demand, with search, click-to-pin, and keyboard control.
   ════════════════════════════════════════════════════════════════ */

(function () {
  const COLORS = window.FRE_COLORS;
  const TOPO_COLOR = window.FRE_TOPO_COLOR;

  let D = null;            // dashboard data, set by init()
  let YEARS = [];
  let canvas, ctx, tooltip;
  let currentYearIdx = 0;
  let isPlaying = false;
  let playTimer = null;
  let playSpeed = 1200;
  let dpr = window.devicePixelRatio || 1;
  let pinnedClub = null;   // club id currently pinned via click
  let hoveredClub = null;

  function worldToScreen(x, y, W, H) {
    const margin = 80;
    const scaleX = (W - margin * 2) / 4.0;
    const scaleY = (H - margin * 2) / 4.0;
    const scale = Math.min(scaleX, scaleY);
    return [W / 2 + x * scale, H / 2 - y * scale];
  }

  function getYearData(idx) {
    const yr = YEARS[idx];
    const raw = D.network[yr];
    if (!raw) return null;
    const W = canvas.width / dpr;
    const H = canvas.height / dpr;
    const posMap = {};
    raw.nodes.forEach((n) => { posMap[n.id] = worldToScreen(n.x, n.y, W, H); });
    const revs = raw.nodes.map((n) => n.revenue);
    const revMin = Math.min(...revs);
    const revMax = Math.max(...revs);
    return { yr, nodes: raw.nodes, edges: raw.edges, posMap, revMin, revMax, W, H };
  }

  function nodeRadius(revenue, revMin, revMax) {
    const t = revMax > revMin ? (revenue - revMin) / (revMax - revMin) : 0.5;
    return 8 + t * 26;
  }

  function hexToRgb(hex) {
    const h = hex.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  function resizeCanvas() {
    const w = canvas.parentElement.clientWidth;
    const h = 620;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    drawYear(currentYearIdx);
  }

  function drawYear(idx) {
    const data = getYearData(idx);
    if (!data) return;
    const { yr, nodes, edges, posMap, revMin, revMax, W, H } = data;

    ctx.clearRect(0, 0, W, H);

    // ── Edges ──
    edges.forEach((e) => {
      const sp = posMap[e.from];
      const ep = posMap[e.to];
      if (!sp || !ep) return;
      const isGJ = e.path === 'Generational Jump';
      const alpha = isGJ ? 0.85 : Math.min(0.5, 0.1 + e.fee / 400);

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = isGJ ? COLORS.magenta : COLORS.blue;
      ctx.lineWidth = isGJ ? 2.0 : Math.max(0.5, Math.min(3.0, e.fee / 80));
      ctx.setLineDash(isGJ ? [] : [6, 6]);

      const mx = (sp[0] + ep[0]) / 2 + (ep[1] - sp[1]) * 0.12;
      const my = (sp[1] + ep[1]) / 2 - (ep[0] - sp[0]) * 0.12;
      ctx.beginPath();
      ctx.moveTo(sp[0], sp[1]);
      ctx.quadraticCurveTo(mx, my, ep[0], ep[1]);
      ctx.stroke();
      ctx.restore();
    });

    // ── Halos ──
    nodes.forEach((n) => {
      const p = posMap[n.id];
      if (!p) return;
      const r = nodeRadius(n.revenue, revMin, revMax);
      const col = TOPO_COLOR[n.topology] || '#fff';
      const [rr, gg, bb] = hexToRgb(col);
      const grad = ctx.createRadialGradient(p[0], p[1], r * 0.5, p[0], p[1], r * 2.5);
      grad.addColorStop(0, `rgba(${rr},${gg},${bb},0.18)`);
      grad.addColorStop(1, `rgba(${rr},${gg},${bb},0)`);
      ctx.save();
      ctx.beginPath();
      ctx.arc(p[0], p[1], r * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.restore();
    });

    // ── Nodes ──
    nodes.forEach((n) => {
      const p = posMap[n.id];
      if (!p) return;
      const r = nodeRadius(n.revenue, revMin, revMax);
      const col = TOPO_COLOR[n.topology] || '#fff';
      const isPinned = pinnedClub === n.id;
      const isHovered = hoveredClub === n.id;

      ctx.save();
      ctx.beginPath();
      ctx.arc(p[0], p[1], isHovered || isPinned ? r * 1.12 : r, 0, Math.PI * 2);
      ctx.fillStyle = col;
      ctx.globalAlpha = 0.92;
      ctx.fill();

      ctx.strokeStyle = isPinned ? '#FFFFFF' : 'rgba(255,255,255,0.6)';
      ctx.lineWidth = isPinned ? 2.6 : 1.5;
      ctx.globalAlpha = 1;
      ctx.stroke();

      if (isPinned) {
        ctx.beginPath();
        ctx.arc(p[0], p[1], r * 1.5, 0, Math.PI * 2);
        ctx.strokeStyle = COLORS.cyan;
        ctx.lineWidth = 1.4;
        ctx.globalAlpha = 0.7;
        ctx.setLineDash([3, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      ctx.restore();

      if (r >= 12 || isPinned || isHovered) {
        ctx.save();
        ctx.font = `${Math.max(9, Math.min(12, r * 0.55))}px Inter, sans-serif`;
        ctx.fillStyle = isPinned ? COLORS.cyan : 'rgba(224,232,255,0.9)';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.shadowColor = 'rgba(0,0,0,0.9)';
        ctx.shadowBlur = 5;
        const label = n.id.length > 14 ? n.id.slice(0, 13) + '…' : n.id;
        ctx.fillText(label, p[0], p[1] + r + 3);
        ctx.restore();
      }
    });

    // Year watermark
    ctx.save();
    ctx.font = `700 ${Math.min(W, H) * 0.13}px Rajdhani, sans-serif`;
    ctx.fillStyle = 'rgba(255,45,120,0.04)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(yr, W / 2, H / 2);
    ctx.restore();
  }

  // ── Play controls ──
  function togglePlay() {
    isPlaying = !isPlaying;
    document.getElementById('play-btn').innerHTML = isPlaying ? '⏸ Pause' : '▶ Play';
    if (isPlaying) {
      if (currentYearIdx >= YEARS.length - 1) currentYearIdx = 0;
      tick();
    } else {
      clearTimeout(playTimer);
    }
  }

  function tick() {
    if (!isPlaying) return;
    currentYearIdx++;
    if (currentYearIdx >= YEARS.length) {
      currentYearIdx = YEARS.length - 1;
      isPlaying = false;
      document.getElementById('play-btn').innerHTML = '▶ Play';
      return;
    }
    updateDisplay();
    playTimer = setTimeout(tick, playSpeed);
  }

  function setSpeed(ms, btn) {
    playSpeed = ms;
    document.querySelectorAll('.speed-btn').forEach((b) => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
  }

  function onSlider(val) {
    currentYearIdx = parseInt(val, 10);
    if (isPlaying) {
      clearTimeout(playTimer);
      isPlaying = false;
      document.getElementById('play-btn').innerHTML = '▶ Play';
    }
    updateDisplay();
  }

  function jumpToYear(yr) {
    const idx = YEARS.indexOf(String(yr));
    if (idx === -1) return;
    onSlider(idx);
  }

  function stepYear(delta) {
    let idx = currentYearIdx + delta;
    idx = Math.max(0, Math.min(YEARS.length - 1, idx));
    onSlider(idx);
  }

  function updateDisplay() {
    document.getElementById('year-slider').value = currentYearIdx;
    document.getElementById('year-display').textContent = YEARS[currentYearIdx];
    drawYear(currentYearIdx);
  }

  // ── Tooltip + click-to-pin ──
  function hitTest(mx, my) {
    const data = getYearData(currentYearIdx);
    if (!data) return null;
    const { nodes, edges, posMap, revMin, revMax } = data;

    for (const n of nodes) {
      const p = posMap[n.id];
      if (!p) continue;
      const r = nodeRadius(n.revenue, revMin, revMax);
      const dx = mx - p[0], dy = my - p[1];
      if (dx * dx + dy * dy < r * r) return { type: 'node', n };
    }
    for (const eg of edges) {
      const sp = posMap[eg.from], ep = posMap[eg.to];
      if (!sp || !ep) continue;
      const mx2 = (sp[0] + ep[0]) / 2 + (ep[1] - sp[1]) * 0.12;
      const my2 = (sp[1] + ep[1]) / 2 - (ep[0] - sp[0]) * 0.12;
      const dx = mx - mx2, dy = my - my2;
      if (dx * dx + dy * dy < 64 && eg.fee >= 5) return { type: 'edge', eg };
    }
    return null;
  }

  function buildNodeTooltip(n) {
    const col = TOPO_COLOR[n.topology] || '#fff';
    const roleDesc = {
      Incubator: 'develops & sells young talent',
      Refinery: 'buys young, sells prime',
      Aggregator: 'trophy-hunting superclub',
    }[n.topology] || '';
    const opColor = n.op >= 0 ? COLORS.green : '#FF4466';
    return `
      <b style="color:${col};font-size:14px">${n.id}</b><br>
      <span style="color:var(--sub)">Role: </span><b>${n.topology}</b>
      <span style="color:var(--sub);font-size:11px"> · ${roleDesc}</span><br>
      <span style="color:var(--sub)">Revenue: </span><b>€${n.revenue.toFixed(0)}M</b><br>
      <span style="color:var(--sub)">Wages: </span><b>€${n.wages.toFixed(0)}M</b>
      <span style="color:var(--sub)"> (${n.w2r.toFixed(1)}% of revenue)</span><br>
      <span style="color:var(--sub)">Operating Profit: </span>
      <b style="color:${opColor}">${n.op >= 0 ? '+' : ''}€${n.op.toFixed(0)}M</b><br>
      <span style="color:var(--dim);font-size:11px">Click to pin · see full history →</span>
    `;
  }

  function buildEdgeTooltip(eg) {
    const pathCol = eg.path === 'Generational Jump' ? COLORS.magenta : COLORS.blue;
    return `
      <b style="font-size:14px">${eg.player}</b>
      <span style="color:var(--sub)"> · ${eg.pos} · Age ${eg.age}</span><br>
      <b>${eg.from}</b> → <b>${eg.to}</b><br>
      <span style="color:var(--sub)">Fee: </span><b>€${eg.fee.toFixed(1)}M</b>
      ${eg.prem > 0 ? `<span style="color:var(--sub)"> · Premium: </span><b>€${eg.prem.toFixed(1)}M added</b>` : ''}<br>
      <span style="color:var(--sub)">Path: </span><b style="color:${pathCol}">${eg.path}</b>
    `;
  }

  function onMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const hit = hitTest(mx, my);

    if (hit) {
      canvas.style.cursor = 'pointer';
      hoveredClub = hit.type === 'node' ? hit.n.id : null;
      tooltip.innerHTML = hit.type === 'node' ? buildNodeTooltip(hit.n) : buildEdgeTooltip(hit.eg);
      tooltip.classList.add('visible');
      const tx = e.clientX + 14, ty = e.clientY - 10;
      tooltip.style.left = Math.min(tx, window.innerWidth - 320) + 'px';
      tooltip.style.top = ty + 'px';
    } else {
      canvas.style.cursor = 'default';
      hoveredClub = null;
      tooltip.classList.remove('visible');
    }
    drawYear(currentYearIdx);
  }

  function onClick(e) {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const hit = hitTest(mx, my);
    if (hit && hit.type === 'node') {
      pinClub(hit.n.id);
    }
  }

  // ── Club pin / detail panel ──
  function pinClub(clubId) {
    pinnedClub = clubId;
    drawYear(currentYearIdx);
    if (window.FRE_openClubPanel) window.FRE_openClubPanel(clubId);
  }

  function unpinClub() {
    pinnedClub = null;
    drawYear(currentYearIdx);
  }

  function focusClub(clubId) {
    // Find first year this club appears, jump there, then pin it.
    for (let i = 0; i < YEARS.length; i++) {
      const raw = D.network[YEARS[i]];
      if (raw && raw.nodes.some((n) => n.id === clubId)) {
        onSlider(i);
        break;
      }
    }
    pinClub(clubId);
  }

  // ── Keyboard shortcuts ──
  function onKeydown(e) {
    const tag = (document.activeElement && document.activeElement.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
    else if (e.code === 'ArrowRight') { stepYear(1); }
    else if (e.code === 'ArrowLeft') { stepYear(-1); }
    else if (e.code === 'Escape') { unpinClub(); }
  }

  // ── Public init ──
  function init(data) {
    D = data;
    YEARS = data.years;
    canvas = document.getElementById('network-canvas');
    ctx = canvas.getContext('2d');
    tooltip = document.getElementById('net-tooltip');

    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mouseleave', () => { tooltip.classList.remove('visible'); hoveredClub = null; drawYear(currentYearIdx); });
    canvas.addEventListener('click', onClick);
    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('keydown', onKeydown);

    document.getElementById('year-slider').max = YEARS.length - 1;
    resizeCanvas();
  }

  window.FRE_Network = {
    init, togglePlay, setSpeed, onSlider, jumpToYear, stepYear,
    unpinClub, focusClub, getYears: () => YEARS,
    getClubsInCurrentYear: () => {
      const data = getYearData(currentYearIdx);
      return data ? data.nodes.map((n) => n.id) : [];
    },
  };
})();
