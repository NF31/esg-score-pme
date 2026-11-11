# FEATURES.md — Outil de scoring ESG pour PME

## Phase 1 — MVP diagnostic

| # | Fonctionnalité | Statut | Notes |
|---|---|---|---|
| F00 | Setup projet (venv, FastAPI CLI, structure, git) | Prêt | `pip install "fastapi[standard]"` + `fastapi dev/run`, 2026-09-11 |
| F01 | Modèle de données (entreprise, questionnaire, scores) | Prêt | `app/models.py` (SQLAlchemy 2.0), Entreprise/Question/Questionnaire/Reponse/Score, 2026-09-12 |
| F02 | Questionnaire ESG structuré (formulaire) | Prêt | 24 questions (8/pilier), `app/seed.py` + endpoints `/questions`, `/entreprises`, `/questionnaires`, 2026-09-12 |
| F03 | Moteur de scoring (calcul du score global + par pilier) | Prêt | `app/scoring.py` + endpoint `/calculer-score`, formule dans `docs/SCORING.md`, 2026-09-12 |
| F04 | Génération d'un rapport de synthèse (PDF ou page web) | Prêt | PDF via `app/rapport.py` (reportlab), endpoint `/rapport`, 2026-09-12 |
| F05 | API backend (FastAPI) exposant les endpoints | Prêt | Squelette + /health, 2026-09-11 |
| F06 | Interface utilisateur simple (Streamlit) | Prêt | `streamlit_app.py`, formulaire entreprise + questionnaire + score + PDF, 2026-09-12 |
| F07 | Persistance en base (PostgreSQL) | Prêt | `app/config.py` (pydantic-settings) + migrations Alembic (`alembic/`), `DATABASE_URL` bascule SQLite ↔ PostgreSQL sans changement de code, 2026-09-12 |
| F08 | Déploiement (Railway/Render) | Prêt | Streamlit + PostgreSQL sur Railway (projet `esg-score-pme`), auto-deploy sur push `main`, migrations Alembic en pre-deploy, 2026-09-12 |
| F09 | Tests unitaires sur le moteur de scoring | Prêt | `tests/test_scoring.py` : score min/max, pondération par poids de question, score global (moyenne égale des piliers répondus, piliers manquants ignorés), idempotence, erreurs (questionnaire introuvable/sans réponse), 2026-09-12 |
| F09b | Lint/format (ruff check + ruff format) | Prêt | Config dans `pyproject.toml`, même règles que Atlas, 2026-09-11 |
| F09c | CI GitHub Actions (lint + tests + SonarQube sur push/PR) | Prêt | `.github/workflows/ci.yml`, modèle Atlas (uv + ruff + pytest), 2026-09-11 |
| F09d | Scan de secrets (gitleaks, CI) | Prêt | `.gitleaks.toml` + `.github/workflows/gitleaks.yml`, modèle Atlas, 2026-09-11 |
| F09e | Analyse qualité (SonarCloud) | Prêt | Automatic Analysis (app GitHub native) — job CI manuel retiré (conflit détecté avec Automatic Analysis), 2026-09-11 |

## Phase 2 — Enrichissement

| # | Fonctionnalité | Statut | Notes |
|---|---|---|---|
| F10 | Import de données publiques (entreprises CAC40/PME labellisées) | Prêt | `app/import_entreprises.py` via l'API gouv.fr recherche-entreprises (nom/secteur/effectif réels, pas de score ESG inventé — cf. `docs/STACK.md`), 2026-09-12 |
| F11 | Comparaison sectorielle (score vs moyenne secteur) | Prêt | `app/benchmark.py` + endpoint `/comparaison-sectorielle`, moyenne des diagnostics réellement complétés dans le même secteur (pas de score inventé), 2026-09-12 |
| F12 | Recommandations priorisées (quick wins) | Prêt | `app/recommandations.py` + endpoint `/recommandations`, règles simples (gain potentiel = poids × marge de progression), pas d'IA, 2026-09-15 |
| F13 | Historique / évolution du score dans le temps | Prêt | `app/historique.py` + endpoint `/entreprises/{id}/historique-scores`, graphe `st.line_chart` dans Streamlit (score global des questionnaires `TERMINE` d'une meme entreprise), 2026-09-16 |

## Phase 3 — Différenciant

| # | Fonctionnalité | Statut | Notes |
|---|---|---|---|
| F14 | Extraction automatique de données depuis un rapport RSE (PDF) via LLM | Prêt | `app/extraction_pdf.py` (Claude, document PDF natif + tool use force) + endpoint `/questionnaires/{id}/extraire-pdf`, pre-remplit les sliders Streamlit (editable, rien n'est ecrit en base automatiquement), 2026-09-16 |
| F15 | Détection de greenwashing (écart discours/données chiffrées) | Prêt | `app/greenwashing.py` + endpoint `/questionnaires/{id}/detecter-greenwashing`, compare la suggestion IA (F14) a la reponse validee par l'utilisateur, aucun nouvel appel LLM, 2026-09-16 |
| F16 | Export rapport aligné format ESRS officiel | Prêt | `app/esrs.py` (referentiel simplifie) + `app/export_esrs.py`, endpoint `/questionnaires/{id}/rapport-esrs`, PDF regroupe par standard ESRS (E1/E3/E5/S1-S4/G1/ESRS 2) plutot que par les 3 piliers, 2026-09-16 |

## Hors périmètre (assumé)
- Pas de vrai partenariat entreprise (étude sur données publiques)
- Pas de microservices (monolithe modulaire volontaire)
- Pas d'authentification multi-utilisateur poussée (hors du cœur du sujet)
