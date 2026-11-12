"""ajout est_exemple sur entreprises

Revision ID: ac52d7cbe4ad
Revises: 1a799d950536
Create Date: 2026-11-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac52d7cbe4ad'
down_revision: Union[str, Sequence[str], None] = '1a799d950536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default : les entreprises deja en base sont des vraies entreprises
    op.add_column(
        'entreprises',
        sa.Column('est_exemple', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('entreprises') as batch_op:
        batch_op.drop_column('est_exemple')
