from app.models.base import Base, TimestampMixin
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid


class AlertConfig(Base, TimestampMixin):
    __tablename__ = "alert_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    frequency = Column(String(20), nullable=False, default="daily")
    categories = Column(JSONB, nullable=False, default=list)
    regions = Column(JSONB, nullable=False, default=list)
    active = Column(Boolean, nullable=False, default=True)
    last_sent = Column(DateTime(timezone=True), nullable=True)
