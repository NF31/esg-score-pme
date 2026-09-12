"""ajout siren sur entreprises

Revision ID: 0d87acb8983b
Revises: f59cf2863c16
Create Date: 2026-09-12 15:21:56.923589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d87acb8983b'
down_revision: Union[str, Sequence[str], None] = 'f59cf2863c16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("entreprises") as batch_op:
        batch_op.add_column(sa.Column("siren", sa.String(length=9), nullable=True))
        batch_op.create_unique_constraint("uq_entreprises_siren", ["siren"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("entreprises") as batch_op:
        batch_op.drop_constraint("uq_entreprises_siren", type_="unique")
        batch_op.drop_column("siren")
