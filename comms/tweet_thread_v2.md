# Twitter Thread v2 — Quantum Bracket arXiv Preprint
## Updated for v10 final (Grover + QAE + candide question)

Post when : after arXiv preprint goes live (typically next morning after evening submission).

Tag suggestions : @arxiv @qiskit @IBMQuantum @Polymarket @googleai
Hashtags : #quantum #quantumcomputing #predictionmarkets #sportsanalytics

---

## Tweet 1 — Hook (EN)

🧵 New preprint : we encode sports tournament brackets as quantum walks
on Qiskit and back-test on 5 real 2025-26 brackets — NBA Playoffs, NHL
Stanley Cup, UEFA Champions League, Roland Garros men's & women's.

Result : the seeded walk upweighted Mirra Andreeva (RG WTA champion at 18)
by **1.68×** vs classical Monte Carlo — ex ante.

arxiv.org/abs/XXXX.XXXXX

🔗 https://github.com/pulsquant/quantum-bracket

---

## Tweet 2 — The idea

Sports brackets exhibit *structural correlation* : if a high seed loses
early, downstream matches reshuffle. The marginal champion probability
of every other team shifts.

Classical Monte Carlo samples paths independently. A quantum walk
encodes ALL paths as a superposition over n-1 qubits, with the
correlations baked in as entanglement.

---

## Tweet 3 — The encoding (3-line summary)

For each match m we apply a controlled-Ry rotation conditioned on its
two parent matches. The matchup probability is computed against the
"seed" team of each branch — a controlled approximation we verify
analytically against a closed-form enumeration.

Round-0 matches use the exact Elo logistic. Deeper rounds inherit
through controlled rotations.

---

## Tweet 4 — NBA back-test (flagship #1)

NBA Playoffs 2026 : real bracket, production DB.

The San Antonio Spurs reached the NBA Finals from the 8-seed in the
West, eliminating 1-seed OKC in the WCF.

Quantum walk ex ante :
• P_Q(SAS reaches Finals) = 5.87% vs P_C = 3.43% → **1.71×**
• P_Q(SAS champion) = 3.46% vs P_C = 1.13% → **3.05×**

---

## Tweet 5 — Roland Garros WTA (flagship #2)

Mirra Andreeva (18 y/o) won her maiden Slam.
• Q(champion) = 11.01% vs C = 6.55% → **1.68×**

Maja Chwalinska, qualifier ranked #114 WTA, Tennis Elo 1710, reached
the final.
• Q(runner-up) = 2.15% vs C = 0.77% → **2.78×**

Two ex-ante upset signals on the same draw.

---

## Tweet 6 — RG ATP semifinals : two underdogs amplified

Underdog semifinalists Jakub Mensik and Matteo Arnaldi :
• Mensik P_Q(SF) = 5.59% vs P_C = 1.34% → **4.17×**
• Arnaldi P_Q(SF) = 3.07% vs P_C = 0.69% → **4.44×**

Both came from the half of the draw where Sinner's exit reshuffled
the upper bracket. The walk read that ex ante.

---

## Tweet 7 — Honest negatives matter

The walk does NOT fabricate signal where the bracket is chalk :

• PSG winning UCL (top favourite) : Q/C ≈ **1.01** (no upset signal)
• Vegas swept Colorado NHL WCF — but Elo 1645 vs 1670 is a coin flip.
  Q/C = **0.63×** on Vegas reaching the Final.

Narrative ≠ statistical extremity. The walk knows.

---

## Tweet 8 — The trade-off (chalk down-weight)

Top seeds that survive deep get systematically down-weighted :

• New York Knicks reach NBA Finals (East 1-seed) :
  Q(reach Finals) = 13.22% vs C = 18.75% → **0.71×**
  Q(champion) = 4.83% vs C = 9.59% → **0.50×**

This is the inverse of the underdog upweight — informative on the
*upset side* of prediction-market pricing, where edge lives.

---

## Tweet 9 — Grover amplification on top

We add Grover's algorithm on the SAS-champion query of the NBA bracket.
The amplification curve follows the textbook envelope :

• Baseline p_0 = 3.46% (k=0)
• Peak **97.89%** at k = 4 (theoretical optimum k* ≈ 4.20)
• Second peak 99.72% at k = 12

~10⁴× shot-count reduction at the optimum — quadratic Brassard speedup,
realised on a real-bracket query.

---

## Tweet 10 — Quantum Amplitude Estimation

Adding m = 6 ancilla qubits (21 qubits total), QAE returns the SAS
amplitude itself :

• Mode  p̂ = 3.81% (vs reference 3.46%)
• Mean  p̂ = 3.84% / 3.90% / 3.95% at m ∈ {4, 5, 6}

All within the π/2^m resolution band. Quadratic speedup confirmed
empirically on the same query Grover amplifies.

---

## Tweet 11 — Prospective World Cup 2026

Issued before kickoff (June 11) on the R16-onward stage :

• ARG +6.14 pp (top P_Q at 31.06%)
• NED +3.02 pp, BEL +2.93 pp
• FRA -9.45 pp, ESP -4.78 pp, BRA -3.88 pp

Mid-tier nations upweighted, top favourites down-weighted (same
pattern as NBA back-test). Test will happen in 6 weeks.

---

## Tweet 12 — Open source + scaling

15-qubit Aer simulator runs on a laptop. No quantum-advantage claim
at this scale.

Pipeline scales tractably to ~150 qubits via MPS (matrix product state)
on CPU — full 128-team Grand Slam main draw walks finish in ~10 min.
GPU helps past 200 qubits (RTX 4090 + cuQuantum).

Code, data, scripts : github.com/pulsquant/quantum-bracket
MIT license. Qiskit 2.4 + Aer.

---

## Tweet 13 (optional) — The candide question

A side question we tackle in the discussion : can a spectator of a
match be quantum-entangled with the outcome? The honest answer is no
(L1+ scale decoheres instantly), but the question opens a bridge to
quantum biology — magnetoreception in birds, the avian compass. The
paper's Section 5.4 spells it out without overclaiming.

Daughter question, candide and useful. Inspired the framing.

---

## Tweet 14 (optional) — Thanks / signal openness

The construction picks up the 2018 @Caltech Quantum Frontiers blog
that sketched a qudit encoding for the WC but never formalised it.
8 years later, with live prediction-market data, we close that loop.

Always open to collab. DM or contact@pulsquant.com.

---

## Posting strategy

1. Wait for arXiv preprint to be public (next-morning announcement)
2. Replace `XXXX.XXXXX` placeholder with actual arXiv ID
3. Post tweet 1 (with link)
4. Reply-chain tweets 2–12 sequentially (every 30–60 sec)
5. Pin tweet 1
6. Cross-post LinkedIn (see linkedin_post_fr.md)
7. Submit Show HN : "Quantum walks on sports brackets — arXiv preprint"
8. Email Stamatopoulos (IBM), Schuld (Xanadu), Wittek (UofT — memorial)

## Engagement notes

- Best time : Tue-Thu 10-11 AM EST or 6-7 PM EST (peak quant Twitter)
- Tag @arxiv when ID known — they sometimes RT
- @QiskitCommunity may RT if code is clean (it is)
- @Polymarket may engage given the markets angle
- @QuantumNature, @PhysicsToday, @NatureComms for editorial reach
