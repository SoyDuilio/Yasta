# app/schemas/landing_lead.py
from pydantic import BaseModel
from typing import Optional

class LandingLeadCreate(BaseModel):
    ruc: str
    sol_user: str
    sol_pass: str
    whatsapp_number: Optional[str] = None
    contact_name: Optional[str] = None
    source_landing: str