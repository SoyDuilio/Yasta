# app/models/sunat_due_date.py
from sqlalchemy import Column, String, Date, Integer
from app.db.base import Base

class SunatDueDate(Base):
    __tablename__ = "sunat_due_dates"
    
    tax_period = Column(String(7), nullable=False, index=True) # Formato YYYY-MM
    ruc_last_digit = Column(Integer, nullable=False, index=True)
    due_date = Column(Date, nullable=False)