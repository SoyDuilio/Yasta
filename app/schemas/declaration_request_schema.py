# app/schemas/declaration_request_schema.py

from pydantic import BaseModel, constr
from datetime import datetime
from typing import Optional

# Importamos los Enums para usarlos en el schema
from app.models.declaration_request import DeclarationRequestStatus
from app.models.monthly_declaration import DeclarationType

# Este schema se usará para los datos que vienen en la lista del JSON
class DeclarationRequestCreate(BaseModel):
    year: int
    month: int
    declaration_type: DeclarationType

# Schema base para la respuesta de la API (lo que sale de la BD)
class DeclarationRequest(BaseModel):
    id: int
    yape_plin_transaction_id: Optional[int]
    client_profile_id: int
    service_contract_id: Optional[int]
    tax_period: str
    declaration_type: DeclarationType
    status: DeclarationRequestStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True