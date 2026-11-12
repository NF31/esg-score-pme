"""Banque de questions ESG — critères ESRS simplifiés, 8 questions par pilier.

Chaque question porte aussi une aide (affichée sous la question), l'action conseillée
quand la réponse est faible et l'effort estimé de cette action (plan d'action, F19).
"""

from sqlalchemy.orm import Session

from app.models import Effort, Pilier, Question

QUESTIONS_SEED: list[dict] = [
    # Environnement
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "L'entreprise mesure-t-elle son empreinte carbone (Scope 1 et 2) ?",
        "esrs_standard": "ESRS E1",
        "aide": (
            "Scope 1 : vos propres émissions (chauffage, véhicules). "
            "Scope 2 : l'électricité et la chaleur achetées."
        ),
        "action": "Réaliser un bilan carbone simplifié (scopes 1 et 2)",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "A-t-elle un plan de réduction de ses émissions de gaz à effet de serre ?",
        "esrs_standard": "ESRS E1",
        "aide": "Des objectifs chiffrés et des actions datées, même simples.",
        "action": "Fixer trois objectifs chiffrés de réduction des émissions",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Suit-elle sa consommation d'énergie et sa part d'énergies renouvelables ?",
        "esrs_standard": "ESRS E1",
        "aide": "Par exemple un relevé mensuel des factures d'électricité et de gaz.",
        "action": "Suivre chaque mois les consommations d'énergie",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Met-elle en place des actions de réduction des déchets et de recyclage ?",
        "esrs_standard": "ESRS E5",
        "aide": "Tri sélectif, valorisation des invendus, réduction des emballages.",
        "action": "Organiser le tri et la valorisation des déchets",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Évalue-t-elle sa consommation d'eau et les actions pour la réduire ?",
        "esrs_standard": "ESRS E3",
        "aide": "Relevés de compteur, équipements économes, récupération d'eau de pluie.",
        "action": "Relever la consommation d'eau et installer des équipements économes",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Intègre-t-elle des critères environnementaux dans le choix fournisseurs ?",
        "esrs_standard": "ESRS E5",
        "aide": "Circuits courts, labels environnementaux, clauses dans les contrats.",
        "action": "Ajouter des critères environnementaux au choix des fournisseurs",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Propose-t-elle des produits ou services éco-conçus ?",
        "esrs_standard": "ESRS E5",
        "aide": "Produits pensés pour durer, être réparés ou recyclés, avec moins de matière.",
        "action": "Lancer une démarche d'éco-conception sur un produit phare",
        "effort": Effort.ELEVE,
    },
    {
        "pilier": Pilier.ENVIRONNEMENT,
        "libelle": "Réalise-t-elle une veille sur les risques climatiques de son activité ?",
        "esrs_standard": "ESRS E1",
        "aide": "Effets possibles des canicules, inondations ou pénuries sur votre activité.",
        "action": "Cartographier les risques climatiques qui touchent l'activité",
        "effort": Effort.MOYEN,
    },
    # Social
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "L'entreprise mesure-t-elle la satisfaction et le bien-être de ses salariés ?",
        "esrs_standard": "ESRS S1",
        "aide": "Enquête annuelle, entretiens individuels, baromètre interne.",
        "action": "Lancer une enquête annuelle de satisfaction des salariés",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Dispose-t-elle d'une politique de formation et de montée en compétence ?",
        "esrs_standard": "ESRS S1",
        "aide": "Plan de formation, budget dédié, entretiens professionnels.",
        "action": "Formaliser un plan de formation annuel",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Suit-elle des indicateurs de diversité et d'égalité professionnelle ?",
        "esrs_standard": "ESRS S1",
        "aide": "Index de l'égalité professionnelle, répartition femmes-hommes, écarts de salaire.",
        "action": "Suivre les indicateurs d'égalité entre les femmes et les hommes",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "A-t-elle mis en place une politique de santé et sécurité au travail ?",
        "esrs_standard": "ESRS S1",
        "aide": "Document unique d'évaluation des risques (DUERP), prévention, formation.",
        "action": "Mettre à jour le document unique d'évaluation des risques",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Mesure-t-elle le turnover et l'absentéisme ?",
        "esrs_standard": "ESRS S1",
        "aide": "Taux de départ et taux d'absentéisme suivis au moins une fois par an.",
        "action": "Calculer chaque année le turnover et l'absentéisme",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Dialogue-t-elle régulièrement avec les représentants du personnel ?",
        "esrs_standard": "ESRS S1",
        "aide": "CSE, réunions régulières, accords d'entreprise.",
        "action": "Planifier des échanges réguliers avec les représentants du personnel",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "S'assure-t-elle du respect des droits humains chez ses fournisseurs ?",
        "esrs_standard": "ESRS S2",
        "aide": "Charte fournisseurs, questionnaire, audit des fournisseurs à risque.",
        "action": "Faire signer une charte d'achats responsables aux fournisseurs",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.SOCIAL,
        "libelle": "Contribue-t-elle à des actions d'insertion ou d'impact local ?",
        "esrs_standard": "ESRS S3",
        "aide": "Partenariats associatifs, recrutement local, mécénat, entreprises d'insertion.",
        "action": "Nouer un partenariat avec une structure d'insertion locale",
        "effort": Effort.MOYEN,
    },
    # Gouvernance
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "L'entreprise a-t-elle formalisé une politique éthique et anti-corruption ?",
        "esrs_standard": "ESRS G1",
        "aide": "Code de conduite, règles sur les cadeaux et les conflits d'intérêts.",
        "action": "Rédiger une charte éthique et anti-corruption",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Dispose-t-elle d'un dispositif d'alerte (whistleblowing) ?",
        "esrs_standard": "ESRS G1",
        "aide": "Un canal confidentiel pour signaler un problème, obligatoire dès 50 salariés.",
        "action": "Mettre en place un dispositif d'alerte interne",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Le comité de direction inclut-il une diversité de profils ?",
        "esrs_standard": "ESRS 2",
        "aide": "Variété de profils, de parcours et de genres parmi les dirigeants.",
        "action": "Diversifier les profils au sein de l'équipe de direction",
        "effort": Effort.ELEVE,
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Publie-t-elle des informations extra-financières de manière régulière ?",
        "esrs_standard": "ESRS 2",
        "aide": "Rapport RSE, page du site, bilan partagé avec les clients ou la banque.",
        "action": "Publier chaque année un court bilan RSE",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "A-t-elle une politique de gestion des risques formalisée ?",
        "esrs_standard": "ESRS 2",
        "aide": "Liste des principaux risques, avec leur probabilité et les mesures prévues.",
        "action": "Formaliser une cartographie des risques",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Rémunère-t-elle ses dirigeants en tenant compte de critères ESG ?",
        "esrs_standard": "ESRS 2",
        "aide": "Une part de la rémunération variable liée à des objectifs RSE.",
        "action": "Lier une part de la rémunération variable à des objectifs RSE",
        "effort": Effort.MOYEN,
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Respecte-t-elle un délai de paiement raisonnable envers ses fournisseurs ?",
        "esrs_standard": "ESRS G1",
        "aide": "Délai légal : 60 jours après la date de la facture au maximum.",
        "action": "Suivre et réduire les délais de paiement fournisseurs",
        "effort": Effort.FAIBLE,
    },
    {
        "pilier": Pilier.GOUVERNANCE,
        "libelle": "Met-elle en place une politique de protection des données (RGPD) ?",
        "esrs_standard": "ESRS S4",
        "aide": "Registre des traitements, information des clients, sécurité des données.",
        "action": "Tenir à jour le registre RGPD des traitements",
        "effort": Effort.FAIBLE,
    },
]


def seed_questions(db: Session) -> None:
    if db.query(Question).count() > 0:
        return
    db.add_all(Question(**data) for data in QUESTIONS_SEED)
    db.commit()
