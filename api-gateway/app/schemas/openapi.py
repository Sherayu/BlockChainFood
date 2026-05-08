from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class AlertConfigBase(BaseModel):
    frequency: str = Field("daily", pattern=r"^(hourly|daily|weekly)$")
    categories: List[str] = []
    regions: List[str] = []
    active: bool = True


class AlertConfigCreate(AlertConfigBase):
    pass


class AlertConfigUpdate(BaseModel):
    frequency: Optional[str] = Field(None, pattern=r"^(hourly|daily|weekly)$")
    categories: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    active: Optional[bool] = None


class AlertConfigResponse(AlertConfigBase):
    id: UUID
    last_sent: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrendingFoodBase(BaseModel):
    name: str
    category: str
    region: str = "global"
    popularity_score: float = 0.0
    trend_velocity: float = 0.0
    source_urls: List[str] = []
    description: Optional[str] = None
    image_url: Optional[str] = None


class TrendingFoodResponse(TrendingFoodBase):
    id: UUID
    discovered_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class IngredientItem(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = "other"


class RecipeBase(BaseModel):
    title: str
    url: str
    source: Optional[str] = None
    source_type: str = "recipe_site"
    rating: float = 0.0
    difficulty: str = "medium"
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None


class RecipeDetail(RecipeBase):
    id: UUID
    food_id: UUID
    ingredients: list = []
    steps: list = []
    tags: list = []
    nutrition: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeListItem(RecipeBase):
    id: UUID
    food_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class StoredIngredientResponse(BaseModel):
    id: UUID
    recipe_id: UUID
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    category: str = "other"
    notes: Optional[str] = None
    stored_at: datetime

    class Config:
        from_attributes = True


class IngredientStoreResponse(BaseModel):
    recipe_id: str
    ingredients_count: int
    status: str
    stored_at: str


class CategoryResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str


class RegionResponse(BaseModel):
    id: str
    name: str
    description: str


class CrawlerStatusResponse(BaseModel):
    status: str
    active_spiders: int = 0
    pages_crawled_today: int = 0
    items_extracted_today: int = 0
    last_crawl: Optional[datetime] = None
    queue_size: int = 0


class AnalysisStatusResponse(BaseModel):
    status: str
    pending_tasks: int = 0
    processed_today: int = 0
    trends_identified_today: int = 0
    last_processed: Optional[datetime] = None
    worker_count: int = 0
