from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fooduser:foodpass123@localhost:5432/food_discovery"
    redis_url: str = "redis://localhost:6379/0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    gemini_api_key: str = ""
    ingredient_extractor_timeout: int = 15
    ingredient_extractor_user_agent: str = "FoodDiscoveryBot/1.0 (+https://fooddiscovery.local)"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
