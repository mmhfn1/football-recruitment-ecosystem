"""
layout.py
---------
Computes a force-directed (spring) layout for every year in the timeline.

Aggregator clubs are pinned in a fixed ring around the origin so they
act as "gravity wells" that draw other clubs toward them — the spring
constant k is scaled inversely with average revenue so richer years
produce tighter clustering.

Public API
----------
    build(club_df, edge_df, years) → dict[int, dict[str, tuple[float, float]]]
"""

from __future__ import annotations

import math

import networkx as nx
import numpy as np
import pandas as pd

from .constants import (
    AGGREGATOR_RING_R,
    K_SCALE,
    LAYOUT_ITERATIONS,
)


def build(
    club_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    years: list[int],
) -> dict[int, dict[str, tuple[float, float]]]:
    """
    Compute a spring layout for each year.

    Parameters
    ----------
    club_df : club × year financial table (must have columns: year, club_name, topology)
    edge_df : transfer edge table (must have: year, from_club, to_club, fee_eur_m)
    years   : ordered list of years to process

    Returns
    -------
    dict mapping year → {club_name: (x, y)}
    """
    print(f"  Computing layouts for {len(years)} years …")
    layouts: dict[int, dict[str, tuple[float, float]]] = {}

    for yr in years:
        pos = _layout_for_year(club_df, edge_df, yr)
        if pos:
            layouts[yr] = pos

    print(f"  Done — {len(layouts)} year-layouts ready.")
    return layouts


# ── Private ────────────────────────────────────────────────────────────────────

def _layout_for_year(
    club_df: pd.DataFrame,
    edge_df: pd.DataFrame,
    yr: int,
) -> dict[str, tuple[float, float]]:
    yr_clubs = club_df[club_df["year"] == yr]["club_name"].unique()
    if len(yr_clubs) == 0:
        return {}

    G = _build_graph(yr_clubs, edge_df[edge_df["year"] == yr])

    topo_map = (
        club_df[club_df["year"] == yr]
        .set_index("club_name")["topology"]
        .to_dict()
    )
    fixed_pos = _aggregator_ring(yr_clubs, topo_map)

    k_val = _spring_constant(club_df, yr)

    try:
        pos = nx.spring_layout(
            G,
            k=k_val,
            seed=yr,
            pos=fixed_pos,
            fixed=list(fixed_pos.keys()),
            iterations=LAYOUT_ITERATIONS,
            weight="weight",
        )
    except Exception:  # noqa: BLE001
        pos = nx.circular_layout(G)

    return {c: (float(v[0]), float(v[1])) for c, v in pos.items()}


def _build_graph(clubs: np.ndarray, yr_edges: pd.DataFrame) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(clubs)
    club_set = set(clubs)
    for _, row in yr_edges.iterrows():
        fc, tc = row["from_club"], row["to_club"]
        if fc in club_set and tc in club_set:
            G.add_edge(fc, tc, weight=max(float(row["fee_eur_m"]), 0.1))
    return G


def _aggregator_ring(
    clubs: np.ndarray,
    topo_map: dict[str, str],
) -> dict[str, tuple[float, float]]:
    """Pin Aggregator clubs in a circle at radius AGGREGATOR_RING_R."""
    agg_clubs = [c for c in clubs if topo_map.get(c) == "Aggregator"]
    n = max(len(agg_clubs), 1)
    return {
        c: (
            AGGREGATOR_RING_R * math.cos(2 * math.pi * i / n),
            AGGREGATOR_RING_R * math.sin(2 * math.pi * i / n),
        )
        for i, c in enumerate(agg_clubs)
    }


def _spring_constant(club_df: pd.DataFrame, yr: int) -> float:
    """k inversely proportional to average revenue — richer years pull harder."""
    avg_rev = club_df[club_df["year"] == yr]["revenue_eur_m"].mean()
    return max(0.5, K_SCALE / max(avg_rev / 100, 1))
