import pytest

from app.historique import historique_scores
from app.models import Entreprise, Pilier
from app.scoring import calculer_scores
from tests.helpers import creer_questionnaire


def test_historique_ordonne_les_questionnaires_termines_par_date(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()

    premier_id = creer_questionnaire(db, {Pilier.SOCIAL: [1]}, entreprise_id=entreprise.id)
    calculer_scores(db, premier_id)
    second_id = creer_questionnaire(db, {Pilier.SOCIAL: [3]}, entreprise_id=entreprise.id)
    calculer_scores(db, second_id)

    historique = historique_scores(db, entreprise.id)

    questionnaires_ordonnes = [score.questionnaire_id for score in historique]
    assert questionnaires_ordonnes.index(premier_id) < questionnaires_ordonnes.index(second_id)
    scores_globaux = [score.valeur for score in historique if score.pilier is None]
    assert scores_globaux == [25.0, 75.0]


def test_historique_ignore_les_questionnaires_non_termines(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()

    termine_id = creer_questionnaire(db, {Pilier.SOCIAL: [2]}, entreprise_id=entreprise.id)
    calculer_scores(db, termine_id)
    creer_questionnaire(db, {}, entreprise_id=entreprise.id)  # jamais calcule -> reste EN_COURS

    historique = historique_scores(db, entreprise.id)

    assert {score.questionnaire_id for score in historique} == {termine_id}


def test_historique_entreprise_sans_diagnostic_complete_est_vide(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.commit()

    assert historique_scores(db, entreprise.id) == []


def test_historique_entreprise_introuvable_leve_une_erreur(db):
    with pytest.raises(ValueError, match="introuvable"):
        historique_scores(db, 999)
