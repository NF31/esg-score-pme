from types import SimpleNamespace

import pytest

from app import extraction_pdf
from app.extraction_pdf import extraire_reponses
from app.models import Pilier, Question

PDF_MINIMAL = b"%PDF-1.4 fake content"


def test_extraction_leve_une_erreur_sans_cle_api(db, monkeypatch):
    monkeypatch.setattr(extraction_pdf.settings, "anthropic_api_key", None)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        extraire_reponses(db, PDF_MINIMAL)


def test_extraction_leve_une_erreur_si_pdf_vide(db, monkeypatch):
    monkeypatch.setattr(extraction_pdf.settings, "anthropic_api_key", "fake-key")

    with pytest.raises(ValueError, match="vide"):
        extraire_reponses(db, b"")


def test_extraction_leve_une_erreur_si_pdf_trop_volumineux(db, monkeypatch):
    monkeypatch.setattr(extraction_pdf.settings, "anthropic_api_key", "fake-key")

    pdf_trop_gros = b"0" * (extraction_pdf.TAILLE_MAX_PDF_OCTETS + 1)

    with pytest.raises(ValueError, match="volumineux"):
        extraire_reponses(db, pdf_trop_gros)


def test_extraction_leve_une_erreur_sans_question_en_base(db, monkeypatch):
    monkeypatch.setattr(extraction_pdf.settings, "anthropic_api_key", "fake-key")

    with pytest.raises(ValueError, match="Aucune question"):
        extraire_reponses(db, PDF_MINIMAL)


def test_extraction_ignore_les_ids_hors_questionnaire(db, monkeypatch):
    monkeypatch.setattr(extraction_pdf.settings, "anthropic_api_key", "fake-key")
    question = Question(pilier=Pilier.ENVIRONNEMENT, libelle="Q", poids=1.0)
    db.add(question)
    db.commit()

    reponse_valide = {"question_id": question.id, "valeur": 3, "justification": "Cite p.12"}
    reponse_invalide = {"question_id": 99999, "valeur": 2, "justification": "Hors questionnaire"}
    bloc_outil = SimpleNamespace(
        type="tool_use", input={"reponses": [reponse_valide, reponse_invalide]}
    )
    fake_message = SimpleNamespace(content=[bloc_outil])

    class FakeMessages:
        def create(self, **kwargs):
            return fake_message

    class FakeClient:
        def __init__(self, api_key):
            self.messages = FakeMessages()

    monkeypatch.setattr(extraction_pdf.anthropic, "Anthropic", FakeClient)

    reponses = extraire_reponses(db, PDF_MINIMAL)

    assert reponses == [reponse_valide]
