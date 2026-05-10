from celery import shared_task
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fooduser:foodpass123@localhost:5432/food_discovery")


@shared_task(bind=True, max_retries=2)
def snapshot_trending_foods(self):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO trending_food_history (food_name, category, region, popularity_score, trend_velocity, source_count)
            SELECT
                tf.name,
                tf.category,
                tf.region,
                tf.popularity_score,
                tf.trend_velocity,
                COUNT(r.id) AS source_count
            FROM trending_food tf
            LEFT JOIN recipe r ON r.food_id = tf.id
            GROUP BY tf.id, tf.name, tf.category, tf.region, tf.popularity_score, tf.trend_velocity
            ON CONFLICT (food_name, category, snapshot_date) DO NOTHING
        """)
        conn.commit()
        count = cur.rowcount
        return {"snapshot_taken": True, "foods_snapshotted": count}
    except Exception as e:
        conn.rollback()
        raise self.retry(exc=e, countdown=300)
    finally:
        cur.close()
        conn.close()
