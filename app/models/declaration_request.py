# app/models/declaration_request.py

import enum
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from app.db.base import Base
from app.models.monthly_declaration import DeclarationType

# --- ¡CAMBIO IMPORTANTE AQUÍ! ---
class DeclarationRequestStatus(str, enum.Enum):
    PENDING_VALIDATION = "pending_validation" #<-- ¡NUEVO ESTADO INICIAL!
    PENDING_ASSIGNMENT = "pending_assignment"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    VALIDATED = "validated" #<-- Nuevo estado para solicitudes ya procesadas

class DeclarationRequest(Base):
    __tablename__ = "declaration_requests"

    # --- Foreign Keys ---
    yape_plin_transaction_id = Column(Integer, ForeignKey("yape_plin_transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True, unique=True)

    # --- Datos de la Solicitud ---
    tax_period = Column(String(7), nullable=False, index=True)
    declaration_type = Column(PGEnum(DeclarationType, name="declarationtype", create_type=False), nullable=False)
    
    # --- ¡CAMBIO IMPORTANTE AQUÍ! ---
    # El estado por defecto ahora es PENDING_VALIDATION. Todas las solicitudes nuevas empezarán aquí.
    status = Column(PGEnum(DeclarationRequestStatus, name="declarationrequeststatus", create_type=False), nullable=False, default=DeclarationRequestStatus.PENDING_VALIDATION)
    
    # --- Relationships ---
    yape_plin_transaction = relationship("YapePlinTransaction", back_populates="declaration_requests")
    client_profile = relationship("ClientProfile", back_populates="declaration_requests")
    service_contract = relationship("ServiceContract", back_populates="fulfills_declaration_request")

    def __repr__(self):
        return f"<DeclarationRequest(id={self.id}, client_id={self.client_profile_id}, period='{self.tax_period}')>"