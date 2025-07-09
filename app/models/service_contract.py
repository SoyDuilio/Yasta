# app/models/service_contract.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, Text, JSON, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class ServiceContractStatus(str, enum.Enum):
    REQUESTED_BY_CLIENT = "requested_by_client"
    PENDING_STAFF_ASSIGNMENT = "pending_staff_assignment"
    ASSIGNED_TO_STAFF = "assigned_to_staff"
    IN_PROGRESS = "in_progress"
    PENDING_CLIENT_ACTION = "pending_client_action"
    PENDING_CLIENT_PAYMENT_FOR_SERVICE = "pending_client_payment_for_service"
    PENDING_SUNAT_PAYMENT_VIA_PLATFORM = "pending_sunat_payment_via_platform"
    COMPLETED_PAID = "completed_paid"
    COMPLETED_NO_PAYMENT_REQUIRED = "completed_no_payment_required"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_STAFF = "cancelled_by_staff"
    FAILED_SUNAT_ERROR = "failed_sunat_error"
    FAILED_MISSING_INFO = "failed_missing_info"

class ServiceContract(Base):
    __tablename__ = "service_contracts"

    client_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_type_id = Column(Integer, ForeignKey("service_types.id"), nullable=False, index=True)
    assigned_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    status = Column(PGEnum(ServiceContractStatus, name="servicecontractstatus"), default=ServiceContractStatus.REQUESTED_BY_CLIENT, nullable=False, index=True)
    tax_period = Column(String(7), nullable=True, index=True)
    specific_data = Column(JSON, nullable=True)
    internal_notes = Column(Text, nullable=True)
    client_feedback_rating = Column(Integer, nullable=True)
    client_feedback_comments = Column(Text, nullable=True)
    final_service_fee = Column(DECIMAL(10, 2), nullable=True)

    requested_at = Column(DateTime(timezone=True), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client = relationship("User", foreign_keys=[client_id], back_populates="contracted_services_as_client")
    service_type = relationship("ServiceType", back_populates="service_contracts")
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id], back_populates="assigned_services_as_staff")

    monthly_declaration = relationship("MonthlyDeclaration", uselist=False, back_populates="service_contract", cascade="all, delete-orphan")
    payroll_receipt = relationship("PayrollReceipt", uselist=False, back_populates="service_contract", cascade="all, delete-orphan")
    
    fee_payments = relationship("FeePayment", back_populates="service_contract", cascade="all, delete-orphan")
    attached_documents = relationship("AttachedDocument", back_populates="service_contract", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="service_contract", cascade="all, delete-orphan")
    access_audits = relationship("CredentialAccessAudit", back_populates="service_contract")

    def __repr__(self):
        return f"<ServiceContract(id={self.id}, client_id={self.client_id}, status='{self.status.value}')>"
    
    # Al final del archivo ServiceContract, dentro de la clase, añade:
    fulfills_declaration_request = relationship("DeclarationRequest", back_populates="service_contract")