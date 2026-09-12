"""Rapport de synthese ESG au format PDF."""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models import Pilier, Questionnaire, Score

LIBELLE_PILIER = {
    Pilier.ENVIRONNEMENT: "Environnement",
    Pilier.SOCIAL: "Social",
    Pilier.GOUVERNANCE: "Gouvernance",
}


def _interpretation(score: float) -> str:
    if score >= 75:
        return "Bonne maturite ESG."
    if score >= 50:
        return "Maturite ESG intermediaire, des axes de progres existent."
    return "Maturite ESG faible, plusieurs axes de progres prioritaires."


def generer_rapport_pdf(db: Session, questionnaire_id: int) -> bytes:
    questionnaire = db.get(Questionnaire, questionnaire_id)
    if questionnaire is None:
        raise ValueError("Questionnaire introuvable")

    scores = db.query(Score).filter(Score.questionnaire_id == questionnaire_id).all()
    if not scores:
        raise ValueError("Aucun score calcule pour ce questionnaire")

    score_global = next(s.valeur for s in scores if s.pilier is None)
    scores_par_pilier = {s.pilier: s.valeur for s in scores if s.pilier is not None}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Rapport de diagnostic ESG", styles["Title"]),
        Paragraph(questionnaire.entreprise.nom, styles["Heading2"]),
        Paragraph(
            f"Secteur : {questionnaire.entreprise.secteur} — "
            f"Effectif : {questionnaire.entreprise.effectif}",
            styles["Normal"],
        ),
        Spacer(1, 1 * cm),
        Paragraph(f"Score global : {score_global:.0f}/100", styles["Heading2"]),
        Paragraph(_interpretation(score_global), styles["Normal"]),
        Spacer(1, 1 * cm),
    ]

    table_data = [["Pilier", "Score / 100"]]
    for pilier in Pilier:
        valeur = scores_par_pilier.get(pilier)
        table_data.append([LIBELLE_PILIER[pilier], f"{valeur:.0f}" if valeur is not None else "—"])

    table = Table(table_data, colWidths=[8 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f6f4f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
