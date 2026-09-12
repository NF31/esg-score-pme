import pytest

from app.models import (
    Entreprise,
    Pilier,
    Question,
    Questionnaire,
    Reponse,
    StatutQuestionnaire,
)
from app.scoring import calculer_scores
from tests.helpers import creer_questionnaire


def test_score_pilier_maximal_donne_cent(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.ENVIRONNEMENT: [4, 4]})

    scores = calculer_scores(db, questionnaire_id)

    score_env = next(s for s in scores if s.pilier is Pilier.ENVIRONNEMENT)
    assert score_env.valeur == 100.0


def test_score_global_est_moyenne_egale_des_piliers(db):
    questionnaire_id = creer_questionnaire(
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
    questionnaire_id = creer_questionnaire(db, {Pilier.SOCIAL: [3]})

    calculer_scores(db, questionnaire_id)

    questionnaire = db.get(Questionnaire, questionnaire_id)
    assert questionnaire.statut == StatutQuestionnaire.TERMINE


def test_calculer_scores_est_idempotent(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.SOCIAL: [2]})

    calculer_scores(db, questionnaire_id)
    scores_apres_deuxieme_appel = calculer_scores(db, questionnaire_id)

    # un score par pilier concerne + un score global, pas de doublon
    assert len(scores_apres_deuxieme_appel) == 2


def test_calculer_scores_sans_reponse_leve_une_erreur(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
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


def test_score_pilier_minimal_donne_zero(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.GOUVERNANCE: [0, 0]})

    scores = calculer_scores(db, questionnaire_id)

    score_gouv = next(s for s in scores if s.pilier is Pilier.GOUVERNANCE)
    assert score_gouv.valeur == 0.0


def test_score_pilier_pondere_par_le_poids_des_questions(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.flush()

    question_faible = Question(pilier=Pilier.ENVIRONNEMENT, libelle="Q1", poids=1.0)
    question_forte = Question(pilier=Pilier.ENVIRONNEMENT, libelle="Q2", poids=3.0)
    db.add_all([question_faible, question_forte])
    db.flush()
    db.add(Reponse(questionnaire_id=questionnaire.id, question_id=question_faible.id, valeur=0))
    db.add(Reponse(questionnaire_id=questionnaire.id, question_id=question_forte.id, valeur=4))
    db.commit()

    scores = calculer_scores(db, questionnaire.id)

    score_env = next(s for s in scores if s.pilier is Pilier.ENVIRONNEMENT)
    # (0*1 + 4*3) / ((1+3)*4) * 100 = 75 -- une simple moyenne non ponderee donnerait 50
    assert score_env.valeur == pytest.approx(75.0)


def test_score_global_ignore_les_piliers_sans_reponse(db):
    questionnaire_id = creer_questionnaire(
        db,
        {
            Pilier.ENVIRONNEMENT: [4, 4],  # 100
            Pilier.SOCIAL: [0, 0],  # 0
        },
    )

    scores = calculer_scores(db, questionnaire_id)

    score_global = next(s for s in scores if s.pilier is None)
    # moyenne sur les 2 piliers repondus, pas /3 : (100 + 0) / 2 = 50
    assert score_global.valeur == pytest.approx(50.0)
