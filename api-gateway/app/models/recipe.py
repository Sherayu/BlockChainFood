from app.models.base import Base
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid


class Recipe(Base):
    __tablename__ = "recipe"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    food_id = Column(UUID(as_uuid=True), ForeignKey("trending_food.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    source_type = Column(String(50), nullable=False, default="recipe_site")
    rating = Column(Float, default=0.0)
    difficulty = Column(String(20), default="medium")
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    ingredients = Column(JSONB, nullable=False, default=list)
    steps = Column(JSONB, nullable=False, default=list)
    tags = Column(JSONB, default=list)
    nutrition = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False)
