"""Base SQLite de la demo : recreee si elle vient d'une version precedente de l'app."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.database import preparer_base_sqlite, schema_sqlite_perime
from app.models import Question
from app.seed import seed_questions


def _colonnes(moteur, table: str) -> set[str]:
    return {c["name"] for c in inspect(moteur).get_columns(table)}


def test_base_vide_est_creee(tmp_path):
    moteur = create_engine(f"sqlite:///{tmp_path}/neuve.db")

    assert preparer_base_sqlite(moteur) is False
    assert "est_exemple" in _colonnes(moteur, "entreprises")


def test_base_a_jour_est_conservee(tmp_path):
    moteur = create_engine(f"sqlite:///{tmp_path}/a_jour.db")
    preparer_base_sqlite(moteur)
    with Session(moteur) as db:
        seed_questions(db)

    assert preparer_base_sqlite(moteur) is False
    with Session(moteur) as db:
        assert db.query(Question).count() == 24


def test_base_d_une_ancienne_version_est_recreee(tmp_path):
    # Reproduit l'incident de la demo : table questions creee avant l'ajout
    # des colonnes aide/action/effort, avec des donnees dedans.
    moteur = create_engine(f"sqlite:///{tmp_path}/ancienne.db")
    with moteur.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE questions (id INTEGER PRIMARY KEY, pilier VARCHAR, "
                "libelle VARCHAR, poids INTEGER, esrs_standard VARCHAR)"
            )
        )
        conn.execute(text("INSERT INTO questions VALUES (1, 'SOCIAL', 'ancienne', 1, 'S1')"))
    assert schema_sqlite_perime(moteur)

    assert preparer_base_sqlite(moteur) is True
    assert {"aide", "action", "effort"} <= _colonnes(moteur, "questions")
    with Session(moteur) as db:
        seed_questions(db)
        assert db.query(Question).count() == 24
