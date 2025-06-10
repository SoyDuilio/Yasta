# app/models/fee_payment.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, DECIMAL, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class PaymentMethodPlatform(str, enum.Enum):
    YAPE = "yape"
    PLIN = "plin"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    OTHER = "other"

class FeePaymentStatus(str, enum.Enum):
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED_PAID = "verified_paid"
    FAILED_VERIFICATION = "failed_verification"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class FeePayment(Base):
    __tablename__ = "fee_payments"

    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True)
    paying_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    verified_by_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    amount_paid = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="PEN", nullable=False)
    payment_method_used = Column(PGEnum(PaymentMethodPlatform, name="paymentmethodplatform"), nullable=False)
    payment_reference = Column(String(255), nullable=True, index=True)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(PGEnum(FeePaymentStatus, name="feepaymentstatus"), default=FeePaymentStatus.PENDING_VERIFICATION, nullable=False)
    verification_notes = Column(Text, nullable=True)
    includes_sunat_tax_amount = Column(DECIMAL(10, 2), nullable=True, default=0.00)

    # Relationships
    service_contract = relationship("ServiceContract", back_populates="fee_payments")
    paying_user = relationship("User", foreign_keys=[paying_user_id], back_populates="initiated_fee_payments")
    verified_by_staff = relationship("User", foreign_keys=[verified_by_staff_id])

    def __repr__(self):
        return f"<FeePayment(id={self.id}, amount_paid={self.amount_paid})>"