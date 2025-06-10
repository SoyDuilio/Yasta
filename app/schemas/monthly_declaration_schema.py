# app/schemas/monthly_declaration_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime, timezone
from decimal import Decimal
from app.models.monthly_declaration import DeclarationType, SunatPaymentStatus

# --- Type Aliases ---
AmountDecimal = Annotated[Decimal, Field(decimal_places=2)] # Para montos monetarios

class MonthlyDeclarationBase(BaseModel):
    declaration_type: DeclarationType = DeclarationType.ORIGINAL
    original_declaration_id: Optional[int] = None

    total_sales_taxable_base: Optional[AmountDecimal] = None
    total_sales_igv: Optional[AmountDecimal] = None
    total_exempt_sales: Optional[AmountDecimal] = None
    total_non_taxable_sales: Optional[AmountDecimal] = None

    total_purchases_taxable_base_for_gc: Optional[AmountDecimal] = None
    total_purchases_igv_for_gc: Optional[AmountDecimal] = None

    calculated_igv_payable: Optional[AmountDecimal] = None
    calculated_income_tax: Optional[AmountDecimal] = None
    total_sunat_debt_payable: Optional[AmountDecimal] = None

    sunat_presentation_date: Optional[datetime] = None # Expected to be timezone-aware UTC
    sunat_order_number: Optional[Annotated[str, Field(max_length=50)]] = None
    sunat_payment_status: SunatPaymentStatus = SunatPaymentStatus.NOT_APPLICABLE
    sunat_payment_nps: Optional[Annotated[str, Field(max_length=50)]] = None
    amount_paid_to_sunat_via_platform: Optional[AmountDecimal] = None
    notes: Optional[str] = None

class MonthlyDeclarationCreate(MonthlyDeclarationBase):
    service_contract_id: int # Set by system

class MonthlyDeclarationUpdate(BaseModel): # What staff can update
    declaration_type: Optional[DeclarationType] = None
    original_declaration_id: Optional[int] = None
    total_sales_taxable_base: Optional[AmountDecimal] = None
    total_sales_igv: Optional[AmountDecimal] = None
    total_exempt_sales: Optional[AmountDecimal] = None
    total_non_taxable_sales: Optional[AmountDecimal] = None
    total_purchases_taxable_base_for_gc: Optional[AmountDecimal] = None
    total_purchases_igv_for_gc: Optional[AmountDecimal] = None
    calculated_igv_payable: Optional[AmountDecimal] = None
    calculated_income_tax: Optional[AmountDecimal] = None
    total_sunat_debt_payable: Optional[AmountDecimal] = None
    sunat_presentation_date: Optional[datetime] = None
    sunat_order_number: Optional[Annotated[str, Field(max_length=50)]] = None
    sunat_payment_status: Optional[SunatPaymentStatus] = None
    sunat_payment_nps: Optional[Annotated[str, Field(max_length=50)]] = None
    amount_paid_to_sunat_via_platform: Optional[AmountDecimal] = None
    notes: Optional[str] = None

class MonthlyDeclarationResponse(MonthlyDeclarationBase):
    id: int
    service_contract_id: int
    # Consider if tax_period from ServiceContract should be included here for convenience
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v),
            # datetime: lambda dt: dt.isoformat() if dt else None
        }