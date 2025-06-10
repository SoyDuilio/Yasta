# app/models/communication.py
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from app.db.base import Base

class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PLATFORM_NOTIFICATION = "platform_notification"

class CommunicationStatus(str, enum.Enum):
    PENDING_SEND = "pending_send"
    SENT = "sent"
    FAILED_TO_SEND = "failed_to_send"
    READ = "read"

class Communication(Base):
    __tablename__ = "communications"

    sender_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    service_contract_id = Column(Integer, ForeignKey("service_contracts.id"), index=True)

    channel = Column(PGEnum(CommunicationChannel, name="communicationchannel"), nullable=False)
    status = Column(PGEnum(CommunicationStatus, name="communicationstatus"), default=CommunicationStatus.PENDING_SEND, nullable=False)
    subject = Column(String(255))
    message_body = Column(Text, nullable=False)
    action_url = Column(String(512))
    sent_at = Column(DateTime(timezone=True))
    provider_response_id = Column(String(255))
    error_message = Column(Text)

    # Relationships
    sender_user = relationship("User", foreign_keys=[sender_user_id], back_populates="sent_communications")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id], back_populates="received_communications")
    service_contract = relationship("ServiceContract", back_populates="communications")