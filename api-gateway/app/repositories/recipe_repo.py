from app.repositories.base import BaseRepository
from app.models.recipe import Recipe
from sqlalchemy import select, desc
from typing import List
from uuid import UUID


class RecipeRepository(BaseRepository[Recipe]):
    def __init__(self, session):
        super().__init__(Recipe, session)

    async def get_by_food(self, food_id: UUID, limit: int = 5) -> List[Recipe]:
        result = await self.session.execute(
            select(Recipe)
            .where(Recipe.food_id == food_id)
            .order_by(desc(Recipe.rating))
            .limit(limit)
        )
        return result.scalars().all()
