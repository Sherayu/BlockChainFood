import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
CRAWL_FREQUENCY_MINUTES = int(os.getenv("CRAWL_FREQUENCY_MINUTES", "60"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
