"""run_wc2026.py — Prospective FIFA World Cup 2026 prediction.

The 2026 FIFA World Cup uses a 48-team format (12 groups of 4, top 2 +
8 best-third → R32 → R16 → QF → SF → F = 31 knockout matches). Full
31-qubit simulation requires ≥ 32 GB of statevector RAM, exceeding most
laptops ; for the laptop-tractable POC we focus on the **R16 onward**
(15 qubits) using the top 16 teams by P(reach R16) from the classical
Monte Carlo run that ships with PulsQuant (`scripts.tournament.
simulate_bracket`, run 2026-06-06T17:04, n_sims=10 000).

Pairing assumption : we use a standard balanced 1v16, 2v15, 3v14, …
bracket. The actual draw of the WC 2026 knockout pairings is fixed by
the group-stage results which won't be known until June 27, 2026 ; this
prediction is therefore an **expected-value baseline** under the
balanced-bracket assumption.

Run :
  python3 -m scripts.run_wc2026
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.qbracket import (
    Bracket,
    Match,
    champion_distribution,
    classical_mc_distribution,
    first_round_probs,
)


# Top 16 teams by P(reach R16) from the PulsQuant classical MC run
# 2026-06-06T17:04. Elo ratings sourced from `lib.bracket.data` (April
# 2026 snapshot, eloratings.net).
WC2026_TOP16 = [
    ("ARG", 2105),  # Argentina — defending champion, top P(winner) 25.9%
    ("FRA", 2050),
    ("BRA", 2045),
    ("ESP", 2025),
    ("POR", 2010),
    ("GER", 1985),
    ("ENG", 1985),
    ("NED", 1955),
    ("BEL", 1945),
    ("URU", 1925),
    ("COL", 1920),
    ("SUI", 1900),
    ("CRO", 1895),
    ("ECU", 1880),
    ("USA", 1850),
    ("AUT", 1820),
]


def build_wc2026_bracket() -> Bracket:
    """Standard balanced 1v16 pairing.

    Pairing :
      1 vs 16, 8 vs 9   → QF top-left
      4 vs 13, 5 vs 12  → QF top-right
      3 vs 14, 6 vs 11  → QF bot-left
      2 vs 15, 7 vs 10  → QF bot-right
    Standard WC-style balanced layout : top seeds never meet before
    the semifinal under this convention.
    """
    teams = [t for t, _ in WC2026_TOP16]
    strength = {t: e for t, e in WC2026_TOP16}

    # Reorder so adjacent pairs (i, i+1) form R16 matchups under
    # balanced bracket : [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]
    seed_order = [1, 16, 8, 9, 5, 12, 4, 13, 6, 11, 3, 14, 7, 10, 2, 15]
    ordered = [teams[i - 1] for i in seed_order]

    matches: list[Match] = []
    # R16 (8 matches).
    r16 = []
    for i in range(0, 16, 2):
        mid = len(matches)
        matches.append(
            Match(
                match_id=mid,
                round_idx=0,
                parent_top=None,
                parent_bot=None,
                team_top=ordered[i],
                team_bot=ordered[i + 1],
            )
        )
        r16.append(mid)
    # QF (4 matches), pairing adjacent R16 winners.
    qf = []
    for i in range(0, 8, 2):
        mid = len(matches)
        matches.append(Match(mid, 1, r16[i], r16[i + 1], None, None))
        qf.append(mid)
    # SF (2 matches).
    sf = []
    for i in range(0, 4, 2):
        mid = len(matches)
        matches.append(Match(mid, 2, qf[i], qf[i + 1], None, None))
        sf.append(mid)
    # Final.
    mid = len(matches)
    matches.append(Match(mid, 3, sf[0], sf[1], None, None))

    return Bracket(matches=matches, teams=ordered, strength=strength)


def main() -> int:
    bracket = build_wc2026_bracket()
    print(f"Built WC 2026 R16+ bracket : {bracket.n_matches} matches, "
          f"{len(bracket.teams)} teams")

    p = first_round_probs(bracket)
    print("\nR16 pairings + P(top wins) :")
    for m, prob in zip(bracket.matches, p, strict=False):
        if m.round_idx == 0:
            print(f"  {m.team_top} ({bracket.strength[m.team_top]}) vs "
                  f"{m.team_bot} ({bracket.strength[m.team_bot]}) → "
                  f"P({m.team_top}) = {prob:.3f}")

    shots = 50_000
    print(f"\nRunning quantum walk ({shots} shots) …")
    q_dist = champion_distribution(bracket, p, shots=shots, seed=42)
    print(f"Running classical MC ({shots} sims) …")
    c_dist = classical_mc_distribution(bracket, p, n_sims=shots, seed=42)

    print("\nWC 2026 champion distribution :")
    print(f"  {'team':>5} {'quantum':>9} {'classical':>10} {'|Δ|':>6}")
    all_teams = sorted(set(q_dist) | set(c_dist), key=lambda t: -q_dist.get(t, 0))
    for t in all_teams:
        q = q_dist.get(t, 0.0)
        c = c_dist.get(t, 0.0)
        d = abs(q - c)
        ratio = q / c if c > 0 else float("inf")
        marker = " ← upset bias > 2×" if ratio > 2.0 and q > 0.02 else ""
        print(f"  {t:>5} {100 * q:>8.2f}% {100 * c:>9.2f}% "
              f"{100 * d:>5.2f}pp{marker}")

    out = {
        "tournament": "FIFA World Cup 2026",
        "stage": "R16 onward (16 teams, 15 matches)",
        "n_qubits": bracket.n_matches,
        "shots": shots,
        "quantum": q_dist,
        "classical": c_dist,
        "elo": dict(WC2026_TOP16),
        "bracket_assumption": "balanced 1v16 pairing",
        "note": (
            "Actual knockout pairings determined by group-stage results "
            "(known June 27, 2026). This is an expected-value baseline "
            "under the balanced-bracket assumption."
        ),
    }
    out_path = Path(__file__).resolve().parents[1] / "data" / "wc2026_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults written to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
