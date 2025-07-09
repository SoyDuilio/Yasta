# app/schemas/payment.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from app.models.fee_payment import PaymentMethodPlatform
from .declaration_request_schema import DeclarationRequestCreate
from app.models.yape_plin_transaction import DigitalWalletProvider


class PaymentManualCreate(BaseModel):
    monto_pagado: Decimal = Field(..., gt=0)
    numero_operacion: str = Field(..., min_length=1, max_length=255)
    origen_app: PaymentMethodPlatform
    # El campo es opcional y puede ser None si no se envía desde el formulario (ej: para Plin)
    codigo_seguridad: Optional[str] = Field(None, max_length=10)


# Schema para los datos cuando el usuario elige la opción manual
class ManualPaymentData(BaseModel):
    provider: Optional[DigitalWalletProvider] = None
    # Hacemos los campos opcionales permitiendo que sean strings vacíos o None
    operation_number: Optional[str] = Field(None, max_length=50)
    # CAMBIO: de 'gt=0' (mayor que) a 'ge=0' (mayor o igual que)
    declared_amount: Optional[float] = Field(None, ge=0)
    security_code: Optional[str] = Field(None, max_length=10)

# El "Contrato Principal": representa todos los datos que nos enviará el nuevo formulario.
# Este schema será recibido como un string JSON y lo parsearemos en la ruta.
class UnifiedPaymentCreate(BaseModel):
    client_profile_id: int
    declarations: List[DeclarationRequestCreate]
    # El método de pago nos dirá si debemos esperar un archivo o datos manuales
    payment_method: str # Esperamos "VOUCHER" o "MANUAL"
    
    # Los datos manuales son opcionales, solo vendrán si payment_method == "MANUAL"
    manual_data: Optional[ManualPaymentData] = None