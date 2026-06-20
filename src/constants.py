"""
constants.py
------------
Central registry of colours, club taxonomy sets, and configuration
used across every module.  Edit this file to reclassify clubs or
tweak the cyberpunk palette without touching any other code.
"""

# ── Timeline ──────────────────────────────────────────────────────────────────
YEARS: list[int] = list(range(2010, 2027))

# ── Cyberpunk colour palette ──────────────────────────────────────────────────
COLORS: dict[str, str] = {
    "bg":            "#05060F",   # deep-space black
    "grid":          "#0D1120",   # subtle grid lines
    "text":          "#E0E8FF",   # primary label text
    "subtext":       "#6A7BAA",   # secondary / muted text
    "incubator":     "#00F5FF",   # cyan  — Incubator nodes
    "refinery":      "#FFB800",   # amber — Refinery nodes
    "aggregator":    "#FF2D78",   # magenta — Aggregator nodes
    "edge_standard": "#3A7FFF",   # electric blue (dashed, Standard Lifecycle)
    "edge_gen_jump": "#FF2D78",   # magenta neon  (solid, Generational Jump)
    "edge_loan":     "#44FF99",   # mint          (loan moves, unused by default)
    "highlight":     "#FFFFFF",
    "panel":         "#0A0E1F",   # tooltip / legend background
}

TOPOLOGY_COLORS: dict[str, str] = {
    "Incubator":  COLORS["incubator"],
    "Refinery":   COLORS["refinery"],
    "Aggregator": COLORS["aggregator"],
}

# ── Club taxonomy ─────────────────────────────────────────────────────────────
# Hard-coded sets override heuristics; add / remove names here to reclassify.

AGGREGATOR_CLUBS: set[str] = {
    "Real Madrid", "FC Barcelona", "Manchester City",
    "Manchester United", "Paris Saint-Germain", "Bayern Munich",
    "Liverpool", "Chelsea", "Juventus",
}

REFINERY_CLUBS: set[str] = {
    "Borussia Dortmund", "Ajax", "Porto", "Benfica", "Sporting CP",
    "RB Leipzig", "Atletico Madrid", "Napoli", "Inter Milan",
    "AS Monaco", "Lille", "Bayer Leverkusen", "Atalanta",
    "Olympique Lyonnais", "PSV Eindhoven",
}

# ── Generational-star name list ───────────────────────────────────────────────
# Players in this set always receive the "Generational Jump" path type,
# regardless of age or fee heuristics.
GEN_JUMP_PLAYERS: set[str] = {
    "Lionel Messi",
    "Cristiano Ronaldo",
    "Kylian Mbappé", "Kylian Mbappe",
    "Neymar",
    "Erling Haaland",
    "Pedri",
    "Gavi",
    "Jude Bellingham",
    "Vinicius Junior",
    "Rodrygo",
    "Endrick",
    "Lamine Yamal",
    "Arda Güler", "Arda Guler",
    "Florian Wirtz",
}

# ── Layout tuning ─────────────────────────────────────────────────────────────
LAYOUT_ITERATIONS: int  = 80    # spring-layout iterations per year
AGGREGATOR_RING_R: float = 0.3  # radial distance for gravity-well anchors
K_SCALE: float           = 2.0  # spring constant numerator (higher = looser)

# ── Visual scaling ────────────────────────────────────────────────────────────
NODE_SIZE_MIN:  float = 8.0
NODE_SIZE_MAX:  float = 42.0
EDGE_WIDTH_MIN: float = 0.4
EDGE_WIDTH_MAX: float = 5.0
HALO_SCALE:     float = 2.2   # halo radius relative to node radius
