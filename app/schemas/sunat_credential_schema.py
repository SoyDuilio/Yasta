# app/schemas/sunat_credential_schema.py
from pydantic import BaseModel, Field # Field reemplaza a constr aquí
from typing import Optional, Annotated # Importar Annotated
from datetime import datetime, timezone # Importar timezone
from app.models.sunat_credential import CredentialStatus

# --- Type Aliases con Annotated y Field ---
SolUsernameStr = Annotated[str, Field(min_length=12, max_length=50)] # e.g., RUC (11) + User (min 1)
SolPasswordStr = Annotated[str, Field(min_length=6, max_length=100)] # Max length es una estimación

class SunatCredentialBase(BaseModel):
    sol_username: SolUsernameStr
    # Password is write-only for creation/update, never read back

class SunatCredentialCreate(SunatCredentialBase):
    sol_password: SolPasswordStr
    # owner_user_id: int # Se asignará en el backend, no lo envía el cliente directamente al crear credenciales para sí mismo.

class SunatCredentialUpdate(BaseModel):
    sol_username: Optional[SolUsernameStr] = None
    sol_password: Optional[SolPasswordStr] = None # Para actualizar la contraseña
    status: Optional[CredentialStatus] = None # Staff might update this after manual check
    validation_failure_reason: Optional[str] = None

class SunatCredentialResponse(SunatCredentialBase):
    id: int
    owner_user_id: int
    status: CredentialStatus
    last_validated_at: Optional[datetime] = None # Asume timezone-aware UTC
    validation_failure_reason: Optional[str] = None
    created_at: datetime # Asume timezone-aware UTC
    updated_at: datetime # Asume timezone-aware UTC

    class Config:
        orm_mode = True
        # json_encoders = {
        #     datetime: lambda dt: dt.isoformat()
        # }

class SunatCredentialRevealRequest(BaseModel):
    service_contract_id: int # To audit why password was needed