"""run_qae_nba_sas.py — Quantum Amplitude Estimation (QAE) on the
P(SAS = NBA champion) query of the 2026 NBA Playoffs bracket.

Companion script to run_grover_nba_sas.py (which implements the
amplification-only Grover variant). This one is the full
Brassard-Hoyer-Mosca-Tapp algorithm : an m-qubit ancilla register
controls iterated applications of the Grover operator Q, an inverse
QFT extracts the phase, and the measurement on the ancillas gives a
2^m-grid estimate of the amplitude.

Why QAE over amplification :
  - Amplification gets you to the optimal k* and tells you P(SAS) is
    close to 1 after rotation, but it does NOT directly tell you what
    the original p_0 was.
  - QAE outputs an estimate of p_0 itself, with O(1/eps) shots for
    additive precision eps (vs O(1/eps^2) classically). This is the
    rigorous quadratic speedup that justifies the algorithm.

Resource cost :
  - m = 5 ancillas → 2^5 = 32-grid resolution, eps_th ~ pi^2/32 ~ 0.10
    on the amplitude (acceptable for a PoC). Total qubits : 20.
  - m = 6 → 64-grid, eps_th ~ 0.05. Total qubits : 21.
  - m = 7 → 128-grid, eps_th ~ 0.025. Total qubits : 22.
  - Aer single-laptop handles 20-22 qubits with circuit transpilation.

Outputs :
  - figures/fig5_qae_estimation.pdf — empirical estimator distribution
    + theoretical p_0 marker.
  - data/qae_nba_results.json — raw numbers.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import QFT
from qiskit_aer import AerSimulator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.qbracket import first_round_probs  # noqa: E402
from scripts.run_nba_playoffs_2026 import build_nba_bracket  # noqa: E402
from scripts.run_grover_nba_sas import (  # noqa: E402
    SAS_CONSTRAINTS,
    _build_bracket_unitary,
    _oracle_sas_champion,
    _diffusion,
    _bitstring_is_sas_champion,
)


# ─── QAE circuit construction ──────────────────────────────────────────


def _flatten(qc: QuantumCircuit) -> QuantumCircuit:
    """Decompose a circuit containing appended sub-circuits down to a
    flat list of basic gates. Required before .to_gate() / .control()
    because Qiskit's to_gate refuses circuits that themselves contain
    composite "circuit-NN_dg" instructions (which arise from .inverse()
    on a composed sub-circuit)."""
    # Two-pass decompose handles A → flat, then D = A·S0·A^† → flat too.
    return qc.decompose().decompose()


def build_grover_operator_Q(A: QuantumCircuit, O: QuantumCircuit) -> QuantumCircuit:
    """Construct the canonical Brassard-style Grover operator Q whose
    eigenvalues on the 2D good/bad subspace are exactly e^{±i 2θ} with
    sin²(θ) = p_0. This is the eigenvalue spectrum that QPE will
    decode into the amplitude estimate.

    Sign convention : our `_diffusion(A)` implementation actually
    builds A · (I - 2|0><0|) · A^† = I - 2|s><s|, which is the
    NEGATIVE of the canonical Grover diffusion D_canon = 2|s><s| - I.
    Composed with our phase oracle O = I - 2|good><good|, the product
    O · _diffusion has eigenvalues e^{i(π ± 2θ)}, off by a global -1
    sign relative to the canonical convention. We bake that -1 back in
    via a global phase of π on the Q circuit, which then propagates
    correctly through QPE's controlled-Q^{2^j} (via the standard phase
    kickback mechanism)."""
    n = A.num_qubits
    Q = QuantumCircuit(n, name="Q")
    Q.compose(O, range(n), inplace=True)
    Q.compose(_diffusion(A), range(n), inplace=True)
    # Restore canonical eigenvalue spectrum e^{±i 2θ} from e^{i(π ± 2θ)}.
    Q.global_phase += math.pi
    return _flatten(Q)


def build_qae_circuit(
    A: QuantumCircuit,
    O: QuantumCircuit,
    m_ancillas: int,
) -> QuantumCircuit:
    """Build the full QAE circuit on m_ancillas + A.num_qubits qubits.

    Layout :
      - ancillas (first m_ancillas qubits)  : control register for QPE.
      - data register (last A.num_qubits)   : bracket state.

    Steps :
      1. Hadamard on all ancillas (uniform superposition).
      2. Apply A on the data register.
      3. For j = 0..m-1, apply controlled-Q^(2^j) with ancilla j as
         control. This implements the controlled unitary of QPE.
      4. Inverse QFT on the ancilla register.
      5. Measure ancillas.

    The measured integer y ∈ {0, ..., 2^m - 1} encodes an estimated
    angle θ_est = π y / 2^m, from which the amplitude estimate is
    p_est = sin²(θ_est).
    """
    n_data = A.num_qubits
    total = m_ancillas + n_data
    qc = QuantumCircuit(total, m_ancillas)

    # Step 1 : Hadamard on ancillas.
    for j in range(m_ancillas):
        qc.h(j)

    # Step 2 : prepare |s> = A|0> on the data register.
    A_flat = _flatten(A)
    qc.append(A_flat.to_gate(label="A"), range(m_ancillas, total))

    # Step 3 : controlled-Q^(2^j) for j = 0..m-1.
    Q = build_grover_operator_Q(A, O)
    for j in range(m_ancillas):
        n_iter = 2 ** j
        # Build Q^(2^j) as iterated Q. We avoid Q.power() because it
        # returns a Gate with auto-generated name that Aer's transpiler
        # sometimes doesn't decompose ; explicit composition is safer.
        Q_power = QuantumCircuit(n_data, name=f"Q^{n_iter}")
        for _ in range(n_iter):
            Q_power.compose(Q, range(n_data), inplace=True)
        # Controlled by ancilla j. Flatten before to_gate to avoid the
        # "circuit-NN_dg is not a gate instruction" error.
        Q_power_flat = _flatten(Q_power)
        ctrl_gate = Q_power_flat.to_gate(label=f"Q^{n_iter}").control(1)
        qc.append(ctrl_gate, [j] + list(range(m_ancillas, total)))

    # Step 4 : inverse QFT on ancillas (without final swaps to keep the
    # bit ordering consistent with the QPE convention).
    qc.append(QFT(m_ancillas, inverse=True, do_swaps=True).to_gate(label="IQFT"),
              range(m_ancillas))

    # Step 5 : measure ancillas.
    qc.measure(range(m_ancillas), range(m_ancillas))
    return qc


# ─── Run QAE and decode ───────────────────────────────────────────────


def run_qae(
    A: QuantumCircuit,
    O: QuantumCircuit,
    m_ancillas: int,
    shots: int = 10000,
    seed: int = 42,
) -> dict:
    """Run the QAE circuit and decode the measurement into a histogram
    over candidate amplitude estimates.

    Returns
    -------
    dict with :
      - "counts"      : measurement histogram on ancilla register
      - "y_grid"      : integers y ∈ {0, ..., 2^m - 1}
      - "p_estimates" : sin²(π y / 2^m) for each y
      - "probabilities" : empirical frequency from counts
      - "p_mode"      : peak amplitude estimate
      - "p_mean"      : weighted-mean amplitude estimate
    """
    qc = build_qae_circuit(A, O, m_ancillas)
    sim = AerSimulator(seed_simulator=seed)
    qc_t = transpile(qc, sim)
    result = sim.run(qc_t, shots=shots).result()
    counts = result.get_counts(qc_t)

    n_grid = 2 ** m_ancillas
    # Build histogram on integer grid 0..n_grid-1.
    hist = np.zeros(n_grid)
    for bits, c in counts.items():
        # Qiskit returns the bitstring MSB-first as q_{m-1}…q_0.
        # Combined with QFT(do_swaps=True), the standard QPE readout
        # gives the integer y directly as int(bitstring, 2). The
        # naive bit-reversal (int(bits[::-1], 2)) is INCORRECT here ;
        # it produces y_swapped = bit_reverse(y_true), confusing the
        # amplitude estimate by a non-trivial permutation of the grid.
        y = int(bits, 2)
        hist[y] += c

    # Decode each y to an amplitude estimate.
    y_grid = np.arange(n_grid)
    angles = math.pi * y_grid / n_grid
    p_estimates = np.sin(angles) ** 2

    # QAE has a two-fold degeneracy : y and (2^m - y) both encode the
    # same |sin(theta)|, so we fold to the lower half.
    folded_p = np.minimum(p_estimates, np.sin(math.pi * (n_grid - y_grid) / n_grid) ** 2)

    probs = hist / shots
    # Mode = argmax of histogram.
    y_mode = int(np.argmax(hist))
    p_mode = min(
        math.sin(math.pi * y_mode / n_grid) ** 2,
        math.sin(math.pi * (n_grid - y_mode) / n_grid) ** 2,
    )
    # Weighted mean (using folded estimates to handle the symmetry).
    p_mean = float(np.sum(probs * folded_p))

    return {
        "counts": dict(counts),
        "y_grid": y_grid.tolist(),
        "p_estimates": folded_p.tolist(),
        "probabilities": probs.tolist(),
        "p_mode": p_mode,
        "p_mean": p_mean,
        "y_mode": y_mode,
    }


# ─── Driver ────────────────────────────────────────────────────────────


def main() -> int:
    bracket = build_nba_bracket()
    p = first_round_probs(bracket)
    A = _build_bracket_unitary(bracket, p)
    O = _oracle_sas_champion(A.num_qubits)
    n_data = A.num_qubits

    print(f"NBA 2026 bracket : {bracket.n_matches} matches, {n_data} qubits")
    print(f"SAS champion constraints : {SAS_CONSTRAINTS}")
    print(f"Reference baseline (Grover sweep k=0) : p_0 ≈ 3.46%\n")

    # We sweep m = 4, 5, 6 to show convergence to the true value.
    results_per_m: dict[int, dict] = {}
    shots = 10000
    for m in [4, 5, 6]:
        print(f"Running QAE with m = {m} ancillas ({m + n_data} total qubits, "
              f"shots = {shots}) …")
        res = run_qae(A, O, m, shots=shots, seed=42 + m)
        results_per_m[m] = res
        print(f"  resolution Δp ≈ {math.pi**2 / 2**m:.4f}")
        print(f"  p_mode = {100 * res['p_mode']:.3f}%  "
              f"(y_mode = {res['y_mode']}, peak count = "
              f"{int(res['probabilities'][res['y_mode']] * shots)})")
        print(f"  p_mean = {100 * res['p_mean']:.3f}%\n")

    # ─── Plot empirical estimator distribution for the best m ──────────
    out_fig = Path(__file__).resolve().parents[1] / "figures"
    out_fig.mkdir(exist_ok=True)
    m_best = 6
    res = results_per_m[m_best]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    n_grid = 2 ** m_best
    p_grid = np.array(res["p_estimates"])
    probs = np.array(res["probabilities"])

    # Aggregate probabilities falling on the same folded p_grid value
    # (the min-folding produces duplicates : y and 2^m - y land on the
    # same estimate, with the same total weight after folding). Without
    # this step, the duplicated bars are stacked at the same x and the
    # eye underestimates the peak mass.
    unique_p, inverse_idx = np.unique(np.round(p_grid, 8), return_inverse=True)
    aggregated = np.zeros_like(unique_p)
    np.add.at(aggregated, inverse_idx, probs)

    # Plot as a stem-style histogram with thin bars (the grid is too
    # dense near p = 0 for the previous width=pi^2/2^m bars not to
    # overlap into a solid block). Each bar is 1.5e-3 wide.
    ax.bar(unique_p, aggregated, width=1.5e-3,
           color="#1f77b4", alpha=0.85, edgecolor="black", linewidth=0.3,
           label=f"QAE histogram, $m = {m_best}$ ancillas")
    ax.axvline(0.0346, color="orange", linestyle="--", linewidth=2,
               label="Reference $p_0 = 3.46\\%$ (Grover sweep $k = 0$)")
    ax.axvline(res["p_mode"], color="red", linestyle=":", linewidth=2,
               label=f"QAE mode estimate : {100 * res['p_mode']:.2f}\\%")
    ax.set_xlabel("Amplitude estimate $\\hat{p}$")
    ax.set_ylabel("Aggregated empirical probability")
    ax.set_title("Quantum Amplitude Estimation on the SAS-champion query")
    ax.set_xlim(-0.005, 0.12)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_fig / "fig5_qae_estimation.pdf")
    fig.savefig(out_fig / "fig5_qae_estimation.png", dpi=150)
    print(f"Wrote figure → {out_fig / 'fig5_qae_estimation.pdf'}")

    # ─── Plot convergence vs m ─────────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ms = sorted(results_per_m.keys())
    p_modes = [results_per_m[m]["p_mode"] for m in ms]
    p_means = [results_per_m[m]["p_mean"] for m in ms]
    eps_th = [math.pi**2 / 2**m for m in ms]
    ax2.plot(ms, [100 * p for p in p_modes], "o-", color="#1f77b4",
             label="QAE mode estimate")
    ax2.plot(ms, [100 * p for p in p_means], "s--", color="#2ca02c",
             label="QAE weighted-mean estimate")
    ax2.axhline(3.46, color="orange", linestyle="--",
                label="Reference $p_0 = 3.46\\%$")
    ax2.fill_between(ms, [100 * (0.0346 - e) for e in eps_th],
                     [100 * (0.0346 + e) for e in eps_th],
                     color="gray", alpha=0.2,
                     label=r"theoretical $\pm \pi^2/2^m$ resolution band")
    ax2.set_xlabel("Number of ancilla qubits $m$")
    ax2.set_ylabel(r"$\hat{p}$ (%)")
    ax2.set_title("QAE convergence vs ancilla register size")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    fig2.savefig(out_fig / "fig5b_qae_convergence.pdf")
    fig2.savefig(out_fig / "fig5b_qae_convergence.png", dpi=150)
    print(f"Wrote figure → {out_fig / 'fig5b_qae_convergence.pdf'}")

    # ─── Dump raw numbers ──────────────────────────────────────────────
    out_data = Path(__file__).resolve().parents[1] / "data"
    out_data.mkdir(exist_ok=True)
    summary = {
        "bracket": "NBA Playoffs 2026",
        "target": "SAS champion",
        "constraints": {str(k): v for k, v in SAS_CONSTRAINTS.items()},
        "reference_p0": 0.0346,
        "shots_per_run": shots,
        "results_per_m": {
            str(m): {
                "n_total_qubits": m + n_data,
                "resolution_pi2_over_2m": math.pi**2 / 2**m,
                "p_mode": r["p_mode"],
                "p_mean": r["p_mean"],
                "y_mode": r["y_mode"],
            }
            for m, r in results_per_m.items()
        },
    }
    (out_data / "qae_nba_results.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote data → {out_data / 'qae_nba_results.json'}")

    print("\nSummary :")
    print(f"  Reference p_0 (Grover sweep k=0, 50k shots) : 3.46%")
    for m in ms:
        r = results_per_m[m]
        print(f"  m = {m} : p_mode = {100*r['p_mode']:5.2f}%, "
              f"p_mean = {100*r['p_mean']:5.2f}%  "
              f"(±{100*math.pi**2/2**m:.2f}% theoretical)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
