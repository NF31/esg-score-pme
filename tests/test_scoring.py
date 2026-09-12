import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Base,
    Entreprise,
    Pilier,
    Question,
    Questionnaire,
    Reponse,
    StatutQuestionnaire,
)
from app.scoring import calculer_scores


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _setup_questionnaire(db, reponses_par_pilier):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie", effectif=42)
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
    return questionnaire.id


def test_score_pilier_maximal_donne_cent(db):
    questionnaire_id = _setup_questionnaire(db, {Pilier.ENVIRONNEMENT: [4, 4]})

    scores = calculer_scores(db, questionnaire_id)

    score_env = next(s for s in scores if s.pilier is Pilier.ENVIRONNEMENT)
    assert score_env.valeur == 100.0


def test_score_global_est_moyenne_egale_des_piliers(db):
    questionnaire_id = _setup_questionnaire(
        db,
        {
            Pilier.ENVIRONNEMENT: [4, 4],  # 100
            Pilier.SOCIAL: [0, 0],  # 0
            Pilier.GOUVERNANCE: [2, 2],  # 50
        },
    )

    scores = calculer_scores(db, questionnaire_id)

    score_global = next(s for s in scores if s.pilier is None)
    assert score_global.valeur == pytest.approx(50.0)


def test_calculer_scores_marque_le_questionnaire_termine(db):
    questionnaire_id = _setup_questionnaire(db, {Pilier.SOCIAL: [3]})

    calculer_scores(db, questionnaire_id)

    questionnaire = db.get(Questionnaire, questionnaire_id)
    assert questionnaire.statut == StatutQuestionnaire.TERMINE


def test_calculer_scores_est_idempotent(db):
    questionnaire_id = _setup_questionnaire(db, {Pilier.SOCIAL: [2]})

    calculer_scores(db, questionnaire_id)
    scores_apres_deuxieme_appel = calculer_scores(db, questionnaire_id)

    # un score par pilier concerne + un score global, pas de doublon
    assert len(scores_apres_deuxieme_appel) == 2


def test_calculer_scores_sans_reponse_leve_une_erreur(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.commit()

    with pytest.raises(ValueError, match="Aucune reponse"):
        calculer_scores(db, questionnaire.id)


def test_calculer_scores_questionnaire_introuvable_leve_une_erreur(db):
    with pytest.raises(ValueError, match="introuvable"):
        calculer_scores(db, 999)
