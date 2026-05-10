import os
import psycopg2
from datetime import datetime, timezone


SPIDER_SOURCE_MAP = {
    "food_blogs": ["Serious Eats", "Bon Appetit", "Epicurious"],
    "rss_feeds": ["Serious Eats", "Bon Appetit", "Epicurious", "Food52", "BBC Good Food", "AllRecipes"],
    "recipe_sites": ["AllRecipes", "Food Network", "BBC Good Food", "Serious Eats"],
}


class CrawlLogPipeline:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.items_count = 0
        self.source_cache = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal="spider_opened")
        crawler.signals.connect(pipeline.spider_closed, signal="spider_closed")
        return pipeline

    def spider_opened(self, spider):
        self.items_count = 0
        db_url = os.getenv("DATABASE_URL", "postgresql://fooduser:foodpass123@postgres:5432/food_discovery")
        try:
            self.conn = psycopg2.connect(db_url)
            self.cursor = self.conn.cursor()
            self._load_source_cache()
        except Exception as e:
            spider.logger.warning(f"[CrawlLogPipeline] Could not connect to DB: {e}")

    def spider_closed(self, spider):
        if not self.cursor:
            return
        try:
            source_names = SPIDER_SOURCE_MAP.get(spider.name, [])
            if not source_names:
                source_name = spider.name.replace("_", " ").title()
                self._insert_log(source_name, spider.name, 200, self.items_count)
            else:
                for name in source_names:
                    self._insert_log(name, spider.name, 200, self.items_count // max(len(source_names), 1))
            self.conn.commit()
        except Exception as e:
            spider.logger.error(f"[CrawlLogPipeline] Error logging crawl: {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()

    def process_item(self, item, spider):
        self.items_count += 1
        return item

    def _load_source_cache(self):
        self.cursor.execute("SELECT id, name FROM crawl_source")
        for row in self.cursor.fetchall():
            self.source_cache[row[1]] = row[0]

    def _insert_log(self, source_name, url_crawled, status_code, items_extracted):
        source_id = self.source_cache.get(source_name)
        if not source_id:
            return
        self.cursor.execute("""
            INSERT INTO crawl_log (source_id, url_crawled, status_code, items_extracted, crawled_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (source_id, url_crawled, status_code, items_extracted, datetime.now(timezone.utc)))
        self.cursor.execute("""
            UPDATE crawl_source SET last_crawl = %s WHERE id = %s
        """, (datetime.now(timezone.utc), source_id))
