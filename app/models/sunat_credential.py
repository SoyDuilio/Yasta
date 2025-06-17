# app/models/sunat_credential.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA desde app/db/base.py
from app.db.base import Base

class SunatCredential(Base): # <-- Asegúrate de que hereda de Base
    __tablename__ = "sunat_credentials"

    # Los campos 'id', 'created_at', 'updated_at' se heredan automáticamente.
    
    sol_username = Column(String(255), nullable=False)
    encrypted_sol_password = Column(String(512), nullable=False) 
    owner_client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    # Relationships
    owner_client_profile = relationship("ClientProfile", back_populates="sunat_credential")
    access_audits = relationship("CredentialAccessAudit", back_populates="credential", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SunatCredential(id={self.id}, sol_username='{self.sol_username}')>"