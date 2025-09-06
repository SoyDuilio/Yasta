"""Add authenticated role to UserRole enum
Revision ID: bc82a6b5ca79
Revises: 9b23430f229c
Create Date: 2025-06-07 11:09:59.597779
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'bc82a6b5ca79'
down_revision: Union[str, None] = '9b23430f229c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Agregar el valor 'authenticated' al tipo ENUM userrole
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'authenticated'")

def downgrade() -> None:
    """Downgrade schema."""
    # Nota: No eliminamos el valor del ENUM porque podría haber datos usándolo
    pass