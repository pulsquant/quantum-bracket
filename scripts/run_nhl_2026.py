"""run_nhl_2026.py — Hand-coded back-test on the 2026 NHL Stanley Cup
Playoffs.

The PulsQuant tournament_brackets table is missing the Conference
Finals (R3) for nhl-playoffs-2026 at the time of writing, so we
hand-code the full 15-series bracket using :

  - R1 results from the production DB (8 series, completed)
  - R2 results from the production DB (4 series, completed)
  - R3 results from public NHL.com / Wikipedia
    Eastern  CF : Carolina beat Montreal 4-1
    Western  CF : Vegas Golden Knights swept Colorado 4-0 (the upset)
  - R4 (Final) : Carolina vs Vegas, series ongoing at writing

Real bracket pairings (per NHL.com schedule) :
  East R2 :
    R2-E1 = R1-East-1.winner vs R1-East-2.winner = CAR vs PHI
    R2-E2 = R1-East-3.winner vs R1-East-4.winner = MTL vs BUF
    R2-E1 winner = CAR (the actual outcome)
    R2-E2 winner = MTL
  West R2 :
    R2-W1 = MIN vs COL → COL won
    R2-W2 = VGK vs ANA → VGK won (after R1 VGK beat UTA, ANA beat EDM)
  R3 :
    East CF : CAR vs MTL → CAR
    West CF : COL vs VGK → VGK (upset, 4-0 sweep)
  R4 : CAR vs VGK (ongoing, currently 1-1).

The pre-playoff Elo ratings put Colorado (1670) and Vegas (1645) close,
with Vegas as a slight underdog. The actual sweep is therefore a
notable correlated-bracket upset path — exactly the kind of run our
seeded quantum walk is designed to upweight ex ante.

Run :
  python3 -m scripts.run_nhl_2026
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from qiskit_aer import AerSimulator

from src.qbracket import (
    Bracket,
    Match,
    build_circuit,
    champion_distribution,
    classical_mc_distribution,
    first_round_probs,
    p_top_wins,
)
from scripts.strengths import NHL_RATINGS


def build_nhl_bracket() -> tuple[Bracket, dict[str, str]]:
    """Construct the 2026 NHL Stanley Cup bracket, R1 → Final."""
    matches: list[Match] = []
    teams = sorted({
        # East
        "NHL-CAR", "NHL-OTT",   # E1: CAR sweeps OTT 4-0
        "NHL-PHI", "NHL-PIT",   # E2: PHI beats PIT 4-2
        "NHL-MTL", "NHL-TB",    # E3: MTL beats TB 4-3 (upset)
        "NHL-BOS", "NHL-BUF",   # E4: BUF beats BOS 4-2 (upset)
        # West
        "NHL-DAL", "NHL-MIN",   # W1: MIN beats DAL 4-2 (upset)
        "NHL-COL", "NHL-LA",    # W2: COL sweeps LA 4-0
        "NHL-UTA", "NHL-VGK",   # W3: VGK beats UTA 4-2
        "NHL-ANA", "NHL-EDM",   # W4: ANA beats EDM 4-2 (BIG upset)
    })

    # R1 East.
    r1_E1 = len(matches); matches.append(Match(r1_E1, 0, None, None, "NHL-CAR", "NHL-OTT"))
    r1_E2 = len(matches); matches.append(Match(r1_E2, 0, None, None, "NHL-PHI", "NHL-PIT"))
    r1_E3 = len(matches); matches.append(Match(r1_E3, 0, None, None, "NHL-MTL", "NHL-TB"))
    r1_E4 = len(matches); matches.append(Match(r1_E4, 0, None, None, "NHL-BOS", "NHL-BUF"))
    # R1 West.
    r1_W1 = len(matches); matches.append(Match(r1_W1, 0, None, None, "NHL-DAL", "NHL-MIN"))
    r1_W2 = len(matches); matches.append(Match(r1_W2, 0, None, None, "NHL-COL", "NHL-LA"))
    r1_W3 = len(matches); matches.append(Match(r1_W3, 0, None, None, "NHL-UTA", "NHL-VGK"))
    r1_W4 = len(matches); matches.append(Match(r1_W4, 0, None, None, "NHL-ANA", "NHL-EDM"))

    # R2 East : pair adjacent R1 winners.
    r2_E1 = len(matches); matches.append(Match(r2_E1, 1, r1_E1, r1_E2, None, None))
    r2_E2 = len(matches); matches.append(Match(r2_E2, 1, r1_E3, r1_E4, None, None))
    # R2 West.
    r2_W1 = len(matches); matches.append(Match(r2_W1, 1, r1_W1, r1_W2, None, None))
    r2_W2 = len(matches); matches.append(Match(r2_W2, 1, r1_W3, r1_W4, None, None))

    # R3 Conference Finals.
    r3_E = len(matches); matches.append(Match(r3_E, 2, r2_E1, r2_E2, None, None))
    r3_W = len(matches); matches.append(Match(r3_W, 2, r2_W1, r2_W2, None, None))

    # R4 Stanley Cup Final.
    r4 = len(matches); matches.append(Match(r4, 3, r3_E, r3_W, None, None))

    # Ground-truth winners by node_id (we use match_id as the key).
    realised: dict[str, str] = {
        "R1-E1": "NHL-CAR",
        "R1-E2": "NHL-PHI",
        "R1-E3": "NHL-MTL",
        "R1-E4": "NHL-BUF",
        "R1-W1": "NHL-MIN",
        "R1-W2": "NHL-COL",
        "R1-W3": "NHL-VGK",
        "R1-W4": "NHL-ANA",
        "R2-E1": "NHL-CAR",     # CAR beat PHI
        "R2-E2": "NHL-MTL",     # MTL beat BUF
        "R2-W1": "NHL-COL",     # COL beat MIN
        "R2-W2": "NHL-VGK",     # VGK beat ANA
        "R3-East-CF": "NHL-CAR",  # CAR beat MTL 4-1
        "R3-West-CF": "NHL-VGK",  # VGK swept COL 4-0 — THE UPSET
        "R4-Final": None,         # ongoing (CAR vs VGK, 1-1 at writing)
    }

    bracket = Bracket(matches=matches, teams=sorted(teams),
                      strength=NHL_RATINGS)
    return bracket, realised


def estimate_reach_finals(
    bracket: Bracket, p_first_round: list[float], team: str,
    shots: int = 50_000, seed: int = 42,
) -> tuple[float, float]:
    """P(team reaches Stanley Cup Final) under Q and C.

    Counts simulations / shots in which the team appears as one of the
    two participants of the Final (i.e. wins all 3 of their pre-Final
    series)."""
    qc = build_circuit(bracket, p_first_round)
    sim = AerSimulator(seed_simulator=seed)
    counts = sim.run(qc, shots=shots).result().get_counts(qc)
    finals = bracket.matches[bracket.champion_match_id]
    assert finals.parent_top is not None and finals.parent_bot is not None

    q_hits = 0
    for bitstring, n in counts.items():
        bits = bitstring.replace(" ", "")[::-1]
        chain = {i: int(b) for i, b in enumerate(bits)}
        team_top = _trace_team(bracket, bracket.matches[finals.parent_top], chain)
        team_bot = _trace_team(bracket, bracket.matches[finals.parent_bot], chain)
        if team_top == team or team_bot == team:
            q_hits += n
    p_q = q_hits / sum(counts.values())

    rng = np.random.default_rng(seed)
    c_hits = 0
    for _ in range(shots):
        winners: dict[int, str] = {}
        for m, p in zip(bracket.matches, p_first_round, strict=False):
            if m.round_idx == 0:
                winners[m.match_id] = m.team_top if rng.random() < p else m.team_bot
            else:
                a = winners[m.parent_top]
                b = winners[m.parent_bot]
                pp = p_top_wins(
                    bracket.strength.get(a, 1500), bracket.strength.get(b, 1500),
                )
                winners[m.match_id] = a if rng.random() < pp else b
        if winners[finals.parent_top] == team or winners[finals.parent_bot] == team:
            c_hits += 1
    p_c = c_hits / shots
    return p_q, p_c


def _trace_team(bracket: Bracket, m: Match, chain: dict[int, int]) -> str:
    while m.round_idx > 0:
        bit = chain[m.match_id]
        if bit == 0:
            m = bracket.matches[m.parent_top]
        else:
            m = bracket.matches[m.parent_bot]
    return m.team_top if chain[m.match_id] == 0 else m.team_bot  # type: ignore


def main() -> int:
    bracket, realised = build_nhl_bracket()
    print(f"Built NHL 2026 bracket : {bracket.n_matches} matches, "
          f"{len(bracket.teams)} teams")
    p = first_round_probs(bracket)

    print("\nFirst-round P(top wins) :")
    for m, prob in zip(bracket.matches, p, strict=False):
        if m.round_idx == 0:
            print(f"  {m.team_top} ({NHL_RATINGS[m.team_top]}) vs "
                  f"{m.team_bot} ({NHL_RATINGS[m.team_bot]}) → "
                  f"P({m.team_top}) = {prob:.3f}")

    shots = 50_000
    print(f"\nRunning quantum walk ({shots} shots) …")
    q_dist = champion_distribution(bracket, p, shots=shots, seed=42)
    print(f"Running classical MC ({shots} sims) …")
    c_dist = classical_mc_distribution(bracket, p, n_sims=shots, seed=42)

    print("\nChampion distribution (top 8) :")
    teams_sorted = sorted(set(q_dist) | set(c_dist),
                         key=lambda t: -q_dist.get(t, 0))[:8]
    print(f"  {'team':>9} {'Q':>8} {'C':>8} {'Q/C':>6}")
    for t in teams_sorted:
        q = q_dist.get(t, 0.0)
        c = c_dist.get(t, 0.0)
        ratio = q / c if c > 1e-4 else float("inf")
        marker = ""
        if t == "NHL-VGK":
            marker = "  ← swept COL 4-0 in WCF (the upset)"
        elif t == "NHL-CAR":
            marker = "  ← East CF winner, Final ongoing"
        elif t == "NHL-COL":
            marker = "  ← top-seed West, eliminated WCF"
        print(f"  {t:>9} {100*q:>7.2f}% {100*c:>7.2f}% {ratio:>5.2f}{marker}")

    # Deep-run marginals.
    print("\nDeep-run marginals (P(team reaches Stanley Cup Final)) :")
    for team in ("NHL-VGK", "NHL-CAR", "NHL-COL", "NHL-EDM"):
        p_q, p_c = estimate_reach_finals(bracket, p, team, shots=shots)
        ratio = p_q / p_c if p_c > 1e-4 else float("inf")
        print(f"  {team:>9} : P_Q={100*p_q:>5.2f}% P_C={100*p_c:>5.2f}% "
              f"Q/C={ratio:.2f}×")

    out = {
        "tournament": "NHL Stanley Cup Playoffs 2026",
        "n_qubits": bracket.n_matches,
        "shots": shots,
        "quantum": q_dist,
        "classical": c_dist,
        "realised": realised,
        "strengths": NHL_RATINGS,
        "note": (
            "Vegas Golden Knights (R3-W) and Carolina Hurricanes (R3-E) "
            "reached the Final. VGK 4-0 sweep over COL was the headline "
            "upset of the playoffs. Final series ongoing (CAR vs VGK, "
            "1-1 at writing)."
        ),
    }
    out_path = (Path(__file__).resolve().parents[1] / "data"
                / "nhl_2026_results.json")
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults written to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
