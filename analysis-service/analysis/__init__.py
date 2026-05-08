import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fooduser:foodpass123@localhost:5432/food_discovery")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_WORKER_COUNT = int(os.getenv("CELERY_WORKER_COUNT", "2"))
