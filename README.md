# Football Recruitment Ecosystem

> **⚠️ All data in this project is synthetic.** Player names, transfer fees,
> club revenues, and every number in the dashboard are procedurally
> generated to *look* like plausible football transfer-market data — they
> do not represent real transfers, real fees, or real club finances.
> See [Synthetic data disclosure](#synthetic-data-disclosure) below for
> details on how it's generated and why some names may look familiar.

A 16-year forensic analysis of how talent flows through European football —
from youth academies to superclubs — visualised as a force-directed network,
plus a four-panel market intelligence dashboard.

**This is a fully static site.** No backend, no FastAPI, no Node server, no
build step. `index.html` loads a single JSON file via `fetch()` and renders
everything in the browser with Canvas (network) and Plotly.js (charts).
That means it deploys to **GitHub Pages** out of the box.

## Live structure

```
.
├── index.html                  ← the entire site (one page, four sections)
├── assets/
│   ├── css/style.css            ← all styling
│   ├── js/
│   │   ├── app.js                ← boot sequence, scroll fx, nav, count-up
│   │   ├── network.js            ← Canvas-based force-directed network
│   │   ├── club-panel.js         ← click-to-pin club history side panel
│   │   ├── search.js             ← club search box
│   │   └── charts.js             ← four Plotly intelligence panels
│   └── data/dashboard_data.json  ← pre-computed data the page fetches
├── scripts/
│   └── export_data.py            ← regenerates dashboard_data.json from CSVs
├── src/                          ← Python data engine (topology classifier,
│                                    force-directed layout, market intelligence)
├── tests/                        ← pytest unit tests for src/engine.py
├── *.csv                         ← raw source data
└── .github/workflows/deploy.yml  ← GitHub Pages auto-deploy on push to main
```

## Viewing it locally

Because `index.html` fetches `assets/data/dashboard_data.json` via
`fetch()`, opening the file directly (`file://…`) will be blocked by most
browsers' CORS rules. Serve the folder instead:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploying to GitHub Pages

**Order matters here** — enable Pages *before* your first push, not after.
If you push the workflow first and enable Pages second, the first run(s)
will fail with `Get Pages site failed ... Not Found`, because the
`github-pages` deployment environment doesn't exist until Pages has been
switched on at least once.

1. Create the repo on GitHub (don't push yet).
2. Go to **Settings → Pages** (left sidebar, under "Code and automation").
3. Under **Build and deployment → Source**, choose **GitHub Actions**
   and save. This is a one-time manual step — it can't be done from a
   workflow using the default token (see note below).
4. Now push this repo to `main`. `.github/workflows/deploy.yml` will run
   automatically and publish the site.

Your site will be live at `https://<username>.github.io/<repo>/`.

**If you already pushed and hit the `Not Found` error:** do step 2–3 above
now, then re-run the failed workflow from the **Actions** tab (or push an
empty commit) — no other changes needed.

**Why the workflow can't enable Pages for you:** `actions/configure-pages`
has an `enablement: true` option that sounds like it should auto-enable
Pages, but it explicitly requires a token with elevated permissions — a
Personal Access Token with `repo` scope, or a GitHub App with
`administration:write` + `pages:write`. The default `GITHUB_TOKEN` this
workflow uses has neither, so `enablement: true` can't actually do
anything with it; this repo's workflow intentionally omits it rather than
include a setting that silently no-ops. The manual one-time toggle above
is the documented, reliable path.

## Regenerating the data

If you update any of the source CSVs (`transfers_history.csv`,
`club_financials.csv`, etc.), regenerate the JSON the site consumes:

```bash
pip install -r requirements.txt
python3 scripts/export_data.py
```

This recomputes club topology classification, force-directed layouts for
all 17 seasons, maturity premiums, scouting blindspot scores, revenue
trajectories, and generational-jump transfers, then writes the result to
`assets/data/dashboard_data.json`. Commit the updated JSON alongside your
CSV changes.

## What's inside the dashboard

**① Ecosystem** — an animated force-directed network. Aggregator
superclubs are pinned as fixed gravity wells; Refineries and Incubators
orbit them based on transfer-fee strength. Click any club to pin it and
open a side panel with its full revenue history sparkline. Use the search
box in the nav to jump straight to a club. Keyboard shortcuts: `Space`
play/pause, `←`/`→` step a year, `Esc` unpin.

**② Intelligence** — four analytical panels: a maturity-premium violin
plot, a scouting-blindspot bar chart, a revenue-trajectory area chart, and
a generational-jumps scatter plot.

**③ Analysis** — full prose interpretation of every chart and the network
itself: what the patterns mean, why they look the way they do, and what
they imply for clubs at each level of the pyramid.

**④ Glossary** — every term, score, and formula used anywhere in the
dashboard, filterable by category.

## Synthetic data disclosure

**Every number in this project is synthetic.** The five source CSVs
(`transfers_history.csv`, `club_financials.csv`, `player_market_values.csv`,
`record_transfers.csv`, `league_metrics.csv`) are procedurally generated by
[`src/sample_data.py`](src/sample_data.py), not sourced from any real
transfer database, club accounts, or football data provider.

What that means concretely:

- **Player names are randomly assembled** from first-name and surname pools,
  which is why you'll see combinations like "Diego Camavinga" and "Peter
  Camavinga" as two different, unrelated synthetic players, or names that
  echo real footballers (e.g. a generated "Liam Mbappe") purely by
  coincidence of the name-pool combinatorics — not because any real player
  data was used.
- **Transfer fees, ages, dates, and club revenues** are drawn from
  distributions designed to *resemble* real football economics (young
  players cheaper, Aggregator-bound transfers more expensive, fees rising
  over the 2010–2026 window, a COVID-era revenue dip, etc.) but the exact
  values are generated, not measured.
- **Club names are real** (Real Madrid, Ajax, Manchester City, and so on),
  but their assigned topology role (Incubator / Refinery / Aggregator),
  the specific transfers attributed to them, and their financial figures
  in this dataset are not their actual transfer history or real financials.
- **The "Generational Jump" superstar list** (Messi, Ronaldo, Mbappé,
  Haaland, etc. — see [`src/constants.py`](src/constants.py)) is the one
  place real player names are deliberately used, purely to seed
  plausible high-fee outlier transfers in the generator. Their associated
  fees, ages, and club pairings in this dataset are still synthetic and
  do not reflect their actual transfer history.

**Why build it this way?** The goal of this project is to demonstrate a
data-engineering and visualisation pipeline — topology classification,
force-directed network layout, market-intelligence scoring — on a dataset
shaped like the real football transfer market, without requiring a
licensed data feed. If you want to point this dashboard at real data,
swap in your own CSVs matching the schemas documented in
[`src/loader.py`](src/loader.py) and rerun `scripts/export_data.py`.

## Tech notes

- The network used to be rendered with Plotly's animated-frame API, which
  has a known WebGL/`Scattergl` rendering bug where node traces silently
  disappear after a frame transition in some browsers. It's now a hand-
  rolled Canvas 2D renderer redrawn on demand — no animation-frame bugs,
  and noticeably faster.
- All four intelligence charts still use Plotly.js (loaded from a CDN)
  since Plotly's violin/bar/scatter rendering is solid and doesn't suffer
  from the same animated-frame issue.
- Generational Jump classification requires **age ≤ 22 AND fee ≥ €40M**
  (or a named superstar) — tightened from an earlier heuristic that
  flagged thousands of routine transfers.
