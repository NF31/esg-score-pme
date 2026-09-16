"""Referentiel simplifie des standards ESRS (European Sustainability Reporting Standards)
utilises pour classer les 24 questions du diagnostic (cf. `app/seed.py`, F16).

Simplification assumee : seuls les standards pertinents pour une PME sont couverts (pas de
E2 Pollution ni E4 Biodiversite, peu probables sans activite industrielle specifique) --
voir `docs/STACK.md` pour la justification complete et les limites de cet alignement.
"""

ESRS_LABELS: dict[str, str] = {
    "ESRS E1": "Changement climatique",
    "ESRS E3": "Ressources en eau et marines",
    "ESRS E5": "Utilisation des ressources et economie circulaire",
    "ESRS S1": "Effectifs de l'entreprise",
    "ESRS S2": "Travailleurs de la chaine de valeur",
    "ESRS S3": "Communautes affectees",
    "ESRS S4": "Consommateurs et utilisateurs finaux",
    "ESRS G1": "Conduite des affaires",
    "ESRS 2": "Informations generales",
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
