# app/schemas/buen_contribuyente.py
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class BuenContribuyenteBase(BaseModel):
    ruc: str = Field(..., min_length=11, max_length=11, pattern=r"^(10|20)\d{9}$")
    razon_social: str
    fecha_incorporacion: date
    numero_resolucion: Optional[str] = None
    observaciones: Optional[str] = None

class BuenContribuyente(BuenContribuyenteBase):
    class Config:
        from_attributes = True # Compatible con SQLAlchemy 2.0+ (era orm_mode)