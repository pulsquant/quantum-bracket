# Post LinkedIn (FR) — Annonce preprint quantum bracket

À publier dès que l'arXiv ID est disponible. Image suggérée :
`figures/fig2_nba_2026.png` (distribution Q vs C sur NBA Playoffs).

---

## Version courte (~250 mots)

🎯 Nouveau preprint arXiv : on encode les tableaux d'élimination des
tournois sportifs en **marches quantiques** sur Qiskit, et on backtest
sur cinq vrais tableaux 2025-2026.

**Le problème** : un bracket sportif contient des corrélations
structurelles entre les matchs — si une tête de série élevée perd tôt,
tout le reste du tableau bouge. Pricer correctement ces corrélations
est central pour les marchés de prédiction et les bookmakers. Le Monte
Carlo classique échantillonne les chemins indépendamment ; la marche
quantique encode TOUS les chemins en superposition avec corrélations
intriquées.

**Les résultats** :
🏀 **NBA Playoffs** : SAS (tête de série 8 à l'Ouest) atteint la
finale NBA en éliminant OKC (1) en finale de conf — la marche
quantique l'amplifiait **×1,71** ex ante (et ×3,05 sur le titre).

🎾 **Roland Garros femmes** : Mirra Andreeva (18 ans) gagne son
premier Slam — amplifiée **×1,68** ex ante. Maja Chwalinska, qualifiée
#114 WTA, atteint la finale — amplifiée **×2,78**.

🎾 **Roland Garros hommes** : demi-finalistes outsiders Mensik
(×4,17) et Arnaldi (×4,44).

✅ **Contrôles négatifs propres** : PSG champion UCL (Q/C ≈ 1,01, pas
d'over-claim), Vegas balayant Colorado NHL (×0,63, le narratif d'upset
ne tient pas statistiquement).

🚀 On ajoute Grover et l'estimation d'amplitude quantique (QAE) :
pic d'amplification à 97,89 % sur la requête SAS-champion, gain de
shots ~10⁴×, et convergence quadratique sur l'estimation
d'amplitude.

À l'échelle simulateur (15 qubits), aucune revendication d'avantage
quantique. La contribution est conceptuelle : un encodage naturel
des corrélations bracket.

📄 arXiv : arxiv.org/abs/XXXX.XXXXX
💻 Code : github.com/pulsquant/quantum-bracket

#QuantumComputing #PredictionMarkets #SportsAnalytics #Qiskit #Recherche

---

## Version longue (~600 mots)

🎯 Mon preprint vient d'être soumis sur arXiv : "Bracket-Structured
Probability Estimation via Quantum Walks and Live Prediction-Market
Validation".

**Pourquoi ce sujet**

Je travaille depuis un an sur l'estimation de probabilités sur les
marchés de prédiction sportifs (Polymarket, Jupiter, Kalshi). Une
récurrence des saisons 2025-2026 : des outsiders qui font des parcours
profonds difficiles à pricer par Monte Carlo standard. Les
San Antonio Spurs (tête de série 8) éliminent OKC (1) en finale de
conférence Ouest NBA. Sinner, Świątek, Sabalenka tombent avant les
quarts à Roland Garros. Vegas balaie Colorado en NHL.

Aucun de ces résultats n'est statistiquement extrême sur son match isolé
— un Elo bien calibré leur donne à chacun 15-30 % de chances. Ce qui
les rend difficiles à pricer, c'est le **poids joint** qu'ils portent
dans l'arbre du tableau une fois conditionné sur un parcours profond.

**L'idée**

Encoder le tableau en circuit quantique : un qubit par match, des
portes RY contrôlées par les deux matchs parents pour propager la
matchup elo-driven le long de l'arbre. Le tableau entier devient une
superposition de chemins, avec les corrélations entre matchs encodées
comme intrication entre qubits conditionnellement dépendants.

À la différence du Monte Carlo classique qui échantillonne chaque
chemin indépendamment, la marche quantique "voit" toutes les
réorganisations simultanément.

**Les backtests**

Cinq vrais tableaux 2025-2026 chargés depuis la base PulsQuant
(production, pas des hypothèses jouet) :

🏀 NBA Playoffs : SAS atteint les finales ×1,71 ex ante (champion ×3,05)
🏒 NHL Conference Finals : Vegas Q/C = 0,63 (le narratif d'upset ne
tient pas statistiquement, et la marche l'attrape)
⚽ UCL : PSG champion Q/C ≈ 1,01 (chalk = pas de signal d'upset
fabriqué)
🎾 RG femmes : Andreeva ×1,68 sur le titre, Chwalinska (qualifiée
#114 WTA) ×2,78 sur la finale
🎾 RG hommes : Mensik ×4,17 et Arnaldi ×4,44 sur les demi-finales

**Extensions opérationnelles**

J'implémente aussi Grover (amplification de la requête "SAS champion") :
pic à 97,89 % d'amplitude à k=4 itérations, gain de shots ~10⁴× sur
une précision relative de 5 %. Puis QAE (estimation d'amplitude
quantique, Brassard-Hoyer-Mosca-Tapp 2002) avec 6 qubits ancilla :
l'estimation converge vers la valeur vraie 3,46 % avec la résolution
théorique π/2^m attendue.

**Limites assumées**

Aucune revendication d'avantage quantique à 15 qubits — sur laptop
le MC classique est plus rapide. La contribution est conceptuelle :
un encodage NATUREL des corrélations bracket que le MC classique ne
reproduit qu'au prix d'un conditionnement explicite chemin par chemin.

Le pipeline passe à l'échelle de manière tractable via MPS (matrix
product state) jusqu'à ~150 qubits sur CPU, et nettement plus haut
sur GPU + cuQuantum. Les 50-100 qubits logiques attendus du matériel
tolérant aux fautes de première génération arrivent.

**Pour qui ça compte**

Si tu travailles sur un problème prédictif à structure bracket —
esports, élections au scrutin majoritaire à deux tours, tournois
d'échecs, championnats juridiques — l'encodage est direct à
réutiliser. Code MIT, scripts de reproduction, paper EN + FR.

📄 arXiv : arxiv.org/abs/XXXX.XXXXX
💻 Code : github.com/pulsquant/quantum-bracket
🇫🇷 Version FR : disponible sur demande

Discussion ouverte. DM ou contact@pulsquant.com.

#QuantumComputing #PredictionMarkets #SportsAnalytics #Qiskit
#Recherche #Quant #ArXiv

---

## Notes de publication

- **Image suggérée** : `figures/fig2_nba_2026.png` (distribution Q vs C
  sur NBA Playoffs, visuellement parlant — barres bleues vs orange,
  redistribution claire de masse)
- **Timing** : mardi-jeudi 9h00 ou 18h00 heure de Paris (audience
  quant FR + US matin)
- **Tag entreprises pertinentes** : @IBM Quantum, @QC Ware, @PASQAL,
  @Atos Quantum, @Quantinuum (selon ton réseau)
- **Si tu veux un boost** : @Lex Sotirelis et @Carla Coupil sur LinkedIn
  pour le réseau quant FR

## Réponse attendue par audience

- **Quant traditionnel** : "intéressant mais où est l'avantage ?"
  → réponse : "conceptuel, pas asymptotique. Lit Section 5"
- **Quantum researcher** : "cuQuantum + tensor network c'est trivial"
  → réponse : "oui, mais l'encodage du bracket est nouveau, pas le
  simulateur"
- **Sports analytics** : "calibration vs Elo source ?"
  → réponse : "Tennis Elo Lockedshall + skellam NHL custom + DC soccer.
  Détails Appendice"
- **Polymarket trader** : "actionnable ?"
  → réponse : "oui, j'ai un bot. Voir issue #455 sur le repo"
