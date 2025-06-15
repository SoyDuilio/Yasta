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