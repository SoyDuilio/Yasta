# app/models/sunat_credential.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA.
from app.db.base import Base

class SunatCredential(Base):
    __tablename__ = "sunat_credentials"

    sol_username = Column(String(255), nullable=False)
    # NOTA: La encriptación debe manejarse en la capa de servicio/CRUD, no aquí.
    encrypted_sol_password = Column(String(512), nullable=False) 
    
    # Clave foránea al perfil del cliente. Es una relación 1 a 1, por lo que debe ser única.
    owner_client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    # --- Relationships ---
    owner_client_profile = relationship("ClientProfile", back_populates="sunat_credential")
    access_audits = relationship("CredentialAccessAudit", back_populates="credential", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SunatCredential(id={self.id}, sol_username='{self.sol_username}')>"