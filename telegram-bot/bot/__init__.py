import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fooduser:foodpass123@postgres:5432/food_discovery")
