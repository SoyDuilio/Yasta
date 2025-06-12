"""Add new values to userrole enum

Revision ID: 8ddb232b6e69
Revises: 983a63c1ff40
Create Date: 2025-06-10 15:04:37.571253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ddb232b6e69'
down_revision: Union[str, None] = '983a63c1ff40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Definimos la lista completa de roles que deben existir
    roles = [
        'authenticated',
        'client_freemium', 
        'client_paid',
        'staff_collaborator',
        'staff_manager',
        'staff_ceo',
        'admin'
    ]
    # Iteramos y añadimos cada valor si no existe ya
    for role in roles:
        op.execute(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{role}'")


def downgrade() -> None:
    # El downgrade de un ENUM es complejo y potencialmente peligroso si los datos ya usan los nuevos valores.
    # Por seguridad, lo dejamos vacío o simplemente ponemos un 'pass'. No vamos a revertir esto.
    pass
