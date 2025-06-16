# Contenido de attached_document.py
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

# Contenido de client_balance_ledger.py
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

# Contenido de client_profile.py
# app/models/client_profile.py
import enum
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA.
from app.db.base import Base

class ClientType(str, enum.Enum):
    NATURAL = "NATURAL"
    JURIDICA = "JURIDICA"

class ClientProfile(Base):
    __tablename__ = "client_profiles"

    ruc = Column(String(11), unique=True, index=True, nullable=False)
    business_name = Column(String(255), index=True, nullable=False)
    client_type = Column(PGEnum(ClientType, name="clienttype"), nullable=False)

    # --- Relationships ---
    # Relación a la tabla de asociación que vincula usuarios a este perfil
    user_accesses = relationship("UserClientAccess", back_populates="client_profile", cascade="all, delete-orphan")

    # Relación a las credenciales SOL de este perfil de cliente (One-to-One)
    sunat_credential = relationship("SunatCredential", uselist=False, back_populates="owner_client_profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClientProfile(id={self.id}, ruc='{self.ruc}', business_name='{self.business_name}')>"

# Contenido de communication.py
# app/models/communication.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PLATFORM_NOTIFICATION = "platform_notification"

class CommunicationStatus(str, enum.Enum):
    PENDING_SEND = "pending_send"
    SENT = "sent"
    FAILED_TO_SEND = "failed_to_send"
    READ = "read"

class Communication(Base):
    __tablename__ = "communications"

    sender_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), index=True)

    channel = Column(PGEnum(CommunicationChannel, name="communicationchannel"), nullable=False)
    status = Column(PGEnum(CommunicationStatus, name="communicationstatus"), default=CommunicationStatus.PENDING_SEND, nullable=False)
    subject = Column(String(255))
    message_body = Column(Text, nullable=False)
    action_url = Column(String(512))
    sent_at = Column(DateTime(timezone=True))
    provider_response_id = Column(String(255))
    error_message = Column(Text)

    # Relationships
    sender_user = relationship("User", foreign_keys=[sender_user_id], back_populates="sent_communications")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id], back_populates="received_communications")
    service_contract = relationship("ServiceContract", back_populates="communications")

# Contenido de company_tax_declaration.py
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

# Contenido de company_transaction.py
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

# Contenido de credential_access_audit.py
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

# Contenido de fee_payment.py
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

# Contenido de monthly_client_summary.py
# app/models/monthly_client_summary.py
from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class MonthlyClientSummary(Base):
    __tablename__ = "monthly_client_summaries"
    
    client_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tax_period = Column(String(7), nullable=False, index=True) # YYYY-MM
    
    total_sales = Column(DECIMAL(14, 2))
    total_purchases = Column(DECIMAL(14, 2))
    total_igv_paid = Column(DECIMAL(14, 2))
    total_income_tax_paid = Column(DECIMAL(14, 2))
    total_platform_fees_paid = Column(DECIMAL(10, 2))
    
    __table_args__ = (UniqueConstraint('client_user_id', 'tax_period', name='_client_period_uc'),)
    
    # Relationships
    client_user = relationship("User")

# Contenido de monthly_declaration.py
# app/models/monthly_declaration.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, DECIMAL, Text
from sqlalchemy.orm import relationship, remote, foreign
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class DeclarationType(str, enum.Enum):
    ORIGINAL = "original"
    SUBSTITUTORY = "substitutory"
    RECTIFICATORY = "rectificatory"

class SunatPaymentStatus(str, enum.Enum):
    NOT_APPLICABLE = "not_applicable"
    PENDING_CLIENT_DIRECT_PAYMENT = "pending_client_direct_payment"
    PAID_BY_CLIENT_DIRECTLY = "paid_by_client_directly"
    PENDING_PAYMENT_VIA_PLATFORM = "pending_payment_via_platform"
    PAID_TO_SUNAT_VIA_PLATFORM = "paid_to_sunat_via_platform"
    PAYMENT_FAILED = "payment_failed"

class MonthlyDeclaration(Base):
    __tablename__ = "monthly_declarations"

    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), unique=True, nullable=False, index=True)
    original_declaration_id = Column(Integer, ForeignKey("monthly_declarations.id"), nullable=True, index=True)

    declaration_type = Column(PGEnum(DeclarationType, name="declarationtype"), default=DeclarationType.ORIGINAL, nullable=False)
    total_sales_taxable_base = Column(DECIMAL(12, 2), nullable=True)
    total_sales_igv = Column(DECIMAL(12, 2), nullable=True)
    total_exempt_sales = Column(DECIMAL(12, 2), nullable=True)
    total_non_taxable_sales = Column(DECIMAL(12, 2), nullable=True)
    total_purchases_taxable_base_for_gc = Column(DECIMAL(12, 2), nullable=True)
    total_purchases_igv_for_gc = Column(DECIMAL(12, 2), nullable=True)
    calculated_igv_payable = Column(DECIMAL(12, 2), nullable=True)
    calculated_income_tax = Column(DECIMAL(12, 2), nullable=True)
    total_sunat_debt_payable = Column(DECIMAL(12, 2), nullable=True)
    sunat_presentation_date = Column(DateTime(timezone=True), nullable=True)
    sunat_order_number = Column(String(50), nullable=True, index=True)
    sunat_payment_status = Column(PGEnum(SunatPaymentStatus, name="sunatpaymentstatus"), default=SunatPaymentStatus.NOT_APPLICABLE, nullable=False)
    sunat_payment_nps = Column(String(50), nullable=True)
    amount_paid_to_sunat_via_platform = Column(DECIMAL(12, 2), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    service_contract = relationship("ServiceContract", back_populates="monthly_declaration")
    original_declaration = relationship(
    "MonthlyDeclaration",
    # Usamos strings para definir la condición de join, evitando problemas de referencia.
    # 'foreign' le dice a SQLAlchemy que 'MonthlyDeclaration.original_declaration_id' es una FK.
    # 'remote' le dice que 'MonthlyDeclaration.id' está en la tabla "remota" (la original).
    primaryjoin="foreign(MonthlyDeclaration.original_declaration_id) == remote(MonthlyDeclaration.id)",
    backref="rectifications",
    # Todavía es buena idea especificar el lado remoto explícitamente.
    remote_side="MonthlyDeclaration.id"
    )

    def __repr__(self):
        return f"<MonthlyDeclaration(id={self.id}, type='{self.declaration_type.value}')>"

# Contenido de payroll_receipt.py
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

# Contenido de service_contract.py
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

# Contenido de service_tariff.py
# app/models/service_tariff.py
from sqlalchemy import (
    Column, String, Date, Text, Integer, ForeignKey, Boolean, DECIMAL
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ServiceTariff(Base):
    __tablename__ = "service_tariffs"

    service_name = Column(String(255), nullable=False, index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="PEN", nullable=False)

    start_date = Column(Date, nullable=False, default=func.current_date())
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    observations = Column(Text, nullable=True)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    last_updated_by_user = relationship("User", foreign_keys=[last_updated_by_user_id])

    def __repr__(self):
        return f"<ServiceTariff(name='{self.service_name}', price={self.price})>"

# Contenido de service_type.py
# app/models/service_type.py
from sqlalchemy import Column, String, Text, Boolean, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class ServiceType(Base):
    __tablename__ = "service_types"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    base_fee = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, default=True)
    requires_period = Column(Boolean, default=False)
    specific_data_schema = Column(JSON, nullable=True)

    # Relationships
    service_contracts = relationship("ServiceContract", back_populates="service_type")

    def __repr__(self):
        return f"<ServiceType(id={self.id}, name='{self.name}')>"

# Contenido de sunat_credential.py
# app/models/sunat_credential.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA.
from app.db.base import Base

class SunatCredential(Base):
    __tablename__ = "sunat_credentials"

    sol_username = Column(String(255), nullable=False)
    # NOTA: La encriptación debe manejarse en la capa de servicio/CRUD, no aquí.
    encrypted_sol_password = Column(String(512), nullable=False) 
    
    # Clave foránea al perfil del cliente. Es una relación 1 a 1, por lo que debe ser única.
    owner_client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    # --- Relationships ---
    owner_client_profile = relationship("ClientProfile", back_populates="sunat_credential")
    access_audits = relationship("CredentialAccessAudit", back_populates="credential", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SunatCredential(id={self.id}, sol_username='{self.sol_username}')>"

# Contenido de sunat_due_date.py
# app/models/sunat_due_date.py
from sqlalchemy import Column, String, Date, Integer
from app.db.base import Base

class SunatDueDate(Base):
    __tablename__ = "sunat_due_dates"
    
    tax_period = Column(String(7), nullable=False, index=True) # Formato YYYY-MM
    ruc_last_digit = Column(Integer, nullable=False, index=True)
    due_date = Column(Date, nullable=False)

# Contenido de sunat_schedule.py
# app/models/sunat_schedule.py
import enum
from sqlalchemy import (
    Column, String, Date, Text, Integer, ForeignKey, UniqueConstraint, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class ContributorGroup(str, enum.Enum):
    GENERAL = "general"
    BUEN_CONTRIBUYENTE = "buen_contribuyente"

class SunatSchedule(Base):
    __tablename__ = "sunat_schedules"

    tax_period = Column(String(7), nullable=False, index=True) # Ej: "2024-06"
    last_ruc_digit = Column(String(1), nullable=False, index=True) # Ej: "0", "1", ...
    due_date = Column(Date, nullable=False) # Fecha de vencimiento
    
    contributor_group = Column(
        PGEnum(ContributorGroup, name="contributorgroup", create_type=False), 
        default=ContributorGroup.GENERAL, 
        nullable=False,
        server_default=ContributorGroup.GENERAL.value
    )

    publication_date = Column(Date, nullable=True)
    legal_base_document = Column(String(255), nullable=True)
    observations = Column(Text, nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    last_updated_by_user = relationship("User", foreign_keys=[last_updated_by_user_id])

    __table_args__ = (UniqueConstraint(
        'tax_period', 
        'last_ruc_digit', 
        'contributor_group', 
        name='_period_ruc_digit_group_uc'
    ),)

    def __repr__(self):
        return f"<SunatSchedule(period='{self.tax_period}', digit='{self.last_ruc_digit}', group='{self.contributor_group.value}')>"

# Contenido de user-old.py
# app/models/user.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base

# Definir el enum de PostgreSQL de forma explícita - ESTO ESTÁ PERFECTO, NO SE TOCA
user_role_enum = PGEnum(
    'authenticated',
    'client_freemium', 
    'client_paid',
    'staff_collaborator',
    'staff_manager',
    'staff_ceo',
    'admin',
    name='userrole',
    create_type=False
)

# El Enum de Python - ESTO ESTÁ PERFECTO, NO SE TOCA
class UserRole(enum.Enum):
    AUTHENTICATED = "authenticated"
    CLIENT_FREEMIUM = "client_freemium"
    CLIENT_PAID = "client_paid"
    STAFF_COLLABORATOR = "staff_collaborator"
    STAFF_MANAGER = "staff_manager"
    STAFF_CEO = "staff_ceo"
    ADMIN = "admin"

class User(Base):
    # --- Campos Comunes (Sin cambios) ---
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True, index=True)
    role = Column(
    PGEnum(
        UserRole,
        name="userrole",
        create_type=False,
        # ESTA ES LA LÍNEA MÁGICA Y LA SOLUCIÓN DEFINITIVA
        values_callable=lambda x: [e.value for e in x]
    ),
    nullable=False,
    server_default=text("'authenticated'::userrole"),
    default=UserRole.AUTHENTICATED
    )
    is_active = Column(Boolean(), default=True)
    last_platform_login_at = Column(DateTime(timezone=True), nullable=True)
    profile_image_url = Column(String(512), nullable=True)
    contact_name = Column(String(255), nullable=True)

    # --- Campos de Cliente (Comentados para ser eliminados por Alembic) ---
    # client_ruc = Column(String(11), unique=True, index=True, nullable=True)
    # business_name = Column(String(255), index=True, nullable=True)
    # terms_accepted_at = Column(DateTime(timezone=True), nullable=True)

    # --- Campos de Staff (Sin cambios) ---
    staff_dni = Column(String(15), unique=True, index=True, nullable=True)
    staff_full_name = Column(String(255), nullable=True)
    staff_ruc_personal = Column(String(11), nullable=True, index=True)

    # --- Relationships ---

    # === NUEVA RELACIÓN AÑADIDA ===
    # Esta es la relación que conecta al Usuario con sus perfiles de cliente
    # a través de la nueva tabla de asociación UserClientAccess.
    client_accesses = relationship("UserClientAccess", back_populates="user", cascade="all, delete-orphan")

    # === RELACIÓN A ELIMINAR (Comentada) ===
    # La relación con SunatCredential se moverá al nuevo modelo ClientProfile.
    # sunat_credentials = relationship(
    #     "SunatCredential",
    #     back_populates="owner_user",
    #     cascade="all, delete-orphan"
    # )

    # === OTRAS RELACIONES (Se mantienen sin cambios) ===
    contracted_services_as_client = relationship(
        "ServiceContract",
        foreign_keys="[ServiceContract.client_id]",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    assigned_services_as_staff = relationship(
        "ServiceContract",
        foreign_keys="[ServiceContract.assigned_staff_id]",
        back_populates="assigned_staff"
    )

    sent_communications = relationship(
        "Communication",
        foreign_keys="[Communication.sender_user_id]",
        back_populates="sender_user",
        cascade="all, delete-orphan"
    )

    received_communications = relationship(
        "Communication",
        foreign_keys="[Communication.recipient_user_id]",
        back_populates="recipient_user",
        cascade="all, delete-orphan"
    )

    initiated_fee_payments = relationship(
        "FeePayment",
        foreign_keys="[FeePayment.paying_user_id]",
        back_populates="paying_user",
        cascade="all, delete-orphan"
    )

    initiated_audits = relationship(
        "CredentialAccessAudit",
        foreign_keys="[CredentialAccessAudit.accessing_user_id]",
        back_populates="accessing_user",
        cascade="all, delete-orphan"
    )

    uploaded_yape_plin_transactions = relationship(
        "YapePlinTransaction",
        foreign_keys="[YapePlinTransaction.uploader_user_id]",
        back_populates="uploader_user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

# Contenido de user.py
# app/models/user.py
from sqlalchemy import func # Necesitamos 'func'
from sqlalchemy.sql import func # A veces es redundante, pero no hace daño
import enum
from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from enum import Enum # Usamos el Enum nativo de Python para los valores
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA desde su nueva ubicación.
from app.db.base import Base

class UserRole(enum.Enum):
    AUTHENTICATED = "authenticated"
    CLIENT_FREEMIUM = "client_freemium"
    CLIENT_PAID = "client_paid"
    STAFF_COLLABORATOR = "staff_collaborator"
    STAFF_MANAGER = "staff_manager"
    STAFF_CEO = "staff_ceo"
    ADMIN = "admin"

class SOLValidationStatus(str, Enum):
    NOT_SUBMITTED = "not_submitted"
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"

class User(Base):
    __tablename__ = "users"

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # La definición de 'role' no se toca, permanece como la tienes.
    role = Column(
        PGEnum(UserRole, name="userrole", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=text("'authenticated'::userrole"),
        default=UserRole.AUTHENTICATED
    )

    # ***** INICIO DE LA CORRECCIÓN *****
    # Aplicamos exactamente el mismo patrón que usaste para 'role'.
    sol_validation_status = Column(
        PGEnum(SOLValidationStatus, name="solvalidationstatus", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        # 'NOT_SUBMITTED' es el valor por defecto del Enum
        server_default=text("'not_submitted'::solvalidationstatus"), 
        default=SOLValidationStatus.NOT_SUBMITTED
    )
    # ***** FIN DE LA CORRECCIÓN *****
    is_active = Column(Boolean(), default=True)
    last_platform_login_at = Column(DateTime(timezone=True), nullable=True)
    contact_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    profile_image_url = Column(String(512), nullable=True)

    # Campos específicos para el personal
    staff_dni = Column(String(15), unique=True, index=True, nullable=True)
    staff_full_name = Column(String(255), nullable=True)
    staff_ruc_personal = Column(String(11), index=True, nullable=True)

    # --- Relationships ---
    # Todas las relaciones ahora usan strings para evitar importaciones circulares.

    # Relación a la tabla de asociación que da acceso a perfiles de cliente
    client_accesses = relationship("UserClientAccess", back_populates="user", cascade="all, delete-orphan")

    # Servicios que este usuario ha contratado como cliente
    contracted_services_as_client = relationship("ServiceContract", foreign_keys="[ServiceContract.client_id]", back_populates="client")

    # Servicios que este usuario tiene asignados como staff
    assigned_services_as_staff = relationship("ServiceContract", foreign_keys="[ServiceContract.assigned_staff_id]", back_populates="assigned_staff")

    # Comunicaciones enviadas y recibidas
    sent_communications = relationship("Communication", foreign_keys="[Communication.sender_user_id]", back_populates="sender_user")
    received_communications = relationship("Communication", foreign_keys="[Communication.recipient_user_id]", back_populates="recipient_user")

    # Pagos de honorarios iniciados por este usuario
    initiated_fee_payments = relationship("FeePayment", foreign_keys="[FeePayment.paying_user_id]", back_populates="paying_user")

    # Auditorías de acceso a credenciales iniciadas por este usuario
    initiated_audits = relationship("CredentialAccessAudit", back_populates="accessing_user")

    # Capturas de Yape/Plin subidas por este usuario
    uploaded_yape_plin_transactions = relationship("YapePlinTransaction", back_populates="uploader_user")
    
    # Documentos adjuntos subidos por este usuario
    uploaded_documents = relationship("AttachedDocument", back_populates="uploaded_by_user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"

# Contenido de user_client_access.py
# app/models/user_client_access.py
import enum
from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship

# Importamos la Base ÚNICA.
from app.db.base import Base

class RelationshipType(str, enum.Enum):
    TITULAR = "TITULAR"
    REPRESENTANTE_LEGAL = "REPRESENTANTE_LEGAL"
    CONTADOR = "CONTADOR"
    ASISTENTE = "ASISTENTE"

class UserClientAccess(Base):
    __tablename__ = "user_client_accesses"
    
    # Esta es una tabla de asociación, por lo que su clave primaria es compuesta
    # y sobreescribimos la columna 'id' de la clase Base para anularla.
    id = None
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), primary_key=True)
    
    relationship_type = Column(PGEnum(RelationshipType, name="relationshiptype"), nullable=False)
    
    __table_args__ = (PrimaryKeyConstraint('user_id', 'client_profile_id'),)

    # --- Relationships ---
    user = relationship("User", back_populates="client_accesses")
    client_profile = relationship("ClientProfile", back_populates="user_accesses")

    def __repr__(self):
        return f"<UserClientAccess(user_id={self.user_id}, client_profile_id={self.client_profile_id}, type='{self.relationship_type.value}')>"

# Contenido de yape_plin_transaction.py
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

# Contenido de __init__.py
# app/models/__init__.py

# El propósito de este archivo es importar todos los modelos en un solo lugar.
# De esta manera, Alembic y SQLAlchemy pueden descubrir todas las tablas
# y sus relaciones simplemente importando 'from app.models import *'.
# El orden aquí es crucial para evitar errores de dependencia.

# 1. Modelos Base o de los que dependen muchos otros.
from .user import User, UserRole
from .client_profile import ClientProfile, ClientType

# 2. Tabla de Asociación que une a los de arriba.
from .user_client_access import UserClientAccess, RelationshipType

# 3. Modelos que dependen de User o ClientProfile.
from .sunat_credential import SunatCredential

# 4. Modelos del core de negocio (Servicios).
from .service_type import ServiceType
from .service_contract import ServiceContract, ServiceContractStatus

# 5. Modelos específicos de cada tipo de servicio.
from .monthly_declaration import MonthlyDeclaration, DeclarationType, SunatPaymentStatus
from .payroll_receipt import PayrollReceipt, PaymentMethodRxh

# 6. Modelos de soporte (Pagos, Documentos, Comunicaciones).
from .fee_payment import FeePayment, PaymentMethodPlatform, FeePaymentStatus
from .yape_plin_transaction import YapePlinTransaction, DigitalWalletProvider, ExtractionStatus
from .attached_document import AttachedDocument, DocumentType
from .communication import Communication, CommunicationChannel, CommunicationStatus

# 7. Modelos de Auditoría y Reportes.
from .credential_access_audit import CredentialAccessAudit
from .monthly_client_summary import MonthlyClientSummary

# 8. Modelos de Contabilidad Interna de la Empresa.
from .company_transaction import CompanyTransaction, TransactionType
from .company_tax_declaration import CompanyTaxDeclaration, TaxDeclarationTypeCompany

# (Aquí añadiremos los nuevos modelos de Cronograma, Tarifas y Saldos cuando lleguemos a ese paso)

