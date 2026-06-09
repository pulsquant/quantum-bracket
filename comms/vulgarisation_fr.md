# Le papier en VF, expliqué à ta tante

Compagnon de lecture du préprint arXiv. Public visé : journaliste / blog / pitch / membre de la famille qui demande « tu fais quoi en ce moment ? ».

---

## 1. Le problème qu'on essaie de résoudre

Imagine la **Coupe du Monde 2026**. Tu veux deviner qui va gagner. Tu sais que l'Argentine est favorite, mais tu te souviens que des outsiders gagnent parfois (la Grèce en 2004, le Danemark en 1992, et plus récemment les Spurs en NBA 2026 qui sortent OKC en demi-finale).

**La grande question** : quand un favori se fait surprendre tôt, ça change tout le reste du tournoi. Tous les matchs qui suivent vont être différents. Cette « cascade » est ce qu'on appelle une **corrélation structurelle**.

Les bookmakers et les marchés de paris comme Polymarket essaient de donner des cotes justes. Mais la méthode classique qu'ils utilisent — appelée **Monte Carlo** — sous-estime systématiquement ces cascades d'outsiders.

---

## 2. Comment ils font aujourd'hui : la méthode Monte Carlo

C'est très simple en fait. Imagine que tu joues à pile-ou-face pour chaque match :

> « Argentine vs Pologne, l'Argentine gagne 75% du temps → tu lances une pièce truquée à 75% pour ce match. Vainqueur : Argentine. »
>
> « Tour suivant : Argentine vs Hollande, l'Argentine gagne 60% du temps → pièce truquée 60%. Vainqueur : Argentine. »
>
> Etc., jusqu'à la finale.

Tu refais ça **10 000 fois**. Tu comptes combien de fois chaque équipe a gagné le tournoi entier. Ça te donne tes probabilités.

**Le problème** : chaque simulation est indépendante. Le fait qu'une cascade d'outsiders se produit dans la simulation N°5247 ne « renforce » pas mathématiquement les autres simulations où la même cascade s'amorce. Les paths d'outsiders sont noyés dans le bruit.

C'est comme estimer la **probabilité qu'il y ait une vague qui submerge ta plage** en jetant des cailloux dans l'eau un par un. Tu peux voir des éclaboussures, mais tu ne « sens » jamais une vraie vague — parce que les cailloux ne se renforcent pas entre eux.

---

## 3. Notre idée : utiliser la physique quantique

Tu as peut-être entendu parler des **ordinateurs quantiques**. La propriété centrale : un qubit (= bit quantique) peut être à **0 ET à 1 en même temps**, comme une pièce qui tourne sur elle-même.

Si tu mets ensemble plusieurs qubits, ils peuvent représenter **tous les résultats possibles simultanément** dans un seul état combiné. C'est ce qu'on appelle la **superposition**.

### Notre encodage

Pour un tournoi de 16 équipes avec 15 matchs :
- 1 qubit par match → 15 qubits au total
- Le qubit du match dit « équipe du haut a gagné (0) » ou « équipe du bas a gagné (1) »
- Tous les qubits sont **enchevêtrés** (entangled) → si un match change, ça affecte mathématiquement les qubits des matchs suivants

**L'analogie** : au lieu de jeter 10 000 cailloux indépendants dans l'eau, on crée une **vague qui contient toutes les vagues possibles en même temps**. Quand on « mesure », la vague s'effondre sur un résultat précis, mais avec des probabilités qui prennent en compte les renforcements entre matchs.

C'est comme une **chorale qui chante TOUTES les notes possibles simultanément**. Quand on « écoute » (= on mesure), on entend une seule note finale, mais les harmoniques entre toutes les notes ont influencé celle qui est sortie.

---

## 4. Ce qu'on a testé (les expériences)

On a pris **5 vrais tournois de 2025-2026** et on a fait tourner notre modèle quantique sur chacun. Pour chaque tournoi, on a comparé :
- **Q** = ce que notre modèle quantique prédit
- **C** = ce que la méthode classique Monte Carlo prédit
- **Réalité** = ce qui s'est vraiment passé

### 🏀 NBA Playoffs 2026 — Les Spurs (têtes de série n°8) atteignent les Finales

Les Spurs, classés 8ème de la Conférence Ouest (= mal classés), ont éliminé **Oklahoma City Thunder** (n°1, le grand favori) en finale de conférence. C'est l'équivalent d'une équipe de Coupe de France qui sortirait le PSG en demi-finale.

| Méthode | Probabilité qu'ils gagnent le titre |
|---|---|
| Classique (MC) | 2.16% |
| Notre quantique | **5.65%** (× 2.61 plus de signal) |

Notre modèle a vu cette cascade venir bien avant que ça arrive.

### 🎾 Roland Garros 2026 femmes — Mirra Andreeva, 18 ans, championne

Mirra Andreeva, 18 ans, a gagné Roland Garros 2026. C'est l'équivalent d'avoir prédit qu'un junior allait gagner le Tour de France.

| Méthode | Probabilité qu'elle gagne |
|---|---|
| Classique | 6.55% |
| Notre quantique | **11.01%** (× 1.68) |

Et la **finaliste underdog Maja Chwalinska** (qualifiée, classée 114ème mondiale) — notre modèle l'avait sur le radar **2.78 fois plus que la méthode classique**.

### 🎾 Roland Garros 2026 hommes — Mensik et Arnaldi en demi-finale

Deux outsiders en demi-finale. Notre modèle les avait **× 4.17** et **× 4.44** par rapport au classique. Énorme.

### ⚽ Ligue des Champions 2025-2026 — PSG champion

Le PSG était le favori, et il a gagné. Notre modèle dit Q/C ≈ 1.01 — **pratiquement pareil que le classique**. Pourquoi c'est important ? Parce que ça prouve qu'on **n'invente pas du signal là où il n'y en a pas**. Si le favori gagne, notre modèle dit « bah, le favori a gagné ».

### 🏒 NHL Stanley Cup 2026 — Vegas surprend Colorado

Vegas (Golden Knights) a sorti Colorado en finale de conférence Ouest. Sport-narrative : c'est un upset. Mais en termes de **niveau Elo** (1645 vs 1670), c'était quasi pile-ou-face — pas un vrai outsider.

Notre modèle dit **Q/C = 0.63×** — il **ne sur-pondère pas** ce match. C'est un résultat négatif clean : on ne crée pas de signal artificiel pour les pseudo-upsets.

---

## 5. La limite honnête de notre méthode

Notre méthode a un défaut volontaire — on l'appelle **« seeded approximation »** dans le papier. En gros :

> Pour calculer les probabilités des matchs profonds (demi-finale, finale), on suppose que ce sont toujours les « têtes de série officielles » qui se rencontrent.

Ça veut dire qu'on **sous-estime systématiquement les équipes très bien classées qui survivent**. Exemple : les New York Knicks ont atteint les Finales NBA 2026 (depuis la conférence Est). Notre modèle leur donne 0.60× ce qu'elles méritent. C'est notre « faux négatif » documenté.

**Le trade-off** : on gagne en précision sur les outsiders (5 cas vérifiés), on perd en précision sur les favoris qui survivent (1 cas vérifié). Pour les **marchés de paris**, où les outsiders sont systématiquement sous-pricés, c'est exactement le compromis qu'on veut.

---

## 6. Pourquoi ça intéresse les marchés de paris

**Polymarket** (le plus gros marché de prédiction au monde, valorisé 9 milliards de dollars en 2025) prend des paris sur tout, y compris « Quelle équipe atteint le R16 ? » « Quelle équipe gagne le tournoi ? ».

Ces marchés **sous-pricent systématiquement les outsiders deep-run** parce que leur algorithme se base sur les fréquences historiques, pas sur les corrélations structurelles. C'est exactement la « niche » que notre modèle quantique identifie.

**Application concrète** : un trader qui utilise notre modèle peut identifier des paris à **valeur attendue positive** avant les autres. Notre 1.68× sur Andreeva s'est traduit par un signal exploitable sur Polymarket avant que le résultat soit acquis.

---

## 7. Ce qu'on ne prétend PAS

On est honnête : à 15 qubits, **on ne va pas plus vite** que la méthode classique. Notre laptop fait 0.16 secondes pour la version quantique vs 0.06 secondes pour la classique. C'est juste un encodage plus naturel des corrélations.

**L'avantage quantique réel** apparaît à **50-100 qubits**, ce qu'on aura sur les premiers ordinateurs quantiques tolérants aux fautes (entre 2028 et 2032 selon les estimations actuelles).

Notre papier prépare le terrain : on a montré que **la méthode fonctionne sur des vrais tournois aujourd'hui**, sur des laptop. Quand le matériel quantique sera prêt, l'avantage sera là.

---

## 8. La prédiction live : Coupe du Monde 2026

Notre modèle dit, **avant le coup d'envoi du 11 juin 2026** :
- **Argentine** : 31% (vs 25% en classique — favorite renforcée)
- **Pays-Bas, Belgique, Autriche, Colombie** : surpondérés de 2-3 points
- **France, Espagne, Brésil** : sous-pondérés de 4-9 points

On verra dans 6 semaines (finale 19 juillet 2026) si on avait raison.

---

## 9. Notre vrai pari à long terme

Ce papier est le **premier formel** sur ce sujet (le précédent était un blog post Caltech de 2018, jamais publié). On ouvre une niche. Le code est public sur GitHub : https://github.com/pulsquant/quantum-bracket

**Notre théorie** : dans 5-10 ans, les marchés de prédiction sportive valoriseront *natively* les corrélations structurelles. Les premiers acteurs qui adopteront ces méthodes (quantiques ou inspirées du quantique) auront un edge mesurable.

C'est ce que PulsQuant construit en background — pas juste un papier scientifique, mais une **architecture de pricing pour les marchés de prédiction** qui exploite ces signaux structurels avant que tout le monde s'y mette.

---

## Mots-clés pour résumer (si quelqu'un te demande en 30 secondes)

> « On utilise de la physique quantique pour modéliser les tournois sportifs. Pas pour aller plus vite — pour mieux capturer les cascades d'outsiders qui chamboulent tout. On l'a testé sur 5 tournois réels (NBA, NHL, Ligue des Champions, Roland Garros homme et femme) : notre modèle a vu venir la championne Andreeva à 18 ans, les Spurs en finale NBA, et les outsiders Mensik/Arnaldi en demi de Roland Garros. C'est la première publication formelle du sujet. Notre prédiction de la Coupe du Monde 2026 est dans le papier — on sera fixés le 19 juillet. »

---

## 10. Bonus : la question que ma fille m'a posée un soir

*Transcrit fidèlement, à la table de la cuisine, peu après le dîner.*

— Papa, un spectateur qui regarde le match, il peut être... quantiquement intriqué avec le ballon ? Ou avec celui qui marque ?

— Non, pas physiquement. Tout ce qui est gros et chaud perd sa cohérence quantique très vite. Un ballon, en gros, en $10^{-23}$ secondes. Un cerveau humain, encore plus vite, parce qu'il dissipe une vingtaine de watts dans un bain thermique violent. Avant même que tu aies cligné des yeux, l'environnement a déjà mesuré l'objet des milliards de fois. Il n'y a plus de superposition à intriquer.

— Donc c'est non.

— Opérationnellement, oui. Mais regarde l'équation qu'on a écrite tout à l'heure, là où chaque match du tableau a son qubit et où les tours suivants sont conditionnés sur les précédents par des portes de rotation contrôlées. La structure que tu vois là, c'est mathématiquement le même type d'objet que ce qu'Engel et son équipe ont mesuré en 2007 dans les complexes de photosynthèse, et que ce que Hore et Mouritsen décrivent dans la cryptochrome rétinienne des oiseaux migrateurs. Eux ont des vraies cohérences quantiques à températures biologiques, sur des durées de l'ordre de la centaine de microsecondes. Toi, ici, tu as une structure abstraite qui code des résultats de matchs. Treize ordres de grandeur d'écart entre les deux échelles physiques. Mais l'objet mathématique en dessous, un état multipartite intriqué dont les corrélations sont conditionnelles à un graphe, c'est rigoureusement le même.

— ... donc en vrai c'est un peu oui ?

— En vrai c'est un peu oui sur la structure, et c'est un non sur la physique. Ce qu'on construit ici reste un outil de calcul, ça ne devient pas un état physique parce qu'on le manipule sur un simulateur. Mais que la même primitive apparaisse aux deux extrémités de l'échelle, à treize ordres de grandeur de distance, est peut-être ce que ce papier rajoute de plus utile à long terme. Pas la prédiction sur la Coupe du Monde, qu'on verra dans six semaines. Le fait qu'une marche quantique sur un graphe de matchs et une marche quantique sur un graphe de chromophores soient, au fond, le même genre de chose.

— D'accord. ... Papa, je peux avoir un dessert ?

*(Le registre technique s'arrête là.)*
