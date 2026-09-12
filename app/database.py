"""Connexion base de données.

PostgreSQL en production/dev partagé, SQLite par défaut en local — piloté par
`DATABASE_URL` (cf. `app/config.py`). Le schéma est géré par les migrations
Alembic (`alembic/`), pas par `Base.metadata.create_all` (sauf en tests).
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

DATABASE_URL = settings.database_url

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
