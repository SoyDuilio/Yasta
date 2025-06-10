# app/models/service_type.py
from sqlalchemy import Column, String, Text, Boolean, DECIMAL, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class ServiceType(Base):
    __tablename__ = "service_types"

    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    base_fee = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_active = Column(Boolean, default=True)
    requires_period = Column(Boolean, default=False)
    specific_data_schema = Column(JSON, nullable=True)

    # Relationships
    service_contracts = relationship("ServiceContract", back_populates="service_type")

    def __repr__(self):
        return f"<ServiceType(id={self.id}, name='{self.name}')>"