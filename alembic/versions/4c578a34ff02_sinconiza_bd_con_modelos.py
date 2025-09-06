"""sinconiza BD con modelos
Revision ID: 4c578a34ff02
Revises: 8ddb232b6e69
Create Date: 2025-06-11 10:12:12.802083
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '4c578a34ff02'
down_revision: Union[str, None] = '8ddb232b6e69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Modificar las columnas existentes para hacerlas no nulas
    op.alter_column('users', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False)
    op.alter_column('users', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False)

def downgrade():
    # Revertir las columnas a nullable=True
    op.alter_column('users', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True)
    op.alter_column('users', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True)