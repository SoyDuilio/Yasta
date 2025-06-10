# app/models/user_client_access.py
import enum
from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA.
from app.db.base import Base

class RelationshipType(str, enum.Enum):
    TITULAR = "TITULAR"
    REPRESENTANTE_LEGAL = "REPRESENTANTE_LEGAL"
    CONTADOR = "CONTADOR"
    ASISTENTE = "ASISTENTE"

class UserClientAccess(Base):
    __tablename__ = "user_client_accesses"
    
    # Esta es una tabla de asociación, por lo que su clave primaria es compuesta
    # y sobreescribimos la columna 'id' de la clase Base para anularla.
    id = None
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), primary_key=True)
    
    relationship_type = Column(PGEnum(RelationshipType, name="relationshiptype"), nullable=False)
    
    __table_args__ = (PrimaryKeyConstraint('user_id', 'client_profile_id'),)

    # --- Relationships ---
    user = relationship("User", back_populates="client_accesses")
    client_profile = relationship("ClientProfile", back_populates="user_accesses")

    def __repr__(self):
        return f"<UserClientAccess(user_id={self.user_id}, client_profile_id={self.client_profile_id}, type='{self.relationship_type.value}')>"