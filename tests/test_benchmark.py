import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.benchmark import comparer_secteur
from app.models import (
    Base,
    Entreprise,
    Pilier,
    Question,
    Questionnaire,
    Reponse,
)
from app.scoring import calculer_scores


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _diagnostic_complet(db, secteur, reponses_par_pilier):
    entreprise = Entreprise(nom="Une entreprise", secteur=secteur, effectif=10)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.flush()

    for pilier, valeurs in reponses_par_pilier.items():
        for valeur in valeurs:
            question = Question(pilier=pilier, libelle="Q", poids=1.0)
            db.add(question)
            db.flush()
            db.add(
                Reponse(questionnaire_id=questionnaire.id, question_id=question.id, valeur=valeur)
            )
    db.commit()
    calculer_scores(db, questionnaire.id)
    return questionnaire.id


def test_comparer_secteur_moyenne_les_autres_entreprises_du_meme_secteur(db):
    _diagnostic_complet(db, "Industrie manufacturiere", {Pilier.ENVIRONNEMENT: [4, 4]})  # 100
    _diagnostic_complet(db, "Industrie manufacturiere", {Pilier.ENVIRONNEMENT: [0, 0]})  # 0
    questionnaire_id = _diagnostic_complet(
        db, "Industrie manufacturiere", {Pilier.ENVIRONNEMENT: [2, 2]}
    )

    comparaison = comparer_secteur(db, questionnaire_id)

    assert comparaison[Pilier.ENVIRONNEMENT]["moyenne"] == pytest.approx(50.0)
    assert comparaison[Pilier.ENVIRONNEMENT]["nb_entreprises"] == 2


def test_comparer_secteur_exclut_les_autres_secteurs(db):
    _diagnostic_complet(db, "Construction", {Pilier.SOCIAL: [4, 4]})
    questionnaire_id = _diagnostic_complet(db, "Industrie manufacturiere", {Pilier.SOCIAL: [2, 2]})

    comparaison = comparer_secteur(db, questionnaire_id)

    assert comparaison == {}


def test_comparer_secteur_exclut_les_questionnaires_non_termines(db):
    entreprise_incomplete = Entreprise(nom="Incomplete", secteur="Construction", effectif=5)
    db.add(entreprise_incomplete)
    db.flush()
    db.add(Questionnaire(entreprise_id=entreprise_incomplete.id))
    db.commit()

    questionnaire_id = _diagnostic_complet(db, "Construction", {Pilier.SOCIAL: [2, 2]})

    comparaison = comparer_secteur(db, questionnaire_id)

    assert comparaison == {}


def test_comparer_secteur_questionnaire_introuvable_leve_une_erreur(db):
    with pytest.raises(ValueError, match="introuvable"):
        comparer_secteur(db, 999)
