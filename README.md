# ESG Score PME

Outil de diagnostic et scoring ESG/RSE pensé pour les PME, dans le cadre de la double licence Numérique et Management (Toulouse Capitole / TSM).

Démo en ligne : https://streamlit-production-6f3b.up.railway.app

## Problématique

Face à la simplification réglementaire européenne (Omnibus/CSRD) et à l'instabilité économique mondiale, dans quelle mesure un outil numérique accessible peut-il permettre aux PME de transformer le reporting extra-financier d'une contrainte administrative en un véritable levier de compétitivité et d'accès au financement ?

## Setup

```bash
uv sync
uv run fastapi dev main.py       # API, sur http://127.0.0.1:8000 (doc interactive sur /docs)
uv run streamlit run streamlit_app.py   # interface utilisateur, sur http://127.0.0.1:8501
```

## Qualité de code

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

CI (lint + tests) et scan de secrets (gitleaks) tournent automatiquement sur chaque push/PR. SonarCloud analyse via son Automatic Analysis (app GitHub native), sans job CI dédié.

## Avancement

Voir [docs/FEATURES.md](docs/FEATURES.md) pour le détail des fonctionnalités et [docs/ROADMAP.md](docs/ROADMAP.md) pour les phases.
