# app/schemas/attached_document_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
from app.models.attached_document import DocumentType
from app.models import DocumentType
# from app.schemas.user_schema import UserGeneralResponse

class AttachedDocumentBase(BaseModel):
    file_name: Annotated[str, Field(max_length=255)]
    document_type: DocumentType = DocumentType.OTHER
    description: Optional[str] = None
    is_visible_to_client: bool = True

class AttachedDocumentCreate(BaseModel): # Para la subida de archivo
    # El archivo se maneja como UploadFile en FastAPI, no directamente en el schema JSON.
    # El backend crea el registro AttachedDocument después de guardar el archivo.
    service_contract_id: Optional[int] = None
    document_type: DocumentType = DocumentType.OTHER
    description: Optional[str] = None
    is_visible_to_client: bool = True
    # uploaded_by_user_id se toma del usuario logueado

class AttachedDocumentUpdate(BaseModel): # Staff puede actualizar metadatos
    document_type: Optional[DocumentType] = None
    description: Optional[str] = None
    is_visible_to_client: Optional[bool] = None
    file_name: Optional[Annotated[str, Field(max_length=255)]] = None # Si se permite renombrar

class AttachedDocumentResponse(AttachedDocumentBase):
    id: int
    service_contract_id: Optional[int] = None
    uploaded_by_user_id: int
    file_mime_type: Optional[Annotated[str, Field(max_length=100)]] = None
    file_size_bytes: Optional[int] = None
    storage_path: Annotated[str, Field(max_length=512)] # O URL de descarga
    created_at: datetime
    updated_at: datetime

    # uploaded_by_user: Optional[UserGeneralResponse] = None

    class Config:
        orm_mode = True