# app/models/declaration_request.py

import enum
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# Importamos la Base y Enums existentes para reutilizarlos
from app.db.base import Base
from app.models.monthly_declaration import DeclarationType # Reutilizamos el Enum que ya tienes

class DeclarationRequestStatus(str, enum.Enum):
    PENDING_ASSIGNMENT = "pending_assignment"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class DeclarationRequest(Base):
    __tablename__ = "declaration_requests"

    # --- Foreign Keys ---
    # Enlace al pago que agrupa esta y otras solicitudes
    yape_plin_transaction_id = Column(Integer, ForeignKey("yape_plin_transactions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Enlace al perfil del cliente (RUC) para el que es esta solicitud
    client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    # Enlace al contrato de servicio que eventualmente cumplirá esta solicitud
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True, unique=True)

    # --- Datos de la Solicitud ---
    tax_period = Column(String(7), nullable=False, index=True) # Formato YYYY-MM
    declaration_type = Column(PGEnum(DeclarationType, name="declarationtype", create_type=False), nullable=False)
    status = Column(PGEnum(DeclarationRequestStatus, name="declarationrequeststatus", create_type=False), nullable=False, default=DeclarationRequestStatus.PENDING_ASSIGNMENT)
    
    # --- Relationships ---
    yape_plin_transaction = relationship("YapePlinTransaction", back_populates="declaration_requests")
    client_profile = relationship("ClientProfile", back_populates="declaration_requests")
    service_contract = relationship("ServiceContract", back_populates="fulfills_declaration_request")

    def __repr__(self):
        return f"<DeclarationRequest(id={self.id}, client_id={self.client_profile_id}, period='{self.tax_period}')>"