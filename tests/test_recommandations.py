import pytest

from app.models import Entreprise, Pilier, Question, Questionnaire, Reponse
from app.recommandations import NB_RECOMMANDATIONS, generer_recommandations
from tests.helpers import creer_questionnaire


def test_recommandations_priorisent_le_gain_potentiel_pas_la_valeur_brute(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.flush()

    question_faible_poids = Question(
        pilier=Pilier.ENVIRONNEMENT, libelle="Q faible poids", poids=1.0
    )
    question_forte_poids = Question(pilier=Pilier.ENVIRONNEMENT, libelle="Q forte poids", poids=3.0)
    db.add_all([question_faible_poids, question_forte_poids])
    db.flush()
    # valeur plus basse mais poids faible -> gain 1*1 = 1
    db.add(
        Reponse(questionnaire_id=questionnaire.id, question_id=question_faible_poids.id, valeur=0)
    )
    # valeur moins basse mais poids fort -> gain 3*3 = 9, doit passer devant
    db.add(
        Reponse(questionnaire_id=questionnaire.id, question_id=question_forte_poids.id, valeur=1)
    )
    db.commit()

    recommandations = generer_recommandations(db, questionnaire.id)

    assert [r.question_id for r in recommandations] == [
        question_forte_poids.id,
        question_faible_poids.id,
    ]


def test_recommandations_ignore_les_reponses_deja_maximales(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.SOCIAL: [4], Pilier.GOUVERNANCE: [2]})

    recommandations = generer_recommandations(db, questionnaire_id)

    assert all(r.valeur_actuelle < 4 for r in recommandations)
    assert len(recommandations) == 1


def test_recommandations_limitees_au_nombre_maximal(db):
    questionnaire_id = creer_questionnaire(
        db, {Pilier.ENVIRONNEMENT: [0] * (NB_RECOMMANDATIONS + 3)}
    )

    recommandations = generer_recommandations(db, questionnaire_id)

    assert len(recommandations) == NB_RECOMMANDATIONS


def test_recommandations_sans_reponse_leve_une_erreur(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.commit()

    with pytest.raises(ValueError, match="Aucune reponse"):
        generer_recommandations(db, questionnaire.id)


def test_recommandations_questionnaire_introuvable_leve_une_erreur(db):
    with pytest.raises(ValueError, match="introuvable"):
        generer_recommandations(db, 999)
