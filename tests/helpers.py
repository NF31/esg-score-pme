from app.models import Entreprise, Pilier, Question, Questionnaire, Reponse


def creer_questionnaire(
    db,
    reponses_par_pilier: dict[Pilier, list[int]],
    secteur: str = "Industrie manufacturiere",
    entreprise_id: int | None = None,
) -> int:
    if entreprise_id is None:
        entreprise = Entreprise(nom="Acme SARL", secteur=secteur, effectif=42)
        db.add(entreprise)
        db.flush()
        entreprise_id = entreprise.id
    questionnaire = Questionnaire(entreprise_id=entreprise_id)
    db.add(questionnaire)
    db.flush()

    for pilier, valeurs in reponses_par_pilier.items():
        for valeur in valeurs:
            question = Question(pilier=pilier, libelle="Q", poids=1.0)
            db.add(question)
            db.flush()
            db.add(
                Reponse(questionnaire_id=questionnaire.id, question_id=question.id, valeur=valeur)
            )
    db.commit()
    return questionnaire.id
