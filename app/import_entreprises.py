"""Import d'entreprises reelles depuis l'API publique recherche-entreprises.api.gouv.fr.

Peuple la table `entreprises` avec des donnees d'identite reelles (nom, secteur,
effectif) pour des entreprises connues (CAC40, PME labellisees), afin de donner un
referentiel sectoriel realiste au benchmark (F11). Aucun score ESG n'est importe :
il n'existe pas d'API publique et gratuite fournissant des scores ESG fiables pour
ces entreprises -- les scores de comparaison viendront des diagnostics reellement
completes dans l'app.
"""

from dataclasses import dataclass

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

# Libelles officiels des tranches d'effectif INSEE, affiches tels quels a l'utilisateur
# (plus honnete qu'un nombre exact que l'API ne fournit pas).
LIBELLE_TRANCHE_EFFECTIF = {
    "00": "0 salarié",
    "01": "1 ou 2 salariés",
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
    "12": "20 à 49 salariés",
    "21": "50 à 99 salariés",
    "22": "100 à 199 salariés",
    "31": "200 à 249 salariés",
    "32": "250 à 499 salariés",
    "41": "500 à 999 salariés",
    "42": "1 000 à 1 999 salariés",
    "51": "2 000 à 4 999 salariés",
    "52": "5 000 à 9 999 salariés",
    "53": "10 000 salariés et plus",
}

# L'API refuse les recherches de moins de 3 caracteres (erreur 400).
LONGUEUR_MIN_RECHERCHE = 3
NB_RESULTATS_RECHERCHE = 8

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


@dataclass(frozen=True)
class EntrepriseTrouvee:
    """Une entreprise du repertoire SIRENE, telle que proposee a l'utilisateur."""

    siren: str
    nom: str
    commune: str
    code_postal: str
    code_naf: str
    secteur: str
    tranche_effectif: str
    effectif: int


def normaliser_resultat(resultat: dict) -> EntrepriseTrouvee:
    siege = resultat.get("siege") or {}
    tranche = resultat.get("tranche_effectif_salarie")
    return EntrepriseTrouvee(
        siren=resultat["siren"],
        nom=resultat.get("nom_complet") or resultat.get("nom_raison_sociale") or "",
        commune=siege.get("libelle_commune") or "",
        code_postal=siege.get("code_postal") or "",
        code_naf=resultat.get("activite_principale") or "",
        secteur=LIBELLE_SECTION_NAF.get(resultat.get("section_activite_principale"), "Non classe"),
        tranche_effectif=LIBELLE_TRANCHE_EFFECTIF.get(tranche, "Effectif non renseigné"),
        effectif=MILIEU_TRANCHE_EFFECTIF.get(tranche, 0),
    )


def rechercher_entreprises(texte: str) -> list[EntrepriseTrouvee]:
    """Recherche par nom ou SIREN dans le repertoire officiel des entreprises.

    Ne garde que les entreprises actives dont les donnees sont diffusables : une
    entreprise ayant demande la non-diffusion (souvent un entrepreneur individuel)
    n'apparait jamais, meme si l'API la renvoie avec des champs masques.
    """
    texte = texte.strip()
    if len(texte) < LONGUEUR_MIN_RECHERCHE:
        raise ValueError(f"Saisissez au moins {LONGUEUR_MIN_RECHERCHE} caracteres.")

    reponse = httpx.get(
        API_URL,
        params={"q": texte, "per_page": NB_RESULTATS_RECHERCHE, "etat_administratif": "A"},
        timeout=10,
    )
    reponse.raise_for_status()
    return [
        normaliser_resultat(r)
        for r in reponse.json()["results"]
        if r.get("statut_diffusion") == "O" and r.get("etat_administratif") == "A"
    ]


def enregistrer_entreprise(db: Session, trouvee: EntrepriseTrouvee) -> Entreprise:
    """Cree l'entreprise, ou la met a jour si son SIREN est deja connu.

    Reutiliser la ligne existante plutot que d'en creer une nouvelle permet a
    l'historique (F13) de suivre la meme entreprise d'un diagnostic a l'autre.
    """
    entreprise = db.query(Entreprise).filter(Entreprise.siren == trouvee.siren).first()
    if entreprise is None:
        entreprise = Entreprise(siren=trouvee.siren, nom=trouvee.nom, secteur="", effectif=0)
        db.add(entreprise)
    entreprise.nom = trouvee.nom
    entreprise.secteur = trouvee.secteur
    entreprise.effectif = trouvee.effectif
    db.commit()
    db.refresh(entreprise)
    return entreprise


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
