# app/schemas/credential_access_audit_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
# from app.schemas.user_schema import UserGeneralResponse
# from app.schemas.sunat_credential_schema import SunatCredentialResponse

class CredentialAccessAuditBase(BaseModel):
    action_performed: Annotated[str, Field(max_length=255)]
    access_successful: Optional[bool] = None
    ip_address: Optional[Annotated[str, Field(max_length=45)]] = None
    user_agent: Optional[str] = None
    reason_for_access: Optional[str] = None
    failure_reason_if_any: Optional[str] = None

class CredentialAccessAuditCreate(CredentialAccessAuditBase):
    credential_id: int
    accessing_user_id: int # Se toma del usuario logueado (staff)
    service_contract_id: Optional[int] = None
    # access_timestamp se genera en el backend

class CredentialAccessAuditResponse(CredentialAccessAuditBase):
    id: int
    credential_id: int
    accessing_user_id: int
    service_contract_id: Optional[int] = None
    access_timestamp: datetime # Timezone-aware
    created_at: datetime # Timezone-aware
    # updated_at no es tan relevante para logs de auditoría inmutables

    # accessing_user: Optional[UserGeneralResponse] = None
    # credential: Optional[SunatCredentialResponse] = None # Cuidado con exponer info sensible de la credencial aquí

    class Config:
        orm_mode = True
        # json_encoders = {
        #     datetime: lambda dt: dt.isoformat() if dt else None
        # }