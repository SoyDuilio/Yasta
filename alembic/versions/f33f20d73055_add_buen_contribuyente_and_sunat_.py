"""Add buen_contribuyente and sunat_schedule tables correctly

Revision ID: f33f20d73055
Revises: b330ad9861a7
Create Date: 2024-06-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f33f20d73055'
down_revision: Union[str, None] = 'b330ad9861a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Comandos ajustados manualmente para el estado real de la BD ###
    
    # PASO 1: Crear los nuevos tipos ENUM, verificando si ya existen para evitar errores.
    solvalidationstatus_enum = postgresql.ENUM('not_submitted', 'pending', 'valid', 'invalid', name='solvalidationstatus')
    solvalidationstatus_enum.create(op.get_bind(), checkfirst=True)

    contributorgroup_enum = postgresql.ENUM('general', 'buen_contribuyente', name='contributorgroup')
    contributorgroup_enum.create(op.get_bind(), checkfirst=True)
    
    # PASO 2: Crear SOLAMENTE las tablas que faltan.
    op.create_table('buen_contribuyentes',
        sa.Column('ruc', sa.String(length=11), nullable=False),
        sa.Column('razon_social', sa.String(length=255), nullable=False),
        sa.Column('fecha_incorporacion', sa.Date(), nullable=False),
        sa.Column('numero_resolucion', sa.String(length=100), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('ruc')
    )
    op.create_index(op.f('ix_buen_contribuyentes_ruc'), 'buen_contribuyentes', ['ruc'], unique=False)

    # LA CORRECCIÓN CLAVE: Al definir el ENUM dentro de la tabla, le decimos
    # a SQLAlchemy que no intente crear el tipo de nuevo, ya que lo hicimos arriba.
    op.create_table('sunat_schedules',
        sa.Column('tax_period', sa.String(length=7), nullable=False),
        sa.Column('last_ruc_digit', sa.String(length=1), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('contributor_group', postgresql.ENUM('general', 'buen_contribuyente', name='contributorgroup', create_type=False), server_default=sa.text("'general'::contributorgroup"), nullable=False),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('legal_base_document', sa.String(length=255), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('last_updated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['last_updated_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tax_period', 'last_ruc_digit', 'contributor_group', name='_period_ruc_digit_group_uc')
    )
    op.create_index(op.f('ix_sunat_schedules_id'), 'sunat_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_sunat_schedules_last_ruc_digit'), 'sunat_schedules', ['last_ruc_digit'], unique=False)
    op.create_index(op.f('ix_sunat_schedules_tax_period'), 'sunat_schedules', ['tax_period'], unique=False)

    # PASO 3: NO HACEMOS NADA EN LA TABLA 'users' PORQUE YA ESTÁ CORRECTA.
    # Se han eliminado las líneas op.add_column y op.alter_column para 'users'.
    

def downgrade() -> None:
    # ### Comandos ajustados para el orden y robustez ###

    # El 'downgrade' solo debe deshacer lo que hizo el 'upgrade'.
    op.drop_index(op.f('ix_sunat_schedules_tax_period'), table_name='sunat_schedules')
    op.drop_index(op.f('ix_sunat_schedules_last_ruc_digit'), table_name='sunat_schedules')
    op.drop_index(op.f('ix_sunat_schedules_id'), table_name='sunat_schedules')
    op.drop_table('sunat_schedules')

    op.drop_index(op.f('ix_buen_contribuyentes_ruc'), table_name='buen_contribuyentes')
    op.drop_table('buen_contribuyentes')
    
    # Eliminar los tipos ENUM, verificando si existen.
    solvalidationstatus_enum = postgresql.ENUM('not_submitted', 'pending', 'valid', 'invalid', name='solvalidationstatus')
    solvalidationstatus_enum.drop(op.get_bind(), checkfirst=True)

    contributorgroup_enum = postgresql.ENUM('general', 'buen_contribuyente', name='contributorgroup')
    contributorgroup_enum.drop(op.get_bind(), checkfirst=True)