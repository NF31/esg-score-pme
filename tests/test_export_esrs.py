import pytest

from app.export_esrs import generer_export_esrs
from app.models import Entreprise, Pilier, Question, Questionnaire, Reponse
from tests.helpers import creer_questionnaire


def test_export_esrs_genere_un_pdf(db):
    questionnaire_id = creer_questionnaire(db, {pilier: [3] for pilier in Pilier})

    pdf_bytes = generer_export_esrs(db, questionnaire_id)

    assert pdf_bytes.startswith(b"%PDF")


def test_export_esrs_leve_une_erreur_questionnaire_introuvable(db):
    with pytest.raises(ValueError, match="introuvable"):
        generer_export_esrs(db, 999)


def test_export_esrs_leve_une_erreur_sans_reponse(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.commit()

    with pytest.raises(ValueError, match="Aucune reponse"):
        generer_export_esrs(db, questionnaire.id)


def test_export_esrs_regroupe_par_standard(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.flush()

    q1 = Question(pilier=Pilier.ENVIRONNEMENT, libelle="Q1", poids=1.0, esrs_standard="ESRS E1")
    q2 = Question(pilier=Pilier.ENVIRONNEMENT, libelle="Q2", poids=1.0, esrs_standard="ESRS E1")
    db.add_all([q1, q2])
    db.flush()
    db.add_all(
        [
            Reponse(questionnaire_id=questionnaire.id, question_id=q1.id, valeur=4),
            Reponse(questionnaire_id=questionnaire.id, question_id=q2.id, valeur=0),
        ]
    )
    db.commit()

    pdf_bytes = generer_export_esrs(db, questionnaire.id)

    assert pdf_bytes.startswith(b"%PDF")
