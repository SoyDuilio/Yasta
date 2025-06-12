"""sinconiza BD con modelos

Revision ID: 4c578a34ff02
Revises: 8ddb232b6e69
Create Date: 2025-06-11 10:12:12.802083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c578a34ff02'
down_revision: Union[str, None] = '8ddb232b6e69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Agregar las columnas con valores por defecto
    op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), 
                                   server_default=sa.func.now(), nullable=False))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), 
                                   server_default=sa.func.now(), nullable=False))

def downgrade():
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
