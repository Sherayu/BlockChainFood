from app.repositories.base import BaseRepository
from app.models.ingredient import StoredIngredient
from app.models.recipe import Recipe
from app.services.ai_ingredient_extractor import AIIngredientExtractor
from sqlalchemy import select, update
from typing import List
from uuid import UUID
from datetime import datetime, timezone


class IngredientRepository(BaseRepository[StoredIngredient]):
    def __init__(self, session):
        super().__init__(StoredIngredient, session)

    async def get_by_recipe(self, recipe_id: UUID) -> List[StoredIngredient]:
        result = await self.session.execute(
            select(StoredIngredient).where(StoredIngredient.recipe_id == recipe_id)
        )
        return result.scalars().all()

    async def extract_and_store(self, recipe_id: UUID) -> dict:
        result = await self.session.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        recipe = result.scalar_one_or_none()
        if not recipe:
            raise ValueError(f"Recipe {recipe_id} not found")

        raw_ingredients = recipe.ingredients if isinstance(recipe.ingredients, list) else []
        now = datetime.now(timezone.utc)
        stored = []

        if not raw_ingredients:
            extractor = AIIngredientExtractor()
            raw_ingredients = await extractor.extract(recipe.url)
            if raw_ingredients:
                await self.session.execute(
                    update(Recipe)
                    .where(Recipe.id == recipe_id)
                    .values(ingredients=raw_ingredients)
                )

        for item in raw_ingredients:
            ingredient = StoredIngredient(
                recipe_id=recipe_id,
                name=item.get("name", ""),
                quantity=item.get("quantity", ""),
                unit=item.get("unit", ""),
                category=item.get("category", "other"),
                stored_at=now,
            )
            self.session.add(ingredient)
            stored.append(ingredient)

        await self.session.commit()
        for ing in stored:
            await self.session.refresh(ing)

        return {
            "recipe_id": str(recipe_id),
            "ingredients_count": len(stored),
            "status": "success",
            "stored_at": now.isoformat(),
        }
