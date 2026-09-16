"""ajout esrs_standard sur questions

Revision ID: 212d6cf5a6ac
Revises: 0d87acb8983b
Create Date: 2026-09-16 15:24:09.101981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '212d6cf5a6ac'
down_revision: Union[str, Sequence[str], None] = '0d87acb8983b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Correspondance figee au moment de cette migration (independante de app/seed.py, qui peut
# evoluer) -- backfill des 24 questions deja seedees en base avant F16.
LIBELLE_VERS_ESRS = {
    "L'entreprise mesure-t-elle son empreinte carbone (Scope 1 et 2) ?": "ESRS E1",
    "A-t-elle un plan de réduction de ses émissions de gaz à effet de serre ?": "ESRS E1",
    "Suit-elle sa consommation d'énergie et sa part d'énergies renouvelables ?": "ESRS E1",
    "Met-elle en place des actions de réduction des déchets et de recyclage ?": "ESRS E5",
    "Évalue-t-elle sa consommation d'eau et les actions pour la réduire ?": "ESRS E3",
    "Intègre-t-elle des critères environnementaux dans le choix fournisseurs ?": "ESRS E5",
    "Propose-t-elle des produits ou services éco-conçus ?": "ESRS E5",
    "Réalise-t-elle une veille sur les risques climatiques de son activité ?": "ESRS E1",
    "L'entreprise mesure-t-elle la satisfaction et le bien-être de ses salariés ?": "ESRS S1",
    "Dispose-t-elle d'une politique de formation et de montée en compétence ?": "ESRS S1",
    "Suit-elle des indicateurs de diversité et d'égalité professionnelle ?": "ESRS S1",
    "A-t-elle mis en place une politique de santé et sécurité au travail ?": "ESRS S1",
    "Mesure-t-elle le turnover et l'absentéisme ?": "ESRS S1",
    "Dialogue-t-elle régulièrement avec les représentants du personnel ?": "ESRS S1",
    "S'assure-t-elle du respect des droits humains chez ses fournisseurs ?": "ESRS S2",
    "Contribue-t-elle à des actions d'insertion ou d'impact local ?": "ESRS S3",
    "L'entreprise a-t-elle formalisé une politique éthique et anti-corruption ?": "ESRS G1",
    "Dispose-t-elle d'un dispositif d'alerte (whistleblowing) ?": "ESRS G1",
    "Le comité de direction inclut-il une diversité de profils ?": "ESRS 2",
    "Publie-t-elle des informations extra-financières de manière régulière ?": "ESRS 2",
    "A-t-elle une politique de gestion des risques formalisée ?": "ESRS 2",
    "Rémunère-t-elle ses dirigeants en tenant compte de critères ESG ?": "ESRS 2",
    "Respecte-t-elle un délai de paiement raisonnable envers ses fournisseurs ?": "ESRS G1",
    "Met-elle en place une politique de protection des données (RGPD) ?": "ESRS S4",
}


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('questions', sa.Column('esrs_standard', sa.String(length=20), nullable=True))

    bind = op.get_bind()
    questions = sa.table(
        'questions', sa.column('libelle', sa.Text), sa.column('esrs_standard', sa.String)
    )
    for libelle, code in LIBELLE_VERS_ESRS.items():
        bind.execute(
            questions.update().where(questions.c.libelle == libelle).values(esrs_standard=code)
        )
    # Questions non reconnues (ajoutees hors seed avant cette migration) : categorie
    # transversale par defaut, plutot que de bloquer la migration.
    bind.execute(
        questions.update()
        .where(questions.c.esrs_standard.is_(None))
        .values(esrs_standard="ESRS 2")
    )

    with op.batch_alter_table('questions') as batch_op:
        batch_op.alter_column('esrs_standard', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('questions', 'esrs_standard')
