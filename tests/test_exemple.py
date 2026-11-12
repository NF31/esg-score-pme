from app.benchmark import comparer_secteur
from app.exemple import CONCURRENTS_EXEMPLE, HISTORIQUE_EXEMPLE, charger_exemple
from app.historique import historique_scores
from app.models import Entreprise, Pilier
from app.scoring import calculer_scores
from app.seed import seed_questions
from tests.helpers import creer_questionnaire


def test_charger_exemple_cree_un_diagnostic_complet_avec_historique(db):
    seed_questions(db)

    questionnaire = charger_exemple(db)

    assert questionnaire.entreprise.est_exemple
    assert len(questionnaire.reponses) == 24
    points_globaux = [
        p for p in historique_scores(db, questionnaire.entreprise_id) if p.pilier is None
    ]
    assert len(points_globaux) == len(HISTORIQUE_EXEMPLE)
    # La comparaison porte sur les concurrents fictifs du meme secteur
    assert comparer_secteur(db, questionnaire.id)[None]["nb_entreprises"] == len(
        CONCURRENTS_EXEMPLE
    )


def test_charger_exemple_deux_fois_ne_duplique_rien(db):
    seed_questions(db)

    premier = charger_exemple(db)
    second = charger_exemple(db)

    assert premier.id == second.id
    assert db.query(Entreprise).count() == len(CONCURRENTS_EXEMPLE) + 1


def test_les_exemples_n_entrent_pas_dans_la_moyenne_d_une_vraie_entreprise(db):
    seed_questions(db)
    exemple = charger_exemple(db)
    vraie = creer_questionnaire(db, {Pilier.SOCIAL: [2]}, secteur=exemple.entreprise.secteur)
    calculer_scores(db, vraie)

    assert comparer_secteur(db, vraie) == {}
