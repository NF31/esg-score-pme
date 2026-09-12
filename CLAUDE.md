# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ESG Score PME — outil de diagnostic et scoring ESG/RSE pour PME, projet réalisé dans le cadre de la
double licence Numérique et Management (Toulouse Capitole / TSM). Problématique et contexte détaillés
dans `README.md`.

All project documentation lives in `docs/` — `docs/FEATURES.md` (backlog phasé avec statut),
`docs/ROADMAP.md` (les 3 phases), `docs/STACK.md` (choix de libs + pourquoi, ajoutées uniquement
quand la feature correspondante est attaquée), `docs/SCORING.md` (formule et pondération du score
ESG).

## Stack

FastAPI (backend) + Streamlit (frontend) + PostgreSQL/SQLAlchemy (persistance), monolithe modulaire
volontaire — pas de microservices, pas de partenariat entreprise réel (étude sur données publiques).
Gestion des dépendances via `uv`. Détail et justification de chaque choix dans `docs/STACK.md`.

## Commands

```bash
uv sync                        # installer les dépendances
uv run fastapi dev main.py     # lancer l'API en dev (reload auto), doc sur /docs
uv run fastapi run main.py     # lancer en mode production
uv run streamlit run streamlit_app.py  # interface utilisateur (http://127.0.0.1:8501)

uv run ruff check .            # lint
uv run ruff format --check .   # format check
uv run pytest                  # tests

uv run alembic revision --autogenerate -m "description"  # après modif de app/models.py
uv run alembic upgrade head                               # appliquer les migrations
```

CI (lint + tests) et gitleaks tournent sur chaque push/PR — voir `.github/workflows/`. SonarCloud
analyse via son Automatic Analysis (app GitHub native), pas de job CI dédié — cf. `docs/STACK.md`.

## Git workflow

Never commit directly on `main` — always branch first, even for a one-line change.
