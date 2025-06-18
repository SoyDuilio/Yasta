from pydantic import BaseModel, Field
from decimal import Decimal

class PaymentManualCreate(BaseModel):
    monto_pagado: Decimal = Field(..., gt=0)
    numero_operacion: str
    origen_app: str # "yape" o "plin"