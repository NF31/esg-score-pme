"""ajout aide, action et effort sur questions

Revision ID: 1a799d950536
Revises: 212d6cf5a6ac
Create Date: 2026-11-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a799d950536'
down_revision: Union[str, Sequence[str], None] = '212d6cf5a6ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EFFORT = sa.Enum('FAIBLE', 'MOYEN', 'ELEVE', name='effort')

# Correspondance figee au moment de cette migration (independante de app/seed.py, qui peut
# evoluer) -- backfill des 24 questions deja seedees en base avant F18/F19.
LIBELLE_VERS_AIDE_ACTION_EFFORT = {
    "L'entreprise mesure-t-elle son empreinte carbone (Scope 1 et 2) ?": (
        "Scope 1 : vos propres émissions (chauffage, véhicules). Scope 2 : l'électricité et la chaleur achetées.",
        'Réaliser un bilan carbone simplifié (scopes 1 et 2)',
        'MOYEN',
    ),
    'A-t-elle un plan de réduction de ses émissions de gaz à effet de serre ?': (
        'Des objectifs chiffrés et des actions datées, même simples.',
        'Fixer trois objectifs chiffrés de réduction des émissions',
        'FAIBLE',
    ),
    "Suit-elle sa consommation d'énergie et sa part d'énergies renouvelables ?": (
        "Par exemple un relevé mensuel des factures d'électricité et de gaz.",
        "Suivre chaque mois les consommations d'énergie",
        'FAIBLE',
    ),
    'Met-elle en place des actions de réduction des déchets et de recyclage ?': (
        'Tri sélectif, valorisation des invendus, réduction des emballages.',
        'Organiser le tri et la valorisation des déchets',
        'FAIBLE',
    ),
    "Évalue-t-elle sa consommation d'eau et les actions pour la réduire ?": (
        "Relevés de compteur, équipements économes, récupération d'eau de pluie.",
        "Relever la consommation d'eau et installer des équipements économes",
        'FAIBLE',
    ),
    'Intègre-t-elle des critères environnementaux dans le choix fournisseurs ?': (
        'Circuits courts, labels environnementaux, clauses dans les contrats.',
        'Ajouter des critères environnementaux au choix des fournisseurs',
        'MOYEN',
    ),
    'Propose-t-elle des produits ou services éco-conçus ?': (
        'Produits pensés pour durer, être réparés ou recyclés, avec moins de matière.',
        "Lancer une démarche d'éco-conception sur un produit phare",
        'ELEVE',
    ),
    'Réalise-t-elle une veille sur les risques climatiques de son activité ?': (
        'Effets possibles des canicules, inondations ou pénuries sur votre activité.',
        "Cartographier les risques climatiques qui touchent l'activité",
        'MOYEN',
    ),
    "L'entreprise mesure-t-elle la satisfaction et le bien-être de ses salariés ?": (
        'Enquête annuelle, entretiens individuels, baromètre interne.',
        'Lancer une enquête annuelle de satisfaction des salariés',
        'FAIBLE',
    ),
    "Dispose-t-elle d'une politique de formation et de montée en compétence ?": (
        'Plan de formation, budget dédié, entretiens professionnels.',
        'Formaliser un plan de formation annuel',
        'MOYEN',
    ),
    "Suit-elle des indicateurs de diversité et d'égalité professionnelle ?": (
        "Index de l'égalité professionnelle, répartition femmes-hommes, écarts de salaire.",
        "Suivre les indicateurs d'égalité entre les femmes et les hommes",
        'FAIBLE',
    ),
    'A-t-elle mis en place une politique de santé et sécurité au travail ?': (
        "Document unique d'évaluation des risques (DUERP), prévention, formation.",
        "Mettre à jour le document unique d'évaluation des risques",
        'FAIBLE',
    ),
    "Mesure-t-elle le turnover et l'absentéisme ?": (
        "Taux de départ et taux d'absentéisme suivis au moins une fois par an.",
        "Calculer chaque année le turnover et l'absentéisme",
        'FAIBLE',
    ),
    'Dialogue-t-elle régulièrement avec les représentants du personnel ?': (
        "CSE, réunions régulières, accords d'entreprise.",
        'Planifier des échanges réguliers avec les représentants du personnel',
        'FAIBLE',
    ),
    "S'assure-t-elle du respect des droits humains chez ses fournisseurs ?": (
        'Charte fournisseurs, questionnaire, audit des fournisseurs à risque.',
        "Faire signer une charte d'achats responsables aux fournisseurs",
        'MOYEN',
    ),
    "Contribue-t-elle à des actions d'insertion ou d'impact local ?": (
        "Partenariats associatifs, recrutement local, mécénat, entreprises d'insertion.",
        "Nouer un partenariat avec une structure d'insertion locale",
        'MOYEN',
    ),
    "L'entreprise a-t-elle formalisé une politique éthique et anti-corruption ?": (
        "Code de conduite, règles sur les cadeaux et les conflits d'intérêts.",
        'Rédiger une charte éthique et anti-corruption',
        'FAIBLE',
    ),
    "Dispose-t-elle d'un dispositif d'alerte (whistleblowing) ?": (
        'Un canal confidentiel pour signaler un problème, obligatoire dès 50 salariés.',
        "Mettre en place un dispositif d'alerte interne",
        'MOYEN',
    ),
    'Le comité de direction inclut-il une diversité de profils ?': (
        'Variété de profils, de parcours et de genres parmi les dirigeants.',
        "Diversifier les profils au sein de l'équipe de direction",
        'ELEVE',
    ),
    'Publie-t-elle des informations extra-financières de manière régulière ?': (
        'Rapport RSE, page du site, bilan partagé avec les clients ou la banque.',
        'Publier chaque année un court bilan RSE',
        'MOYEN',
    ),
    'A-t-elle une politique de gestion des risques formalisée ?': (
        'Liste des principaux risques, avec leur probabilité et les mesures prévues.',
        'Formaliser une cartographie des risques',
        'MOYEN',
    ),
    'Rémunère-t-elle ses dirigeants en tenant compte de critères ESG ?': (
        'Une part de la rémunération variable liée à des objectifs RSE.',
        'Lier une part de la rémunération variable à des objectifs RSE',
        'MOYEN',
    ),
    'Respecte-t-elle un délai de paiement raisonnable envers ses fournisseurs ?': (
        'Délai légal : 60 jours après la date de la facture au maximum.',
        'Suivre et réduire les délais de paiement fournisseurs',
        'FAIBLE',
    ),
    'Met-elle en place une politique de protection des données (RGPD) ?': (
        'Registre des traitements, information des clients, sécurité des données.',
        'Tenir à jour le registre RGPD des traitements',
        'FAIBLE',
    ),
}


def upgrade() -> None:
    """Upgrade schema."""
    EFFORT.create(op.get_bind(), checkfirst=True)
    op.add_column('questions', sa.Column('aide', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('action', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('effort', EFFORT, nullable=True))

    bind = op.get_bind()
    questions = sa.table(
        'questions',
        sa.column('libelle', sa.Text),
        sa.column('aide', sa.Text),
        sa.column('action', sa.Text),
        sa.column('effort', EFFORT),
    )
    for libelle, (aide, action, effort) in LIBELLE_VERS_AIDE_ACTION_EFFORT.items():
        bind.execute(
            questions.update()
            .where(questions.c.libelle == libelle)
            .values(aide=aide, action=action, effort=effort)
        )
    # Questions non reconnues (ajoutees hors seed) : effort moyen par defaut, sans aide
    # ni action, plutot que de bloquer la migration.
    bind.execute(questions.update().where(questions.c.effort.is_(None)).values(effort='MOYEN'))

    with op.batch_alter_table('questions') as batch_op:
        batch_op.alter_column('effort', existing_type=EFFORT, nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('questions') as batch_op:
        batch_op.drop_column('effort')
        batch_op.drop_column('action')
        batch_op.drop_column('aide')
    EFFORT.drop(op.get_bind(), checkfirst=True)
