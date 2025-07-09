# app/models/client_profile.py
import enum
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA.
from app.db.base import Base

class ClientType(str, enum.Enum):
    NATURAL = "NATURAL"
    JURIDICA = "JURIDICA"

class ClientProfile(Base):
    __tablename__ = "client_profiles"

    ruc = Column(String(11), unique=True, index=True, nullable=False)
    business_name = Column(String(255), index=True, nullable=False)
    client_type = Column(PGEnum(ClientType, name="clienttype"), nullable=False)

    # --- Relationships ---
    # Relación a la tabla de asociación que vincula usuarios a este perfil
    user_accesses = relationship("UserClientAccess", back_populates="client_profile", cascade="all, delete-orphan")

    # Relación a las credenciales SOL de este perfil de cliente (One-to-One)
    sunat_credential = relationship("SunatCredential", uselist=False, back_populates="owner_client_profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClientProfile(id={self.id}, ruc='{self.ruc}', business_name='{self.business_name}')>"
    
    # Al final del archivo ClientProfile, dentro de la clase, añade:
    declaration_requests = relationship("DeclarationRequest", back_populates="client_profile", cascade="all, delete-orphan")