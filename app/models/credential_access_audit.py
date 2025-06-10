# app/models/credential_access_audit.py
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class CredentialAccessAudit(Base):
    __tablename__ = "credential_access_audits"
    
    credential_id = Column(Integer, ForeignKey("sunat_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    accessing_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True)
    
    action_performed = Column(String(255), nullable=False)
    access_successful = Column(Boolean)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    reason_for_access = Column(Text)
    failure_reason_if_any = Column(Text)

    # Relationships
    credential = relationship("SunatCredential", back_populates="access_audits")
    accessing_user = relationship("User", foreign_keys=[accessing_user_id], back_populates="initiated_audits")
    service_contract = relationship("ServiceContract", back_populates="access_audits")