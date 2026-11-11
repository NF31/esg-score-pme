from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "streamlit_app.py")
# Le timeout par defaut (3s) est trop court sur un runner CI froid : le script importe
# SQLAlchemy/FastAPI/reportlab et seed la base a chaque run, ce qui peut depasser 3s sans
# que l'app ait de probleme reel (teste en local : ~0.5s).
TIMEOUT_CI = 15


def test_app_charge_sans_erreur():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT_CI)
    at.run()
    assert not at.exception
    assert at.title[0].value == "Diagnostic ESG pour PME"


def test_creer_entreprise_affiche_le_questionnaire():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT_CI)
    at.run()

    # Les champs sont dans un st.form : leurs valeurs ne sont envoyees qu'avec le
    # bouton de soumission. Un .run() entre deux saisies les reinitialise
    # (Streamlit >= 1.67), donc on remplit tout puis on soumet en un seul run.
    at.text_input[0].input("Ma PME")
    at.selectbox[0].select("Information et communication")
    at.number_input[0].set_value(15)
    at.button[0].click().run()

    assert not at.exception
    assert "Ma PME" in at.header[0].value
    assert len(at.slider) == 24
