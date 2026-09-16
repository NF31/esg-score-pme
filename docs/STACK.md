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
| `httpx` | F10 | Requêtes vers l'API publique recherche-entreprises.api.gouv.fr |
| `pandas` | F13 | Mise en forme du DataFrame pour le graphe d'évolution du score (`st.line_chart`) |
| `anthropic` | F14 | Extraction de données depuis des rapports RSE (PDF) via LLM |

## Note : `pandas` écarté pour F03, ajouté pour F13

Le moteur de scoring (F03) a finalement été écrit en Python pur (agrégations simples sur
des listes), sans avoir besoin de `pandas` — évite une dépendance lourde non justifiée
pour un calcul qui ne le nécessitait pas. `pandas` a finalement rejoint les dépendances
directes en F13 : déjà tiré transitivement par `streamlit`, `st.line_chart` en attend un
DataFrame pour l'historique des scores.

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

Si l'API doit un jour être exposée séparément (intégrations externes), upgrade vers le plan
Hobby ($5/mois) ou remplacement du service unique par un process manager lançant les deux apps.

## Décision : import CAC40 sans score ESG invente (F10)

`app/import_entreprises.py` peuple `entreprises` avec des donnees reelles (nom, secteur,
effectif) via l'API publique et gratuite `recherche-entreprises.api.gouv.fr` (aucune cle
requise). Aucune API publique gratuite ne fournit de vrais scores ESG pour ces entreprises :
le benchmark (F11) comparera donc un diagnostic a la moyenne des diagnostics reellement
completes dans l'app pour un secteur donne, pas a un score CAC40 fabrique.

**Limite assumee** : l'API expose des entites juridiques individuelles, pas le perimetre
consolide d'un groupe. Un grand groupe diversifie (LVMH, TotalEnergies...) a des dizaines de
filiales sous des codes NAF differents (immobilier, R&D, distribution...) ; la recherche par
nom peut remonter une filiale peu representative de l'activite reelle du groupe. Le filtre
`categorie_entreprise == "GE"` (grande entreprise) reduit ce bruit sans le supprimer. Le champ
`effectif` est egalement une approximation : l'INSEE ne publie jamais l'effectif exact (secret
statistique), seulement une tranche — on stocke le milieu de la tranche.

Lancement manuel (pas au demarrage de l'app, pour ne pas dependre du reseau a chaque boot) :
```bash
uv run python -m app.import_entreprises
```

## Décision : extraction PDF via document natif Claude, pas de parsing texte intermediaire (F14)

`app/extraction_pdf.py` envoie le PDF du rapport RSE directement a l'API Anthropic (bloc
`document` en base64) plutot que d'extraire le texte au prealable avec une lib type
`pypdf`/`pdfplumber` : les modeles Claude recents lisent nativement le PDF (mise en page,
tableaux, graphiques compris), ce qui evite une dependance et une etape de parsing en plus
pour un gain de fiabilite. La sortie est forcee via *tool use* (`tool_choice` sur
`enregistrer_reponses_extraites`) plutot que du texte libre a parser, pour garantir un JSON
valide (question_id, valeur 0-4, justification) sans regex fragile.

**Choix assumé** : l'extraction ne fait que *suggerer* des valeurs qui pre-remplissent les
sliders Streamlit — rien n'est ecrit en base par `extraire_reponses()`. L'utilisateur garde
la main pour corriger avant de calculer le score : une valeur ESG reste en partie subjective,
l'IA n'a pas vocation a se substituer entierement au diagnostic humain. Cle `ANTHROPIC_API_KEY`
lue via `app/config.py` (`.env`, jamais committee) ; en son absence l'extraction leve une
erreur explicite plutot que d'echouer silencieusement, le reste de l'app fonctionne sans elle.

**Limite de taille (10 Mo)** : l'app etant publique et sans authentification, un upload PDF non
borne exposerait a un abus de cout sur l'API Anthropic (payante) -- limite appliquee a deux
niveaux, `maxUploadSize` dans `.streamlit/config.toml` (rejet cote serveur avant lecture
complete) et une verification dans `extraire_reponses()` (defense en profondeur, couvre aussi
l'endpoint FastAPI `/questionnaires/{id}/extraire-pdf`).

## Décision : greenwashing par comparaison, pas par nouvel appel LLM (F15)

`app/greenwashing.py` ne fait aucun appel a l'API Anthropic : il compare les suggestions deja
extraites du rapport RSE en F14 (encore en session Streamlit) aux reponses finalement validees
par l'utilisateur, et signale les ecarts significatifs. Alternative ecartee : un second appel
Claude dedie a la detection d'affirmations vagues dans le texte du rapport — plus couteux (un
appel LLM de plus par diagnostic) et moins fiable a evaluer/tester (sortie qualitative libre),
alors que comparer deux valeurs numeriques deja disponibles est une regle simple, deterministe
et testable sans API. Limite assumee : la detection ne fonctionne que si l'utilisateur a utilise
l'extraction PDF (F14) sur ce questionnaire ; sans elle, aucune donnee de comparaison n'existe.

## Décision : alignement ESRS simplifié, pas de conformité CSRD complète (F16)

`app/esrs.py` classe chacune des 24 questions sous un standard ESRS reel (ESRS E1 Changement
climatique, E3 Eau, E5 Ressources et economie circulaire, S1 Effectifs, S2 Travailleurs de la
chaine de valeur, S3 Communautes affectees, S4 Consommateurs, G1 Conduite des affaires, ESRS 2
Informations generales) plutot que les 3 piliers generiques E/S/G utilises ailleurs dans l'app.
`app/export_esrs.py` regroupe le PDF selon cette structure.

**Limites assumees** : ce n'est pas un export CSRD conforme -- pas d'analyse de double
materialite (obligatoire dans un vrai rapport CSRD), pas de balisage XBRL, et la correspondance
question -> standard est une simplification pedagogique (une seule question par sujet, alors
qu'un standard ESRS reel comporte des dizaines de datapoints). L'objectif est de montrer que le
diagnostic peut se lire dans la structure du referentiel officiel, pas de produire un document
deposable aupres d'un regulateur. E2 (Pollution) et E4 (Biodiversite) ne sont pas couverts,
peu pertinents sans activite industrielle ou impact ecosystemique specifique pour une PME type.

Migration Alembic (`212d6cf5a6ac`) : colonne ajoutee nullable, backfillee par correspondance de
libelle exact pour les questions deja seedees en base, puis passee `NOT NULL` -- pattern standard
pour ajouter une colonne obligatoire sans casser les donnees existantes en prod.

## Principe

On n'ajoute une dépendance que quand la feature qui en a besoin est attaquée — pas de lib installée "au cas où". Chaque ajout doit être justifiable en une phrase face à un jury.
