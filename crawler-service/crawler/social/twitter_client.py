import requests
import json
from datetime import datetime, timezone
import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class TwitterClient:
    def __init__(self, bearer_token: str = None):
        self.bearer_token = bearer_token
        self.session = requests.Session()
        self.redis_client = redis.from_url(REDIS_URL)
        self.queries = [
            "trending recipe food",
            "viral recipe",
            "new dish",
            "cooking trend",
            "#foodtrends",
        ]

    def fetch_trending(self, limit: int = 50):
        results = []
        if not self.bearer_token:
            return results

        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        for query in self.queries:
            url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={limit}&tweet.fields=public_metrics,created_at"
            try:
                resp = self.session.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for tweet in data.get("data", []):
                        item = self._parse_tweet(tweet)
                        results.append(item)
                        self.redis_client.rpush("crawl_results", json.dumps(item))
            except Exception as e:
                print(f"Twitter error for '{query}': {e}")

        return results

    def _parse_tweet(self, tweet: dict) -> dict:
        metrics = tweet.get("public_metrics", {})
        score = (
            metrics.get("like_count", 0) * 0.5
            + metrics.get("retweet_count", 0) * 0.3
            + metrics.get("reply_count", 0) * 0.2
        )

        return {
            "title": tweet.get("text", "")[:200],
            "url": f"https://twitter.com/i/web/status/{tweet.get('id', '')}",
            "source": "Twitter/X",
            "source_type": "social_twitter",
            "description": tweet.get("text", ""),
            "image_url": "",
            "ingredients": [],
            "steps": [],
            "rating": min(5.0, score / 100),
            "difficulty": "medium",
            "prep_time_minutes": None,
            "cook_time_minutes": None,
            "servings": None,
            "tags": ["twitter", "trending"],
            "nutrition": {},
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }
