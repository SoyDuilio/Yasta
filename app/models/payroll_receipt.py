# app/models/payroll_receipt.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, Date, DECIMAL, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class PaymentMethodRxh(str, enum.Enum):
    DEPOSITO_EN_CUENTA = "001"
    TRANSFERENCIA_FONDOS = "003"
    EFECTIVO = "008"
    OTROS = "009"

class PayrollReceipt(Base):
    __tablename__ = "payroll_receipts"

    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), unique=True, nullable=False, index=True)
    rxh_series_number = Column(String(10), nullable=False)
    rxh_correlative_number = Column(String(20), nullable=False, index=True)
    rxh_issue_date = Column(Date, nullable=False, index=True)
    acquirer_doc_type = Column(String(10), nullable=False)
    acquirer_doc_number = Column(String(20), nullable=False, index=True)
    acquirer_name_or_business_name = Column(String(255), nullable=False)
    service_description = Column(Text, nullable=False)
    gross_amount = Column(DECIMAL(12, 2), nullable=False)
    has_income_tax_withholding = Column(Boolean, default=False)
    income_tax_withholding_amount = Column(DECIMAL(12, 2), nullable=True, default=0.00)
    net_amount_payable = Column(DECIMAL(12, 2), nullable=False)
    payment_date = Column(Date, nullable=True)
    payment_method = Column(PGEnum(PaymentMethodRxh, name="paymentmethodrxh"), nullable=True)
    observation = Column(Text, nullable=True)

    # Relationships
    service_contract = relationship("ServiceContract", back_populates="payroll_receipt")

    def __repr__(self):
        return f"<PayrollReceipt(id={self.id}, number='{self.rxh_correlative_number}')>"