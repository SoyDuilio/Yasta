# app/schemas/company_tax_declaration_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime, date
from decimal import Decimal
from app.models.company_tax_declaration import TaxDeclarationTypeCompany
# from app.schemas.attached_document_schema import AttachedDocumentResponse

AmountDecimal = Annotated[Decimal, Field(decimal_places=2)]

class CompanyTaxDeclarationBase(BaseModel):
    tax_period: Annotated[str, Field(min_length=4, max_length=7)] # YYYY o YYYY-MM
    declaration_type: TaxDeclarationTypeCompany
    presentation_date: Optional[datetime] = None # Timezone-aware
    sunat_order_number: Optional[Annotated[str, Field(max_length=50)]] = None
    total_tax_payable: Optional[AmountDecimal] = None
    total_tax_paid: Optional[AmountDecimal] = None
    payment_date: Optional[date] = None
    payment_reference_nps: Optional[Annotated[str, Field(max_length=50)]] = None
    constancy_document_id: Optional[int] = None
    notes: Optional[str] = None

class CompanyTaxDeclarationCreate(CompanyTaxDeclarationBase):
    pass

class CompanyTaxDeclarationUpdate(BaseModel):
    tax_period: Optional[Annotated[str, Field(min_length=4, max_length=7)]] = None
    declaration_type: Optional[TaxDeclarationTypeCompany] = None
    presentation_date: Optional[datetime] = None
    sunat_order_number: Optional[Annotated[str, Field(max_length=50)]] = None
    total_tax_payable: Optional[AmountDecimal] = None
    total_tax_paid: Optional[AmountDecimal] = None
    payment_date: Optional[date] = None
    payment_reference_nps: Optional[Annotated[str, Field(max_length=50)]] = None
    constancy_document_id: Optional[int] = None
    notes: Optional[str] = None

class CompanyTaxDeclarationResponse(CompanyTaxDeclarationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # constancy_document: Optional[AttachedDocumentResponse] = None

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v),
        }