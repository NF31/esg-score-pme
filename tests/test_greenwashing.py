import pytest

from app.greenwashing import detecter_ecarts
from app.models import Entreprise, Pilier, Question, Questionnaire
from tests.helpers import creer_questionnaire


def test_detecte_un_ecart_au_dessus_du_seuil(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.ENVIRONNEMENT: [1]})
    question_id = db.query(Question).one().id

    suggestions_ia = [
        {"question_id": question_id, "valeur": 4, "justification": "Rapport tres positif"}
    ]

    ecarts = detecter_ecarts(db, questionnaire_id, suggestions_ia)

    assert len(ecarts) == 1
    assert ecarts[0]["ecart"] == 3
    assert ecarts[0]["valeur_rapport"] == 4
    assert ecarts[0]["valeur_reelle"] == 1
    assert ecarts[0]["justification_rapport"] == "Rapport tres positif"


def test_ignore_un_ecart_sous_le_seuil(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.SOCIAL: [2]})
    question_id = db.query(Question).one().id

    suggestions_ia = [
        {"question_id": question_id, "valeur": 3, "justification": "Legerement optimiste"}
    ]

    assert detecter_ecarts(db, questionnaire_id, suggestions_ia) == []


def test_ignore_les_suggestions_sans_reponse_correspondante(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.GOUVERNANCE: [0]})

    suggestions_ia = [{"question_id": 99999, "valeur": 4, "justification": "Hors questionnaire"}]

    assert detecter_ecarts(db, questionnaire_id, suggestions_ia) == []


def test_trie_les_ecarts_du_plus_grand_au_plus_petit(db):
    questionnaire_id = creer_questionnaire(db, {Pilier.ENVIRONNEMENT: [0, 0]})
    questions = db.query(Question).order_by(Question.id).all()

    suggestions_ia = [
        {"question_id": questions[0].id, "valeur": 2, "justification": "Petit ecart"},
        {"question_id": questions[1].id, "valeur": 4, "justification": "Gros ecart"},
    ]

    ecarts = detecter_ecarts(db, questionnaire_id, suggestions_ia)

    assert [e["question_id"] for e in ecarts] == [questions[1].id, questions[0].id]


def test_leve_une_erreur_sans_reponse(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.commit()

    with pytest.raises(ValueError, match="Aucune reponse"):
        detecter_ecarts(db, questionnaire.id, [])


def test_leve_une_erreur_questionnaire_introuvable(db):
    with pytest.raises(ValueError, match="introuvable"):
        detecter_ecarts(db, 999, [])
