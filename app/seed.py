"""Banque de questions ESG — critères ESRS simplifiés, 8 questions par pilier."""

from sqlalchemy.orm import Session

from app.models import Pilier, Question

QUESTIONS_SEED: list[dict] = [
    # Environnement
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "L'entreprise mesure-t-elle son empreinte carbone (Scope 1 et 2) ?",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "A-t-elle un plan de réduction de ses émissions de gaz à effet de serre ?",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Suit-elle sa consommation d'énergie et sa part d'énergies renouvelables ?",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Met-elle en place des actions de réduction des déchets et de recyclage ?",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Évalue-t-elle sa consommation d'eau et les actions pour la réduire ?",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Intègre-t-elle des critères environnementaux dans le choix fournisseurs ?",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Propose-t-elle des produits ou services éco-conçus ?",
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Réalise-t-elle une veille sur les risques climatiques de son activité ?",
    },
    # Social
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "L'entreprise mesure-t-elle la satisfaction et le bien-être de ses salariés ?",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Dispose-t-elle d'une politique de formation et de montée en compétence ?",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Suit-elle des indicateurs de diversité et d'égalité professionnelle ?",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "A-t-elle mis en place une politique de santé et sécurité au travail ?",
    },
    {"pilier": Pilier.SOCIAL, "libelle": "Mesure-t-elle le turnover et l'absentéisme ?"},
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Dialogue-t-elle régulièrement avec les représentants du personnel ?",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "S'assure-t-elle du respect des droits humains chez ses fournisseurs ?",
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Contribue-t-elle à des actions d'insertion ou d'impact local ?",
    },
    # Gouvernance
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "L'entreprise a-t-elle formalisé une politique éthique et anti-corruption ?",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Dispose-t-elle d'un dispositif d'alerte (whistleblowing) ?",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Le comité de direction inclut-il une diversité de profils ?",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Publie-t-elle des informations extra-financières de manière régulière ?",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "A-t-elle une politique de gestion des risques formalisée ?",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Rémunère-t-elle ses dirigeants en tenant compte de critères ESG ?",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Respecte-t-elle un délai de paiement raisonnable envers ses fournisseurs ?",
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Met-elle en place une politique de protection des données (RGPD) ?",
    },
]


def seed_questions(db: Session) -> None:
    if db.query(Question).count() > 0:
        return
    db.add_all(Question(**data) for data in QUESTIONS_SEED)
    db.commit()
