# app/models/company_tax_declaration.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, DECIMAL, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class TaxDeclarationTypeCompany(str, enum.Enum):
    MONTHLY_IGV_RENTA = "monthly_igv_renta"
    ANNUAL_RENTA = "annual_renta"
    PLAME = "plame"
    OTHER = "other"

class CompanyTaxDeclaration(Base):
    __tablename__ = "company_tax_declarations"

    tax_period = Column(String(7), nullable=False, index=True)
    declaration_type = Column(PGEnum(TaxDeclarationTypeCompany, name="taxdeclarationtypecompany"), nullable=False, index=True)
    presentation_date = Column(DateTime(timezone=True), nullable=True)
    sunat_order_number = Column(String(50), nullable=True, index=True)
    total_tax_payable = Column(DECIMAL(12, 2), nullable=True)
    total_tax_paid = Column(DECIMAL(12, 2), nullable=True)
    payment_date = Column(Date, nullable=True)
    payment_reference_nps = Column(String(50), nullable=True)
    constancy_document_id = Column(Integer, ForeignKey("attached_documents.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    constancy_document = relationship("AttachedDocument")