# app/models/sunat_schedule.py
import enum
from sqlalchemy import (
    Column, String, Date, Text, Integer, ForeignKey, UniqueConstraint, text # <-- Importamos text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class ContributorGroup(str, enum.Enum):
    GENERAL = "general"
    BUEN_CONTRIBUYENTE = "buen_contribuyente"

# Definimos el tipo ENUM de PostgreSQL una sola vez, para reutilizarlo.
# create_type=False le dice a SQLAlchemy que no intente crear el tipo por sí mismo,
# ya que Alembic lo gestionará de forma más explícita.
contributor_group_enum = PGEnum(
    ContributorGroup, 
    name="contributorgroup", 
    create_type=False,
    values_callable=lambda obj: [e.value for e in obj] # Buena práctica para compatibilidad
)


class SunatSchedule(Base):
    __tablename__ = "sunat_schedules"

    tax_period = Column(String(7), nullable=False, index=True) # Ej: "2024-06"
    last_ruc_digit = Column(String(1), nullable=False, index=True) # Ej: "0", "1", ...
    due_date = Column(Date, nullable=False) # Fecha de vencimiento
    
    # --- LA CORRECCIÓN ESTÁ AQUÍ ---
    contributor_group = Column(
        contributor_group_enum, # Usamos la instancia del ENUM definida arriba
        nullable=False,
        # Usamos text() para hacer un CAST explícito a nivel de base de datos.
        # Esto genera el SQL correcto: DEFAULT 'general'::contributorgroup
        server_default=text("'general'::contributorgroup"),
        default=ContributorGroup.GENERAL
    )

    publication_date = Column(Date, nullable=True)
    legal_base_document = Column(String(255), nullable=True)
    observations = Column(Text, nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    last_updated_by_user = relationship("User", foreign_keys=[last_updated_by_user_id])

    __table_args__ = (UniqueConstraint(
        'tax_period', 
        'last_ruc_digit', 
        'contributor_group', 
        name='_period_ruc_digit_group_uc'
    ),)

    def __repr__(self):
        return f"<SunatSchedule(period='{self.tax_period}', digit='{self.last_ruc_digit}', group='{self.contributor_group.value}')>"