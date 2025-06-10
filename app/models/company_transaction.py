# app/models/company_transaction.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, DECIMAL, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class CompanyTransaction(Base):
    __tablename__ = "company_transactions"

    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    description = Column(Text, nullable=False)
    transaction_type = Column(PGEnum(TransactionType, name="transactiontype"), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), default="PEN", nullable=False)
    category = Column(String(100), nullable=True, index=True)
    related_fee_payment_id = Column(Integer, ForeignKey("fee_payments.id"), nullable=True, index=True)
    reference_document_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    related_fee_payment = relationship("FeePayment")