from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.import_entreprises import importer_entreprises
from app.models import Base, Entreprise

RESULTAT_TOTALENERGIES = {
    "siren": "542051180",
    "nom_complet": "TOTALENERGIES SE",
    "nom_raison_sociale": "TOTALENERGIES SE",
    "section_activite_principale": "D",
    "tranche_effectif_salarie": "53",
}


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


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
