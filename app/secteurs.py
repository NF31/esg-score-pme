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
