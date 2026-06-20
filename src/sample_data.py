"""
sample_data.py
--------------
Generates plausible synthetic football-transfer data that mirrors the
expected CSV schemas.  Used as a fallback when real data files are absent
or as a standalone fixture for unit tests.

All five tables are returned by ``generate()`` in a single dict.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .constants import (
    AGGREGATOR_CLUBS,
    GEN_JUMP_PLAYERS,
    REFINERY_CLUBS,
    YEARS,
)

# ── Club universe ──────────────────────────────────────────────────────────────
_ALL_CLUBS: list[str] = sorted(
    AGGREGATOR_CLUBS
    | REFINERY_CLUBS
    | {
        "Sevilla", "Valencia", "Fiorentina", "Lazio", "Roma",
        "Olympique Marseille", "Stade Rennais", "Eintracht Frankfurt",
        "Wolfsburg", "Borussia Monchengladbach", "Athletic Bilbao",
        "Real Sociedad", "Real Betis", "Feyenoord",
        "Tottenham", "Arsenal", "Aston Villa", "Newcastle United",
        "West Ham", "Everton", "AC Milan",
    }
)

_LEAGUES: dict[str, str] = {
    "Real Madrid": "La_Liga",        "FC Barcelona": "La_Liga",
    "Atletico Madrid": "La_Liga",    "Valencia": "La_Liga",
    "Sevilla": "La_Liga",            "Athletic Bilbao": "La_Liga",
    "Real Sociedad": "La_Liga",      "Real Betis": "La_Liga",
    "Manchester City": "Premier_League",
    "Manchester United": "Premier_League",
    "Liverpool": "Premier_League",   "Chelsea": "Premier_League",
    "Arsenal": "Premier_League",     "Tottenham": "Premier_League",
    "Aston Villa": "Premier_League", "Newcastle United": "Premier_League",
    "West Ham": "Premier_League",    "Everton": "Premier_League",
    "Bayern Munich": "Bundesliga",   "Borussia Dortmund": "Bundesliga",
    "RB Leipzig": "Bundesliga",      "Bayer Leverkusen": "Bundesliga",
    "Eintracht Frankfurt": "Bundesliga",
    "Wolfsburg": "Bundesliga",       "Borussia Monchengladbach": "Bundesliga",
    "Paris Saint-Germain": "Ligue_1","AS Monaco": "Ligue_1",
    "Olympique Lyonnais": "Ligue_1", "Olympique Marseille": "Ligue_1",
    "Lille": "Ligue_1",              "Stade Rennais": "Ligue_1",
    "Juventus": "Serie_A",           "Inter Milan": "Serie_A",
    "Napoli": "Serie_A",             "AC Milan": "Serie_A",
    "Roma": "Serie_A",               "Lazio": "Serie_A",
    "Fiorentina": "Serie_A",         "Atalanta": "Serie_A",
    "Ajax": "Eredivisie",            "PSV Eindhoven": "Eredivisie",
    "Feyenoord": "Eredivisie",
    "Porto": "Primeira_Liga",        "Benfica": "Primeira_Liga",
    "Sporting CP": "Primeira_Liga",
}

_COUNTRY_BY_LEAGUE: dict[str, str] = {
    "Premier_League": "ENG", "La_Liga": "ESP",
    "Bundesliga": "GER",     "Ligue_1": "FRA",
    "Serie_A": "ITA",        "Eredivisie": "NED",
    "Primeira_Liga": "POR",
}

_BASE_REVENUES: dict[str, int] = {
    "Real Madrid": 800,         "FC Barcelona": 750,
    "Manchester City": 720,     "Manchester United": 680,
    "Paris Saint-Germain": 650, "Bayern Munich": 700,
    "Liverpool": 600,           "Chelsea": 560,
    "Juventus": 400,            "Atletico Madrid": 350,
}


def _club_league(club: str) -> str:
    return _LEAGUES.get(club, "Other")


def _club_country(club: str) -> str:
    return _COUNTRY_BY_LEAGUE.get(_club_league(club), "OTH")


# ── Public API ─────────────────────────────────────────────────────────────────

def generate(seed: int = 42, n_transfers: int = 2_000) -> dict[str, pd.DataFrame]:
    """
    Return a dict with keys:
        transfers, financials, market_values, record_transfers, league_metrics

    Parameters
    ----------
    seed        : random seed for reproducibility
    n_transfers : number of synthetic transfer rows to generate
    """
    rng = np.random.default_rng(seed)
    return {
        "transfers":        _transfers(rng, n_transfers),
        "financials":       _financials(rng),
        "market_values":    _market_values(rng),
        "record_transfers": _record_transfers(rng),
        "league_metrics":   _league_metrics(rng),
    }


# ── Private builders ───────────────────────────────────────────────────────────

def _transfers(rng: np.random.Generator, n: int) -> pd.DataFrame:
    positions = ["GK", "CB", "LB", "RB", "DM", "CM", "AM", "LW", "RW", "FW", "SS"]
    rows = []
    for i in range(n):
        yr  = int(rng.integers(YEARS[0], YEARS[-1] + 1))
        age = int(rng.integers(16, 35))
        fc  = _ALL_CLUBS[int(rng.integers(0, len(_ALL_CLUBS)))]
        tc  = _ALL_CLUBS[int(rng.integers(0, len(_ALL_CLUBS)))]
        while tc == fc:
            tc = _ALL_CLUBS[int(rng.integers(0, len(_ALL_CLUBS)))]
        fee  = float(round(rng.exponential(20), 2))
        rows.append({
            "transfer_id":      f"T{i:06d}",
            "year":             yr,
            "date":             f"{yr}-07-01",
            "season":           f"{yr}-{yr + 1}",
            "transfer_window":  "summer" if rng.random() > 0.3 else "winter",
            "player_name":      f"Player {i}",
            "position":         positions[int(rng.integers(0, len(positions)))],
            "age":              age,
            "from_club":        fc,
            "from_league":      _club_league(fc),
            "from_country":     _club_country(fc),
            "to_club":          tc,
            "to_league":        _club_league(tc),
            "to_country":       _club_country(tc),
            "fee_eur_m":        fee,
            "is_free_transfer": 1 if fee < 0.5 else 0,
            "is_loan":          1 if rng.random() < 0.15 else 0,
            "is_intra_league":  1 if _club_league(fc) == _club_league(tc) else 0,
            "is_intra_country": 1 if _club_country(fc) == _club_country(tc) else 0,
        })
    return pd.DataFrame(rows)


def _financials(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for club in _ALL_CLUBS:
        base = _BASE_REVENUES.get(club, int(rng.integers(50, 300)))
        for yr in YEARS:
            growth = 1.0 + 0.06 * (yr - YEARS[0]) + float(rng.normal(0, 0.03))
            rev    = max(10.0, round(base * growth, 1))
            rows.append({
                "year":                    yr,
                "club_name":               club,
                "league":                  _club_league(club),
                "country":                 _club_country(club),
                "stadium_capacity":        int(rng.integers(20_000, 90_000)),
                "revenue_eur_m":           rev,
                "wage_bill_eur_m":         round(rev * float(rng.uniform(0.4, 0.65)), 1),
                "wages_to_revenue_pct":    round(float(rng.uniform(38, 70)), 1),
                "net_transfer_spend_eur_m": round(float(rng.normal(0, 40)), 1),
                "operating_profit_eur_m":  round(float(rng.normal(10, 30)), 1),
            })
    return pd.DataFrame(rows)


def _market_values(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for player in GEN_JUMP_PLAYERS:
        peak = int(rng.integers(2015, 2023))
        for yr in YEARS:
            dist = abs(yr - peak)
            val  = max(5.0, 180 * math.exp(-0.18 * dist) + float(rng.normal(0, 5)))
            rows.append({
                "year":               yr,
                "player_name":        player,
                "age":                17 + (yr - YEARS[0]),
                "position":           "FW",
                "market_value_eur_m": round(val, 1),
                "is_peak_year":       1 if yr == peak else 0,
            })
    return pd.DataFrame(rows)


def _record_transfers(rng: np.random.Generator, n: int = 40) -> pd.DataFrame:
    agg_list = list(AGGREGATOR_CLUBS)
    years    = rng.integers(YEARS[0], YEARS[-1] + 1, n)
    rows = []
    for i, yr in enumerate(years):
        rows.append({
            "transfer_id":    f"R{i:03d}",
            "date":           f"{int(yr)}-07-01",
            "year":           int(yr),
            "season":         f"{int(yr)}-{int(yr) + 1}",
            "player_name":    f"RecordStar {i}",
            "position":       "FW",
            "age_at_transfer": int(rng.integers(18, 28)),
            "from_club":      _ALL_CLUBS[int(rng.integers(0, len(_ALL_CLUBS)))],
            "to_club":        agg_list[int(rng.integers(0, len(agg_list)))],
            "fee_eur_m":      round(float(rng.uniform(80, 250)), 1),
            "is_free_transfer": 0,
            "is_loan":        0,
            "is_extension":   0,
        })
    return pd.DataFrame(rows)


def _league_metrics(rng: np.random.Generator) -> pd.DataFrame:
    config = [
        ("Premier_League", "ENG", 20, 2_500),
        ("La_Liga",        "ESP", 20, 2_000),
        ("Bundesliga",     "GER", 18, 1_600),
        ("Ligue_1",        "FRA", 20, 1_100),
        ("Serie_A",        "ITA", 20, 1_200),
        ("Eredivisie",     "NED", 18,   400),
        ("Primeira_Liga",  "POR", 18,   300),
    ]
    rows = []
    for lg, co, n_teams, base_rev in config:
        for yr in YEARS:
            rows.append({
                "year":                yr,
                "league":              lg,
                "country":             co,
                "num_teams":           n_teams,
                "total_revenue_eur_m": round(base_rev * (1 + 0.05 * (yr - YEARS[0])), 0),
                "avg_attendance":      int(rng.integers(20_000, 55_000)),
                "avg_ticket_eur":      int(rng.integers(30, 120)),
                "foreign_players_pct": int(rng.integers(40, 75)),
            })
    return pd.DataFrame(rows)
