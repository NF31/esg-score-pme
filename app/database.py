"""Connexion base de données.

SQLite par défaut pour le développement ; F07 branchera PostgreSQL en
changeant simplement `DATABASE_URL` (le reste du code ne change pas).
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./esg.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
