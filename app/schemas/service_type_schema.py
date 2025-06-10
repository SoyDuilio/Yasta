# app/schemas/service_type_schema.py
from pydantic import BaseModel, Field # Field reemplaza a constr aquí
from typing import Optional, Any, Dict, Annotated # Importar Annotated
from datetime import datetime, timezone # Importar timezone
from decimal import Decimal

# --- Type Aliases con Annotated y Field ---
ServiceTypeNameStr = Annotated[str, Field(min_length=3, max_length=100)]
BaseFeeDecimal = Annotated[Decimal, Field(ge=0, decimal_places=2)]

class ServiceTypeBase(BaseModel):
    name: ServiceTypeNameStr
    description: Optional[str] = None
    base_fee: BaseFeeDecimal
    is_active: bool = True
    requires_period: bool = False
    specific_data_schema: Optional[Dict[str, Any]] = None # JSON schema

class ServiceTypeCreate(ServiceTypeBase):
    pass

class ServiceTypeUpdate(BaseModel):
    name: Optional[ServiceTypeNameStr] = None
    description: Optional[str] = None
    base_fee: Optional[BaseFeeDecimal] = None
    is_active: Optional[bool] = None
    requires_period: Optional[bool] = None
    specific_data_schema: Optional[Dict[str, Any]] = None

class ServiceTypeResponse(ServiceTypeBase):
    id: int
    created_at: datetime # Asume timezone-aware UTC
    updated_at: datetime # Asume timezone-aware UTC

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v), # o str(v) si prefieres strings para decimales
            # datetime: lambda dt: dt.isoformat() # Si necesitas formato con offset
        }