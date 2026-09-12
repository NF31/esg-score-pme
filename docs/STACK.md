# STACK.md — choix techniques et pourquoi

## Déjà en place

| Lib | Rôle | Pourquoi ce choix plutôt qu'une alternative |
|---|---|---|
| `fastapi[standard]` | Backend API | Typage natif, doc Swagger auto-générée, rapide à écrire seul — voir README pour la comparaison vs Django/Flask |
| `pytest` | Tests | Standard Python, utilisé sur Atlas |
| `ruff` | Lint + format | Un seul outil pour les deux, utilisé sur Atlas |
| `sqlalchemy` | F01 | ORM pour modéliser entreprise/questionnaire/scores — schéma défini dans `app/models.py` |
| `reportlab` | F04 | Génération du rapport de synthèse en PDF (`app/rapport.py`) |
| `streamlit` | F06 | Frontend simple (`streamlit_app.py`), appelle directement les fonctions `app/` (pas de client HTTP) — cohérent avec le monolithe modulaire, pas de duplication de logique avec l'API FastAPI |
| `psycopg[binary]` | F07 | Driver PostgreSQL |
| `alembic` | F07 | Migrations de schéma versionnées (comme sur Atlas) — `alembic/` |
| `pydantic-settings` | F07 | Gestion propre des variables d'environnement (`app/config.py`, `.env`) |

## À ajouter plus tard — Phase 2/3 (au moment de la feature, pas avant)

| Lib | Feature liée | Pourquoi |
|---|---|---|
| `httpx` | F10 | Requêtes vers des sources de données publiques |
| `anthropic` | F14 | Extraction de données depuis des rapports RSE (PDF) via LLM |

## Note : `pandas` écarté pour F03

Le moteur de scoring (F03) a finalement été écrit en Python pur (agrégations simples sur
des listes), sans avoir besoin de `pandas` — évite une dépendance lourde non justifiée
pour un calcul qui ne le nécessitait pas.

## Décision : SQLite en local, PostgreSQL en dev partagé/prod (F07)

`app/database.py` lit `DATABASE_URL` via `app/config.py` (pydantic-settings), avec
`sqlite:///./esg.db` comme défaut local. En pointant cette variable vers une instance
PostgreSQL, aucun code applicatif ne change — seul le schéma est alors géré par les
migrations Alembic (`alembic upgrade head`) plutôt que par `Base.metadata.create_all`,
qui reste actif uniquement quand `DATABASE_URL` est du SQLite (dev rapide sans
migration). Commandes utiles :

```bash
uv run alembic revision --autogenerate -m "description"  # après modif de app/models.py
uv run alembic upgrade head                               # appliquer les migrations
uv run alembic downgrade -1                                # revenir en arrière d'une révision
```

## Décision : SonarCloud en Automatic Analysis, pas en CI

Le job SonarQube dans `.github/workflows/ci.yml` a été retiré : lors de l'import du projet sur
SonarCloud, l'**Automatic Analysis** (app GitHub native) s'active par défaut et entre en conflit
avec une analyse pilotée par token depuis la CI (erreur "project not found" côté scanner). On garde
l'Automatic Analysis — zéro maintenance, déjà fonctionnelle — plutôt que de désactiver ce mode pour
répliquer le pattern CI-based de kbeauty-shop.

## Décision : déploiement Railway, un seul service (Streamlit) + Postgres (F08)

Compte Railway personnel (projet `esg-score-pme`), pattern bootstrap habituel : dev sur compte
perso, transfert au client/à l'école si besoin plus tard. Le plan gratuit limite le nombre de
services provisionnables ; avec Postgres + un service applicatif la limite est atteinte, donc pas
de 2e service pour exposer l'API FastAPI séparément. Ce n'est pas un problème fonctionnel :
`streamlit_app.py` appelle déjà directement les fonctions `app/` (cf. décision F06 ci-dessus), donc
Streamlit seul suffit à livrer le produit complet (formulaire → score → rapport PDF) sans dépendre
d'un service API en ligne. Config Railway :
- service `streamlit`, connecté au repo GitHub (`main`), auto-deploy sur push
- `preDeployCommand: uv run alembic upgrade head` — migre le schéma avant chaque redémarrage
- `startCommand: uv run streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
- `DATABASE_URL` référence le service Postgres du même projet (`postgresql+psycopg://...`)
- config faite via `railway` CLI/API (pas de `railway.json` versionné — cf. décision Atlas similaire)

Si l'API doit un jour être exposée séparément (F10+, intégrations externes), upgrade vers le plan
Hobby ($5/mois) ou remplacement du service unique par un process manager lançant les deux apps.

## Principe

On n'ajoute une dépendance que quand la feature qui en a besoin est attaquée — pas de lib installée "au cas où". Chaque ajout doit être justifiable en une phrase face à un jury.
