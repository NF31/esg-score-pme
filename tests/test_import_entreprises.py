from unittest.mock import MagicMock, patch

import pytest

from app.import_entreprises import (
    EntrepriseTrouvee,
    enregistrer_entreprise,
    importer_entreprises,
    normaliser_resultat,
    rechercher_entreprises,
)
from app.models import Entreprise

RESULTAT_TOTALENERGIES = {
    "siren": "542051180",
    "nom_complet": "TOTALENERGIES SE",
    "nom_raison_sociale": "TOTALENERGIES SE",
    "section_activite_principale": "D",
    "tranche_effectif_salarie": "53",
}


def test_importer_entreprises_cree_une_entreprise(db):
    with patch("app.import_entreprises.rechercher_entreprise", return_value=RESULTAT_TOTALENERGIES):
        importees = importer_entreprises(db, ["TotalEnergies"])

    assert len(importees) == 1
    entreprise = db.query(Entreprise).filter(Entreprise.siren == "542051180").one()
    assert entreprise.nom == "TOTALENERGIES SE"
    assert entreprise.secteur == "Production et distribution d'energie"
    assert entreprise.effectif == 10000


def test_importer_entreprises_ignore_un_nom_sans_resultat(db):
    with patch("app.import_entreprises.rechercher_entreprise", return_value=None):
        importees = importer_entreprises(db, ["Entreprise Inexistante Xyz"])

    assert importees == []
    assert db.query(Entreprise).count() == 0


def test_importer_entreprises_met_a_jour_sans_dupliquer(db):
    with patch("app.import_entreprises.rechercher_entreprise", return_value=RESULTAT_TOTALENERGIES):
        importer_entreprises(db, ["TotalEnergies"])
        importer_entreprises(db, ["TotalEnergies"])

    assert db.query(Entreprise).count() == 1


def _reponse_api(resultats: list[dict]):
    reponse = MagicMock()
    reponse.json.return_value = {"results": resultats}
    return reponse


RESULTAT_PME = {
    "siren": "123456789",
    "nom_complet": "BOULANGERIE DU CANAL",
    "siege": {"libelle_commune": "TOULOUSE", "code_postal": "31000"},
    "activite_principale": "10.71C",
    "section_activite_principale": "C",
    "tranche_effectif_salarie": "11",
    "etat_administratif": "A",
    "statut_diffusion": "O",
}


def test_rechercher_entreprises_normalise_les_resultats():
    with patch("app.import_entreprises.httpx.get", return_value=_reponse_api([RESULTAT_PME])):
        resultats = rechercher_entreprises("boulangerie toulouse")

    assert resultats == [
        EntrepriseTrouvee(
            siren="123456789",
            nom="BOULANGERIE DU CANAL",
            commune="TOULOUSE",
            code_postal="31000",
            code_naf="10.71C",
            secteur="Industrie manufacturiere",
            tranche_effectif="10 à 19 salariés",
            effectif=15,
        )
    ]


def test_rechercher_entreprises_exclut_les_non_diffusibles_et_les_fermees():
    non_diffusible = {**RESULTAT_PME, "siren": "1", "statut_diffusion": "P"}
    fermee = {**RESULTAT_PME, "siren": "2", "etat_administratif": "C"}
    with patch(
        "app.import_entreprises.httpx.get",
        return_value=_reponse_api([non_diffusible, fermee, RESULTAT_PME]),
    ):
        resultats = rechercher_entreprises("boulangerie")

    assert [r.siren for r in resultats] == ["123456789"]


def test_rechercher_entreprises_refuse_une_recherche_trop_courte():
    with patch("app.import_entreprises.httpx.get") as appel_api, pytest.raises(ValueError):
        rechercher_entreprises(" ab ")
    appel_api.assert_not_called()


def test_enregistrer_entreprise_reutilise_le_meme_siren(db):
    trouvee = normaliser_resultat(RESULTAT_PME)

    premiere = enregistrer_entreprise(db, trouvee)
    seconde = enregistrer_entreprise(db, trouvee)

    assert premiere.id == seconde.id
    assert db.query(Entreprise).count() == 1
    assert premiere.secteur == "Industrie manufacturiere"
    assert premiere.effectif == 15
