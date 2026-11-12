"""Plan d'action priorise -- quick wins bases sur des regles simples (pas d'IA).

Chaque action est classee par rapport gain / effort (F19) : le gain est le nombre de
points que le score global gagnerait si la question passait a 4/4, l'effort vient du
referentiel de questions (`app/seed.py`). Une action a faible effort qui rapporte
3 points passe donc devant une action a effort eleve qui en rapporte 4.

Le gain tient compte du poids de la question : une question a poids 1.0 repondue 0/4 a
moins d'impact qu'une question a poids 3.0 repondue 1/4, meme si sa valeur brute est
plus basse. Detail de la formule dans docs/SCORING.md.
"""

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.models import Effort, Pilier, Questionnaire, Reponse
from app.scoring import VALEUR_MAX

NB_RECOMMANDATIONS = 5

# Cout relatif de chaque niveau d'effort, utilise pour classer les actions
COUT_EFFORT = {Effort.FAIBLE: 1, Effort.MOYEN: 2, Effort.ELEVE: 3}


@dataclass
class Recommandation:
    question_id: int
    pilier: Pilier
    libelle: str
    valeur_actuelle: int
    gain_potentiel: float
    action: str | None
    effort: Effort
    gain_points: float


def generer_recommandations(db: Session, questionnaire_id: int) -> list[Recommandation]:
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

    # Le score global est la moyenne egale des piliers repondus (docs/SCORING.md) : un
    # point gagne dans un pilier vaut 1/nb_piliers point de score global.
    poids_par_pilier: dict[Pilier, float] = defaultdict(float)
    for reponse in reponses:
        poids_par_pilier[reponse.question.pilier] += reponse.question.poids
    nb_piliers = len(poids_par_pilier)

    recommandations = []
    for reponse in reponses:
        if reponse.valeur >= VALEUR_MAX:
            continue
        question = reponse.question
        gain_potentiel = (VALEUR_MAX - reponse.valeur) * question.poids
        gain_pilier = gain_potentiel / (poids_par_pilier[question.pilier] * VALEUR_MAX) * 100
        recommandations.append(
            Recommandation(
                question_id=reponse.question_id,
                pilier=question.pilier,
                libelle=question.libelle,
                valeur_actuelle=reponse.valeur,
                gain_potentiel=gain_potentiel,
                action=question.action,
                effort=question.effort,
                gain_points=gain_pilier / nb_piliers,
            )
        )
    recommandations.sort(
        key=lambda r: (r.gain_points / COUT_EFFORT[r.effort], r.gain_points), reverse=True
    )
    return recommandations[:NB_RECOMMANDATIONS]
