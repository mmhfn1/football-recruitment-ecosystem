/* ════════════════════════════════════════════════════════════════
   charts.js — Four Plotly intelligence panels
   Maturity Violin · Scouting Blindspots · Revenue Trajectory · Gen Jumps
   ════════════════════════════════════════════════════════════════ */

(function () {
  const COLORS = window.FRE_COLORS;
  const TOPO_COLOR = window.FRE_TOPO_COLOR;

  function hexToRgb(hex) {
    const h = hex.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  const plotConfig = { responsive: true, displayModeBar: false };

  function plotLayout(extra) {
    return Object.assign({
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: COLORS.text, family: 'Inter, sans-serif', size: 12 },
      margin: { l: 60, r: 30, t: 20, b: 60 },
      showlegend: false,
      hovermode: 'closest',
      hoverlabel: { bgcolor: COLORS.panel, bordercolor: COLORS.magenta, font: { color: COLORS.text, size: 12 } },
      xaxis: { gridcolor: COLORS.grid, linecolor: COLORS.border, tickcolor: COLORS.border, zerolinecolor: COLORS.border },
      yaxis: { gridcolor: COLORS.grid, linecolor: COLORS.border, tickcolor: COLORS.border, zerolinecolor: COLORS.border },
    }, extra || {});
  }

  function renderViolin(D) {
    const traces = Object.entries(D.violin).map(([topo, vals]) => {
      const col = TOPO_COLOR[topo];
      const [rr, gg, bb] = hexToRgb(col);
      const sorted = [...vals].sort((a, b) => a - b);
      const med = sorted[Math.floor(vals.length / 2)];
      const mn = vals.reduce((a, b) => a + b, 0) / vals.length;
      const mx = Math.max(...vals);
      const q1 = sorted[Math.floor(vals.length * 0.25)];
      const q3 = sorted[Math.floor(vals.length * 0.75)];
      return {
        type: 'violin', y: vals, name: topo,
        box: { visible: true }, meanline: { visible: true },
        fillcolor: `rgba(${rr},${gg},${bb},0.35)`,
        line: { color: col, width: 1.5 },
        marker: { color: col, opacity: 0.4, size: 3 },
        hovertemplate:
          `<b style="color:${col}">${topo}</b><br>` +
          `Median: <b>€${med.toFixed(1)}M</b><br>` +
          `Average: <b>€${mn.toFixed(1)}M</b><br>` +
          `IQR: €${q1.toFixed(1)}M – €${q3.toFixed(1)}M<br>` +
          `Highest: <b>€${mx.toFixed(1)}M</b><br>` +
          `<i>Final fee − first fee for same player</i><extra></extra>`,
      };
    });
    Plotly.newPlot('chart-violin', traces, plotLayout({
      yaxis: { title: { text: 'Maturity Premium (€ M)', font: { color: COLORS.sub } },
               ticksuffix: ' M', gridcolor: COLORS.grid, zerolinecolor: COLORS.border },
      xaxis: { title: { text: 'Club Role', font: { color: COLORS.sub } }, gridcolor: COLORS.grid },
    }), plotConfig);
  }

  function renderBlindspot(D) {
    const bs = D.blindspots;
    const cols = bs.map((b) => {
      const t = b.score / bs[0].score;
      const v = Math.round(55 + t * 200);
      return `rgba(0,${v},${Math.min(255, v + 55)},0.8)`;
    });
    Plotly.newPlot('chart-blindspot', [{
      type: 'bar',
      x: bs.map((b) => b.country), y: bs.map((b) => b.score),
      marker: { color: cols, line: { color: COLORS.cyan, width: 0.5 } },
      customdata: bs.map((b) => [b.exports, b.sold_agg.toFixed(1), b.code]),
      hovertemplate:
        '<b>%{x}</b><br>' +
        'Blindspot Score: <b>%{y:.3f}</b><br>' +
        'Players exported: <b>%{customdata[0]}</b><br>' +
        'Direct Aggregator spend: <b>€%{customdata[1]}M</b><br>' +
        '<i>Higher score = more talent overlooked by elite clubs</i><extra></extra>',
      name: 'Blindspot Score',
    }], plotLayout({
      yaxis: { title: { text: 'Blindspot Score', font: { color: COLORS.sub } }, gridcolor: COLORS.grid },
      xaxis: { title: { text: 'Country', font: { color: COLORS.sub } }, tickangle: -30, gridcolor: COLORS.grid },
      margin: { l: 55, r: 20, t: 20, b: 80 },
    }), plotConfig);
  }

  function renderRevenue(D) {
    const traces = Object.entries(D.revenue).map(([topo, pts]) => {
      const col = TOPO_COLOR[topo];
      const [rr, gg, bb] = hexToRgb(col);
      return {
        type: 'scatter', mode: 'lines+markers',
        x: pts.map((p) => p.year), y: pts.map((p) => p.rev),
        name: topo,
        line: { color: col, width: 2.5 },
        marker: { color: col, size: 5 },
        fill: 'tozeroy', fillcolor: `rgba(${rr},${gg},${bb},0.07)`,
        hovertemplate:
          `<b style="color:${col}">${topo}</b> — <b>%{x}</b><br>` +
          'Avg Revenue: <b>€%{y:.0f}M</b><br>' +
          '<i>Average across all clubs in this role that season</i><extra></extra>',
      };
    });
    Plotly.newPlot('chart-revenue', traces, plotLayout({
      showlegend: true,
      legend: { bgcolor: 'transparent', font: { color: COLORS.sub, size: 11 } },
      yaxis: { title: { text: 'Avg Annual Revenue (€ M)', font: { color: COLORS.sub } },
               tickprefix: '€', ticksuffix: 'M', gridcolor: COLORS.grid },
      xaxis: { title: { text: 'Season', font: { color: COLORS.sub } }, dtick: 2, gridcolor: COLORS.grid },
      margin: { l: 75, r: 20, t: 20, b: 60 },
    }), plotConfig);
  }

  function plasmaColor(t) {
    const r = Math.round(13 + t * 230);
    const g = Math.round(8 + t * 190 * (t < 0.5 ? t * 2 : 2 - t * 2));
    const b = Math.round(135 - t * 135);
    return `rgb(${r},${g},${b})`;
  }

  function renderGenJump(D) {
    const gj = D.gen_jumps;
    const years = gj.map((g) => g.year);
    const minY = Math.min(...years), maxY = Math.max(...years);
    const cols = years.map((y) => plasmaColor((y - minY) / (maxY - minY || 1)));
    Plotly.newPlot('chart-genjump', [{
      type: 'scattergl', mode: 'markers',
      x: gj.map((g) => g.age), y: gj.map((g) => g.fee),
      marker: {
        color: cols, size: 9, opacity: 0.85,
        line: { color: 'rgba(5,6,15,0.6)', width: 1 },
      },
      customdata: gj.map((g) => [g.player, g.from, g.to, g.year, g.pos, g.from_l, g.to_l]),
      hovertemplate:
        '<b>%{customdata[0]}</b> · %{customdata[4]}<br>' +
        '%{customdata[1]} (%{customdata[5]})<br>' +
        '→ %{customdata[2]} (%{customdata[6]})<br>' +
        'Age: <b>%{x} yrs</b>  ·  Fee: <b>€%{y:.1f}M</b><br>' +
        'Season: <b>%{customdata[3]}</b><extra></extra>',
      name: 'Elite Transfer',
    }], plotLayout({
      xaxis: { title: { text: 'Age at Transfer (years)', font: { color: COLORS.sub } },
               ticksuffix: ' yrs', range: [15.3, 23], dtick: 1, gridcolor: COLORS.grid },
      yaxis: { title: { text: 'Transfer Fee (€ M)', font: { color: COLORS.sub } },
               tickprefix: '€', ticksuffix: 'M', gridcolor: COLORS.grid },
      margin: { l: 75, r: 20, t: 20, b: 60 },
    }), plotConfig);
  }

  function renderAll(D) {
    renderViolin(D);
    renderBlindspot(D);
    renderRevenue(D);
    renderGenJump(D);

    // Plotly needs a resize nudge once parent containers finish their
    // fade-in transition (they start at 0 width-affecting opacity states
    // in some browsers' layout calc).
    window.addEventListener('resize', () => {
      ['chart-violin', 'chart-blindspot', 'chart-revenue', 'chart-genjump'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) Plotly.Plots.resize(el);
      });
    });
  }

  window.FRE_Charts = { renderAll };
})();
