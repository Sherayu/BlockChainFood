from fastapi import APIRouter
from app.schemas.openapi import CategoryResponse

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])

CATEGORIES = [
    CategoryResponse(id="desserts", name="Desserts", description="Sweet dishes and desserts", icon="🍰"),
    CategoryResponse(id="starters", name="Starters", description="Appetizers and starters", icon="🥗"),
    CategoryResponse(id="main-course", name="Main Course", description="Main course dishes", icon="🍛"),
    CategoryResponse(id="baking", name="Baking", description="Baked goods and breads", icon="🥖"),
    CategoryResponse(id="beverages", name="Beverages", description="Drinks and beverages", icon="☕"),
    CategoryResponse(id="snacks", name="Snacks", description="Snacks and small bites", icon="🍿"),
]


@router.get("", response_model=list[CategoryResponse])
async def list_categories():
    return CATEGORIES
