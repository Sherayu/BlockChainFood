from celery import shared_task
import json
import redis
import os
import psycopg2
from datetime import datetime, timezone

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fooduser:foodpass123@localhost:5432/food_discovery")


@shared_task(bind=True, max_retries=3)
def process_crawl_data(self):
    r = redis.from_url(REDIS_URL)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    processed = 0

    try:
        while True:
            raw = r.lpop("crawl_results")
            if not raw:
                break

            try:
                item = json.loads(raw)
                _store_item(cur, item)
                conn.commit()
                processed += 1
            except Exception as e:
                conn.rollback()
                print(f"[Analysis] Error processing item: {e}")

        if processed > 0:
            detect_food_trends.delay()
    finally:
        cur.close()
        conn.close()
        r.close()

    return {"processed": processed}


def _store_item(cur, item):
    cur.execute("""
        INSERT INTO recipe (id, food_id, title, url, source, source_type, rating,
                           difficulty, prep_time_minutes, cook_time_minutes, servings,
                           thumbnail_url, description, ingredients, steps, tags, nutrition, created_at)
        VALUES (gen_random_uuid(), NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        item.get("title", ""),
        item.get("url", ""),
        item.get("source", ""),
        item.get("source_type", "recipe_site"),
        item.get("rating", 0.0),
        item.get("difficulty", "medium"),
        item.get("prep_time_minutes"),
        item.get("cook_time_minutes"),
        item.get("servings"),
        item.get("image_url", ""),
        item.get("description", ""),
        json.dumps(item.get("ingredients", [])),
        json.dumps(item.get("steps", [])),
        json.dumps(item.get("tags", [])),
        json.dumps(item.get("nutrition", {})),
        datetime.now(timezone.utc),
    ))


from analysis.tasks.detect_trends import detect_food_trends
