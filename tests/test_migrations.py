"""Vérifie que la migration Alembic initiale crée le schéma attendu."""

import tempfile
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.models import Base

ALEMBIC_INI = str(Path(__file__).parent.parent / "alembic.ini")


def test_upgrade_head_cree_les_memes_tables_que_les_modeles():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_url = f"sqlite:///{tmpdir}/migration_test.db"
        config = Config(ALEMBIC_INI)
        config.set_main_option("sqlalchemy.url", db_url)

        command.upgrade(config, "head")

        engine = create_engine(db_url)
        tables_migrees = set(inspect(engine).get_table_names()) - {"alembic_version"}
        assert tables_migrees == set(Base.metadata.tables)

        command.downgrade(config, "base")
        # alembic_version elle-même n'est jamais supprimée par un downgrade
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
