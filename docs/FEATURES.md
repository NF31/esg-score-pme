# FEATURES.md — Outil de scoring ESG pour PME

## Phase 1 — MVP diagnostic

| # | Fonctionnalité | Statut | Notes |
|---|---|---|---|
| F00 | Setup projet (venv, FastAPI CLI, structure, git) | 🟢 | `pip install "fastapi[standard]"` + `fastapi dev/run`, 2026-09-11 |
| F01 | Modèle de données (entreprise, questionnaire, scores) | 🟢 | `app/models.py` (SQLAlchemy 2.0), Entreprise/Question/Questionnaire/Reponse/Score, 2026-09-12 |
| F02 | Questionnaire ESG structuré (formulaire) | 🟢 | 24 questions (8/pilier), `app/seed.py` + endpoints `/questions`, `/entreprises`, `/questionnaires`, 2026-09-12 |
| F03 | Moteur de scoring (calcul du score global + par pilier) | 🔴 | Pondération justifiée dans le rapport |
| F04 | Génération d'un rapport de synthèse (PDF ou page web) | 🔴 | |
| F05 | API backend (FastAPI) exposant les endpoints | 🟢 | Squelette + /health, 2026-09-11 |
| F06 | Interface utilisateur simple (Streamlit) | 🔴 | Saisie questionnaire + affichage résultat |
| F07 | Persistance en base (PostgreSQL) | 🔴 | Historisation des réponses |
| F08 | Déploiement (Railway/Render) | 🔴 | |
| F09 | Tests unitaires sur le moteur de scoring | 🔴 | Priorité : la logique métier doit être fiable — squelette `test_health.py` en place |
| F09b | Lint/format (ruff check + ruff format) | 🟢 | Config dans `pyproject.toml`, même règles que Atlas, 2026-09-11 |
| F09c | CI GitHub Actions (lint + tests + SonarQube sur push/PR) | 🟢 | `.github/workflows/ci.yml`, modèle Atlas (uv + ruff + pytest), 2026-09-11 |
| F09d | Scan de secrets (gitleaks, CI) | 🟢 | `.gitleaks.toml` + `.github/workflows/gitleaks.yml`, modèle Atlas, 2026-09-11 |
| F09e | Analyse qualité (SonarCloud) | 🟢 | Automatic Analysis (app GitHub native) — job CI manuel retiré (conflit détecté avec Automatic Analysis), 2026-09-11 |

## Phase 2 — Enrichissement

| # | Fonctionnalité | Statut | Notes |
|---|---|---|---|
| F10 | Import de données publiques (entreprises CAC40/PME labellisées) | 🔴 | Pour peupler un benchmark |
| F11 | Comparaison sectorielle (score vs moyenne secteur) | 🔴 | |
| F12 | Recommandations priorisées (quick wins) | 🔴 | Règles simples au départ, pas besoin d'IA |
| F13 | Historique / évolution du score dans le temps | 🔴 | Graphe simple |

## Phase 3 — Différenciant

| # | Fonctionnalité | Statut | Notes |
|---|---|---|---|
| F14 | Extraction automatique de données depuis un rapport RSE (PDF) via LLM | 🔴 | Angle IA, bonus soutenance |
| F15 | Détection de greenwashing (écart discours/données chiffrées) | 🔴 | Optionnel, fort impact si présenté |
| F16 | Export rapport aligné format ESRS officiel | 🔴 | Renforce la crédibilité réglementaire |

## Hors périmètre (assumé)
- Pas de vrai partenariat entreprise (étude sur données publiques)
- Pas de microservices (monolithe modulaire volontaire)
- Pas d'authentification multi-utilisateur poussée (hors du cœur du sujet)
