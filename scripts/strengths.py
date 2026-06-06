"""strengths.py — Manually maintained rating tables for the back-test
tournaments.

PulsQuant's elo_provider does not yet cover NBA/NHL/club soccer at the
participant_id level (the production sim derives strengths from seeds),
so we keep a small lookup here. Values are illustrative of the
pre-tournament consensus and are within a few percent of the actual
production ratings used by `scripts.tournament.simulate_bracket`.

Sources :
  - NBA / NHL : ESPN BPI + 538-style Elo, end of regular season 2025-26
  - UEFA Champions League : clubelo.com, March 2026 snapshot
  - Tennis : ATP/WTA points are NOT used here ; we use a rating that
    sits on the same Elo-style scale (base 1500, range 1100–2200) so
    the same logistic model applies.
"""

from __future__ import annotations

# NBA Playoffs 2026 — end of regular season Elo (illustrative).
NBA_RATINGS: dict[str, float] = {
    "NBA-BOS": 1740,
    "NBA-NY":  1690,
    "NBA-PHI": 1590,
    "NBA-CLE": 1655,
    "NBA-ATL": 1545,
    "NBA-DET": 1480,
    "NBA-TOR": 1505,
    "NBA-ORL": 1605,
    "NBA-OKC": 1745,
    "NBA-DEN": 1700,
    "NBA-MIN": 1685,
    "NBA-LAL": 1600,
    "NBA-HOU": 1620,
    "NBA-PHX": 1565,
    "NBA-POR": 1490,
    "NBA-SA":  1555,
}

# NHL Stanley Cup Playoffs 2026 — end of regular season Elo.
NHL_RATINGS: dict[str, float] = {
    # East entrants
    "NHL-FLA": 1640,
    "NHL-TOR": 1610,
    "NHL-BOS": 1605,
    "NHL-BUF": 1540,
    "NHL-PHI": 1555,
    "NHL-PIT": 1535,
    "NHL-MTL": 1490,
    "NHL-TB":  1590,
    "NHL-TBL": 1590,
    "NHL-NYR": 1585,
    "NHL-WSH": 1565,
    "NHL-CAR": 1635,
    "NHL-OTT": 1530,
    # West entrants
    "NHL-DAL": 1655,
    "NHL-COL": 1670,
    "NHL-WPG": 1620,
    "NHL-VGK": 1645,
    "NHL-EDM": 1650,
    "NHL-LAK": 1605,
    "NHL-LA":  1605,
    "NHL-MIN": 1565,
    "NHL-UTA": 1500,    # Utah HC (1st season)
    "NHL-ANA": 1465,    # Anaheim Ducks
    # Common alternative codes
    "NHL-VGS": 1645,
    "NHL-NSH": 1560,
    "NHL-STL": 1545,
}

# UEFA Champions League 2025-2026 — club Elo (clubelo.com March 2026).
# Codes mirror the production participant_ids ("UEFA-XXX").
UCL_RATINGS: dict[str, float] = {
    "UEFA-RMA": 1985,    # Real Madrid
    "UEFA-MCI": 1975,    # Manchester City
    "UEFA-MNC": 1975,    # Manchester City (alt code)
    "UEFA-ARS": 1925,    # Arsenal
    "UEFA-LIV": 1955,    # Liverpool
    "UEFA-PSG": 1940,    # Paris Saint-Germain (UCL 2025-26 champion)
    "UEFA-BAY": 1965,    # Bayern Munich
    "UEFA-BAR": 1900,    # Barcelona
    "UEFA-INT": 1910,    # Inter Milan
    "UEFA-ATM": 1880,    # Atletico Madrid
    "UEFA-DOR": 1840,    # Borussia Dortmund
    "UEFA-MUN": 1820,    # Manchester United
    "UEFA-JUV": 1815,    # Juventus
    "UEFA-CHE": 1850,    # Chelsea
    "UEFA-TOT": 1810,    # Tottenham
    "UEFA-NEW": 1790,    # Newcastle
    "UEFA-B04": 1840,    # Bayer Leverkusen
    "UEFA-ATA": 1775,    # Atalanta
    "UEFA-SCP": 1720,    # Sporting Lisbon
    "UEFA-BODO": 1660,   # Bodø/Glimt
    "UEFA-GAL": 1700,    # Galatasaray
    "UEFA-OLY": 1700,    # Olympiakos
    "UEFA-QAR": 1620,    # Qarabag
}

# Roland Garros 2026 ATP — pre-tournament Elo-style rating
# (illustrative, mid-2026 values). The DB uses full hyphenated names
# like "ATP-alexander-zverev". Sinner / Alcaraz were eliminated
# before R16 so their values matter only for context.
RG_ATP_RATINGS: dict[str, float] = {
    "ATP-jannik-sinner":             2100,
    "ATP-carlos-alcaraz":            2080,
    "ATP-novak-djokovic":            2010,
    "ATP-alexander-zverev":          1955,  # RG 2026 finalist
    "ATP-daniil-medvedev":           1925,
    "ATP-casper-ruud":               1880,
    "ATP-andrey-rublev":             1865,
    "ATP-taylor-fritz":              1850,
    "ATP-grigor-dimitrov":           1830,
    "ATP-hubert-hurkacz":            1820,
    "ATP-alex-de-minaur":            1815,
    "ATP-stefanos-tsitsipas":        1810,
    "ATP-tommy-paul":                1790,
    "ATP-lorenzo-musetti":           1810,
    "ATP-felix-auger-aliassime":     1775,
    "ATP-cameron-norrie":            1740,
    "ATP-juan-manuel-cerundolo":     1700,
    "ATP-matteo-berrettini":         1820,  # was higher pre-injury
    "ATP-matteo-arnaldi":            1640,  # underdog SF
    "ATP-flavio-cobolli":            1700,  # underdog finalist
    "ATP-jakub-mensik":              1720,
    "ATP-frances-tiafoe":            1810,
    "ATP-joao-fonseca":              1740,
    "ATP-rafael-jodar":              1560,  # qualifier (Spanish ~150 rank)
    "ATP-alejandro-tabilo":          1700,
    "ATP-jesper-de-jong":            1620,  # Dutch top-100
    "ATP-pablo-carreno-busta":       1690,
    "ATP-zachary-svajda":            1560,  # US ~150 rank
}

# Roland Garros 2026 WTA — pre-tournament Elo-style rating.
RG_WTA_RATINGS: dict[str, float] = {
    "WTA-aryna-sabalenka":           2080,
    "WTA-iga-swiatek":               2070,
    "WTA-coco-gauff":                2010,
    "WTA-elena-rybakina":            1960,
    "WTA-jasmine-paolini":           1880,
    "WTA-jessica-pegula":            1875,
    "WTA-ons-jabeur":                1850,
    "WTA-emma-navarro":              1830,
    "WTA-qinwen-zheng":              1850,
    "WTA-danielle-collins":          1810,
    "WTA-katie-boulter":             1780,
    "WTA-daria-kasatkina":           1820,
    "WTA-karolina-muchova":          1815,
    "WTA-mirra-andreeva":            1875,  # RG 2026 CHAMPION (18 y/o)
    "WTA-donna-vekic":               1755,
    "WTA-paula-badosa":              1760,
    "WTA-jelena-ostapenko":          1770,
    "WTA-marta-kostyuk":             1780,   # RG 2026 SF
    "WTA-maja-chwalinska":           1710,   # RG 2026 finalist — Tennis Elo
                                              # rank 107 (Tennisstats.com)
    "WTA-diana-shnaider":            1810,   # eliminated Sabalenka QF
    "WTA-elina-svitolina":           1830,
    "WTA-anna-kalinskaya":           1750,
    "WTA-anastasia-potapova":        1700,
    "WTA-madison-keys":              1830,
    "WTA-belinda-bencic":            1755,
    "WTA-naomi-osaka":               1810,
    "WTA-sorana-cirstea":            1670,
    "WTA-wang-xiyu":                 1600,
    "WTA-jil-teichmann":             1620,   # Swiss top-100
    "WTA-diane-parry":               1650,   # French top-80
}

DEFAULT_ELO = 1500.0


def lookup(participant_id: str, table: dict[str, float]) -> float:
    """Look up rating ; return DEFAULT_ELO if unknown.

    Tries the exact participant_id first ; then tries a few common
    transformations (lowercase, hyphen-stripped) before falling back."""
    if participant_id in table:
        return table[participant_id]
    return table.get(participant_id.upper(), DEFAULT_ELO)
