from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import config, foods, recipes, ingredients, categories, regions, status
from app.middleware.rate_limiter import RateLimitMiddleware

app = FastAPI(
    title="Food Discovery Platform API",
    description="API for managing food trend discovery, recipe analysis, and alert configuration. "
    "Supports crawling food & lifestyle feeds, analyzing trending recipes, "
    "and delivering daily alerts via Telegram bot.",
    version="1.0.0",
    contact={
        "name": "Food Discovery Platform",
        "email": "admin@fooddiscovery.local",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

app.include_router(config.router)
app.include_router(foods.router)
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(categories.router)
app.include_router(regions.router)
app.include_router(status.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}
