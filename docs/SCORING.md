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
