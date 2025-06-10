# app/models/monthly_client_summary.py
from sqlalchemy import Column, ForeignKey, Integer, String, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class MonthlyClientSummary(Base):
    __tablename__ = "monthly_client_summaries"
    
    client_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tax_period = Column(String(7), nullable=False, index=True) # YYYY-MM
    
    total_sales = Column(DECIMAL(14, 2))
    total_purchases = Column(DECIMAL(14, 2))
    total_igv_paid = Column(DECIMAL(14, 2))
    total_income_tax_paid = Column(DECIMAL(14, 2))
    total_platform_fees_paid = Column(DECIMAL(10, 2))
    
    __table_args__ = (UniqueConstraint('client_user_id', 'tax_period', name='_client_period_uc'),)
    
    # Relationships
    client_user = relationship("User")