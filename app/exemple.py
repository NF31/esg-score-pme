"""Entreprise exemple de la demo (F20) -- un diagnostic deja rempli, en un clic.

Permet de voir tout de suite la page de resultats complete (comparaison sectorielle,
historique, plan d'action) sans remplir les 24 questions. Toutes les entreprises creees
ici sont fictives, marquees `est_exemple`, et ne se comparent qu'entre elles : leurs
scores n'entrent jamais dans la moyenne sectorielle d'une vraie entreprise.

Les reponses sont fixes (pas d'aleatoire) pour que la demo soit identique a chaque
chargement. Elles suivent l'ordre de la banque de questions (`app/seed.py`).
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Entreprise, Pilier, Question, Questionnaire, Reponse
from app.scoring import calculer_scores

NOM_EXEMPLE = "Boulangerie du Canal (exemple fictif)"
SECTEUR_EXEMPLE = "Industrie manufacturiere"

# Trois diagnostics successifs de l'entreprise exemple (il y a un an, il y a six mois,
# aujourd'hui) : 8 reponses par pilier, Environnement, Social, Gouvernance.
HISTORIQUE_EXEMPLE: list[tuple[int, list[int]]] = [
    (365, [0, 0, 2, 1, 1, 1, 1, 0] + [2, 1, 1, 2, 1, 2, 1, 3] + [0, 0, 1, 1, 1, 0, 2, 2]),
    (180, [1, 0, 3, 2, 1, 1, 1, 0] + [2, 2, 2, 3, 2, 2, 1, 3] + [1, 0, 1, 1, 2, 0, 3, 2]),
    (0, [1, 0, 3, 3, 2, 1, 2, 1] + [3, 2, 2, 3, 2, 3, 2, 3] + [2, 1, 2, 2, 3, 1, 3, 3]),
]

# Concurrents fictifs du meme secteur, un diagnostic chacun
CONCURRENTS_EXEMPLE: list[tuple[str, int, list[int]]] = [
    (
        "Fournil des Carmes (exemple fictif)",
        12,
        [1, 1, 2, 2, 1, 1, 1, 0] + [2, 2, 1, 3, 2, 2, 1, 2] + [1, 0, 1, 1, 2, 0, 3, 2],
    ),
    (
        "Pains et Viennoiseries Saint-Cyprien (exemple fictif)",
        25,
        [0, 0, 2, 2, 1, 0, 1, 0] + [2, 1, 1, 2, 1, 2, 1, 2] + [1, 0, 1, 0, 1, 0, 2, 2],
    ),
    (
        "Atelier Pâtissier du Capitole (exemple fictif)",
        8,
        [1, 1, 3, 2, 2, 2, 2, 1] + [3, 2, 2, 3, 2, 2, 2, 3] + [2, 1, 2, 1, 2, 1, 3, 3],
    ),
    (
        "Minoterie Garonne (exemple fictif)",
        40,
        [2, 1, 3, 3, 2, 1, 1, 2] + [2, 3, 2, 3, 3, 3, 1, 2] + [2, 2, 1, 2, 3, 1, 3, 3],
    ),
]


def _questions_ordonnees(db: Session) -> list[Question]:
    ordre_piliers = {Pilier.ENVIRONNEMENT: 0, Pilier.SOCIAL: 1, Pilier.GOUVERNANCE: 2}
    questions = db.query(Question).order_by(Question.id).all()
    return sorted(questions, key=lambda q: ordre_piliers[q.pilier])


def _creer_diagnostic(
    db: Session,
    entreprise: Entreprise,
    questions: list[Question],
    valeurs: list[int],
    il_y_a_jours: int,
) -> Questionnaire:
    questionnaire = Questionnaire(
        entreprise_id=entreprise.id,
        created_at=datetime.now(UTC) - timedelta(days=il_y_a_jours),
    )
    db.add(questionnaire)
    db.flush()
    for question, valeur in zip(questions, valeurs, strict=True):
        db.add(Reponse(questionnaire_id=questionnaire.id, question_id=question.id, valeur=valeur))
    db.commit()
    calculer_scores(db, questionnaire.id)
    return questionnaire


def charger_exemple(db: Session) -> Questionnaire:
    """Cree l'entreprise exemple et ses concurrents, ou reprend ceux deja crees.

    Renvoie le diagnostic le plus recent de l'entreprise exemple.
    """
    entreprise = (
        db.query(Entreprise)
        .filter(Entreprise.est_exemple.is_(True), Entreprise.nom == NOM_EXEMPLE)
        .first()
    )
    if entreprise is None:
        questions = _questions_ordonnees(db)
        for nom, effectif, valeurs in CONCURRENTS_EXEMPLE:
            concurrent = Entreprise(
                nom=nom, secteur=SECTEUR_EXEMPLE, effectif=effectif, est_exemple=True
            )
            db.add(concurrent)
            db.flush()
            _creer_diagnostic(db, concurrent, questions, valeurs, il_y_a_jours=30)

        entreprise = Entreprise(
            nom=NOM_EXEMPLE, secteur=SECTEUR_EXEMPLE, effectif=15, est_exemple=True
        )
        db.add(entreprise)
        db.flush()
        for il_y_a_jours, valeurs in HISTORIQUE_EXEMPLE:
            _creer_diagnostic(db, entreprise, questions, valeurs, il_y_a_jours)

    return (
        db.query(Questionnaire)
        .filter(Questionnaire.entreprise_id == entreprise.id)
        .order_by(Questionnaire.created_at.desc())
        .first()
    )
