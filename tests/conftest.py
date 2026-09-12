import os
import tempfile

# Doit s'executer avant tout import de app.database (qui lit DATABASE_URL a
# l'import), pour que streamlit_app.py n'ecrive jamais dans le vrai esg.db
# pendant les tests.
_tmpdir = tempfile.mkdtemp()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmpdir}/test.db")

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models import Base  # noqa: E402


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
