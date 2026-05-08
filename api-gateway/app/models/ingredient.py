from app.models.base import Base
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid


class StoredIngredient(Base):
    __tablename__ = "stored_ingredient"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipe.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(String(100), nullable=True)
    unit = Column(String(100), nullable=True)
    category = Column(String(50), default="other")
    notes = Column(Text, nullable=True)
    stored_at = Column(DateTime(timezone=True), nullable=False)
