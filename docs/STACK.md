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

## Décision : déploiement Railway, un seul service (Streamlit) + Postgres (F08, remplacé en 2026-11)

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

## Décision : démo publique sur Streamlit Community Cloud (2026-11-12)

**Symptôme.** Le lien « Démo en ligne » du README renvoyait une page Railway « Application not
found » (404), alors que le dépôt venait de passer en public.

**Cause.** La période d'essai du compte Railway a pris fin. Railway a alors coupé le service
`streamlit` et la base Postgres, sans prévenir côté dépôt : rien dans la CI ne vérifiait que la démo
répondait encore.

**Solution retenue.** Plutôt que de payer le plan Hobby (environ 5 $/mois) pour une simple démo, la
démo publique tourne désormais sur Streamlit Community Cloud, gratuit pour un dépôt public. Aucune
modification de code n'a été nécessaire, car l'application gérait déjà les deux cas :
- sans `DATABASE_URL`, la configuration (`app/config.py`) bascule sur SQLite, et `streamlit_app.py`
  crée alors le schéma (`preparer_base_sqlite`, voir la leçon sur le schéma SQLite périmé) puis
  charge le questionnaire (`seed_questions`) au démarrage ;
- Community Cloud lit directement `uv.lock`, donc les dépendances installées sont celles du projet.

Réglages : dépôt `NF31/esg-score-pme`, branche `main`, fichier `streamlit_app.py`, aucun secret,
adresse https://esg-score-pme.streamlit.app. Le redéploiement est automatique à chaque push sur
`main`.

**Limites acceptées.**
- La base SQLite est éphémère : les diagnostics saisis disparaissent au redémarrage de l'application,
  ce qui convient à une démo. Pour conserver les données, il suffirait de renseigner `DATABASE_URL`
  dans les secrets vers un Postgres gratuit (Neon par exemple) ; Alembic devrait alors être lancé à
  la main, Community Cloud n'ayant pas d'étape de pré-déploiement.
- Sans clé `ANTHROPIC_API_KEY`, le pré-remplissage depuis un rapport PDF (F14) affiche un message
  d'erreur propre au lieu d'appeler l'API. La clé n'est volontairement pas configurée sur une
  application publique sans authentification, pour éviter qu'un tiers ne consomme le crédit API.
- Après quelques jours sans visite, l'application se met en veille et met une trentaine de secondes
  à redémarrer.

**Vérification.** Le parcours complet (création de l'entreprise, questionnaire, calcul du score) a
été joué dans un navigateur sur l'adresse publique avant la mise à jour du README.

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

## Décision : recherche d'entreprise dans le répertoire officiel, pas de saisie libre (F17)

**Problème.** L'ancien formulaire acceptait n'importe quel nom (« Lol », par exemple) et un
secteur choisi à la main. Le diagnostic pouvait donc porter sur une entreprise qui n'existe
pas, et la comparaison sectorielle reposait sur une déclaration non vérifiée.

**Solution.** L'utilisateur cherche son entreprise par nom ou SIREN dans l'API publique
recherche-entreprises.api.gouv.fr (déjà utilisée par F10, gratuite et sans clé). Le secteur
vient de la section NAF officielle et l'effectif de la tranche INSEE : ce sont des données de
référence, pas une saisie. L'entreprise est ensuite retrouvée par son SIREN, ce qui relie
naturellement ses diagnostics successifs dans l'historique.

**Règles.**
- Seules les entreprises actives (`etat_administratif = A`) et diffusibles
  (`statut_diffusion = O`) sont proposées : une personne qui a demandé la non-diffusion de
  ses données n'apparaît jamais, même si l'API renvoie une fiche masquée.
- L'API refuse les recherches de moins de 3 caractères : l'interface le dit avant l'appel.
- Les résultats sont mis en cache une heure (`st.cache_data`) pour ne pas solliciter l'API
  à chaque interaction.
- Si l'API ne répond pas, un message clair s'affiche ; l'entreprise exemple (F20) reste
  disponible.

## Décision : entreprise exemple isolée du benchmark (F20)

Pour qu'un visiteur voie la page de résultats complète sans remplir 24 questions, un bouton
charge une entreprise fictive avec trois diagnostics et quatre concurrents fictifs. Le
projet refuse d'inventer des scores pour de vraies entreprises (cf. F10) : ces données sont
donc marquées `est_exemple`, signalées comme fictives dans leur nom et à l'écran, et la
comparaison sectorielle ne mélange jamais exemples et vraies entreprises. Les réponses sont
fixes, pour que la démo soit identique à chaque chargement.

## Décision : réponses conservées d'un pilier à l'autre avec `persist_state` (F18)

Le questionnaire n'affiche qu'un pilier à la fois. Par défaut, Streamlit oublie la valeur
d'un widget qui n'est plus affiché ; chaque question utilise donc `persist_state="page"`,
qui garde la réponse quand on change de pilier, sans code de synchronisation maison.

## Leçon : tester les migrations sur PostgreSQL, pas seulement SQLite (F18)

**Symptôme.** La migration `1a799d950536` passait sur SQLite mais échouait sur PostgreSQL :
`column "effort" is of type effort but expression is of type character varying`.

**Cause.** SQLite n'a pas de vrai type énuméré et accepte du texte partout. PostgreSQL crée
un type `effort` et refuse une mise à jour typée `VARCHAR` dans cette colonne.

**Solution.** Dans le backfill, la colonne est déclarée avec le même `sa.Enum` que la
migration, pour que SQLAlchemy envoie la bonne conversion. Vérification faite avec un
PostgreSQL 16 jetable lancé par Docker (montée, descente, remontée).

**Point ouvert.** Sur PostgreSQL, descendre jusqu'à `base` puis remonter échoue sur la
migration initiale (`type "pilier" already exists`) : `f59cf2863c16` ne supprime pas ses
types énumérés au `downgrade`. Sans effet en production (on ne redescend jamais à zéro),
mais à corriger dans un ticket dédié.

## Leçon : une base SQLite d'une ancienne version fait planter la démo (2026-11-12)

**Symptôme.** Juste après le déploiement de F17 à F20, la démo publique affichait dès
l'ouverture `sqlalchemy.exc.OperationalError` sur `seed_questions`, à la ligne
`db.query(Question).count()`.

**Cause.** Sur Streamlit Community Cloud, l'application tourne en SQLite, dans un fichier
`esg.db` créé par la version précédente. Au démarrage, `Base.metadata.create_all` crée les
tables manquantes mais n'ajoute jamais de colonne à une table existante : les nouvelles
colonnes (`questions.aide`, `action`, `effort`, `entreprises.est_exemple`) n'existaient pas,
d'où une erreur « no such column » à la première requête. Les tests partaient toujours d'une
base neuve et ne pouvaient pas voir le problème.

**Solution.** Correctif immédiat : un redémarrage de l'application (« Reboot app » sur
share.streamlit.io) a remis le serveur à neuf, donc sans ancien fichier. Correctif durable :
`preparer_base_sqlite` (`app/database.py`) compare les colonnes de chaque table existante
avec les modèles ; si une colonne manque, la base SQLite est vidée puis recréée. C'est
acceptable parce qu'une base SQLite ne contient ici que des données de démo ou de test ;
PostgreSQL reste géré par Alembic, qui conserve les données. `tests/test_database.py`
reproduit l'incident avec une table `questions` de l'ancienne version. Le scénario a aussi été
rejoué avec la vraie version précédente de l'application : base créée par elle, puis nouvelle
version lancée dessus, sans erreur.

**À retenir.** Quand un ticket ajoute une colonne, tester aussi le passage de l'ancienne
version à la nouvelle, pas seulement une installation neuve.

## Principe

On n'ajoute une dépendance que quand la feature qui en a besoin est attaquée — pas de lib installée "au cas où". Chaque ajout doit être justifiable en une phrase face à un jury.
