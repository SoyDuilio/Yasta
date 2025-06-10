# app/schemas/fee_payment_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal
from app.models.fee_payment import PaymentMethodPlatform, FeePaymentStatus
from app.schemas.user_schema import UserGeneralResponse # Para mostrar info del pagador/verificador

AmountDecimal = Annotated[Decimal, Field(decimal_places=2)]
CurrencyStr = Annotated[str, Field(min_length=3, max_length=3)] # PEN, USD

class FeePaymentBase(BaseModel):
    amount_paid: AmountDecimal = Field(..., gt=0) # Debe ser mayor que cero
    currency: CurrencyStr = "PEN"
    payment_method_used: PaymentMethodPlatform
    payment_reference: Optional[Annotated[str, Field(max_length=255)]] = None
    payment_date: datetime # Fecha y hora del pago, timezone-aware
    includes_sunat_tax_amount: Optional[AmountDecimal] = Field(default=0.00)

class FeePaymentCreateByClient(FeePaymentBase): # Cliente informa un pago
    service_contract_id: Optional[int] = None # Opcional, si no está atado a un servicio
    # paying_user_id se toma del usuario logueado

class FeePaymentCreateByStaff(FeePaymentBase): # Staff registra un pago directamente
    service_contract_id: Optional[int] = None
    paying_user_id: int
    status: FeePaymentStatus = FeePaymentStatus.VERIFIED_PAID # Staff usualmente lo registra como verificado
    verified_by_staff_id: Optional[int] = None # Se toma del staff logueado
    verification_notes: Optional[str] = None

class FeePaymentUpdateByStaff(BaseModel): # Staff verifica o actualiza
    status: Optional[FeePaymentStatus] = None
    verified_by_staff_id: Optional[int] = None # Se toma del staff logueado que actualiza
    verification_notes: Optional[str] = None
    payment_reference: Optional[Annotated[str, Field(max_length=255)]] = None # Puede corregir referencia
    # Otros campos si es necesario actualizar

class FeePaymentResponse(FeePaymentBase):
    id: int
    service_contract_id: Optional[int] = None
    paying_user_id: int
    status: FeePaymentStatus
    verified_by_staff_id: Optional[int] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    paying_user: Optional[UserGeneralResponse] = None
    verified_by_staff: Optional[UserGeneralResponse] = None
    # service_contract: Optional[ServiceContractResponse] = None # Podría ser útil

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v),
            # datetime: lambda dt: dt.isoformat() if dt else None
        }