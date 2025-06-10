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