"""Create service_tariffs table

Revision ID: 462cd9a60ff2
Revises: b330ad9861a7
Create Date: 2025-06-17 14:55:44.042264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '462cd9a60ff2'
down_revision: Union[str, None] = 'b330ad9861a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands corrected for data type mismatch ###
    op.create_table('service_tariffs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('service_type_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['service_type_id'], ['service_types.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands corrected for data type mismatch ###
    op.drop_table('service_tariffs')
    # ### end Alembic commands ###