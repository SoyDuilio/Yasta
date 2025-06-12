# app/models/service_tariff.py
from sqlalchemy import (
    Column, String, Date, Text, Integer, ForeignKey, Boolean, DECIMAL
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ServiceTariff(Base):
    __tablename__ = "service_tariffs"

    service_name = Column(String(255), nullable=False, index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="PEN", nullable=False)

    start_date = Column(Date, nullable=False, default=func.current_date())
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    observations = Column(Text, nullable=True)
    
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    last_updated_by_user = relationship("User", foreign_keys=[last_updated_by_user_id])

    def __repr__(self):
        return f"<ServiceTariff(name='{self.service_name}', price={self.price})>"