"""Referentiel simplifie des standards ESRS (European Sustainability Reporting Standards)
utilises pour classer les 24 questions du diagnostic (cf. `app/seed.py`, F16).

Simplification assumee : seuls les standards pertinents pour une PME sont couverts (pas de
E2 Pollution ni E4 Biodiversite, peu probables sans activite industrielle specifique) --
voir `docs/STACK.md` pour la justification complete et les limites de cet alignement.
"""

from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models import Reponse

VALEUR_MAX_ESRS = 4

# Libelles courts pour les graphiques, ou le libelle officiel ne tient pas
LIBELLES_COURTS_ESRS: dict[str, str] = {
    "ESRS E1": "Climat",
    "ESRS E3": "Eau",
    "ESRS E5": "Ressources",
    "ESRS S1": "Salariés",
    "ESRS S2": "Chaîne de valeur",
    "ESRS S3": "Territoire",
    "ESRS S4": "Clients",
    "ESRS G1": "Éthique",
    "ESRS 2": "Transparence",
}

ESRS_LABELS: dict[str, str] = {
    "ESRS E1": "Changement climatique",
    "ESRS E3": "Ressources en eau et marines",
    "ESRS E5": "Utilisation des ressources et économie circulaire",
    "ESRS S1": "Effectifs de l'entreprise",
    "ESRS S2": "Travailleurs de la chaîne de valeur",
    "ESRS S3": "Communautés affectées",
    "ESRS S4": "Consommateurs et utilisateurs finaux",
    "ESRS G1": "Conduite des affaires",
    "ESRS 2": "Informations générales",
}

# Ordre d'affichage officiel (environnement, social, gouvernance, transversal)
ORDRE_ESRS = [
    "ESRS E1",
    "ESRS E3",
    "ESRS E5",
    "ESRS S1",
    "ESRS S2",
    "ESRS S3",
    "ESRS S4",
    "ESRS G1",
    "ESRS 2",
]


def scores_par_esrs(db: Session, questionnaire_id: int) -> dict[str, float]:
    """Score sur 100 de chaque standard ESRS couvert par les reponses, dans l'ordre officiel.

    Moyenne simple des reponses du standard (sans les poids du score par pilier) : c'est
    un profil descriptif, pas un second score officiel.
    """
    reponses = (
        db.query(Reponse)
        .options(joinedload(Reponse.question))
        .filter(Reponse.questionnaire_id == questionnaire_id)
        .all()
    )
    valeurs: dict[str, list[int]] = defaultdict(list)
    for reponse in reponses:
        valeurs[reponse.question.esrs_standard].append(reponse.valeur)
    return {
        code: sum(valeurs[code]) / (len(valeurs[code]) * VALEUR_MAX_ESRS) * 100
        for code in ORDRE_ESRS
        if valeurs.get(code)
    }
