"""Nomenclature de secteurs partagee entre la saisie utilisateur (F02) et l'import
d'entreprises reelles (F10), condition necessaire pour que la comparaison sectorielle
(F11) puisse regrouper des entreprises comparables.

Basee sur les 21 sections de la nomenclature NAF (INSEE) -- stable, ne change quasiment
jamais.
"""

LIBELLE_SECTION_NAF = {
    "A": "Agriculture, sylviculture et peche",
    "B": "Industries extractives",
    "C": "Industrie manufacturiere",
    "D": "Production et distribution d'energie",
    "E": "Production et distribution d'eau, gestion des dechets",
    "F": "Construction",
    "G": "Commerce, reparation d'automobiles et de motocycles",
    "H": "Transports et entreposage",
    "I": "Hebergement et restauration",
    "J": "Information et communication",
    "K": "Activites financieres et d'assurance",
    "L": "Activites immobilieres",
    "M": "Activites specialisees, scientifiques et techniques",
    "N": "Activites de services administratifs et de soutien",
    "O": "Administration publique",
    "P": "Enseignement",
    "Q": "Sante humaine et action sociale",
    "R": "Arts, spectacles et activites recreatives",
    "S": "Autres activites de services",
    "T": "Activites des menages employeurs",
    "U": "Activites extra-territoriales",
}

SECTEURS = sorted(LIBELLE_SECTION_NAF.values())

# Libelles accentues pour l'affichage : les libelles ci-dessus restent la cle stockee en
# base (comparaison sectorielle, API), on ne les modifie donc pas.
AFFICHAGE_SECTEUR = {
    "Agriculture, sylviculture et peche": "Agriculture, sylviculture et pêche",
    "Production et distribution d'energie": "Production et distribution d'énergie",
    "Production et distribution d'eau, gestion des dechets": (
        "Production et distribution d'eau, gestion des déchets"
    ),
    "Industrie manufacturiere": "Industrie manufacturière",
    "Commerce, reparation d'automobiles et de motocycles": (
        "Commerce, réparation d'automobiles et de motocycles"
    ),
    "Hebergement et restauration": "Hébergement et restauration",
    "Activites financieres et d'assurance": "Activités financières et d'assurance",
    "Activites immobilieres": "Activités immobilières",
    "Activites specialisees, scientifiques et techniques": (
        "Activités spécialisées, scientifiques et techniques"
    ),
    "Activites de services administratifs et de soutien": (
        "Activités de services administratifs et de soutien"
    ),
    "Sante humaine et action sociale": "Santé humaine et action sociale",
    "Arts, spectacles et activites recreatives": "Arts, spectacles et activités récréatives",
    "Autres activites de services": "Autres activités de services",
    "Activites des menages employeurs": "Activités des ménages employeurs",
    "Activites extra-territoriales": "Activités extra-territoriales",
    "Non classe": "Non classé",
}


def libelle_secteur(secteur: str) -> str:
    return AFFICHAGE_SECTEUR.get(secteur, secteur)
