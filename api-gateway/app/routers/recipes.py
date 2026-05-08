from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.recipe_repo import RecipeRepository
from app.schemas.openapi import RecipeListItem, RecipeDetail
from uuid import UUID

router = APIRouter(prefix="/api/v1", tags=["Recipes"])


@router.get("/foods/{food_id}/recipes", response_model=list[RecipeListItem])
async def get_food_recipes(
    food_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = RecipeRepository(db)
    recipes = await repo.get_by_food(food_id)
    return recipes


@router.get("/recipes/{recipe_id}", response_model=RecipeDetail)
async def get_recipe_details(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = RecipeRepository(db)
    recipe = await repo.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
