# app/schemas/monthly_client_summary_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal

AmountDecimal14_2 = Annotated[Decimal, Field(decimal_places=2)] # Para montos grandes
AmountDecimal10_2 = Annotated[Decimal, Field(decimal_places=2)] # Para montos de fees

class MonthlyClientSummaryBase(BaseModel):
    tax_period: Annotated[str, Field(pattern=r"^\d{4}-\d{2}$")] # YYYY-MM
    total_sales: Optional[AmountDecimal14_2] = None
    total_purchases: Optional[AmountDecimal14_2] = None
    total_igv_paid: Optional[AmountDecimal14_2] = None
    total_income_tax_paid: Optional[AmountDecimal14_2] = None
    total_platform_fees_paid: Optional[AmountDecimal10_2] = None

class MonthlyClientSummaryCreate(MonthlyClientSummaryBase):
    client_user_id: int
    # Los datos se calculan y se insertan/actualizan mediante un proceso batch o trigger

class MonthlyClientSummaryResponse(MonthlyClientSummaryBase):
    id: int # Si Base tiene id
    client_user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v),
        }