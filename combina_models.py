# Contenido de attached_document.py
# app/models/attached_document.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, Text, Boolean
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base
# from app.models.service_contract import ServiceContract
# from app.models.user import User

class DocumentType(str, enum.Enum):
    SUNAT_DECLARATION_CONSTANCY = "sunat_declaration_constancy" # Constancia de Declaración
    SUNAT_PAYMENT_VOUCHER = "sunat_payment_voucher"       # Constancia de Pago a SUNAT (NPS)
    RXH_PDF = "rxh_pdf"                                   # PDF del Recibo por Honorarios
    YAPE_PLIN_SCREENSHOT = "yape_plin_screenshot"         # Captura de Yape/Plin (referencia a YapePlinTransaction)
    CONSOLIDATED_REPORT_PDF = "consolidated_report_pdf"   # Reporte consolidado generado por nosotros
    CLIENT_UPLOADED_DOCUMENT = "client_uploaded_document" # Documento subido por el cliente (genérico)
    STAFF_UPLOADED_DOCUMENT = "staff_uploaded_document"   # Documento subido por staff (genérico)
    OTHER = "other"

class AttachedDocument(Base):
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True) # Opcional, podría ser un doc general del cliente
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True) # Quién subió el documento

    file_name = Column(String(255), nullable=False) # Nombre original del archivo
    file_mime_type = Column(String(100), nullable=True) # ej: application/pdf, image/jpeg
    file_size_bytes = Column(Integer, nullable=True)
    storage_path = Column(String(512), nullable=False) # ej: S3 key o path local
    document_type = Column(SQLAlchemyEnum(DocumentType), default=DocumentType.OTHER, nullable=False)
    description = Column(Text, nullable=True) # Descripción opcional
    is_visible_to_client = Column(Boolean, default=True) # Para controlar visibilidad

    # Relationships
    service_contract = relationship("ServiceContract", back_populates="attached_documents")
    uploaded_by_user = relationship("User") # No necesita back_populates si User no lista documentos directamente

    def __repr__(self):
        return f"<AttachedDocument(id={self.id}, file_name='{self.file_name}', type='{self.document_type.value}')>"

# Contenido de client_profile.py
# app/models/client_profile.py
import enum
from sqlalchemy import Column, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ClientType(str, enum.Enum):
    NATURAL = "NATURAL"
    JURIDICA = "JURIDICA"

class ClientProfile(Base):
    __tablename__ = "client_profiles"
    
    ruc = Column(String(11), unique=True, index=True, nullable=False)
    business_name = Column(String(255), index=True, nullable=False)
    client_type = Column(SQLAlchemyEnum(ClientType, name="clienttype"), nullable=False)

    user_accesses = relationship("UserClientAccess", back_populates="client_profile", cascade="all, delete-orphan")
    sunat_credentials = relationship("SunatCredential", back_populates="owner_client_profile", cascade="all, delete-orphan")

# Contenido de communication.py
# app/models/communication.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

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

    channel = Column(SQLAlchemyEnum(CommunicationChannel), nullable=False)
    status = Column(SQLAlchemyEnum(CommunicationStatus), default=CommunicationStatus.PENDING_SEND, nullable=False)
    subject = Column(String(255))
    message_body = Column(Text, nullable=False)
    action_url = Column(String(512))
    sent_at = Column(DateTime(timezone=True))
    provider_response_id = Column(String(255))
    error_message = Column(Text)

    sender_user = relationship("User", foreign_keys=[sender_user_id], back_populates="sent_communications")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id], back_populates="received_communications")
    service_contract = relationship("ServiceContract", back_populates="communications")

# Contenido de company_tax_declaration.py
# app/models/company_tax_declaration.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, DECIMAL, Text, Date
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base
# from app.models.attached_document import AttachedDocument

class TaxDeclarationTypeCompany(str, enum.Enum):
    MONTHLY_IGV_RENTA = "monthly_igv_renta" # PDT 621
    ANNUAL_RENTA = "annual_renta"         # Renta Anual
    PLAME = "plame"                       # Planilla Electrónica
    # Otros que apliquen a tu empresa
    OTHER = "other"

class CompanyTaxDeclaration(Base):
    tax_period = Column(String(7), nullable=False, index=True) # YYYY-MM para mensuales, YYYY para anuales
    declaration_type = Column(SQLAlchemyEnum(TaxDeclarationTypeCompany), nullable=False, index=True)
    presentation_date = Column(DateTime(timezone=True), nullable=True) # Fecha de presentación
    sunat_order_number = Column(String(50), nullable=True, index=True) # Nro de Orden
    total_tax_payable = Column(DECIMAL(12, 2), nullable=True) # Impuesto resultante
    total_tax_paid = Column(DECIMAL(12, 2), nullable=True)    # Impuesto efectivamente pagado
    payment_date = Column(Date, nullable=True)              # Fecha de pago del impuesto
    payment_reference_nps = Column(String(50), nullable=True) # NPS del pago

    # ID del documento adjunto (constancia)
    constancy_document_id = Column(Integer, ForeignKey("attached_documents.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    constancy_document = relationship("AttachedDocument") # Asumiendo que AttachedDocument puede ser genérico

    def __repr__(self):
        return f"<CompanyTaxDeclaration(id={self.id}, period='{self.tax_period}', type='{self.declaration_type.value}')>"

# Contenido de company_transaction.py
# app/models/company_transaction.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, DECIMAL, Text
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base
# from app.models.fee_payment import FeePayment # Para referencia

class TransactionType(str, enum.Enum):
    INCOME = "income"   # Ingreso (ej: por servicios cobrados)
    EXPENSE = "expense" # Egreso (ej: pago de sueldos, software, publicidad)

class CompanyTransaction(Base):
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    description = Column(Text, nullable=False)
    transaction_type = Column(SQLAlchemyEnum(TransactionType), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), default="PEN", nullable=False)

    # Categoría para mejor organización (ej: "Ingreso por Servicios", "Costos Operativos", "Marketing")
    category = Column(String(100), nullable=True, index=True)
    # Referencia a un pago de cliente si este ingreso está directamente ligado a él
    related_fee_payment_id = Column(Integer, ForeignKey("fee_payments.id"), nullable=True, index=True)
    # Referencia a una factura de proveedor o documento de sustento del gasto
    reference_document_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True) # Notas adicionales

    # Relationships
    related_fee_payment = relationship("FeePayment") # Si un FeePayment puede tener múltiples CompanyTransactions (raro) o es 1-1.

    def __repr__(self):
        return f"<CompanyTransaction(id={self.id}, type='{self.transaction_type.value}', amount={self.amount})>"

# Contenido de credential_access_audit.py
# app/models/credential_access_audit.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class CredentialAccessAudit(Base):
    __tablename__ = "credential_access_audits"
    
    credential_id = Column(Integer, ForeignKey("sunat_credentials.id", ondelete="CASCADE"), nullable=False, index=True)
    accessing_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), index=True)
    
    action_performed = Column(String(255), nullable=False)
    access_successful = Column(Boolean)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    reason_for_access = Column(Text)
    failure_reason_if_any = Column(Text)

    credential = relationship("SunatCredential", back_populates="access_audits")
    accessing_user = relationship("User", back_populates="initiated_audits")
    service_contract = relationship("ServiceContract")

# Contenido de fee_payment.py
# app/models/fee_payment.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, DECIMAL, Text
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base
# from app.models.user import User
# from app.models.service_contract import ServiceContract

class PaymentMethodPlatform(str, enum.Enum):
    YAPE = "yape"
    PLIN = "plin"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash" # Si aplica
    OTHER = "other"

class FeePaymentStatus(str, enum.Enum):
    PENDING_VERIFICATION = "pending_verification" # Cliente dice que pagó, estamos verificando
    VERIFIED_PAID = "verified_paid"
    FAILED_VERIFICATION = "failed_verification" # No se pudo verificar el pago
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class FeePayment(Base):
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), nullable=True, index=True) # Puede ser nulo si es un pago general no atado a un servicio específico
    paying_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True) # Quién realizó el pago (cliente)

    amount_paid = Column(DECIMAL(10, 2), nullable=False) # Monto pagado por nuestro servicio
    currency = Column(String(3), default="PEN", nullable=False) # PEN, USD, etc.
    payment_method_used = Column(SQLAlchemyEnum(PaymentMethodPlatform), nullable=False)
    payment_reference = Column(String(255), nullable=True, index=True) # ID de transacción Yape/Plin, Nro Operación bancaria
    payment_date = Column(DateTime(timezone=True), nullable=False) # Fecha y hora del pago
    status = Column(SQLAlchemyEnum(FeePaymentStatus), default=FeePaymentStatus.PENDING_VERIFICATION, nullable=False)
    verified_by_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Staff que verificó
    verification_notes = Column(Text, nullable=True)

    # Si el pago también cubre impuestos a SUNAT que nosotros gestionaremos
    # This is for tracking, actual payment to SUNAT is in MonthlyDeclaration
    includes_sunat_tax_amount = Column(DECIMAL(10, 2), nullable=True, default=0.00)

    # Relationships
    service_contract = relationship("ServiceContract", back_populates="fee_payments")
    paying_user = relationship("User", foreign_keys=[paying_user_id], back_populates="initiated_fee_payments")
    verified_by_staff = relationship("User", foreign_keys=[verified_by_staff_id]) # Simple relationship, no backpop needed here usually

    def __repr__(self):
        return f"<FeePayment(id={self.id}, amount_paid={self.amount_paid}, status='{self.status.value}')>"

# Contenido de monthly_client_summary.py
# app/models/monthly_client_summary.py
from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

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
    client_user = relationship("User")

# Contenido de monthly_declaration.py
# app/models/monthly_declaration.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, DECIMAL, Text, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.db.database import Base

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
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), unique=True, nullable=False, index=True)
    original_declaration_id = Column(Integer, ForeignKey("monthly_declarations.id"), nullable=True, index=True)

    declaration_type = Column(SQLAlchemyEnum(DeclarationType), default=DeclarationType.ORIGINAL, nullable=False)
    total_sales_taxable_base = Column(DECIMAL(12, 2), nullable=True)
    # ... (todos tus otros campos como antes) ...
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
    sunat_payment_status = Column(SQLAlchemyEnum(SunatPaymentStatus), default=SunatPaymentStatus.NOT_APPLICABLE, nullable=False)
    sunat_payment_nps = Column(String(50), nullable=True)
    amount_paid_to_sunat_via_platform = Column(DECIMAL(12, 2), nullable=True)
    notes = Column(Text, nullable=True)

    service_contract = relationship("ServiceContract", back_populates="monthly_declaration")

    original_declaration = relationship(
        "MonthlyDeclaration", # Nombre de la clase como string
        # primaryjoin ahora usa strings para referenciar las columnas:
        # "NombreDeClase.nombre_columna"
        primaryjoin="MonthlyDeclaration.original_declaration_id == remote(MonthlyDeclaration.id)",
        # remote_side también usa strings para la columna remota
        remote_side="MonthlyDeclaration.id", # <--- CORRECCIÓN: Usar string
        backref="rectifications",
        # Opcional: Usar uselist=False si una rectificatoria solo puede tener UN original
        # lo cual tiene sentido. El backref "rectifications" seguirá siendo una lista.
        uselist=False
    )

    def __repr__(self):
        return f"<MonthlyDeclaration(id={self.id}, type='{self.declaration_type.value}', order_number='{self.sunat_order_number}')>"

# Contenido de payroll_receipt.py
# app/models/payroll_receipt.py
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Enum as SQLAlchemyEnum, DECIMAL, Text, Boolean
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base
# from app.models.service_contract import ServiceContract # ForeignKey usa string

class PaymentMethodRxh(str, enum.Enum): # Medios de pago comunes para RxH según SUNAT
    DEPOSITO_EN_CUENTA = "001" # Depósito en cuenta
    TRANSFERENCIA_FONDOS = "003" # Transferencia de fondos
    EFECTIVO = "008" # Efectivo
    OTROS = "009" # Otros medios de pago (SUNAT lista más)
    # Puedes añadir más según la tabla de SUNAT

class PayrollReceipt(Base):
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), unique=True, nullable=False, index=True) # One-to-One

    # Data from the service_contract.specific_data will be used to fill this,
    # or staff can input it directly if this service is chosen.
    rxh_series_number = Column(String(10), nullable=False) # E001-XXXX o R001-XXXX
    rxh_correlative_number = Column(String(20), nullable=False, index=True) # El número correlativo
    rxh_issue_date = Column(Date, nullable=False, index=True)

    # Acquirer details (cliente del que emite el RxH)
    acquirer_doc_type = Column(String(10), nullable=False) # RUC, DNI, CARNET_EXT, PASAPORTE
    acquirer_doc_number = Column(String(20), nullable=False, index=True)
    acquirer_name_or_business_name = Column(String(255), nullable=False)

    service_description = Column(Text, nullable=False)
    gross_amount = Column(DECIMAL(12, 2), nullable=False) # Monto bruto
    has_income_tax_withholding = Column(Boolean, default=False) # ¿Aplica retención IR?
    income_tax_withholding_amount = Column(DECIMAL(12, 2), nullable=True, default=0.00) # Monto retenido
    net_amount_payable = Column(DECIMAL(12, 2), nullable=False) # Monto neto a cobrar

    payment_date = Column(Date, nullable=True) # Fecha en que se pagó el RxH (no la emisión)
    payment_method = Column(SQLAlchemyEnum(PaymentMethodRxh), nullable=True)
    observation = Column(Text, nullable=True) # Observaciones en el RxH

    # Relationships
    service_contract = relationship("ServiceContract", back_populates="payroll_receipt")

    def __repr__(self):
        return f"<PayrollReceipt(id={self.id}, series='{self.rxh_series_number}', number='{self.rxh_correlative_number}')>"

# Contenido de service_contract.py
# app/models/service_contract.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, Text, JSON, DECIMAL
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.db.database import Base
# from app.models.user import User # ForeignKey uses string
# from app.models.service_type import ServiceType

class ServiceContractStatus(str, enum.Enum):
    REQUESTED_BY_CLIENT = "requested_by_client"
    PENDING_STAFF_ASSIGNMENT = "pending_staff_assignment"
    ASSIGNED_TO_STAFF = "assigned_to_staff"
    IN_PROGRESS = "in_progress"
    PENDING_CLIENT_ACTION = "pending_client_action" # e.g., payment, information
    PENDING_CLIENT_PAYMENT_FOR_SERVICE = "pending_client_payment_for_service" # For our fee
    PENDING_SUNAT_PAYMENT_VIA_PLATFORM = "pending_sunat_payment_via_platform" # If we pay SUNAT
    COMPLETED_PAID = "completed_paid"
    COMPLETED_NO_PAYMENT_REQUIRED = "completed_no_payment_required"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_STAFF = "cancelled_by_staff"
    FAILED_SUNAT_ERROR = "failed_sunat_error"
    FAILED_MISSING_INFO = "failed_missing_info"

class ServiceContract(Base):
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_type_id = Column(Integer, ForeignKey("service_types.id"), nullable=False, index=True)
    assigned_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # Staff user

    status = Column(SQLAlchemyEnum(ServiceContractStatus),
                    default=ServiceContractStatus.REQUESTED_BY_CLIENT,
                    nullable=False, index=True)
    # For services like monthly declarations, e.g., "2023-11"
    tax_period = Column(String(7), nullable=True, index=True) # YYYY-MM
    # Custom data for this specific service instance, validated against ServiceType.specific_data_schema
    # e.g., for RxH: { "recipient_ruc": "...", "amount": ..., "description": "..." }
    specific_data = Column(JSON, nullable=True)
    internal_notes = Column(Text, nullable=True) # For staff communication
    client_feedback_rating = Column(Integer, nullable=True) # e.g., 1-5 stars
    client_feedback_comments = Column(Text, nullable=True)
    final_service_fee = Column(DECIMAL(10, 2), nullable=True) # Could differ from base_fee

    # Timestamps for state transitions
    requested_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    client = relationship("User", foreign_keys=[client_id], back_populates="contracted_services_as_client")
    service_type = relationship("ServiceType", back_populates="service_contracts")
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id], back_populates="assigned_services_as_staff")

    # One-to-one or One-to-many specific service data tables
    monthly_declaration = relationship("MonthlyDeclaration", uselist=False, back_populates="service_contract", cascade="all, delete-orphan")
    payroll_receipt = relationship("PayrollReceipt", uselist=False, back_populates="service_contract", cascade="all, delete-orphan")
    # dev_request = relationship("DevolutionRequest", uselist=False, back_populates="service_contract") # Example for future

    fee_payments = relationship("FeePayment", back_populates="service_contract", cascade="all, delete-orphan")
    attached_documents = relationship("AttachedDocument", back_populates="service_contract", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="service_contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ServiceContract(id={self.id}, client_id={self.client_id}, service_type_id={self.service_type_id}, status='{self.status.value}')>"

# Contenido de service_type.py
# app/models/service_type.py
from sqlalchemy import Column, String, Text, Boolean, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class ServiceType(Base):
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    base_fee = Column(DECIMAL(10, 2), nullable=False, default=0.00) # S/.
    is_active = Column(Boolean, default=True)
    requires_period = Column(Boolean, default=False) # e.g., for monthly declarations
    # For custom fields required by this service type, e.g., for RxH data points.
    # Store a JSON schema definition here to validate 'specific_data' in ServiceContract.
    specific_data_schema = Column(JSON, nullable=True)

    # Relationships
    service_contracts = relationship("ServiceContract", back_populates="service_type")

    def __repr__(self):
        return f"<ServiceType(id={self.id}, name='{self.name}')>"

# Contenido de sunat_credential.py
# app/models/sunat_credential.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SunatCredential(Base):
    __tablename__ = "sunat_credentials"

    sol_username = Column(String(255), nullable=False)
    encrypted_sol_password = Column(String(512), nullable=False) 
    owner_client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    owner_client_profile = relationship("ClientProfile", back_populates="sunat_credentials")
    access_audits = relationship("CredentialAccessAudit", back_populates="credential", cascade="all, delete-orphan")

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
import enum
from sqlalchemy import Boolean, Column, DateTime, Integer, String, text, Enum as PGEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UserRole(enum.Enum):
    AUTHENTICATED = "authenticated"
    CLIENT_FREEMIUM = "client_freemium"
    CLIENT_PAID = "client_paid"
    STAFF_COLLABORATOR = "staff_collaborator"
    STAFF_MANAGER = "staff_manager"
    STAFF_CEO = "staff_ceo"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(PGEnum(UserRole, name="userrole", create_type=False, values_callable=lambda x: [e.value for e in x]),
                nullable=False, server_default=text("'authenticated'::userrole"), default=UserRole.AUTHENTICATED)
    is_active = Column(Boolean(), default=True)
    last_platform_login_at = Column(DateTime(timezone=True))
    contact_name = Column(String(255))
    phone_number = Column(String(20), index=True)
    profile_image_url = Column(String(512))
    staff_dni = Column(String(15), index=True)
    staff_full_name = Column(String(255))
    staff_ruc_personal = Column(String(11), index=True)

    client_accesses = relationship("UserClientAccess", back_populates="user", cascade="all, delete-orphan")
    contracted_services_as_client = relationship("ServiceContract", foreign_keys="[ServiceContract.client_id]", back_populates="client")
    assigned_services_as_staff = relationship("ServiceContract", foreign_keys="[ServiceContract.assigned_staff_id]", back_populates="assigned_staff")
    sent_communications = relationship("Communication", foreign_keys="[Communication.sender_user_id]", back_populates="sender_user")
    received_communications = relationship("Communication", foreign_keys="[Communication.recipient_user_id]", back_populates="recipient_user")
    initiated_fee_payments = relationship("FeePayment", foreign_keys="[FeePayment.paying_user_id]", back_populates="paying_user")
    uploaded_yape_plin_transactions = relationship("YapePlinTransaction", back_populates="uploader_user")
    initiated_audits = relationship("CredentialAccessAudit", foreign_keys="[CredentialAccessAudit.accessing_user_id]", back_populates="accessing_user")
    balance_transactions = relationship("ClientBalanceLedger", back_populates="client_user", cascade="all, delete-orphan")

# Contenido de user_client_access.py
# app/models/user_client_access.py
import enum
from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLAlchemyEnum, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class RelationshipType(str, enum.Enum):
    TITULAR = "TITULAR"
    REPRESENTANTE_LEGAL = "REPRESENTANTE_LEGAL"
    CONTADOR = "CONTADOR"
    ASISTENTE = "ASISTENTE"

class UserClientAccess(Base):
    __tablename__ = "user_client_access"
    
    # Se sobreescribe el 'id' de la clase Base
    id = None
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    client_profile_id = Column(Integer, ForeignKey("client_profiles.id", ondelete="CASCADE"), primary_key=True)
    
    relationship_type = Column(SQLAlchemyEnum(RelationshipType, name="relationshiptype"), nullable=False)
    
    __table_args__ = (PrimaryKeyConstraint('user_id', 'client_profile_id'),)

    user = relationship("User", back_populates="client_accesses")
    client_profile = relationship("ClientProfile", back_populates="user_accesses")

# Contenido de yape_plin_transaction.py
# app/models/yape_plin_transaction.py
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as SQLAlchemyEnum, DECIMAL, Text, Time, Date
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base
# from app.models.user import User
# from app.models.fee_payment import FeePayment # Para posible enlace

class DigitalWalletProvider(str, enum.Enum):
    YAPE = "yape"
    PLIN = "plin"
    OTHER = "other"

class ExtractionStatus(str, enum.Enum):
    PENDING = "pending"         # OCR y LLM pendientes
    OCR_COMPLETED = "ocr_completed" # OCR hecho, LLM pendiente
    LLM_EXTRACTION_COMPLETED = "llm_extraction_completed" # Datos extraídos
    OCR_FAILED = "ocr_failed"
    LLM_FAILED = "llm_failed"
    MANUAL_VERIFICATION_REQUIRED = "manual_verification_required"
    VERIFIED_MATCHED = "verified_matched" # Comparado y coincide con un FeePayment
    VERIFIED_UNMATCHED = "verified_unmatched" # Verificado pero no se encuentra FeePayment asociado

class YapePlinTransaction(Base):
    uploader_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True) # Cliente que subió la captura
    # Podría estar vinculado a un FeePayment si el cliente sube la captura como prueba de ese FeePayment.
    # O podría ser una tabla donde se suben todas las capturas y luego se intentan conciliar.
    # Para MVP, podríamos vincularlo a FeePayment si el flujo es:
    # 1. Cliente registra FeePayment (dice que pagó).
    # 2. Cliente sube captura para ESE FeePayment.
    fee_payment_id = Column(Integer, ForeignKey("fee_payments.id"), nullable=True, index=True)

    original_image_filename = Column(String(255), nullable=False)
    image_storage_path = Column(String(512), nullable=False) # ej: S3 path o path local
    provider = Column(SQLAlchemyEnum(DigitalWalletProvider), nullable=True) # Podría ser inferido por el LLM

    # Fields extracted by OCR/LLM
    extracted_amount = Column(DECIMAL(10, 2), nullable=True)
    extracted_currency = Column(String(3), nullable=True) # PEN
    extracted_recipient_name = Column(String(255), nullable=True) # Nombre del Destino
    extracted_sender_name = Column(String(255), nullable=True)    # Nombre del Remitente (si aparece)
    extracted_transaction_date = Column(Date, nullable=True)       # Fecha de la transacción
    extracted_transaction_time = Column(Time, nullable=True)       # Hora de la transacción
    extracted_security_code = Column(String(10), nullable=True)   # Código de Seguridad Yape (3 dígitos usualmente)
    extracted_phone_suffix = Column(String(10), nullable=True)    # Últimos dígitos del cel (ej: ***123)
    extracted_operation_number = Column(String(50), nullable=True, index=True) # Nro. de operación

    raw_ocr_text = Column(Text, nullable=True) # Texto completo del OCR
    llm_confidence_score = Column(DECIMAL(3,2), nullable=True) # 0.00 a 1.00 de confianza del LLM
    extraction_status = Column(SQLAlchemyEnum(ExtractionStatus), default=ExtractionStatus.PENDING, nullable=False)
    processing_notes = Column(Text, nullable=True) # Notas del proceso de extracción/verificación

    # Relationships
    uploader_user = relationship("User", back_populates="uploaded_yape_plin_transactions")
    fee_payment = relationship("FeePayment") # No back_populates si el FeePayment no necesita saber de esto directamente

    def __repr__(self):
        return f"<YapePlinTransaction(id={self.id}, status='{self.extraction_status.value}')>"

# Contenido de __init__.py
# app/models/__init__.py

# app/models/__init__.py
from .user import User, UserRole
from .client_profile import ClientProfile, ClientType
from .user_client_access import UserClientAccess, RelationshipType
from .sunat_credential import SunatCredential
# (Añade aquí el resto de tus modelos si tienes más)

# --- PIEZAS FUNDAMENTALES (Entidades Principales e Independientes) ---
# Se importan primero porque otros modelos dependen de ellos.
from .service_type import ServiceType

# --- TABLA DE ASOCIACIÓN ('Pegamento') ---
# Se importa DESPUÉS de User y ClientProfile porque los une.

# --- MODELOS DEPENDIENTES (Relacionados con los de arriba) ---
# Estos modelos probablemente tienen ForeignKeys a User, ClientProfile, etc.
from .service_contract import ServiceContract
from .monthly_declaration import MonthlyDeclaration
from .payroll_receipt import PayrollReceipt
from .fee_payment import FeePayment
from .yape_plin_transaction import YapePlinTransaction
from .attached_document import AttachedDocument
from .communication import Communication
from .credential_access_audit import CredentialAccessAudit
from .monthly_client_summary import MonthlyClientSummary
from .company_transaction import CompanyTransaction
from .company_tax_declaration import CompanyTaxDeclaration

