# ESG Score PME

Outil de diagnostic et scoring ESG/RSE pensé pour les PME, dans le cadre de la double licence Numérique et Management (Toulouse Capitole / TSM).

Démo en ligne : https://esg-score-pme.streamlit.app (l'application peut mettre une trentaine de secondes à se réveiller si personne ne l'a ouverte depuis quelques jours).

## Problématique

Face à la simplification réglementaire européenne (Omnibus/CSRD) et à l'instabilité économique mondiale, dans quelle mesure un outil numérique accessible peut-il permettre aux PME de transformer le reporting extra-financier d'une contrainte administrative en un véritable levier de compétitivité et d'accès au financement ?

## Fonctionnalités

- **Recherche de l'entreprise** : par nom ou SIREN dans le répertoire officiel des
  entreprises ; secteur et effectif sont remplis à partir des données INSEE.
- **Diagnostic** : 24 questions (8 par pilier environnement, social, gouvernance) avec des
  réponses en langage clair, un pilier à la fois, puis une note de A à E, un score par pilier
  et un rapport PDF.
- **Comparaison sectorielle** : score de l'entreprise face à la moyenne des diagnostics
  réellement complétés dans son secteur (aucun score inventé).
- **Plan d'action** : actions concrètes classées par points gagnés pour le moins d'effort.
- **Profil ESRS** : radar des scores par thème (climat, eau, salariés, éthique...).
- **Historique** : évolution du score d'une même entreprise dans le temps.
- **Pré-remplissage par IA** : extraction des réponses depuis un rapport RSE en PDF, toujours
  validées par l'utilisateur avant enregistrement.
- **Détection de greenwashing** : écart entre ce que dit le rapport et les réponses validées.
- **Export ESRS** : rapport regroupé par standard ESRS (E1, E3, E5, S1-S4, G1, ESRS 2).
- **Entreprise exemple** : un bouton charge un diagnostic fictif complet pour découvrir
  l'outil sans rien remplir.

Stack : FastAPI, SQLAlchemy et Alembic, PostgreSQL, Streamlit. La démo publique tourne sur Streamlit Community Cloud.

## Setup

```bash
uv sync
uv run fastapi dev main.py       # API, sur http://127.0.0.1:8000 (doc interactive sur /docs)
uv run streamlit run streamlit_app.py   # interface utilisateur, sur http://127.0.0.1:8501
```

Optionnel — pré-remplissage du questionnaire depuis un rapport RSE (PDF) via l'IA (F14) : définir
`ANTHROPIC_API_KEY` dans un fichier `.env` à la racine (jamais commité). Sans cette clé, le reste
de l'application fonctionne normalement.

## Qualité de code

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

CI (lint + tests) et scan de secrets (gitleaks) tournent automatiquement sur chaque push/PR. SonarCloud analyse via son Automatic Analysis (app GitHub native), sans job CI dédié.

## Avancement

Voir [docs/FEATURES.md](docs/FEATURES.md) pour le détail des fonctionnalités et [docs/ROADMAP.md](docs/ROADMAP.md) pour les phases.
