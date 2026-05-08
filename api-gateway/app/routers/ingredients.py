from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.ingredient_repo import IngredientRepository
from app.schemas.openapi import StoredIngredientResponse, IngredientStoreResponse
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/v1", tags=["Ingredients"])


@router.post("/recipes/{recipe_id}/ingredients", response_model=IngredientStoreResponse, status_code=201)
async def extract_and_store_ingredients(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = IngredientRepository(db)
    try:
        result = await repo.extract_and_store(recipe_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/recipes/{recipe_id}/ingredients", response_model=List[StoredIngredientResponse])
async def get_stored_ingredients(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = IngredientRepository(db)
    return await repo.get_by_recipe(recipe_id)
