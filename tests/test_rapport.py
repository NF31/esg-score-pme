import pytest

from app.models import Entreprise, Pilier, Questionnaire
from app.rapport import generer_rapport_pdf
from app.scoring import calculer_scores
from tests.helpers import creer_questionnaire


def test_genere_un_pdf_valide(db):
    questionnaire_id = creer_questionnaire(db, {pilier: [3] for pilier in Pilier})
    calculer_scores(db, questionnaire_id)

    pdf_bytes = generer_rapport_pdf(db, questionnaire_id)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_rapport_sans_score_leve_une_erreur(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.commit()

    with pytest.raises(ValueError, match="Aucun score"):
        generer_rapport_pdf(db, questionnaire.id)


def test_rapport_questionnaire_introuvable_leve_une_erreur(db):
    with pytest.raises(ValueError, match="introuvable"):
        generer_rapport_pdf(db, 999)
