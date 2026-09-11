# STACK.md — choix techniques et pourquoi

## Déjà en place

| Lib | Rôle | Pourquoi ce choix plutôt qu'une alternative |
|---|---|---|
| `fastapi[standard]` | Backend API | Typage natif, doc Swagger auto-générée, rapide à écrire seul — voir README pour la comparaison vs Django/Flask |
| `pytest` | Tests | Standard Python, utilisé sur Atlas |
| `ruff` | Lint + format | Un seul outil pour les deux, utilisé sur Atlas |

## À ajouter — Phase 1 (MVP diagnostic)

| Lib | Feature liée | Pourquoi |
|---|---|---|
| `sqlalchemy` | F01 | ORM pour modéliser entreprise/questionnaire/scores |
| `psycopg[binary]` | F07 | Driver PostgreSQL |
| `alembic` | F07 | Migrations de schéma versionnées (comme sur Atlas) |
| `pandas` | F03 | Agrégation des réponses pour le calcul du score |
| `pydantic-settings` | — | Gestion propre des variables d'environnement (`.env`) |
| `streamlit` | F06 | Frontend simple, adapté à un outil data/diagnostic — voir justification stack précédente (pas de React) |

## À ajouter plus tard — Phase 2/3 (au moment de la feature, pas avant)

| Lib | Feature liée | Pourquoi |
|---|---|---|
| `httpx` | F10 | Requêtes vers des sources de données publiques |
| `reportlab` | F04 | Génération du rapport de synthèse en PDF |
| `anthropic` | F14 | Extraction de données depuis des rapports RSE (PDF) via LLM |

## Principe

On n'ajoute une dépendance que quand la feature qui en a besoin est attaquée — pas de lib installée "au cas où". Chaque ajout doit être justifiable en une phrase face à un jury.
