"""Export du diagnostic ESG structure selon les standards ESRS (F16).

Reprend les reponses du questionnaire, regroupees par standard ESRS (`app/esrs.py`)
plutot que par les 3 piliers simplifies E/S/G utilises dans le reste de l'app -- pour
se rapprocher de la structure d'un rapport de durabilite CSRD reel. Ce n'est pas un
export CSRD/ESRS conforme (pas de double materialite, pas de balisage XBRL) : voir
`docs/STACK.md` pour les limites assumees.
"""

import io
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session, joinedload

from app.esrs import ESRS_LABELS, ORDRE_ESRS
from app.models import Questionnaire, Reponse

VALEUR_MAX = 4


def generer_export_esrs(db: Session, questionnaire_id: int) -> bytes:
    questionnaire = db.get(Questionnaire, questionnaire_id)
    if questionnaire is None:
        raise ValueError("Questionnaire introuvable")

    reponses = (
        db.query(Reponse)
        .options(joinedload(Reponse.question))
        .filter(Reponse.questionnaire_id == questionnaire_id)
        .all()
    )
    if not reponses:
        raise ValueError("Aucune reponse enregistree pour ce questionnaire")

    reponses_par_standard: dict[str, list[Reponse]] = defaultdict(list)
    for reponse in reponses:
        reponses_par_standard[reponse.question.esrs_standard].append(reponse)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Export du diagnostic ESG -- structure ESRS", styles["Title"]),
        Paragraph(questionnaire.entreprise.nom, styles["Heading2"]),
        Paragraph(
            f"Secteur : {questionnaire.entreprise.secteur} — "
            f"Effectif : {questionnaire.entreprise.effectif}",
            styles["Normal"],
        ),
        Spacer(1, 0.5 * cm),
        Paragraph(
            "Regroupement indicatif par standard ESRS (European Sustainability Reporting "
            "Standards), a titre pedagogique -- ne constitue pas un rapport de durabilite "
            "CSRD conforme (pas d'analyse de double materialite, pas de balisage XBRL).",
            styles["Italic"],
        ),
        Spacer(1, 0.5 * cm),
    ]

    for code in ORDRE_ESRS:
        reponses_standard = reponses_par_standard.get(code)
        if not reponses_standard:
            continue

        score_standard = (
            sum(r.valeur for r in reponses_standard) / (len(reponses_standard) * VALEUR_MAX) * 100
        )

        elements.append(
            Paragraph(
                f"{code} — {ESRS_LABELS[code]} ({score_standard:.0f}/100)", styles["Heading3"]
            )
        )

        table_data = [["Critere", "Reponse"]]
        for reponse in reponses_standard:
            table_data.append([reponse.question.libelle, f"{reponse.valeur}/4"])

        table = Table(table_data, colWidths=[13 * cm, 2.5 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f6f4f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 0.5 * cm))

    doc.build(elements)
    return buffer.getvalue()
