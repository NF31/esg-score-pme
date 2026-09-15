"""Recommandations priorisees -- quick wins bases sur des regles simples (pas d'IA).

Priorise les questions au gain potentiel le plus eleve (poids fort x marge de
progression forte), pas simplement les moins bonnes reponses : une question a poids
1.0 repondue 0/4 a moins d'impact sur le score qu'une question a poids 3.0 repondue
1/4, meme si sa valeur brute est plus basse.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from app.models import Pilier, Questionnaire, Reponse
from app.scoring import VALEUR_MAX

NB_RECOMMANDATIONS = 5


@dataclass
class Recommandation:
    question_id: int
    pilier: Pilier
    libelle: str
    valeur_actuelle: int
    gain_potentiel: float


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

    recommandations = [
        Recommandation(
            question_id=reponse.question_id,
            pilier=reponse.question.pilier,
            libelle=reponse.question.libelle,
            valeur_actuelle=reponse.valeur,
            gain_potentiel=(VALEUR_MAX - reponse.valeur) * reponse.question.poids,
        )
        for reponse in reponses
        if reponse.valeur < VALEUR_MAX
    ]
    recommandations.sort(key=lambda r: r.gain_potentiel, reverse=True)
    return recommandations[:NB_RECOMMANDATIONS]
