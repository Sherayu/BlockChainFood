from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.food_repo import TrendingFoodRepository
from app.schemas.openapi import TrendingFoodResponse
from typing import Optional, List

router = APIRouter(prefix="/api/v1/foods", tags=["Foods"])


@router.get("/trending", response_model=List[TrendingFoodResponse])
async def get_trending_foods(
    category: Optional[str] = Query(None, description="Filter by food category"),
    region: Optional[str] = Query(None, description="Filter by region"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    repo = TrendingFoodRepository(db)
    return await repo.get_trending(category=category, region=region, limit=limit)
