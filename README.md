# Quantum Bracket — Quantum walk on tournament brackets for prediction-market probability estimation

Reference code for the arXiv preprint **"Bracket-Structured Probability
Estimation via Quantum Walks and Live Prediction-Market Validation"**
(June 2026).

## What it does

Encodes a single-elimination tournament bracket (NBA Playoffs, FIFA
World Cup knockout, Roland Garros draw, etc.) as a Qiskit quantum
circuit where each match becomes a qubit and bracket structural
correlations are encoded as multi-controlled rotations between match
qubits.

Sampling the circuit yields a champion-distribution that systematically
upweights paths in which underdog upsets propagate through multiple
rounds — empirically validated against the 2026 NBA Playoffs, where
the seeded quantum walk assigned **3.05× the realised-champion
probability** of an unbiased classical Monte Carlo for the San Antonio
Spurs (8-seed Finals winner).

## Repo layout

```
quantum_bracket/
├── src/
│   └── qbracket.py             — Bracket data model, quantum circuit
│                                 builder, classical MC baseline.
├── scripts/
│   ├── smoke_test.py           — 8-team sanity check (Q vs C).
│   ├── verify_seeded_bias.py   — Closed-form verification that Q ≈ S.
│   ├── run_nba_playoffs_2026.py — 15-qubit back-test, SAS upset.
│   ├── run_wc2026.py           — Prospective WC 2026 R16+ prediction.
│   └── make_plots.py           — Generate paper figures.
├── data/                       — JSON outputs (one per experiment).
├── figures/                    — PDF + PNG figures for the paper.
├── paper/
│   ├── main.tex                — arXiv preprint source.
│   └── references.bib          — BibTeX bibliography.
├── venv/                       — Python 3.10 virtualenv with Qiskit 2.4.
└── README.md
```

## Reproducing the results

```bash
cd research/quantum_bracket
python3 -m venv venv
source venv/bin/activate
pip install qiskit qiskit-aer numpy matplotlib scipy

# 8-team sanity check (~3 seconds)
python3 -m scripts.smoke_test

# Closed-form verification (~10 seconds)
python3 -m scripts.verify_seeded_bias

# 2026 NBA Playoffs back-test (~30 seconds, 15 qubits)
python3 -m scripts.run_nba_playoffs_2026

# 2026 FIFA World Cup R16+ prospective (~30 seconds, 15 qubits)
python3 -m scripts.run_wc2026

# Generate paper figures (~1 minute)
python3 -m scripts.make_plots
```

## Citation

If you use this code in academic work, please cite the preprint :

```bibtex
@misc{pulsquant_quantum_bracket_2026,
  title  = {Bracket-Structured Probability Estimation via Quantum
            Walks and Live Prediction-Market Validation},
  author = {PulsQuant Research},
  year   = {2026},
  note   = {arXiv preprint, submitted June 2026.}
}
```

## Honest limitations

1. **No quantum advantage claimed.** At 15 qubits the Qiskit Aer
   sampling is competitive with but not faster than naive Python MC
   (0.16 s vs 0.06 s for 50 000 shots/sims). The contribution is the
   conceptual encoding, not a performance speedup at this scale.

2. **Seeded approximation.** The conditional encoding for deeper-round
   matches uses canonical seed-following paths to identify which
   teams meet, rather than encoding all $2^{r-1}$ parent
   configurations. This introduces a controlled bias toward
   structural-upset paths, which we document and verify rather than
   eliminate. The bias is reproducible and matches a closed-form
   seeded estimator to within sampling noise (max $|\Delta| =
   0.09$ pp on the 16-team bracket).

3. **Prospective WC 2026 is a balanced-bracket baseline.** The actual
   knockout pairings will be determined by the group-stage results
   (June 27, 2026), which were not yet known at the time of
   submission. The reported probabilities are expected values under
   the standard 1-vs-16 balanced bracket assumption.

## License

MIT.

## Acknowledgments

Built on top of the PulsQuant production bracket simulator
(`scripts/tournament/simulate_bracket.py`), which provides the
classical Monte Carlo baseline and the WC 2026 group-stage marginals.
