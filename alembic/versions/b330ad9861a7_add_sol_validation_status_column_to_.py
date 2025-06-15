"""Add sol_validation_status column to users

Revision ID: b330ad9861a7
Revises: 4c578a34ff02
Create Date: 2025-06-14 20:57:16.700926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b330ad9861a7'
down_revision: Union[str, None] = '4c578a34ff02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Versión MANUALMENTE CORREGIDA
def upgrade() -> None:
    # Paso 1: Crear el tipo ENUM primero
    sol_status_enum = postgresql.ENUM('not_submitted', 'pending', 'valid', 'invalid', name='solvalidationstatus')
    sol_status_enum.create(op.get_bind())

    # Paso 2: Ahora, añadir la columna que USA el tipo recién creado
    op.add_column('users', 
        sa.Column(
            'sol_validation_status', 
            sol_status_enum, # Usamos la variable definida arriba
            server_default=sa.text("'not_submitted'::solvalidationstatus"), 
            nullable=False
        )
    )


# Versión MANUALMENTE CORREGIDA
def downgrade() -> None:
    # Paso 1: Eliminar la columna primero
    op.drop_column('users', 'sol_validation_status')

    # Paso 2: Ahora, eliminar el tipo ENUM
    sol_status_enum = postgresql.ENUM('not_submitted', 'pending', 'valid', 'invalid', name='solvalidationstatus')
    sol_status_enum.drop(op.get_bind())
