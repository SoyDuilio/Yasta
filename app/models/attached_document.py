# app/models/attached_document.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class DocumentType(str, enum.Enum):
    SUNAT_DECLARATION_CONSTANCY = "sunat_declaration_constancy"
    SUNAT_PAYMENT_VOUCHER = "sunat_payment_voucher"
    RXH_PDF = "rxh_pdf"
    YAPE_PLIN_SCREENSHOT = "yape_plin_screenshot"
    CONSOLIDATED_REPORT_PDF = "consolidated_report_pdf"
    CLIENT_UPLOADED_DOCUMENT = "client_uploaded_document"
    STAFF_UPLOADED_DOCUMENT = "staff_uploaded_document"
    OTHER = "other"

class AttachedDocument(Base):
    __tablename__ = "attached_documents"
    
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    storage_path = Column(String(512), nullable=False)
    document_type = Column(PGEnum(DocumentType, name="documenttype"), default=DocumentType.OTHER, nullable=False)
    description = Column(Text, nullable=True)
    is_visible_to_client = Column(Boolean, default=True)

    # Relationships
    service_contract = relationship("ServiceContract", back_populates="attached_documents")
    uploaded_by_user = relationship("User", back_populates="uploaded_documents")

    def __repr__(self):
        return f"<AttachedDocument(id={self.id}, file_name='{self.file_name}')>"