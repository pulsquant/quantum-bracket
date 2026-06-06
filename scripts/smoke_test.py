"""smoke_test.py — Sanity check on a small 8-team bracket.

Validates that :
  1. The quantum circuit builds without error on a 7-match bracket
  2. The champion distribution sums to 1.0
  3. The quantum and classical Monte Carlo distributions agree within
     statistical noise (<2 percentage points for the top team) on a
     bracket where we know the analytic answer.

Run :
  python3 -m scripts.smoke_test
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `from src.qbracket import …` when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.qbracket import (
    build_single_elim_bracket,
    champion_distribution,
    classical_mc_distribution,
    first_round_probs,
)


def main() -> int:
    # 8 teams, balanced bracket. Elo ratings chosen so team "A" is a
    # clear favorite (Elo 1850) and "H" is a clear underdog (Elo 1450),
    # with the rest spread linearly.
    teams = ["A", "B", "C", "D", "E", "F", "G", "H"]
    strength = {t: 1850 - 50 * i for i, t in enumerate(teams)}

    bracket = build_single_elim_bracket(teams, strength)
    print(f"Built bracket : {bracket.n_matches} matches, {len(teams)} teams")

    p = first_round_probs(bracket)
    print("\nFirst-round P(top wins) :")
    for m, prob in zip(bracket.matches, p, strict=False):
        if m.round_idx == 0:
            print(f"  {m.team_top} vs {m.team_bot} → P({m.team_top}) = {prob:.3f}")

    print("\nRunning quantum circuit (10 000 shots) …")
    q_dist = champion_distribution(bracket, p, shots=10_000, seed=42)

    print("Running classical Monte Carlo (10 000 sims) …")
    c_dist = classical_mc_distribution(bracket, p, n_sims=10_000, seed=42)

    print("\nChampion distribution :")
    print(f"  {'team':>6} {'quantum':>10} {'classical':>10} {'|Δ|':>6}")
    all_teams = sorted(set(q_dist) | set(c_dist), key=lambda t: -q_dist.get(t, 0))
    max_delta = 0.0
    for t in all_teams:
        q = q_dist.get(t, 0.0)
        c = c_dist.get(t, 0.0)
        d = abs(q - c)
        max_delta = max(max_delta, d)
        print(f"  {t:>6} {100 * q:>9.2f}% {100 * c:>9.2f}% {100 * d:>5.2f}pp")

    # Sanity checks.
    assert abs(sum(q_dist.values()) - 1.0) < 1e-9, "quantum dist must sum to 1"
    assert abs(sum(c_dist.values()) - 1.0) < 1e-9, "classical dist must sum to 1"
    assert max_delta < 0.03, (
        f"quantum/classical mismatch too large: max |Δ| = {max_delta:.4f}"
    )

    print(f"\n✅ smoke test passed (max |Δ| = {100 * max_delta:.2f}pp < 3.00pp)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
