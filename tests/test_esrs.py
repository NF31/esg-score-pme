from app.esrs import ORDRE_ESRS, scores_par_esrs
from app.models import Entreprise, Pilier, Question, Questionnaire, Reponse


def test_scores_par_esrs_moyenne_par_standard_dans_l_ordre_officiel(db):
    entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
    db.add(entreprise)
    db.flush()
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.flush()
    reponses = [("ESRS G1", 4), ("ESRS E1", 0), ("ESRS E1", 2)]
    for code, valeur in reponses:
        question = Question(pilier=Pilier.GOUVERNANCE, libelle="Q", esrs_standard=code)
        db.add(question)
        db.flush()
        db.add(Reponse(questionnaire_id=questionnaire.id, question_id=question.id, valeur=valeur))
    db.commit()

    scores = scores_par_esrs(db, questionnaire.id)

    assert scores == {"ESRS E1": 25, "ESRS G1": 100}
    assert list(scores) == [code for code in ORDRE_ESRS if code in scores]
