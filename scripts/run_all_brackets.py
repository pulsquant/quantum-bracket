"""run_all_brackets.py — Multi-tournament back-test using real bracket data.

Pulls the actual 2026 brackets from PulsQuant's `tournament_brackets`
table (so we don't have to assume a balanced 1-vs-8 layout) and runs
the seeded quantum walk vs classical MC for each. The realised
results in `winner_participant_id` give us ground truth for back-test
metrics (champion-marginal hit, deep-run-marginal upweight).

Run :
  python3 -m scripts.run_all_brackets
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db_bracket_loader import load_bracket_from_db, load_participants
from src.qbracket import (
    Bracket,
    champion_distribution,
    classical_mc_distribution,
    first_round_probs,
)

from scripts.strengths import (
    NBA_RATINGS,
    NHL_RATINGS,
    UCL_RATINGS,
    RG_ATP_RATINGS,
    RG_WTA_RATINGS,
    lookup,
    DEFAULT_ELO,
)


# Per-tournament cutoff round = the round_order at which our loaded
# slice begins (this becomes round_idx 0 in the qbracket model).
# UCL : skip the KOP qualifier (round 1) ; start at R16 = round 2.
# NHL : full slice (R1, R2, R4 — R3 missing in DB, accept 13 qubits).
# NBA : full slice = 15 qubits.
# Tennis : skip the qualif (R-3..R-1) and the early main rounds
#          (R1=128→64, R2=64→32, R3=32→16) ; start at R16 = round 4.
TOURNAMENTS = [
    ("nba-playoffs-2026",      "NBA Playoffs 2026 (live)",         NBA_RATINGS,    None),
    # NHL : DB is missing the Conference Finals (R3) ; the R1+R2+R4
    # chain is incomplete for our encoder. We hand-code the NHL
    # bracket in a separate script (run_nhl_2026.py) using the real
    # R1/R2/R4 outcomes plus the publicly-known R3 results.
    ("uefa-cl-2025-2026",      "UEFA Champions League 2025-2026",   UCL_RATINGS,    2),
    ("atp-roland-garros-2026", "Roland Garros 2026 ATP — R16+",     RG_ATP_RATINGS, 4),
    ("wta-roland-garros-2026", "Roland Garros 2026 WTA — R16+",     RG_WTA_RATINGS, 4),
]


def run_one(tournament_id: str, label: str, ratings: dict[str, float],
            cutoff_round: int | None) -> dict:
    print(f"\n{'='*70}\n=== {label}  [{tournament_id}] ===")
    # Build strength dict — accept any participant_id we encounter.
    try:
        bracket, winners = load_bracket_from_db(
            tournament_id, strength={}, cutoff_round=cutoff_round
        )
    except ValueError as e:
        print(f"  ⚠ {e}")
        return {"tournament_id": tournament_id, "error": str(e)}

    # Fill strengths : the loader returned a Bracket with empty strength.
    # We replace it with a fresh Bracket carrying the participant ratings.
    strengths: dict[str, float] = {}
    for m in bracket.matches:
        for t in (m.team_top, m.team_bot):
            if t is not None and t not in strengths:
                strengths[t] = lookup(t, ratings)
    bracket = Bracket(
        matches=bracket.matches,
        teams=bracket.teams,
        strength=strengths,
    )

    n_qubits = bracket.n_matches
    print(f"  {n_qubits} qubits, {len(bracket.teams)} R{bracket.matches[0].round_idx} entrants")
    if n_qubits > 20:
        print(f"  ⚠ {n_qubits} qubits > 20 : skipping (RAM limit)")
        return {"tournament_id": tournament_id, "error": "too many qubits"}

    # Show R1 entrants + strengths.
    print(f"\n  First-round matchups (round_idx=0) :")
    for m in bracket.matches:
        if m.round_idx == 0:
            st = strengths[m.team_top]
            sb = strengths[m.team_bot]
            print(f"    {m.team_top:<25} ({st:.0f}) vs {m.team_bot:<25} ({sb:.0f})")

    p = first_round_probs(bracket)

    shots = 50_000
    print(f"\n  Running quantum walk ({shots} shots) …")
    q_dist = champion_distribution(bracket, p, shots=shots, seed=42)
    print(f"  Running classical MC ({shots} sims) …")
    c_dist = classical_mc_distribution(bracket, p, n_sims=shots, seed=42)

    print(f"\n  Top 8 champion-marginal :")
    print(f"    {'team':>26} {'P_Q':>8} {'P_C':>8} {'Q/C':>6}")
    all_t = sorted(set(q_dist) | set(c_dist), key=lambda t: -q_dist.get(t, 0))[:8]
    for t in all_t:
        q = q_dist.get(t, 0.0)
        c = c_dist.get(t, 0.0)
        ratio = q / c if c > 1e-4 else float("inf")
        print(f"    {t[:26]:>26} {100*q:>7.2f}% {100*c:>7.2f}% {ratio:>5.2f}")

    # Identify the realised champion + finalists via the DB winners.
    # We re-query the deepest 1-2 rounds to find the F + SF winners.
    realised = _query_realised_finalists(tournament_id, cutoff_round)
    print(f"\n  Realised :")
    for k, v in realised.items():
        if v:
            qv = q_dist.get(v, 0.0)
            cv = c_dist.get(v, 0.0)
            r = qv / cv if cv > 1e-4 else float("inf")
            print(f"    {k}: {v[:30]:<30} P_Q={100*qv:>5.2f}% P_C={100*cv:>5.2f}% Q/C={r:.2f}×")

    return {
        "tournament_id": tournament_id,
        "label": label,
        "n_qubits": n_qubits,
        "shots": shots,
        "quantum": q_dist,
        "classical": c_dist,
        "winners": winners,
        "strengths": strengths,
        "realised": realised,
    }


def _query_realised_finalists(
    tournament_id: str, cutoff_round: int | None
) -> dict[str, str | None]:
    """Return {champion, runner_up, sf_loser_1, sf_loser_2}."""
    from lib.pulsquant_db import connect

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SET statement_timeout = '20s'")
        cur.execute(
            """
            SELECT round_order, bracket_position, participant_top,
                   participant_bottom, winner_participant_id
            FROM tournament_brackets
            WHERE tournament_id = %s
            ORDER BY round_order DESC, bracket_position
            LIMIT 10
            """,
            (tournament_id,),
        )
        rows = cur.fetchall()
    if not rows:
        return {"champion": None, "runner_up": None}

    # Final = deepest row.
    final_row = rows[0]
    f_top, f_bot, f_winner = final_row[2], final_row[3], final_row[4]
    champion = f_winner
    runner_up = f_top if f_winner == f_bot else f_bot if f_winner == f_top else None

    # Semifinals (= rows 2 and 3 if structure is consistent).
    sf_losers: list[str] = []
    for r in rows[1:]:
        if r[0] == final_row[0] - 1 and r[4] is not None:
            loser = r[2] if r[4] == r[3] else r[3]
            if loser != champion and loser != runner_up:
                sf_losers.append(loser)

    return {
        "champion": champion,
        "runner_up": runner_up,
        "sf_loser_1": sf_losers[0] if len(sf_losers) > 0 else None,
        "sf_loser_2": sf_losers[1] if len(sf_losers) > 1 else None,
    }


def main() -> int:
    results = []
    for t_id, label, ratings, cutoff in TOURNAMENTS:
        results.append(run_one(t_id, label, ratings, cutoff))

    out = Path(__file__).resolve().parents[1] / "data" / "all_brackets_results.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n\nAll results written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
