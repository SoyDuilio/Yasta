# app/models/client_balance_ledger.py
import enum
from sqlalchemy import (
    Column, String, Text, Integer, ForeignKey, DECIMAL, DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class LedgerTransactionType(str, enum.Enum):
    CREDIT_PAYMENT = "credit_payment"
    DEBIT_SERVICE = "debit_service"
    CREDIT_REFUND = "credit_refund"
    DEBIT_FEE = "debit_fee"
    ADJUSTMENT = "adjustment"

class ClientBalanceLedger(Base):
    __tablename__ = "client_balance_ledgers"

    client_profile_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=False, index=True)
    transaction_type = Column(PGEnum(LedgerTransactionType, name="ledgertransactiontype", create_type=False), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text, nullable=False)
    
    payer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payer_name_external = Column(String(255), nullable=True)
    
    transaction_datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    related_service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True)
    related_fee_payment_id = Column(Integer, ForeignKey("fee_payments.id"), nullable=True, index=True)
    processed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    client_profile = relationship("ClientProfile")
    payer_user = relationship("User", foreign_keys=[payer_user_id])
    processed_by_user = relationship("User", foreign_keys=[processed_by_user_id])
    service_contract = relationship("ServiceContract")
    fee_payment = relationship("FeePayment")

    def __repr__(self):
        return f"<ClientBalanceLedger(client_id={self.client_profile_id}, type='{self.transaction_type.value}', amount={self.amount})>"