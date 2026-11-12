"""Connexion base de données.

PostgreSQL en production/dev partagé, SQLite par défaut en local — piloté par
`DATABASE_URL` (cf. `app/config.py`). Le schéma est géré par les migrations
Alembic (`alembic/`) en PostgreSQL ; en SQLite (dev rapide, démo publique, tests),
il est créé directement depuis les modèles par `preparer_base_sqlite`.
"""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base

DATABASE_URL = settings.database_url

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def schema_sqlite_perime(moteur: Engine) -> bool:
    """Vrai si une table existante n'a pas toutes les colonnes des modeles.

    `create_all` cree les tables manquantes mais n'ajoute jamais de colonne a une
    table deja la : une base SQLite creee par une version precedente de l'app
    ferait alors planter la premiere requete ("no such column").
    """
    inspecteur = inspect(moteur)
    tables_existantes = set(inspecteur.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in tables_existantes:
            continue
        colonnes = {c["name"] for c in inspecteur.get_columns(table.name)}
        if not set(table.columns.keys()) <= colonnes:
            return True
    return False


def preparer_base_sqlite(moteur: Engine) -> bool:
    """Prepare une base SQLite (dev rapide, demo publique) sans passer par Alembic.

    Si le schema est perime, la base est videe puis recreee : acceptable ici car
    une base SQLite ne contient que des donnees de demo ou de test. Retourne
    True si la base a ete recreee. PostgreSQL reste gere par Alembic.
    """
    recreee = schema_sqlite_perime(moteur)
    if recreee:
        Base.metadata.drop_all(moteur)
    Base.metadata.create_all(moteur)
    return recreee


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
