"""Historique des scores -- evolution du score global et par pilier au fil des
questionnaires termines d'une meme entreprise.

Seuls les questionnaires `TERMINE` (donc avec des scores calcules) comptent : un
questionnaire en cours ne produit pas de point sur le graphe.
"""

from sqlalchemy.orm import Session, joinedload

from app.models import Entreprise, Questionnaire, Score, StatutQuestionnaire


def historique_scores(db: Session, entreprise_id: int) -> list[Score]:
    entreprise = db.get(Entreprise, entreprise_id)
    if entreprise is None:
        raise ValueError("Entreprise introuvable")

    return (
        db.query(Score)
        .join(Questionnaire)
        .options(joinedload(Score.questionnaire))
        .filter(
            Questionnaire.entreprise_id == entreprise_id,
            Questionnaire.statut == StatutQuestionnaire.TERMINE,
        )
        .order_by(Questionnaire.created_at, Score.pilier)
        .all()
    )
