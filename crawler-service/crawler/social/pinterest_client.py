import requests
import json
from datetime import datetime, timezone
import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class PinterestClient:
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.session = requests.Session()
        self.redis_client = redis.from_url(REDIS_URL)
        self.boards = ["recipes/food", "desserts", "baking", "healthy-recipes"]

    def fetch_trending(self, limit: int = 50):
        results = []
        query = "trending recipes food"
        url = f"https://api.pinterest.com/v5/search/pins?query={query}&page_size={limit}"

        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

        try:
            resp = self.session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for pin in data.get("items", []):
                    item = self._parse_pin(pin)
                    results.append(item)
                    self.redis_client.rpush("crawl_results", json.dumps(item))
        except Exception as e:
            print(f"Pinterest error: {e}")

        return results

    def _parse_pin(self, pin: dict) -> dict:
        return {
            "title": pin.get("title", pin.get("description", "")),
            "url": pin.get("link", pin.get("id", "")),
            "source": "Pinterest",
            "source_type": "social_pinterest",
            "description": pin.get("description", ""),
            "image_url": pin.get("media", {}).get("images", {}).get("originals", {}).get("url", ""),
            "ingredients": [],
            "steps": [],
            "rating": pin.get("reaction_counts", {}).get(1, 0),
            "difficulty": "medium",
            "prep_time_minutes": None,
            "cook_time_minutes": None,
            "servings": None,
            "tags": ["pinterest"],
            "nutrition": {},
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }
