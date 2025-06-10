# app/schemas/yape_plin_transaction_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import date, time, datetime
from decimal import Decimal
from app.models.yape_plin_transaction import DigitalWalletProvider, ExtractionStatus

AmountDecimal = Annotated[Decimal, Field(decimal_places=2)]

class YapePlinTransactionBase(BaseModel):
    # Info antes de la extracción (para creación)
    original_image_filename: Annotated[str, Field(max_length=255)]
    image_storage_path: Annotated[str, Field(max_length=512)] # Esto se setea en el backend tras la subida
    fee_payment_id: Optional[int] = None # Si se asocia al subir

class YapePlinTransactionCreate(BaseModel): # Lo que se envía para crear un registro (solo el ID de la imagen subida)
    uploaded_file_id: str # Un identificador temporal del archivo subido, el backend lo procesa
    fee_payment_id: Optional[int] = None

class YapePlinTransactionUpdateBySystem(BaseModel): # Para actualizar tras OCR/LLM
    provider: Optional[DigitalWalletProvider] = None
    extracted_amount: Optional[AmountDecimal] = None
    extracted_currency: Optional[Annotated[str, Field(max_length=3)]] = None
    extracted_recipient_name: Optional[Annotated[str, Field(max_length=255)]] = None
    extracted_sender_name: Optional[Annotated[str, Field(max_length=255)]] = None
    extracted_transaction_date: Optional[date] = None
    extracted_transaction_time: Optional[time] = None
    extracted_security_code: Optional[Annotated[str, Field(max_length=10)]] = None
    extracted_phone_suffix: Optional[Annotated[str, Field(max_length=10)]] = None
    extracted_operation_number: Optional[Annotated[str, Field(max_length=50)]] = None
    raw_ocr_text: Optional[str] = None
    llm_confidence_score: Optional[Annotated[Decimal, Field(ge=0, le=1, decimal_places=2)]] = None
    extraction_status: Optional[ExtractionStatus] = None
    processing_notes: Optional[str] = None

class YapePlinTransactionResponse(YapePlinTransactionBase, YapePlinTransactionUpdateBySystem):
    id: int
    uploader_user_id: int
    created_at: datetime
    updated_at: datetime

    # uploader_user: Optional[UserGeneralResponse] = None # Podría ser útil

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v),
            # time: lambda t: t.isoformat() if t else None,
            # date: lambda d: d.isoformat() if d else None,
            # datetime: lambda dt: dt.isoformat() if dt else None
        }