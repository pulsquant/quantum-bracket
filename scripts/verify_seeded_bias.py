"""verify_seeded_bias.py — Confirm the quantum walk seeded approximation
is a *deliberate* bias, not an implementation bug.

We compare three estimators on the same bracket :
  Q  — Quantum walk via Qiskit Aer (the qbracket.py implementation)
  C  — Classical MC (the true unbiased baseline)
  S  — Closed-form *seeded* probability (enumerates all 2^n paths
       in the bracket but uses the SAME seeded-team approximation
       that the quantum circuit applies in deeper rounds)

If Q ≈ S, then the deviation Q vs C is the seeded approximation's bias,
not a quantum-specific artifact. This is precisely the kind of result
we want to put in the paper : the approximation is a controlled design
choice, not a hidden bug.

The closed-form seeded estimator works by iterating over all 2^(n_matches)
binary outcomes ; for n=15 that's 32768 paths, trivial on CPU.
"""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.qbracket import (
    Bracket,
    champion_distribution,
    classical_mc_distribution,
    first_round_probs,
    p_top_wins,
    _walk_to_team,
)


def seeded_closed_form(bracket: Bracket, p_first_round: list[float]) -> dict[str, float]:
    """Closed-form champion distribution under the same seeded approximation
    that the quantum circuit applies.

    For each binary outcome of every match (2^n_matches paths), we :
      1. Use p_first_round for round-0 matches.
      2. For deeper-round matches, use the seeded matchup probability —
         identical to what _attach_conditional_match computes via MCRY.
      3. Multiply the path probability and accumulate into the champion's
         bucket.
    """
    champ_probs: dict[str, float] = {}
    n = bracket.n_matches

    for outcomes in product([0, 1], repeat=n):
        path_prob = 1.0
        for m, p, o in zip(bracket.matches, p_first_round, outcomes, strict=False):
            if m.round_idx == 0:
                # outcome = 0 means top wins → prob = p ; outcome = 1 → 1-p
                path_prob *= p if o == 0 else (1.0 - p)
            else:
                # Deeper round : use seeded matchup
                pt_outcome = outcomes[m.parent_top]
                pb_outcome = outcomes[m.parent_bot]
                top_team = _walk_to_team(bracket, bracket.matches[m.parent_top],
                                          pt_outcome)
                bot_team = _walk_to_team(bracket, bracket.matches[m.parent_bot],
                                          pb_outcome)
                s_top = bracket.strength.get(top_team, 1500.0)
                s_bot = bracket.strength.get(bot_team, 1500.0)
                p_match = p_top_wins(s_top, s_bot)
                path_prob *= p_match if o == 0 else (1.0 - p_match)

        # Trace champion from outcomes.
        m = bracket.matches[bracket.champion_match_id]
        chain = {i: outcomes[i] for i in range(n)}
        while m.round_idx > 0:
            bit = chain[m.match_id]
            m = bracket.matches[m.parent_top if bit == 0 else m.parent_bot]
        bit = chain[m.match_id]
        champ = m.team_top if bit == 0 else m.team_bot
        champ_probs[champ] = champ_probs.get(champ, 0.0) + path_prob

    return champ_probs


def compare_on_bracket(bracket: Bracket, label: str, shots: int = 50_000):
    p = first_round_probs(bracket)
    print(f"\n=== {label} ({bracket.n_matches} qubits) ===")

    q = champion_distribution(bracket, p, shots=shots, seed=42)
    c = classical_mc_distribution(bracket, p, n_sims=shots, seed=42)
    s = seeded_closed_form(bracket, p)

    teams = sorted(set(q) | set(c) | set(s), key=lambda t: -q.get(t, 0))
    print(f"  {'team':>5} {'Q (Aer)':>9} {'S (closed)':>11} {'C (MC)':>8} "
          f"{'|Q−S|':>6} {'|Q−C|':>6}")
    max_qs = 0.0
    max_qc = 0.0
    for t in teams:
        qv = q.get(t, 0.0)
        cv = c.get(t, 0.0)
        sv = s.get(t, 0.0)
        d_qs = abs(qv - sv)
        d_qc = abs(qv - cv)
        max_qs = max(max_qs, d_qs)
        max_qc = max(max_qc, d_qc)
        print(f"  {t:>5} {100 * qv:>8.2f}% {100 * sv:>10.2f}% "
              f"{100 * cv:>7.2f}% {100 * d_qs:>5.2f}pp {100 * d_qc:>5.2f}pp")

    print(f"\n  max |Q−S| (Q matches seeded closed-form ?) : {100 * max_qs:.2f}pp")
    print(f"  max |Q−C| (seeded bias vs unbiased MC)     : {100 * max_qc:.2f}pp")
    return max_qs, max_qc


def main():
    from src.qbracket import build_single_elim_bracket

    # 8-team bracket : sanity, seeded approx is close to exact at low depth.
    teams8 = ["A", "B", "C", "D", "E", "F", "G", "H"]
    strength8 = {t: 1850 - 50 * i for i, t in enumerate(teams8)}
    b8 = build_single_elim_bracket(teams8, strength8)
    qs8, qc8 = compare_on_bracket(b8, "8-team smoke", shots=50_000)

    # 16-team bracket : seeded approx should disagree noticeably with MC,
    # but Q should agree closely with S.
    teams16 = [f"T{i+1}" for i in range(16)]
    strength16 = {t: 2100 - 30 * i for i, t in enumerate(teams16)}
    b16 = build_single_elim_bracket(teams16, strength16)
    qs16, qc16 = compare_on_bracket(b16, "16-team Elo spread", shots=50_000)

    print("\n" + "=" * 60)
    if qs8 < 0.02 and qs16 < 0.02:
        print("✅ VERIFIED : Quantum walk Q matches the closed-form seeded "
              "estimator S in both regimes.")
        print("   → The Q vs C divergence is a property of the seeded "
              "approximation, NOT a quantum implementation bug.")
        print("   → This is a deliberate, documentable design choice.")
    else:
        print(f"⚠ Q vs S diverges (max {max(qs8, qs16):.4f}). Check encoding.")


if __name__ == "__main__":
    main()
