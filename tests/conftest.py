import os
import tempfile

# Doit s'executer avant tout import de app.database (qui lit DATABASE_URL a
# l'import), pour que streamlit_app.py n'ecrive jamais dans le vrai esg.db
# pendant les tests.
_tmpdir = tempfile.mkdtemp()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmpdir}/test.db")
