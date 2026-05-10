from app.models.base import Base
from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
import uuid


class TrendingFood(Base):
    __tablename__ = "trending_food"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category = Column(ENUM('desserts', 'starters', 'main-course', 'baking', 'beverages', 'snacks', name='food_category', create_type=False), nullable=False)
    region = Column(ENUM('indian', 'south-asian', 'mexican', 'italian', 'mediterranean', 'east-asian', 'global', name='region', create_type=False), nullable=False, default='global')
    popularity_score = Column(Float, nullable=False, default=0.0)
    trend_velocity = Column(Float, nullable=False, default=0.0)
    source_urls = Column(JSONB, nullable=False, default=list)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    discovered_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
