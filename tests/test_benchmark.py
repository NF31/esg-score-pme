import pytest

from app.benchmark import comparer_secteur
from app.models import Entreprise, Pilier, Questionnaire
from app.scoring import calculer_scores
from tests.helpers import creer_questionnaire


def test_comparer_secteur_moyenne_les_autres_entreprises_du_meme_secteur(db):
    id1 = creer_questionnaire(
        db, {Pilier.ENVIRONNEMENT: [4, 4]}, secteur="Industrie manufacturiere"
    )
    calculer_scores(db, id1)
    id2 = creer_questionnaire(
        db, {Pilier.ENVIRONNEMENT: [0, 0]}, secteur="Industrie manufacturiere"
    )
    calculer_scores(db, id2)
    questionnaire_id = creer_questionnaire(
        db, {Pilier.ENVIRONNEMENT: [2, 2]}, secteur="Industrie manufacturiere"
    )
    calculer_scores(db, questionnaire_id)

    comparaison = comparer_secteur(db, questionnaire_id)

    assert comparaison[Pilier.ENVIRONNEMENT]["moyenne"] == pytest.approx(50.0)
    assert comparaison[Pilier.ENVIRONNEMENT]["nb_entreprises"] == 2


def test_comparer_secteur_exclut_les_autres_secteurs(db):
    id1 = creer_questionnaire(db, {Pilier.SOCIAL: [4, 4]}, secteur="Construction")
    calculer_scores(db, id1)
    questionnaire_id = creer_questionnaire(
        db, {Pilier.SOCIAL: [2, 2]}, secteur="Industrie manufacturiere"
    )
    calculer_scores(db, questionnaire_id)

    comparaison = comparer_secteur(db, questionnaire_id)

    assert comparaison == {}


def test_comparer_secteur_exclut_les_questionnaires_non_termines(db):
    entreprise_incomplete = Entreprise(nom="Incomplete", secteur="Construction", effectif=5)
    db.add(entreprise_incomplete)
    db.flush()
    db.add(Questionnaire(entreprise_id=entreprise_incomplete.id))
    db.commit()

    questionnaire_id = creer_questionnaire(db, {Pilier.SOCIAL: [2, 2]}, secteur="Construction")
    calculer_scores(db, questionnaire_id)

    comparaison = comparer_secteur(db, questionnaire_id)

    assert comparaison == {}


def test_comparer_secteur_questionnaire_introuvable_leve_une_erreur(db):
    with pytest.raises(ValueError, match="introuvable"):
        comparer_secteur(db, 999)


def test_comparer_secteur_ignore_les_anciens_diagnostics_de_la_meme_entreprise(db):
    premier = creer_questionnaire(db, {Pilier.SOCIAL: [0]})
    calculer_scores(db, premier)
    entreprise_id = db.get(Questionnaire, premier).entreprise_id
    second = creer_questionnaire(db, {Pilier.SOCIAL: [4]}, entreprise_id=entreprise_id)
    calculer_scores(db, second)

    assert comparer_secteur(db, second) == {}
