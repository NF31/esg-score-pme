# SCORING.md — formule et pondération du score ESG

## Score par pilier

Pour un pilier donné (Environnement, Social, Gouvernance), le score est la moyenne
pondérée des réponses (échelle 0-4) sur ce pilier, normalisée sur 100 :

```
score_pilier = (somme(valeur_i * poids_i) / somme(poids_i * 4)) * 100
```

Le poids par défaut de chaque question est 1.0 — une question peut être pondérée plus
fort si elle est jugée plus structurante pour le pilier (ex. mesure de l'empreinte
carbone vs. éco-conception), sans changer la formule.

Seules les questions auxquelles l'entreprise a répondu comptent dans le calcul : un
questionnaire partiellement rempli donne quand même un score, sur le périmètre répondu.

## Score global : moyenne égale des 3 piliers

```
score_global = (score_environnement + score_social + score_gouvernance) / 3
```

**Choix assumé** : chaque pilier pèse un tiers du score global, quel que soit le nombre
de questions posées dans chacun. Alternative écartée : pondérer par le nombre de
réponses (un pilier avec plus de questions pèserait plus lourd), rejetée pour ne pas
favoriser artificiellement un pilier simplement parce qu'il contient plus de questions
dans la banque — l'équilibre E/S/G est un principe ESRS, pas un hasard de conception du
questionnaire.

## Recalcul

Le calcul est idempotent : relancer `/questionnaires/{id}/calculer-score` recalcule et
remplace les scores existants plutôt que d'en accumuler, ce qui permet de recalculer
après correction d'une réponse.

## Comparaison sectorielle (F11)

`/questionnaires/{id}/comparaison-sectorielle` renvoie, pour chaque pilier et le score
global, la moyenne des scores des **autres** questionnaires `TERMINE` d'entreprises du
même secteur (le questionnaire courant est exclu de sa propre moyenne). Aucun score
ESG n'est inventé pour les entreprises importées en F10 (CAC40) : elles n'ont pas de
questionnaire complété, donc ne contribuent à aucune moyenne tant qu'aucun diagnostic
réel n'est fait en leur nom. Condition nécessaire pour que le secteur soit un critère de
regroupement fiable : la saisie d'entreprise (formulaire et API) est contrainte à la même
nomenclature de secteurs que l'import F10 (`app/secteurs.py`, 21 sections NAF), plutôt
qu'un champ texte libre.

## Recommandations priorisées (F12)

`/questionnaires/{id}/recommandations` renvoie jusqu'à 5 questions à traiter en priorité,
triées par **gain potentiel** décroissant :

```
gain_potentiel = (4 - valeur_reponse) * poids_question
```

**Choix assumé** : trier par gain potentiel plutôt que par valeur de réponse brute. Une
question à poids 3.0 répondue 1/4 (gain 9) a plus d'impact sur le score qu'une question à
poids 1.0 répondue 0/4 (gain 1), même si sa réponse est moins mauvaise en apparence — c'est
elle le vrai "quick win". Les réponses déjà maximales (4/4) sont exclues, aucun gain
possible. Règle simple et explicable, pas de modèle ni d'IA nécessaire pour cette feature.

## Historique des scores (F13)

`/entreprises/{id}/historique-scores` renvoie, pour une entreprise donnée, tous les scores
(global et par pilier) de ses questionnaires **`TERMINE`**, triés par date de création du
questionnaire croissante. Un questionnaire `EN_COURS` ne produit aucun point : seuls les
scores réellement calculés (via `/calculer-score`) apparaissent dans l'historique.

**Choix assumé** : l'historique se lit au niveau de l'entreprise, pas du questionnaire — une
entreprise qui refait un diagnostic plus tard crée un nouveau `Questionnaire` rattaché à la
même entreprise plutôt que de modifier l'ancien, ce qui préserve chaque point de mesure passé.
Dans l'interface Streamlit, "Refaire un diagnostic (meme entreprise)" permet d'enchaîner un
nouveau questionnaire sur la même entreprise pour illustrer cette évolution.
