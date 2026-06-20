"""
tests/test_engine.py
--------------------
Unit tests for the data engine (topology, path types, market intelligence).
Run with:  pytest tests/
"""

from __future__ import annotations

import pandas as pd
import pytest

# Make the src package importable from the project root
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import engine, sample_data
from src.constants import AGGREGATOR_CLUBS, REFINERY_CLUBS


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def synthetic_data():
    return sample_data.generate(seed=0, n_transfers=500)


@pytest.fixture(scope="module")
def built(synthetic_data):
    club_df, edge_df, intel = engine.build(synthetic_data)
    return club_df, edge_df, intel


# ── classify_topology ──────────────────────────────────────────────────────────

class TestClassifyTopology:
    def test_aggregator_hard_coded(self):
        for club in AGGREGATOR_CLUBS:
            assert engine.classify_topology(club, 0.1, 0.1, 1) == "Aggregator"

    def test_refinery_hard_coded(self):
        for club in REFINERY_CLUBS:
            assert engine.classify_topology(club, 0.1, 0.1, 5) == "Refinery"

    def test_unknown_high_refine_ratio(self):
        assert engine.classify_topology("UnknownFC", 0.2, 0.5, 10) == "Refinery"

    def test_unknown_high_youth_share(self):
        assert engine.classify_topology("UnknownFC", 0.6, 0.1, 10) == "Incubator"

    def test_unknown_default_incubator(self):
        assert engine.classify_topology("UnknownFC", 0.1, 0.1, 10) == "Incubator"


# ── build() output shapes ──────────────────────────────────────────────────────

class TestBuildOutputs:
    def test_club_df_has_topology(self, built):
        club_df, _, _ = built
        assert "topology" in club_df.columns

    def test_topology_values_valid(self, built):
        club_df, _, _ = built
        valid = {"Incubator", "Refinery", "Aggregator"}
        assert set(club_df["topology"].unique()).issubset(valid)

    def test_edge_df_has_path_type(self, built):
        _, edge_df, _ = built
        assert "path_type" in edge_df.columns

    def test_path_type_values_valid(self, built):
        _, edge_df, _ = built
        valid = {"Standard Lifecycle", "Generational Jump"}
        assert set(edge_df["path_type"].unique()).issubset(valid)

    def test_edge_df_no_loans(self, built):
        _, edge_df, _ = built
        assert (edge_df["is_loan"] == 0).all()

    def test_edge_df_no_zero_fees(self, built):
        _, edge_df, _ = built
        assert (edge_df["fee_eur_m"] > 0).all()

    def test_maturity_premium_non_negative(self, built):
        _, _, intel = built
        mp = intel["maturity_premium"]["maturity_premium"].dropna()
        assert (mp >= 0).all()

    def test_blindspot_score_non_negative(self, built):
        _, _, intel = built
        bs = intel["blindspots"]
        if not bs.empty:
            assert (bs["blindspot_score"] >= 0).all()


# ── Aggregator clubs are always classified correctly ───────────────────────────

class TestAggregatorTopology:
    def test_known_aggregators_in_output(self, built):
        club_df, _, _ = built
        agg_in_data = (
            club_df[club_df["club_name"].isin(AGGREGATOR_CLUBS)]["topology"].unique()
        )
        # Every Aggregator that appears in the data must be classified correctly
        assert set(agg_in_data) == {"Aggregator"} or len(agg_in_data) == 0
