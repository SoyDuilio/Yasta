# app/schemas/company_transaction_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal
from app.models.company_transaction import TransactionType

AmountDecimal = Annotated[Decimal, Field(decimal_places=2)]
CurrencyStr = Annotated[str, Field(min_length=3, max_length=3)]

class CompanyTransactionBase(BaseModel):
    transaction_date: datetime # Timezone-aware
    description: str
    transaction_type: TransactionType
    amount: AmountDecimal = Field(..., gt=0)
    currency: CurrencyStr = "PEN"
    category: Optional[Annotated[str, Field(max_length=100)]] = None
    related_fee_payment_id: Optional[int] = None
    reference_document_number: Optional[Annotated[str, Field(max_length=50)]] = None
    notes: Optional[str] = None

class CompanyTransactionCreate(CompanyTransactionBase):
    pass # Los campos son directos

class CompanyTransactionUpdate(BaseModel):
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    amount: Optional[AmountDecimal] = Field(None, gt=0)
    currency: Optional[CurrencyStr] = None
    category: Optional[Annotated[str, Field(max_length=100)]] = None
    related_fee_payment_id: Optional[int] = None
    reference_document_number: Optional[Annotated[str, Field(max_length=50)]] = None
    notes: Optional[str] = None

class CompanyTransactionResponse(CompanyTransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # related_fee_payment: Optional[FeePaymentResponse] = None # Podría ser útil

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v),
        }