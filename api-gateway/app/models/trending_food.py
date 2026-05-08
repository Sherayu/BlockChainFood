from app.models.base import Base, TimestampMixin
from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid


class TrendingFood(Base, TimestampMixin):
    __tablename__ = "trending_food"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False, default="global")
    popularity_score = Column(Float, nullable=False, default=0.0)
    trend_velocity = Column(Float, nullable=False, default=0.0)
    source_urls = Column(JSONB, nullable=False, default=list)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    discovered_at = Column(DateTime(timezone=True), nullable=False)
