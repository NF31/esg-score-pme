from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "streamlit_app.py")


def test_app_charge_sans_erreur():
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception
    assert at.title[0].value == "Diagnostic ESG pour PME"


def test_creer_entreprise_affiche_le_questionnaire():
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.text_input[0].input("Ma PME").run()
    at.selectbox[0].select("Information et communication").run()
    at.number_input[0].set_value(15).run()
    at.button[0].click().run()

    assert not at.exception
    assert "Ma PME" in at.header[0].value
    assert len(at.slider) == 24
