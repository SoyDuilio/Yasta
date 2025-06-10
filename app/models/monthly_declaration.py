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