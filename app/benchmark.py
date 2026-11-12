"""Comparaison sectorielle -- moyenne des scores des autres entreprises du meme secteur.

La moyenne ne porte que sur des diagnostics reellement completes dans l'app (aucun
score ESG n'est invente pour les entreprises importees en F10 -- cf. docs/STACK.md).
"""

from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models import Entreprise, Pilier, Questionnaire, Score, StatutQuestionnaire


def comparer_secteur(db: Session, questionnaire_id: int) -> dict[Pilier | None, dict]:
    questionnaire = db.get(Questionnaire, questionnaire_id)
    if questionnaire is None:
        raise ValueError("Questionnaire introuvable")

    entreprise = db.get(Entreprise, questionnaire.entreprise_id)

    scores_secteur: dict[Pilier | None, list[float]] = defaultdict(list)
    autres_scores = (
        db.query(Score)
        .join(Questionnaire)
        .join(Entreprise)
        .options(joinedload(Score.questionnaire))
        .filter(
            Entreprise.secteur == entreprise.secteur,
            # Les entreprises fictives de la demo ne se comparent qu'entre elles (F20)
            Entreprise.est_exemple == entreprise.est_exemple,
            Questionnaire.statut == StatutQuestionnaire.TERMINE,
            # Les anciens diagnostics de la meme entreprise ne sont pas des concurrents
            Questionnaire.entreprise_id != questionnaire.entreprise_id,
        )
        .all()
    )
    for score in autres_scores:
        scores_secteur[score.pilier].append(score.valeur)

    return {
        pilier: {"moyenne": sum(valeurs) / len(valeurs), "nb_entreprises": len(valeurs)}
        for pilier, valeurs in scores_secteur.items()
    }
