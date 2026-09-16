"""Detection de greenwashing -- ecart entre ce que le rapport RSE laisse entendre (F14)
et la reponse finale, validee ou corrigee par l'utilisateur, au questionnaire.

Aucun nouvel appel au LLM : on reutilise les suggestions deja extraites du PDF par
`app.extraction_pdf.extraire_reponses`. Si l'utilisateur corrige une suggestion a la baisse
de facon significative, c'est un signal que le rapport survend la realite sur ce point.
"""

from sqlalchemy.orm import Session, joinedload

from app.models import Questionnaire, Reponse

SEUIL_ECART_PAR_DEFAUT = 2


def detecter_ecarts(
    db: Session,
    questionnaire_id: int,
    suggestions_ia: list[dict],
    seuil: int = SEUIL_ECART_PAR_DEFAUT,
) -> list[dict]:
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

    suggestions_par_id = {s["question_id"]: s for s in suggestions_ia}

    ecarts = []
    for reponse in reponses:
        suggestion = suggestions_par_id.get(reponse.question_id)
        if suggestion is None:
            continue
        ecart = suggestion["valeur"] - reponse.valeur
        if ecart >= seuil:
            ecarts.append(
                {
                    "question_id": reponse.question_id,
                    "pilier": reponse.question.pilier,
                    "libelle": reponse.question.libelle,
                    "valeur_rapport": suggestion["valeur"],
                    "valeur_reelle": reponse.valeur,
                    "ecart": ecart,
                    "justification_rapport": suggestion["justification"],
                }
            )

    return sorted(ecarts, key=lambda e: e["ecart"], reverse=True)
