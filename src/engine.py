"""
engine.py
---------
The data-processing core of the Football Recruitment Ecosystem.

Three public functions:

    classify_topology(club, youth_share, refine_ratio, revenue_rank)
        → "Incubator" | "Refinery" | "Aggregator"

    build(data) → (club_df, edge_df, intel)
        Full pipeline: merge tables, classify clubs, flag career path types,
        compute maturity premiums and scouting blindspots.

    ──────────────────────────────────────────────
    club_df columns (one row per club × year):
        year, club_name, league, country, revenue_eur_m, …,
        topology, youth_out_share, refine_ratio

    edge_df columns (one row per non-loan paid transfer):
        …all transfer columns…, from_topo, to_topo,
        path_type, maturity_premium, first_fee, last_fee

    intel keys:
        blindspots        – DataFrame indexed by country
        maturity_premium  – DataFrame indexed by player_name
    ──────────────────────────────────────────────
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import AGGREGATOR_CLUBS, GEN_JUMP_PLAYERS, REFINERY_CLUBS


# ══════════════════════════════════════════════════════════════════════════════
# Topology classification
# ══════════════════════════════════════════════════════════════════════════════

def classify_topology(
    club: str,
    youth_out_share: float,
    refine_ratio: float,
    revenue_rank: int,  # noqa: ARG001  (kept for future heuristic use)
    refine_ratio_threshold: float = 0.30,
) -> str:
    """
    Assign one of three topology roles to a club.

    Hard-coded membership in AGGREGATOR_CLUBS / REFINERY_CLUBS always wins.
    For unknown clubs:

    1. refine_ratio > refine_ratio_threshold  →  Refinery
    2. otherwise                              →  Incubator

    refine_ratio_threshold defaults to 0.30 but is recalibrated per-dataset
    in build() (see _refine_ratio_threshold) so the heuristic actually
    produces a real 3-way split instead of every non-hard-coded club
    collapsing into Refinery when refine_ratio happens to run high
    across the board (as it does for synthetic / generated datasets).
    """
    if club in AGGREGATOR_CLUBS:
        return "Aggregator"
    if club in REFINERY_CLUBS:
        return "Refinery"
    if refine_ratio > refine_ratio_threshold:
        return "Refinery"
    return "Incubator"


# ══════════════════════════════════════════════════════════════════════════════
# Main pipeline
# ══════════════════════════════════════════════════════════════════════════════

def build(
    data: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Run the full data engine.

    Parameters
    ----------
    data : dict returned by ``loader.load()``

    Returns
    -------
    club_df, edge_df, intel  (see module docstring for schemas)
    """
    th = data["transfers"].copy()
    cf = data["financials"].copy()

    _coerce_numerics(th, cf)

    # ── Topology signals ─────────────────────────────────────────────────────
    youth_share  = _youth_out_share(th)
    refine_ratio = _refine_ratio(th)
    rev_rank     = cf.groupby("club_name")["revenue_eur_m"].mean() \
                     .rank(ascending=False).astype(int)

    # ── Club × year table ────────────────────────────────────────────────────
    club_df = cf.merge(
        youth_share.reset_index().rename(columns={"from_club": "club_name"}),
        on="club_name", how="left",
    ).merge(
        refine_ratio.reset_index().rename(columns={"from_club": "club_name"}),
        on="club_name", how="left",
    )
    club_df[["youth_out_share", "refine_ratio"]] = (
        club_df[["youth_out_share", "refine_ratio"]].fillna(0)
    )

    # The fixed 0.30 refine_ratio threshold can saturate for some datasets
    # (every non-hard-coded club scores above it, leaving zero Incubators).
    # Recalibrate to the median refine_ratio among clubs that aren't already
    # hard-coded into AGGREGATOR_CLUBS / REFINERY_CLUBS, so roughly half of
    # the *unclassified* pool lands on each side — a genuine 3-way split
    # rather than a heuristic that only ever fires one way.
    threshold = _refine_ratio_threshold(club_df, refine_ratio)

    rank_series = rev_rank.reindex(club_df["club_name"]).values
    club_df["topology"] = [
        classify_topology(r.club_name, r.youth_out_share, r.refine_ratio, rv, threshold)
        for r, rv in zip(club_df.itertuples(index=False), rank_series)
    ]

    # ── Edge table ───────────────────────────────────────────────────────────
    topo_map = club_df.groupby("club_name")["topology"].first().to_dict()
    edge_df  = _build_edges(th, topo_map)

    # ── Market intelligence ──────────────────────────────────────────────────
    intel = {
        "blindspots":      _scouting_blindspots(th),
        "maturity_premium": _maturity_premiums(th),
    }

    return club_df, edge_df, intel


# ══════════════════════════════════════════════════════════════════════════════
# Private helpers
# ══════════════════════════════════════════════════════════════════════════════

def _coerce_numerics(th: pd.DataFrame, cf: pd.DataFrame) -> None:
    """Cast key columns to numeric in-place, filling NaN with 0."""
    for col in ("year", "age", "fee_eur_m", "is_loan", "is_free_transfer"):
        if col in th.columns:
            th[col] = pd.to_numeric(th[col], errors="coerce").fillna(0)
    for col in ("year", "revenue_eur_m"):
        if col in cf.columns:
            cf[col] = pd.to_numeric(cf[col], errors="coerce").fillna(0)


def _refine_ratio_threshold(club_df: pd.DataFrame, refine_ratio: pd.Series) -> float:
    """
    Pick a refine_ratio cutoff that actually splits the *unclassified* club
    pool (i.e. clubs not already hard-coded into AGGREGATOR_CLUBS or
    REFINERY_CLUBS) into Refinery vs Incubator roughly evenly, using the
    median as the cutoff.

    Falls back to the original fixed 0.30 threshold if there are too few
    unclassified clubs to compute a meaningful median (e.g. small or
    fully hard-coded datasets).
    """
    unclassified = (
        club_df.drop_duplicates("club_name")["club_name"]
        .loc[lambda s: ~s.isin(AGGREGATOR_CLUBS) & ~s.isin(REFINERY_CLUBS)]
    )
    vals = refine_ratio.reindex(unclassified).dropna()
    if len(vals) < 4:
        return 0.30
    return float(vals.median())


def _youth_out_share(th: pd.DataFrame) -> pd.Series:
    """Fraction of outbound non-loan transfers that involve players aged < 21."""
    mask_non_loan = th["is_loan"] == 0
    youth_out = (
        th[mask_non_loan & (th["age"] < 21)]
        .groupby("from_club").size()
    )
    total_out = th[mask_non_loan].groupby("from_club").size().replace(0, np.nan)
    return (youth_out / total_out).fillna(0).rename("youth_out_share")


def _refine_ratio(th: pd.DataFrame) -> pd.Series:
    """
    Proxy refine ratio:  number of above-median-fee sales to Aggregators
    divided by the number of sub-21 arrivals (+ 1 to avoid div-by-zero).
    """
    med_fee   = th["fee_eur_m"].median()
    to_agg    = th[th["to_club"].isin(AGGREGATOR_CLUBS) & (th["is_loan"] == 0)]
    refine_in = th[th["age"] < 21].groupby("to_club").size().rename("refine_in")
    refine_out = (
        to_agg[to_agg["fee_eur_m"] > med_fee]
        .groupby("from_club").size()
        .rename("refine_out")
    )
    denominator = (refine_in.reindex(refine_out.index) + 1).replace(0, np.nan)
    return (refine_out / denominator).fillna(0).clip(0, 1).rename("refine_ratio")


def _path_type(row: pd.Series) -> str:
    """
    Label a transfer as 'Generational Jump' or 'Standard Lifecycle'.

    Generational Jump conditions (any one sufficient):
      • Player is in the known GEN_JUMP_PLAYERS superstar set.
      • Age <= 22 AND fee >= 40 M AND destination is an Aggregator.
        (elite youth arriving at a superclub for serious money)

    The old heuristic (any Incubator->Aggregator move) produced thousands of
    false positives. Requiring both an age cap AND a meaningful fee threshold
    ensures only genuinely exceptional moves are flagged.
    """
    if row["player_name"] in GEN_JUMP_PLAYERS:
        return "Generational Jump"
    if (row["age"] <= 22
            and row["fee_eur_m"] >= 40
            and row["to_topo"] == "Aggregator"):
        return "Generational Jump"
    return "Standard Lifecycle"


def _build_edges(th: pd.DataFrame, topo_map: dict[str, str]) -> pd.DataFrame:
    """Filter to paid non-loan transfers and annotate with path type + premiums."""
    edge_df = th[(th["is_loan"] == 0) & (th["fee_eur_m"] > 0)].copy()
    edge_df["from_topo"] = edge_df["from_club"].map(topo_map).fillna("Incubator")
    edge_df["to_topo"]   = edge_df["to_club"].map(topo_map).fillna("Incubator")
    edge_df["path_type"] = edge_df.apply(_path_type, axis=1)

    premiums = _maturity_premiums(th)
    edge_df  = edge_df.merge(
        premiums[["player_name", "maturity_premium", "first_fee", "last_fee"]],
        on="player_name", how="left",
    )
    return edge_df


def _maturity_premiums(th: pd.DataFrame) -> pd.DataFrame:
    """
    For each player, compute the delta between the last known transfer fee
    (typically paid by an Aggregator) and the first known fee (Incubator cost).
    Delta is clipped at 0 — we only care about positive premiums.
    """
    paid = th[(th["is_loan"] == 0) & (th["fee_eur_m"] > 0)].sort_values("year")
    agg  = (
        paid.groupby("player_name")
        .agg(
            first_fee=("fee_eur_m", "first"),
            last_fee=("fee_eur_m",  "last"),
            n_transfers=("fee_eur_m", "count"),
        )
        .reset_index()
    )
    agg["maturity_premium"] = (agg["last_fee"] - agg["first_fee"]).clip(lower=0)
    return agg


def _scouting_blindspots(th: pd.DataFrame) -> pd.DataFrame:
    """
    Countries that export a lot of talent but have low direct recruitment
    by Aggregator clubs.

    blindspot_score = total_exports / (total_sold_to_aggregators + 1)
    High score → lots of supply, little Aggregator attention.
    """
    if "from_country" not in th.columns:
        return pd.DataFrame()

    sold_to_agg = (
        th[th["to_club"].isin(AGGREGATOR_CLUBS)]
        .groupby("from_country")["fee_eur_m"]
        .sum()
        .rename("total_sold_to_agg")
    )
    total_exports = (
        th[th["is_loan"] == 0]
        .groupby("from_country")["fee_eur_m"]
        .count()
        .rename("total_exports")
    )
    df = pd.concat([sold_to_agg, total_exports], axis=1).fillna(0)
    df["blindspot_score"] = df["total_exports"] / (df["total_sold_to_agg"] + 1)
    return df.sort_values("blindspot_score", ascending=False)
