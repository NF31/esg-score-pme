"""Extraction de reponses au questionnaire ESG depuis un rapport RSE (PDF), via Claude.

Le PDF est envoye directement au modele (document natif, pas d'extraction de texte
intermediaire). Le resultat ne fait que *suggerer* une valeur par question : il pre-remplit
le questionnaire dans Streamlit mais reste entierement modifiable avant calcul du score --
aucune reponse n'est ecrite en base par ce module (cf. docs/STACK.md, F14).
"""

import base64

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Question

MODELE = "claude-sonnet-5"
TAILLE_MAX_PDF_OCTETS = 10 * 1024 * 1024  # 10 Mo -- cf. .streamlit/config.toml

OUTIL_ENREGISTRER_REPONSES = {
    "name": "enregistrer_reponses_extraites",
    "description": (
        "Enregistre, pour chaque question du questionnaire ESG fournie, la valeur estimee "
        "(0 a 4) d'apres le rapport RSE et une courte justification."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reponses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_id": {"type": "integer"},
                        "valeur": {"type": "integer", "minimum": 0, "maximum": 4},
                        "justification": {
                            "type": "string",
                            "description": (
                                "1-2 phrases citant l'element du rapport qui justifie la valeur"
                            ),
                        },
                    },
                    "required": ["question_id", "valeur", "justification"],
                },
            }
        },
        "required": ["reponses"],
    },
}

PROMPT_SYSTEME = """Tu es un expert RSE qui analyse un rapport RSE/extra-financier d'entreprise \
pour pre-remplir un questionnaire d'auto-diagnostic ESG interne.

Pour chaque question fournie, estime une valeur de 0 a 4 (0 = aucune pratique/donnee \
mentionnee, 4 = pratique exemplaire et documentee avec des donnees chiffrees) d'apres ce que \
le rapport decrit reellement. Si le rapport ne mentionne rien sur une question, reponds 0 et \
dis-le dans la justification -- n'invente jamais une pratique non mentionnee. Reponds pour \
TOUTES les questions fournies via l'outil enregistrer_reponses_extraites."""


def extraire_reponses(db: Session, pdf_bytes: bytes) -> list[dict]:
    if not settings.anthropic_api_key:
        raise ValueError("Cle ANTHROPIC_API_KEY non configuree")
    if not pdf_bytes:
        raise ValueError("Fichier PDF vide")
    if len(pdf_bytes) > TAILLE_MAX_PDF_OCTETS:
        raise ValueError("Fichier PDF trop volumineux (limite 10 Mo)")

    questions = db.query(Question).order_by(Question.pilier, Question.id).all()
    if not questions:
        raise ValueError("Aucune question en base")

    liste_questions = "\n".join(f"- id={q.id} [{q.pilier.value}] {q.libelle}" for q in questions)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=MODELE,
        max_tokens=4096,
        system=PROMPT_SYSTEME,
        tools=[OUTIL_ENREGISTRER_REPONSES],
        tool_choice={"type": "tool", "name": "enregistrer_reponses_extraites"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64.standard_b64encode(pdf_bytes).decode("utf-8"),
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Questions du questionnaire ESG :\n{liste_questions}",
                    },
                ],
            }
        ],
    )

    bloc_outil = next(bloc for bloc in message.content if bloc.type == "tool_use")
    reponses = bloc_outil.input["reponses"]

    ids_valides = {q.id for q in questions}
    return [r for r in reponses if r["question_id"] in ids_valides]
