"""Moteur de scoring ESG — calcul du score par pilier et du score global.

Formule et pondérations justifiées dans docs/SCORING.md.
"""

from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models import Pilier, Questionnaire, Reponse, Score, StatutQuestionnaire

VALEUR_MAX = 4


def calculer_scores(db: Session, questionnaire_id: int) -> list[Score]:
    questionnaire = db.get(Questionnaire, questionnaire_id)
    if questionnaire is None:
        raise ValueError("Questionnaire introuvable")

    reponses = (
        db.query(Reponse)
        .options(joinedload(Reponse.question))
        .filter(Reponse.questionnaire_id == questionnaire_id)
        .all()
    )
    if not reponses:
        raise ValueError("Aucune reponse enregistree pour ce questionnaire")

    par_pilier: dict[Pilier, list[tuple[int, float]]] = defaultdict(list)
    for reponse in reponses:
        par_pilier[reponse.question.pilier].append((reponse.valeur, reponse.question.poids))

    db.query(Score).filter(Score.questionnaire_id == questionnaire_id).delete()

    scores_par_pilier: dict[Pilier, float] = {}
    for pilier, valeurs_poids in par_pilier.items():
        poids_total = sum(poids for _, poids in valeurs_poids)
        somme_ponderee = sum(valeur * poids for valeur, poids in valeurs_poids)
        score_pilier = (somme_ponderee / (poids_total * VALEUR_MAX)) * 100
        scores_par_pilier[pilier] = score_pilier
        db.add(Score(questionnaire_id=questionnaire_id, pilier=pilier, valeur=score_pilier))

    score_global = sum(scores_par_pilier.values()) / len(scores_par_pilier)
    score_global_obj = Score(questionnaire_id=questionnaire_id, pilier=None, valeur=score_global)
    db.add(score_global_obj)

    questionnaire.statut = StatutQuestionnaire.TERMINE
    db.commit()

    return db.query(Score).filter(Score.questionnaire_id == questionnaire_id).all()
