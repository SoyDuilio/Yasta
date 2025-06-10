# app/schemas/payroll_receipt_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import date, datetime # Date para fechas sin hora
from decimal import Decimal
from app.models.payroll_receipt import PaymentMethodRxh

AmountDecimal = Annotated[Decimal, Field(decimal_places=2)]

class PayrollReceiptBase(BaseModel):
    rxh_series_number: Annotated[str, Field(max_length=10)] # E001
    rxh_correlative_number: Annotated[str, Field(max_length=20)]
    rxh_issue_date: date

    acquirer_doc_type: Annotated[str, Field(max_length=10)]
    acquirer_doc_number: Annotated[str, Field(max_length=20)]
    acquirer_name_or_business_name: Annotated[str, Field(max_length=255)]

    service_description: str
    gross_amount: AmountDecimal
    has_income_tax_withholding: bool = False
    income_tax_withholding_amount: Optional[AmountDecimal] = Field(default=0.00)
    net_amount_payable: AmountDecimal

    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethodRxh] = None
    observation: Optional[str] = None

class PayrollReceiptCreate(PayrollReceiptBase):
    service_contract_id: int # Set by system

class PayrollReceiptUpdate(BaseModel): # Staff can update details if needed
    rxh_series_number: Optional[Annotated[str, Field(max_length=10)]] = None
    rxh_correlative_number: Optional[Annotated[str, Field(max_length=20)]] = None
    rxh_issue_date: Optional[date] = None
    acquirer_doc_type: Optional[Annotated[str, Field(max_length=10)]] = None
    acquirer_doc_number: Optional[Annotated[str, Field(max_length=20)]] = None
    acquirer_name_or_business_name: Optional[Annotated[str, Field(max_length=255)]] = None
    service_description: Optional[str] = None
    gross_amount: Optional[AmountDecimal] = None
    has_income_tax_withholding: Optional[bool] = None
    income_tax_withholding_amount: Optional[AmountDecimal] = None
    net_amount_payable: Optional[AmountDecimal] = None
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethodRxh] = None
    observation: Optional[str] = None

class PayrollReceiptResponse(PayrollReceiptBase):
    id: int
    service_contract_id: int
    created_at: datetime # Timezone-aware UTC
    updated_at: datetime # Timezone-aware UTC

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v),
            # datetime: lambda dt: dt.isoformat() if dt else None,
            # date: lambda d: d.isoformat() if d else None
        }