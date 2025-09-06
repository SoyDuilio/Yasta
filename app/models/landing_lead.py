from sqlalchemy import Column, String, DateTime, func, Integer
from app.db.base import Base

class LandingLead(Base):
    __tablename__ = "landing_leads"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ruc = Column(String(11), index=True, nullable=True) # Permitir nulo para el Plan B
    contact_name = Column(String, nullable=True)
    whatsapp_number = Column(String(20), nullable=True)
    
    sol_user = Column(String, nullable=True)
    encrypted_sol_pass = Column(String, nullable=True)
    
    source_landing = Column(String, nullable=True)
    
    # --- ¡EL CAMPO QUE FALTABA! ---
    status = Column(String, default="pending_contact")