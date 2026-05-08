import json
import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisPublisherPipeline:
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_item(self, item, spider):
        self.redis_client.rpush("crawl_results", json.dumps(item, default=str))
        return item
