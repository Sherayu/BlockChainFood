import requests
import json
from datetime import datetime, timezone
import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedditClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FoodDiscoveryBot/1.0 (by /u/food_discovery_bot)"
        })
        self.redis_client = redis.from_url(REDIS_URL)
        self.subreddits = ["cooking", "food", "recipes", "Baking", "IndianFood", "MexicanFood"]

    def fetch_trending(self, limit: int = 25):
        results = []
        for subreddit in self.subreddits:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for post in data.get("data", {}).get("children", []):
                        post_data = post.get("data", {})
                        if self._is_food_related(post_data):
                            item = self._parse_post(subreddit, post_data)
                            results.append(item)
                            self.redis_client.rpush("crawl_results", json.dumps(item))
            except Exception as e:
                print(f"Reddit error r/{subreddit}: {e}")
        return results

    def _is_food_related(self, post: dict) -> bool:
        title = post.get("title", "").lower()
        keywords = ["recipe", "cook", "bake", "food", "dish", "ingredient",
                     "dinner", "lunch", "breakfast", "dessert", "spice"]
        return any(k in title for k in keywords)

    def _parse_post(self, subreddit: str, post: dict) -> dict:
        title = post.get("title", "")
        selftext = post.get("selftext", "")
        url = post.get("url", f"https://www.reddit.com{post.get('permalink', '')}")
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)

        popularity = min(100, (score * 0.6 + num_comments * 0.4))

        return {
            "title": title,
            "url": url,
            "source": f"Reddit r/{subreddit}",
            "source_type": "social_reddit",
            "description": selftext[:500] if selftext else "",
            "image_url": post.get("url_overridden_by_dest", ""),
            "ingredients": [],
            "steps": [],
            "rating": popularity / 20,
            "difficulty": "medium",
            "prep_time_minutes": None,
            "cook_time_minutes": None,
            "servings": None,
            "tags": [subreddit, "reddit"],
            "nutrition": {},
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }
