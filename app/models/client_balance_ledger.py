# app/models/client_balance_ledger.py
import enum
from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLAlchemyEnum, DECIMAL, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class LedgerTransactionType(str, enum.Enum):
    CREDIT = "credit"  # Recarga de saldo
    DEBIT = "debit"    # Consumo de servicio

class ClientBalanceLedger(Base):
    __tablename__ = "client_balance_ledgers"
    
    client_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = Column(SQLAlchemyEnum(LedgerTransactionType), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text, nullable=False) # Ej: "Recarga Yape", "Consumo Declaración Ene-2025"
    
    # Opcional: Para vincular la transacción a un pago o contrato específico
    related_fee_payment_id = Column(Integer, ForeignKey("fee_payments.id"), nullable=True)
    related_service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True)

    client_user = relationship("User", back_populates="balance_transactions")
    fee_payment = relationship("FeePayment")
    service_contract = relationship("ServiceContract")