# app/models/yape_plin_transaction.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, DECIMAL, Text, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class DigitalWalletProvider(str, enum.Enum):
    YAPE = "yape"
    PLIN = "plin"
    OTHER = "other"

class ExtractionStatus(str, enum.Enum):
    PENDING = "pending"
    OCR_COMPLETED = "ocr_completed"
    LLM_EXTRACTION_COMPLETED = "llm_extraction_completed"
    OCR_FAILED = "ocr_failed"
    LLM_FAILED = "llm_failed"
    MANUAL_VERIFICATION_REQUIRED = "manual_verification_required"
    VERIFIED_MATCHED = "verified_matched"
    VERIFIED_UNMATCHED = "verified_unmatched"

class YapePlinTransaction(Base):
    __tablename__ = "yape_plin_transactions"

    uploader_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fee_payment_id = Column(Integer, ForeignKey("fee_payments.id"), nullable=True, index=True)
    
    original_image_filename = Column(String(255), nullable=False)
    image_storage_path = Column(String(512), nullable=False)
    provider = Column(PGEnum(DigitalWalletProvider, name="digitalwalletprovider"), nullable=True)
    
    extracted_amount = Column(DECIMAL(10, 2), nullable=True)
    extracted_currency = Column(String(3), nullable=True)
    extracted_recipient_name = Column(String(255), nullable=True)
    extracted_sender_name = Column(String(255), nullable=True)
    extracted_transaction_date = Column(Date, nullable=True)
    extracted_transaction_time = Column(Time, nullable=True)
    extracted_security_code = Column(String(10), nullable=True)
    extracted_phone_suffix = Column(String(10), nullable=True)
    extracted_operation_number = Column(String(50), nullable=True, index=True)

    raw_ocr_text = Column(Text, nullable=True)
    llm_confidence_score = Column(DECIMAL(3,2), nullable=True)
    extraction_status = Column(PGEnum(ExtractionStatus, name="extractionstatus"), default=ExtractionStatus.PENDING, nullable=False)
    processing_notes = Column(Text, nullable=True)

    # Relationships
    uploader_user = relationship("User", back_populates="uploaded_yape_plin_transactions")
    fee_payment = relationship("FeePayment")

    def __repr__(self):
        return f"<YapePlinTransaction(id={self.id}, status='{self.extraction_status.value}')>"