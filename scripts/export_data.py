#!/usr/bin/env python3
"""
export_data.py
--------------
Regenerates assets/data/dashboard_data.json from the raw CSV sources.

Run this whenever transfers_history.csv / club_financials.csv / etc. change.
The static site (index.html) fetches the JSON this script produces — there
is no backend, no FastAPI, no server of any kind. Everything downstream is
plain HTML/CSS/JS that GitHub Pages can serve directly.

Usage:
    python3 scripts/export_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import engine, loader, layout          # noqa: E402
from src.constants import YEARS, TOPOLOGY_COLORS  # noqa: E402


COUNTRY_NAMES = {
    "FRA": "France", "USA": "United States", "ITA": "Italy", "GER": "Germany",
    "NED": "Netherlands", "ENG": "England", "TUR": "Turkey", "POR": "Portugal",
    "ESP": "Spain", "SAU": "Saudi Arabia", "BRA": "Brazil", "ARG": "Argentina",
    "BEL": "Belgium", "MEX": "Mexico", "NGA": "Nigeria", "COL": "Colombia",
    "CHI": "Chile", "URU": "Uruguay", "MAR": "Morocco", "SEN": "Senegal",
    "CIV": "Côte d'Ivoire", "GHA": "Ghana", "CMR": "Cameroon", "JPN": "Japan",
    "KOR": "South Korea", "AUT": "Austria", "CRO": "Croatia", "SRB": "Serbia",
    "DEN": "Denmark", "SWE": "Sweden", "NOR": "Norway", "SCO": "Scotland",
    "WAL": "Wales", "RSA": "South Africa",
}


def build_network(club_df, edge_df, layouts) -> dict:
    out = {}
    for yr in YEARS:
        pos = layouts.get(yr, {})
        if not pos:
            continue
        yr_cf = club_df[club_df["year"] == yr]
        yr_edges = edge_df[edge_df["year"] == yr]

        nodes = []
        for _, row in yr_cf.iterrows():
            club = row["club_name"]
            if club not in pos:
                continue
            x, y = pos[club]
            nodes.append({
                "id": club, "x": x, "y": y,
                "topology": row["topology"],
                "revenue": float(row["revenue_eur_m"]),
                "wages": float(row.get("wage_bill_eur_m", 0) or 0),
                "w2r": float(row.get("wages_to_revenue_pct", 0) or 0),
                "op": float(row.get("operating_profit_eur_m", 0) or 0),
                "league": row.get("league", ""),
                "country": row.get("country", ""),
            })

        edges = []
        for _, row in yr_edges.iterrows():
            fc, tc = row["from_club"], row["to_club"]
            if fc not in pos or tc not in pos:
                continue
            age = row.get("age", float("nan"))
            edges.append({
                "from": fc, "to": tc,
                "fee": float(row["fee_eur_m"]),
                "player": row["player_name"],
                "age": int(age) if not np.isnan(age) else 0,
                "pos": row.get("position", ""),
                "path": row["path_type"],
                "prem": float(row.get("maturity_premium") or 0),
                "from_l": str(row.get("from_league", "")).replace("_", " "),
                "to_l": str(row.get("to_league", "")).replace("_", " "),
            })

        out[str(yr)] = {"nodes": nodes, "edges": edges}
    return out


def build_violin(edge_df) -> dict:
    """
    Maturity premium per player, grouped by the topology role of the club
    that received them in their *final* paid transfer — i.e. whichever
    role ultimately captured the matured value.

    intel["maturity_premium"] alone is player-level with no topology
    attached, so this joins through edge_df (which already carries
    to_topo per transfer) instead.
    """
    paid = edge_df[edge_df["fee_eur_m"] > 0].sort_values("year")
    last_transfer = paid.groupby("player_name").tail(1)
    merged = last_transfer[["player_name", "to_topo", "maturity_premium"]].dropna(
        subset=["maturity_premium"]
    )
    positive = merged[merged["maturity_premium"] > 0]
    cap = positive["maturity_premium"].quantile(0.97) if len(positive) else 0

    out = {}
    for topo in TOPOLOGY_COLORS:
        vals = (
            positive[positive["to_topo"] == topo]["maturity_premium"]
            .clip(upper=cap)
            .tolist()
        )
        out[topo] = vals[:200]
    return out


def build_blindspots(intel) -> list:
    bs = intel["blindspots"].head(15)
    return [
        {
            "country": COUNTRY_NAMES.get(c, c),
            "code": c,
            "score": float(row["blindspot_score"]),
            "exports": int(row["total_exports"]),
            "sold_agg": float(row["total_sold_to_agg"]),
        }
        for c, row in bs.iterrows()
    ]


def build_revenue(club_df) -> dict:
    out = {}
    for topo in TOPOLOGY_COLORS:
        grp = (
            club_df[club_df["topology"] == topo]
            .groupby("year")["revenue_eur_m"].mean()
            .reset_index()
        )
        out[topo] = [
            {"year": int(r["year"]), "rev": float(r["revenue_eur_m"])}
            for _, r in grp.iterrows()
        ]
    return out


def build_gen_jumps(edge_df) -> list:
    gj = edge_df[edge_df["path_type"] == "Generational Jump"].dropna(
        subset=["age", "fee_eur_m"]
    )
    return [
        {
            "player": r["player_name"], "age": float(r["age"]),
            "fee": float(r["fee_eur_m"]), "year": int(r["year"]),
            "from": r["from_club"], "to": r["to_club"],
            "pos": r.get("position", ""),
            "from_l": str(r.get("from_league", "")).replace("_", " "),
            "to_l": str(r.get("to_league", "")).replace("_", " "),
        }
        for _, r in gj.iterrows()
    ]


def build_summary(club_df, edge_df, intel, gen_jumps) -> dict:
    mp = intel["maturity_premium"]
    top_players = (
        mp.nlargest(10, "maturity_premium")
        [["player_name", "first_fee", "last_fee", "maturity_premium"]]
        .to_dict("records")
    )
    top_gj = sorted(gen_jumps, key=lambda x: x["fee"], reverse=True)[:10]

    def avg_rev(year, topo):
        sub = club_df[(club_df["year"] == year) & (club_df["topology"] == topo)]
        return float(sub["revenue_eur_m"].mean()) if len(sub) else 0.0

    return {
        "total_transfers": int(len(edge_df)),
        "total_fees": float(edge_df["fee_eur_m"].sum()),
        "avg_fee": float(edge_df["fee_eur_m"].mean()),
        "top_players": top_players,
        "top_gj": top_gj,
        "rev_2010_agg": avg_rev(2010, "Aggregator"),
        "rev_2026_agg": avg_rev(2026, "Aggregator"),
        "rev_2010_inc": avg_rev(2010, "Incubator"),
        "rev_2026_inc": avg_rev(2026, "Incubator"),
        "n_clubs": int(club_df["club_name"].nunique()),
        "years": len(YEARS),
        "gen_jumps": len(gen_jumps),
    }


def main() -> None:
    print("Loading data …")
    data = loader.load(data_dir=str(ROOT))
    club_df, edge_df, intel = engine.build(data)
    layouts = layout.build(club_df, edge_df, YEARS)

    print("Exporting network …")
    network = build_network(club_df, edge_df, layouts)

    print("Exporting intelligence panels …")
    violin = build_violin(edge_df)
    blindspots = build_blindspots(intel)
    revenue = build_revenue(club_df)
    gen_jumps = build_gen_jumps(edge_df)
    summary = build_summary(club_df, edge_df, intel, gen_jumps)

    payload = {
        "network": network,
        "violin": violin,
        "blindspots": blindspots,
        "revenue": revenue,
        "gen_jumps": gen_jumps,
        "summary": summary,
        "years": [str(y) for y in YEARS],
    }

    out_path = ROOT / "assets" / "data" / "dashboard_data.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, allow_nan=False)

    print(f"Wrote {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
