"""
loader.py
---------
Loads the five source CSVs from a directory.
For any file that is absent or unreadable, the corresponding synthetic
table from ``sample_data.generate()`` is substituted transparently.

Column names are normalised (stripped, lowercased, spaces → underscores)
so that downstream code can rely on a stable schema regardless of source.
"""

from __future__ import annotations

import os

import pandas as pd

from . import sample_data

# Maps internal key → expected filename
_FILE_MAP: dict[str, str] = {
    "transfers":        "transfers_history.csv",
    "financials":       "club_financials.csv",
    "market_values":    "player_market_values.csv",
    "record_transfers": "record_transfers.csv",
    "league_metrics":   "league_metrics.csv",
}


def load(data_dir: str = ".") -> dict[str, pd.DataFrame]:
    """
    Load all five CSVs from *data_dir*.

    Parameters
    ----------
    data_dir : path to the directory that contains the CSV files.
               Defaults to the current working directory.

    Returns
    -------
    dict with keys: transfers, financials, market_values,
                    record_transfers, league_metrics
    """
    fallback = sample_data.generate()
    result: dict[str, pd.DataFrame] = {}

    for key, fname in _FILE_MAP.items():
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                print(f"  [✓] {fname}  ({len(df):,} rows)")
                result[key] = df
            except Exception as exc:  # noqa: BLE001
                print(f"  [!] Could not parse {fname}: {exc}  → synthetic fallback")
                result[key] = fallback[key]
        else:
            print(f"  [·] {fname} not found  → synthetic fallback")
            result[key] = fallback[key]

    _normalise_columns(result)
    return result


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalise_columns(data: dict[str, pd.DataFrame]) -> None:
    """Normalise column names in-place: strip whitespace, lowercase, spaces → _."""
    for df in data.values():
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
