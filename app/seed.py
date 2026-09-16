"""Banque de questions ESG — critères ESRS simplifiés, 8 questions par pilier."""

from sqlalchemy.orm import Session

from app.models import Pilier, Question

QUESTIONS_SEED: list[dict] = [
    # Environnement
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "L'entreprise mesure-t-elle son empreinte carbone (Scope 1 et 2) ?",
        "esrs_standard": "ESRS E1",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "A-t-elle un plan de réduction de ses émissions de gaz à effet de serre ?",
        "esrs_standard": "ESRS E1",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Suit-elle sa consommation d'énergie et sa part d'énergies renouvelables ?",
        "esrs_standard": "ESRS E1",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Met-elle en place des actions de réduction des déchets et de recyclage ?",
        "esrs_standard": "ESRS E5",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Évalue-t-elle sa consommation d'eau et les actions pour la réduire ?",
        "esrs_standard": "ESRS E3",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Intègre-t-elle des critères environnementaux dans le choix fournisseurs ?",
        "esrs_standard": "ESRS E5",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Propose-t-elle des produits ou services éco-conçus ?",
        "esrs_standard": "ESRS E5",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Réalise-t-elle une veille sur les risques climatiques de son activité ?",
        "esrs_standard": "ESRS E1",
    },
    # Social
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "L'entreprise mesure-t-elle la satisfaction et le bien-être de ses salariés ?",
        "esrs_standard": "ESRS S1",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Dispose-t-elle d'une politique de formation et de montée en compétence ?",
        "esrs_standard": "ESRS S1",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Suit-elle des indicateurs de diversité et d'égalité professionnelle ?",
        "esrs_standard": "ESRS S1",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "A-t-elle mis en place une politique de santé et sécurité au travail ?",
        "esrs_standard": "ESRS S1",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Mesure-t-elle le turnover et l'absentéisme ?",
        "esrs_standard": "ESRS S1",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Dialogue-t-elle régulièrement avec les représentants du personnel ?",
        "esrs_standard": "ESRS S1",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "S'assure-t-elle du respect des droits humains chez ses fournisseurs ?",
        "esrs_standard": "ESRS S2",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Contribue-t-elle à des actions d'insertion ou d'impact local ?",
        "esrs_standard": "ESRS S3",
    },
    # Gouvernance
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "L'entreprise a-t-elle formalisé une politique éthique et anti-corruption ?",
        "esrs_standard": "ESRS G1",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Dispose-t-elle d'un dispositif d'alerte (whistleblowing) ?",
        "esrs_standard": "ESRS G1",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Le comité de direction inclut-il une diversité de profils ?",
        "esrs_standard": "ESRS 2",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Publie-t-elle des informations extra-financières de manière régulière ?",
        "esrs_standard": "ESRS 2",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "A-t-elle une politique de gestion des risques formalisée ?",
        "esrs_standard": "ESRS 2",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Rémunère-t-elle ses dirigeants en tenant compte de critères ESG ?",
        "esrs_standard": "ESRS 2",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Respecte-t-elle un délai de paiement raisonnable envers ses fournisseurs ?",
        "esrs_standard": "ESRS G1",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Met-elle en place une politique de protection des données (RGPD) ?",
        "esrs_standard": "ESRS S4",
    },
]


def seed_questions(db: Session) -> None:
    if db.query(Question).count() > 0:
        return
    db.add_all(Question(**data) for data in QUESTIONS_SEED)
    db.commit()
