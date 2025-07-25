"""Add client_profile_id to yape_plin_transactions

Revision ID: 567c0bed3411
Revises: 8b1f8d1372a2
Create Date: 2025-07-03 17:51:07.772257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '567c0bed3411'
down_revision: Union[str, None] = '8b1f8d1372a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('yape_plin_transactions', sa.Column('client_profile_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'yape_plin_transactions', 'client_profiles', ['client_profile_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'yape_plin_transactions', type_='foreignkey')
    op.drop_column('yape_plin_transactions', 'client_profile_id')
    # ### end Alembic commands ###
