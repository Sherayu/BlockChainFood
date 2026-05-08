from app.models.base import Base, TimestampMixin
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid


class CrawlSource(Base, TimestampMixin):
    __tablename__ = "crawl_source"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    source_type = Column(String(50), nullable=False)
    crawl_frequency_minutes = Column(Integer, nullable=False, default=60)
    active = Column(Boolean, nullable=False, default=True)
    last_crawl = Column(DateTime(timezone=True), nullable=True)
