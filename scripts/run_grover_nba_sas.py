"""run_grover_nba_sas.py — Grover amplitude amplification on the
P(SAS = NBA champion) query of the 2026 NBA Playoffs bracket.

Proof of concept for the quantum advantage flagged as future work in the
companion paper. Applies amplitude amplification to the bracket prep
unitary A and measures how the SAS-champion bitstrings get amplified as a
function of the number of Grover iterations k. The expected behaviour
is the textbook sine-squared envelope sin^2((2k+1) theta) with
sin(theta) = sqrt(p_SAS).

Why SAS : SAS was the 8-seed West that reached the 2026 NBA Finals after
eliminating the 1-seed OKC in the Western Conference Finals. On the
seeded quantum walk it sits at P_Q(SAS champion) approx 5.6%, so the
optimal number of Grover iterations is moderate (k* approx 3) which
keeps the circuit depth tractable on a single-laptop Aer simulator.

Outputs :
  - figures/fig4_grover_speedup.pdf — Grover amplification curve
  - data/grover_nba_results.json — raw numbers (per-k P(SAS champion))

Usage :
    python3 -m scripts.run_grover_nba_sas
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.qbracket import (  # noqa: E402
    build_circuit,
    first_round_probs,
)
from scripts.run_nba_playoffs_2026 import build_nba_bracket  # noqa: E402


# ─── Bracket → "SAS champion" qubit pattern ─────────────────────────────
#
# Tracing the 2026 NBA bracket builder in scripts/run_nba_playoffs_2026.py :
#   match 4  = OKC (top) vs SAS (bot)        round 0  → q[4] = 1 if SAS wins
#   match 5  = LAC vs DAL                    round 0
#   match 10 = West CSF, parents 4 & 5       round 1  → q[10] = 0 if SAS advances
#                                                       (SAS came from parent_top = 4)
#   match 11 = West CSF, parents 6 & 7
#   match 13 = West CF,  parents 10 & 11     round 2  → q[13] = 0 if SAS advances
#                                                       (SAS came from parent_top = 10)
#   match 14 = NBA Finals, parents 12 & 13   round 3  → q[14] = 1 if West wins
#                                                       (SAS is on the bot/West side)
#
# So the "SAS champion" subspace is defined by :
#   q[4] = 1, q[10] = 0, q[13] = 0, q[14] = 1
# The 11 other qubits (0,1,2,3,5,6,7,8,9,11,12) are free.
SAS_CONSTRAINTS: dict[int, int] = {4: 1, 10: 0, 13: 0, 14: 1}


def _build_bracket_unitary(bracket, p_first_round) -> QuantumCircuit:
    """Re-build the bracket prep circuit WITHOUT measurement, so we can
    invert it for the Grover diffusion operator."""
    # We re-implement the build but skip the measurement at the end.
    n = bracket.n_matches
    qc = QuantumCircuit(n)
    # Copy logic from src.qbracket.build_circuit minus the measurement.
    from src.qbracket import _attach_conditional_match  # noqa: PLC0415
    for m, p in zip(bracket.matches, p_first_round, strict=False):
        if m.round_idx == 0:
            theta = 2 * math.asin(math.sqrt(max(0.0, min(1.0, 1.0 - p))))
            qc.ry(theta, m.match_id)
        else:
            _attach_conditional_match(qc, m, bracket)
    return qc


def _oracle_sas_champion(n_qubits: int) -> QuantumCircuit:
    """Phase oracle : flip the global phase of states where the SAS
    constraints are satisfied. Implemented as a multi-controlled Z gate
    on the 4 constraint qubits (with X gates wrapping the 0-controls)."""
    qc = QuantumCircuit(n_qubits, name="O_SAS")
    # Flip qubits that need to be 0 → 1 so they can act as standard controls.
    zero_ctrl = [q for q, v in SAS_CONSTRAINTS.items() if v == 0]
    for q in zero_ctrl:
        qc.x(q)
    # Multi-controlled Z on the 4 constraint qubits :
    # MCZ = H · MCX · H on the target.
    constraint_qubits = sorted(SAS_CONSTRAINTS.keys())
    target = constraint_qubits[-1]
    controls = constraint_qubits[:-1]
    qc.h(target)
    qc.mcx(controls, target)
    qc.h(target)
    # Un-flip.
    for q in zero_ctrl:
        qc.x(q)
    return qc


def _diffusion(A: QuantumCircuit) -> QuantumCircuit:
    """The Grover diffusion operator D = A · (2|0><0| - I) · A^†.

    Reflects about the bracket prep state |s> = A|0>, not about the
    uniform superposition (which would be incorrect because A produces
    a non-uniform state)."""
    n = A.num_qubits
    qc = QuantumCircuit(n, name="D")
    qc.append(A.inverse(), range(n))
    # Reflection about |0...0> : X all, MCZ, X all.
    for q in range(n):
        qc.x(q)
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)
    for q in range(n):
        qc.x(q)
    qc.append(A, range(n))
    return qc


def _bitstring_is_sas_champion(bitstring: str) -> bool:
    """Qiskit returns bitstrings with q[0] on the RIGHT. Check that the
    SAS-constraint qubits have the right values."""
    bits = bitstring.replace(" ", "")[::-1]
    return all(int(bits[q]) == v for q, v in SAS_CONSTRAINTS.items())


def measure_sas_probability(qc: QuantumCircuit, shots: int, seed: int = 42) -> float:
    """Append measurements, decompose (Aer rejects nested sub-circuits with
    auto-generated names like `circuit-46`), run on Aer, return the
    empirical P(SAS champion)."""
    from qiskit import transpile  # noqa: PLC0415
    n = qc.num_qubits
    meas = QuantumCircuit(n, n)
    meas.compose(qc, inplace=True)
    meas.measure(range(n), range(n))
    sim = AerSimulator(seed_simulator=seed)
    # Transpile decomposes the appended sub-circuits to gates Aer knows.
    meas_t = transpile(meas, sim)
    result = sim.run(meas_t, shots=shots).result()
    counts = result.get_counts(meas_t)
    sas = sum(c for b, c in counts.items() if _bitstring_is_sas_champion(b))
    return sas / shots


def main() -> int:
    bracket = build_nba_bracket()
    p = first_round_probs(bracket)
    A = _build_bracket_unitary(bracket, p)
    O = _oracle_sas_champion(A.num_qubits)
    D = _diffusion(A)

    print(f"NBA 2026 bracket : {bracket.n_matches} matches, {A.num_qubits} qubits")
    print(f"SAS champion constraints : {SAS_CONSTRAINTS}")

    # Baseline : measure P(SAS champion) on A|0> with no amplification.
    baseline_shots = 50_000
    p0 = measure_sas_probability(A, shots=baseline_shots, seed=42)
    print(f"\nBaseline P(SAS champion) on A|0> with {baseline_shots} shots : "
          f"{100 * p0:.3f}%")
    print(f"  (theoretical optimal k* = pi/(4·arcsin(sqrt(p0))) "
          f"= {math.pi / (4 * math.asin(math.sqrt(max(p0, 1e-6)))):.2f})")

    # Sweep Grover iterations k from 0 to k_max.
    k_max = 15
    sweep: list[dict] = []
    print(f"\nSweeping Grover iterations 0..{k_max} (each with {baseline_shots} shots) :")
    for k in range(k_max + 1):
        qc = QuantumCircuit(A.num_qubits)
        qc.append(A, range(A.num_qubits))
        for _ in range(k):
            qc.append(O, range(A.num_qubits))
            qc.append(D, range(A.num_qubits))
        pk = measure_sas_probability(qc, shots=baseline_shots, seed=42 + k)
        sweep.append({"k": k, "p_sas": pk})
        marker = "  ←  peak" if pk > 0.85 else ""
        print(f"  k = {k:2d}   P(SAS champion) = {100 * pk:6.2f}%{marker}")

    # Find the empirical optimum.
    k_opt = max(sweep, key=lambda s: s["p_sas"])
    print(f"\nEmpirical optimum : k = {k_opt['k']} → "
          f"P(SAS champion) = {100 * k_opt['p_sas']:.2f}%")

    # Speedup analysis : how many shots would we need WITHOUT amplification
    # to reach the same statistical confidence on the SAS-champion count ?
    #
    # Without amplification : counting binomial(N_unamp, p0) — std error
    # on the count is sqrt(N_unamp · p0 · (1-p0)). For a target relative
    # precision rho on p0, N_unamp = (1-p0) / (p0 · rho^2).
    #
    # With amplification at k_opt, the same target precision on
    # P(SAS champion after amplif) = p_opt is reached with
    # N_amp = (1-p_opt) / (p_opt · rho^2). For p_opt close to 1,
    # N_amp is tiny while N_unamp is large.
    rho = 0.05  # 5% relative precision
    p_opt = k_opt["p_sas"]
    N_unamp = (1 - p0) / (p0 * rho ** 2)
    N_amp = (1 - p_opt) / (p_opt * rho ** 2)
    speedup = N_unamp / max(N_amp, 1)
    print("\nShot-count speedup for 5% relative precision on the "
          "SAS-champion frequency :")
    print(f"  Without amplification : {N_unamp:,.0f} shots")
    print(f"  With Grover (k = {k_opt['k']}) : {N_amp:,.1f} shots")
    print(f"  Speedup : {speedup:,.0f}×")

    # Plot.
    out_dir = Path(__file__).resolve().parents[1] / "figures"
    out_dir.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ks = [s["k"] for s in sweep]
    ps = [s["p_sas"] for s in sweep]
    # Theoretical envelope sin^2((2k+1) θ) with sin(θ) = sqrt(p0).
    theta = math.asin(math.sqrt(p0))
    ks_smooth = np.linspace(0, k_max, 300)
    p_theory = np.sin((2 * ks_smooth + 1) * theta) ** 2
    ax.plot(ks_smooth, p_theory, "--", color="gray", alpha=0.6,
            label=r"theory $\sin^2((2k+1)\theta)$")
    ax.plot(ks, ps, "o-", color="#1f77b4",
            label="Aer measurement (50k shots / point)")
    ax.axhline(p0, color="orange", linestyle=":",
               label=f"baseline $p_0$ = {100*p0:.2f}%")
    ax.set_xlabel("Grover iterations $k$")
    ax.set_ylabel(r"$P(\text{SAS champion})$")
    ax.set_title("Grover amplification on the SAS-champion bracket query")
    ax.set_xticks(range(0, k_max + 1))
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    plt.tight_layout()
    fig.savefig(out_dir / "fig4_grover_speedup.pdf")
    fig.savefig(out_dir / "fig4_grover_speedup.png", dpi=150)
    print(f"\nWrote figure → {out_dir / 'fig4_grover_speedup.pdf'}")

    # Dump raw numbers.
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(exist_ok=True)
    out_json = {
        "bracket": "NBA Playoffs 2026",
        "target": "SAS champion",
        "constraints": {str(q): v for q, v in SAS_CONSTRAINTS.items()},
        "shots_per_point": baseline_shots,
        "baseline_p0": p0,
        "optimal_k": k_opt["k"],
        "optimal_p": k_opt["p_sas"],
        "shot_speedup_for_5pct_precision": speedup,
        "sweep": sweep,
    }
    (data_dir / "grover_nba_results.json").write_text(json.dumps(out_json, indent=2))
    print(f"Wrote data → {data_dir / 'grover_nba_results.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
