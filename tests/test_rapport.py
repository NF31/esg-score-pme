import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Entreprise, Pilier, Question, Questionnaire, Reponse
from app.rapport import generer_rapport_pdf
from app.scoring import calculer_scores


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _questionnaire_note(db) -> int:
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.flush()

    for pilier in Pilier:
        question = Question(pilier=pilier, libelle="Q", poids=1.0)
        db.add(question)
        db.flush()
        db.add(Reponse(questionnaire_id=questionnaire.id, question_id=question.id, valeur=3))
    db.commit()
    return questionnaire.id


def test_genere_un_pdf_valide(db):
    questionnaire_id = _questionnaire_note(db)
    calculer_scores(db, questionnaire_id)

    pdf_bytes = generer_rapport_pdf(db, questionnaire_id)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_rapport_sans_score_leve_une_erreur(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie", effectif=42)
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
