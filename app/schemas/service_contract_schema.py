# app/schemas/service_contract_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Annotated
from datetime import datetime
from decimal import Decimal
from app.models.service_contract import ServiceContractStatus
from app.schemas.user_schema import UserGeneralResponse # Para mostrar info del cliente/staff
from app.schemas.service_type_schema import ServiceTypeResponse

# Validaciones para tax_period
TaxPeriodStr = Annotated[str, Field(pattern=r"^\d{4}-\d{2}$")]

class ServiceContractBase(BaseModel):
    service_type_id: int
    tax_period: Optional[TaxPeriodStr] = None # YYYY-MM
    specific_data: Optional[Dict[str, Any]] = None

class ServiceContractCreate(ServiceContractBase):
    client_id: int # Set by system for logged-in client

class ServiceContractUpdateByClient(BaseModel): # What a client can update
    status: Optional[ServiceContractStatus] = None # e.g., to cancel
    client_feedback_rating: Optional[Annotated[int, Field(ge=1, le=5)]] = None # Ejemplo con Field en Annotated
    client_feedback_comments: Optional[str] = None
    # Client might provide specific_data if pending_client_action
    specific_data: Optional[Dict[str, Any]] = None


class ServiceContractUpdateByStaff(BaseModel): # What staff can update
    assigned_staff_id: Optional[int] = None
    status: Optional[ServiceContractStatus] = None
    tax_period: Optional[TaxPeriodStr] = None # YYYY-MM
    specific_data: Optional[Dict[str, Any]] = None
    internal_notes: Optional[str] = None
    final_service_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ServiceContractResponse(ServiceContractBase):
    id: int
    client_id: int
    assigned_staff_id: Optional[int] = None
    status: ServiceContractStatus
    internal_notes: Optional[str] = None # Potentially only for staff view
    client_feedback_rating: Optional[int] = None
    client_feedback_comments: Optional[str] = None
    final_service_fee: Optional[Annotated[Decimal, Field(ge=0, decimal_places=2)]] = None # Ejemplo
    requested_at: datetime
    assigned_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested responses for related data
    client: Optional[UserGeneralResponse] = None # Populate with client info
    service_type: Optional[ServiceTypeResponse] = None # Populate with service type info
    assigned_staff: Optional[UserGeneralResponse] = None # Populate with staff info

    # We will add schemas for monthly_declaration, payroll_receipt etc. and include them here
    # monthly_declaration: Optional[MonthlyDeclarationResponse] = None
    # payroll_receipt: Optional[PayrollReceiptResponse] = None

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }