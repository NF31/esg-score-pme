"""Import d'entreprises reelles depuis l'API publique recherche-entreprises.api.gouv.fr.

Peuple la table `entreprises` avec des donnees d'identite reelles (nom, secteur,
effectif) pour des entreprises connues (CAC40, PME labellisees), afin de donner un
referentiel sectoriel realiste au benchmark (F11). Aucun score ESG n'est importe :
il n'existe pas d'API publique et gratuite fournissant des scores ESG fiables pour
ces entreprises -- les scores de comparaison viendront des diagnostics reellement
completes dans l'app.
"""

import httpx
from sqlalchemy.orm import Session

from app.models import Entreprise
from app.secteurs import LIBELLE_SECTION_NAF

API_URL = "https://recherche-entreprises.api.gouv.fr/search"

# Tranches d'effectif salarie INSEE -- l'API ne donne jamais le nombre exact
# (secret statistique), seulement un code de tranche. On stocke le milieu de la
# tranche comme approximation dans le champ `effectif` (int) du modele.
MILIEU_TRANCHE_EFFECTIF = {
    "00": 0,
    "01": 1,
    "02": 4,
    "03": 7,
    "11": 15,
    "12": 35,
    "21": 75,
    "22": 150,
    "31": 225,
    "32": 375,
    "41": 750,
    "42": 1500,
    "51": 3500,
    "52": 7500,
    "53": 10000,
}

CAC40_NOMS = [
    "Air Liquide",
    "Airbus",
    "ArcelorMittal",
    "AXA",
    "BNP Paribas",
    "Bouygues",
    "Capgemini",
    "Carrefour",
    "Credit Agricole",
    "Danone",
    "Dassault Systemes",
    "Edenred",
    "Engie",
    "EssilorLuxottica",
    "Eurofins Scientific",
    "Hermes",
    "Kering",
    "Legrand",
    "L'Oreal",
    "LVMH",
    "Michelin",
    "Orange",
    "Pernod Ricard",
    "Publicis",
    "Renault",
    "Safran",
    "Saint-Gobain",
    "Sanofi",
    "Schneider Electric",
    "Societe Generale",
    "Stellantis",
    "STMicroelectronics",
    "Teleperformance",
    "Thales",
    "TotalEnergies",
    "Veolia",
    "Vinci",
    "Vivendi",
]


def rechercher_entreprise(nom: str) -> dict | None:
    reponse = httpx.get(API_URL, params={"q": nom, "per_page": 5}, timeout=10)
    reponse.raise_for_status()
    resultats = reponse.json()["results"]
    if not resultats:
        return None
    # Les grands groupes ont souvent une multitude de filiales/holdings sous le
    # meme nom (immobilier, R&D...) qui remontent avant l'entite operationnelle
    # principale. Preferer une "grande entreprise" (GE) limite ce bruit, sans
    # garantir la filiale la plus representative du secteur reel du groupe.
    return next(
        (r for r in resultats if r.get("categorie_entreprise") == "GE"),
        resultats[0],
    )


def importer_entreprises(db: Session, noms: list[str]) -> list[Entreprise]:
    importees = []
    for nom in noms:
        resultat = rechercher_entreprise(nom)
        if resultat is None:
            continue

        siren = resultat["siren"]
        entreprise = db.query(Entreprise).filter(Entreprise.siren == siren).first()
        if entreprise is None:
            entreprise = Entreprise(siren=siren, nom=nom, secteur=nom, effectif=0)
            db.add(entreprise)

        entreprise.nom = resultat["nom_complet"] or resultat["nom_raison_sociale"]
        section = resultat.get("section_activite_principale")
        entreprise.secteur = LIBELLE_SECTION_NAF.get(section, "Non classe")
        tranche = resultat.get("tranche_effectif_salarie")
        entreprise.effectif = MILIEU_TRANCHE_EFFECTIF.get(tranche, 0)

        importees.append(entreprise)

    db.commit()
    return importees


if __name__ == "__main__":
    from app.database import SessionLocal

    with SessionLocal() as session:
        entreprises = importer_entreprises(session, CAC40_NOMS)
        print(f"{len(entreprises)}/{len(CAC40_NOMS)} entreprises importees.")
