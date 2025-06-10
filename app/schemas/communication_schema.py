# app/schemas/communication_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
from app.models.communication import CommunicationChannel, CommunicationStatus
from app.schemas.user_schema import UserGeneralResponse # Para mostrar info de sender/recipient

class CommunicationBase(BaseModel):
    channel: CommunicationChannel
    subject: Optional[Annotated[str, Field(max_length=255)]] = None
    message_body: str
    action_url: Optional[Annotated[str, Field(max_length=512)]] = None

class CommunicationCreate(CommunicationBase): # Para crear una nueva comunicación
    sender_user_id: Optional[int] = None # El sistema o el usuario logueado
    recipient_user_id: Optional[int] = None # Necesario si no es un INTERNAL_LOG
    service_contract_id: Optional[int] = None

class CommunicationUpdateBySystem(BaseModel): # Para actualizar estado tras envío
    status: Optional[CommunicationStatus] = None
    sent_at: Optional[datetime] = None # Timezone-aware
    provider_response_id: Optional[Annotated[str, Field(max_length=255)]] = None
    error_message: Optional[str] = None

class CommunicationResponse(CommunicationBase):
    id: int
    sender_user_id: Optional[int] = None
    recipient_user_id: Optional[int] = None
    service_contract_id: Optional[int] = None
    status: CommunicationStatus
    sent_at: Optional[datetime] = None # Timezone-aware
    provider_response_id: Optional[Annotated[str, Field(max_length=255)]] = None
    error_message: Optional[str] = None
    created_at: datetime # Timezone-aware
    updated_at: datetime # Timezone-aware

    sender_user: Optional[UserGeneralResponse] = None
    recipient_user: Optional[UserGeneralResponse] = None
    # service_contract: Optional[ServiceContractResponse] = None

    class Config:
        orm_mode = True
        # json_encoders = {
        #     datetime: lambda dt: dt.isoformat() if dt else None
        # }