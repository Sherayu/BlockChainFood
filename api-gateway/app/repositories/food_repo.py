from app.repositories.base import BaseRepository
from app.models.trending_food import TrendingFood
from sqlalchemy import select, desc
from typing import Optional, List
from uuid import UUID


class TrendingFoodRepository(BaseRepository[TrendingFood]):
    def __init__(self, session):
        super().__init__(TrendingFood, session)

    async def get_trending(
        self,
        category: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 10,
    ) -> List[TrendingFood]:
        query = select(TrendingFood).order_by(desc(TrendingFood.popularity_score))

        if category:
            query = query.where(TrendingFood.category == category)
        if region:
            query = query.where(TrendingFood.region == region)

        result = await self.session.execute(query.limit(limit))
        return result.scalars().all()
