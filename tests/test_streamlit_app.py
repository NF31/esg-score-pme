from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from app.import_entreprises import EntrepriseTrouvee
from app.models import Pilier

APP_PATH = str(Path(__file__).parent.parent / "streamlit_app.py")
# Le timeout par defaut (3s) est trop court sur un runner CI froid : le script importe
# SQLAlchemy/FastAPI/reportlab et seed la base a chaque run, ce qui peut depasser 3s sans
# que l'app ait de probleme reel (teste en local : ~0.5s).
TIMEOUT_CI = 15

ENTREPRISE_TROUVEE = EntrepriseTrouvee(
    siren="123456789",
    nom="BOULANGERIE DU CANAL",
    commune="TOULOUSE",
    code_postal="31000",
    code_naf="10.71C",
    secteur="Industrie manufacturiere",
    tranche_effectif="10 à 19 salariés",
    effectif=15,
)


def _app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT_CI)
    at.run()
    return at


def _rechercher(at: AppTest, texte: str) -> None:
    at.text_input[0].input(texte)
    [b for b in at.button if b.label == "Rechercher"][0].click().run()


def _bouton(at: AppTest, libelle: str):
    return next(b for b in at.button if b.label.startswith(libelle))


def test_app_charge_sans_erreur():
    at = _app()

    assert not at.exception
    assert at.title[0].value == "Diagnostic ESG pour PME"


def test_recherche_sans_resultat_affiche_un_message():
    at = _app()
    with patch("app.import_entreprises.rechercher_entreprises", return_value=[]):
        _rechercher(at, "zzzz introuvable")

    assert not at.exception
    assert "Aucune entreprise active" in at.info[0].value


def test_parcours_complet_entreprise_questionnaire_resultats():
    at = _app()
    with patch("app.import_entreprises.rechercher_entreprises", return_value=[ENTREPRISE_TROUVEE]):
        _rechercher(at, "boulangerie du canal")
    at.radio[0].set_value(0).run()
    _bouton(at, "Commencer le diagnostic").click().run()

    assert not at.exception
    assert at.header[0].value == "BOULANGERIE DU CANAL"
    # Un pilier a la fois : 8 questions affichees sur 24
    assert len(at.segmented_control) == 1 + 8

    for _ in range(3):
        for question in at.segmented_control[1:]:
            question.set_value(2)
        at.run()
        suivant = [b for b in at.button if b.label.startswith("Suivant")]
        if suivant:
            suivant[0].click().run()

    calculer = _bouton(at, "Calculer mon score")
    assert not calculer.disabled
    calculer.click().run()

    assert not at.exception
    assert [m.value for m in at.metric if m.label == "Note ESG"] == ["C"]
    assert [m.value for m in at.metric if m.label == "Score global"] == ["50/100"]


def test_calcul_bloque_tant_que_des_questions_manquent():
    at = _app()
    with patch("app.import_entreprises.rechercher_entreprises", return_value=[ENTREPRISE_TROUVEE]):
        _rechercher(at, "boulangerie du canal")
    at.radio[0].set_value(0).run()
    _bouton(at, "Commencer le diagnostic").click().run()
    at.segmented_control[0].set_value(Pilier.GOUVERNANCE).run()

    assert _bouton(at, "Calculer mon score").disabled


def test_exemple_affiche_les_resultats_complets():
    at = _app()
    _bouton(at, "Essayer avec un exemple").click().run()

    assert not at.exception
    assert "exemple fictif" in at.header[0].value
    assert [m.label for m in at.metric][:2] == ["Note ESG", "Score global"]
    assert "Moyenne calculée sur 4 autre(s) diagnostic(s)" in " ".join(c.value for c in at.caption)
