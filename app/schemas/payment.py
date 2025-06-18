# app/schemas/payment.py
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from app.models.fee_payment import PaymentMethodPlatform

class PaymentManualCreate(BaseModel):
    monto_pagado: Decimal = Field(..., gt=0)
    numero_operacion: str = Field(..., min_length=1, max_length=255)
    origen_app: PaymentMethodPlatform
    # El campo es opcional y puede ser None si no se envía desde el formulario (ej: para Plin)
    codigo_seguridad: Optional[str] = Field(None, max_length=10)