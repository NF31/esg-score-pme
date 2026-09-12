# STACK.md — choix techniques et pourquoi

## Déjà en place

| Lib | Rôle | Pourquoi ce choix plutôt qu'une alternative |
|---|---|---|
| `fastapi[standard]` | Backend API | Typage natif, doc Swagger auto-générée, rapide à écrire seul — voir README pour la comparaison vs Django/Flask |
| `pytest` | Tests | Standard Python, utilisé sur Atlas |
| `ruff` | Lint + format | Un seul outil pour les deux, utilisé sur Atlas |
| `sqlalchemy` | F01 | ORM pour modéliser entreprise/questionnaire/scores — schéma défini dans `app/models.py`, pas encore branché sur une vraie base (cf. F07) |
| `reportlab` | F04 | Génération du rapport de synthèse en PDF (`app/rapport.py`) |
| `streamlit` | F06 | Frontend simple (`streamlit_app.py`), appelle directement les fonctions `app/` (pas de client HTTP) — cohérent avec le monolithe modulaire, pas de duplication de logique avec l'API FastAPI |

## À ajouter — Phase 1 (MVP diagnostic)

| Lib | Feature liée | Pourquoi |
|---|---|---|
| `psycopg[binary]` | F07 | Driver PostgreSQL |
| `alembic` | F07 | Migrations de schéma versionnées (comme sur Atlas) |
| `pydantic-settings` | — | Gestion propre des variables d'environnement (`.env`) |

## À ajouter plus tard — Phase 2/3 (au moment de la feature, pas avant)

| Lib | Feature liée | Pourquoi |
|---|---|---|
| `httpx` | F10 | Requêtes vers des sources de données publiques |
| `anthropic` | F14 | Extraction de données depuis des rapports RSE (PDF) via LLM |

## Note : `pandas` écarté pour F03

Le moteur de scoring (F03) a finalement été écrit en Python pur (agrégations simples sur
des listes), sans avoir besoin de `pandas` — évite une dépendance lourde non justifiée
pour un calcul qui ne le nécessitait pas.

## Décision : SQLite en dev le temps de F07

`app/database.py` branche SQLAlchemy sur `sqlite:///./esg.db` par défaut (variable
`DATABASE_URL`), pour que les endpoints de F02 (entreprises/questionnaires/réponses)
soient fonctionnels sans attendre F07. Le passage à PostgreSQL (F07) ne changera que
la valeur de `DATABASE_URL` — aucun code applicatif à modifier.

## Décision : SonarCloud en Automatic Analysis, pas en CI

Le job SonarQube dans `.github/workflows/ci.yml` a été retiré : lors de l'import du projet sur
SonarCloud, l'**Automatic Analysis** (app GitHub native) s'active par défaut et entre en conflit
avec une analyse pilotée par token depuis la CI (erreur "project not found" côté scanner). On garde
l'Automatic Analysis — zéro maintenance, déjà fonctionnelle — plutôt que de désactiver ce mode pour
répliquer le pattern CI-based de kbeauty-shop.

## Principe

On n'ajoute une dépendance que quand la feature qui en a besoin est attaquée — pas de lib installée "au cas où". Chaque ajout doit être justifiable en une phrase face à un jury.
