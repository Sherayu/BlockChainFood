from celery import shared_task
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timezone
from collections import Counter
import json

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fooduser:foodpass123@localhost:5432/food_discovery")


@shared_task(bind=True, max_retries=3)
def detect_food_trends(self):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    trends = []

    try:
        cur.execute("""
            SELECT title, source, source_type, tags, ingredients,
                   rating, url, description, thumbnail_url
            FROM recipe
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        recipes = cur.fetchall()

        if not recipes:
            return {"trends_identified": 0}

        title_words = []
        tag_counts = Counter()
        source_counts = Counter()

        for recipe in recipes:
            words = recipe["title"].lower().split()
            title_words.extend(words)

            tags = recipe.get("tags") or []
            if isinstance(tags, str):
                tags = json.loads(tags)
            for tag in tags:
                tag_counts[tag] += 1

            source_counts[recipe["source_type"]] += 1

        title_freq = Counter(title_words)
        common_words = {"the", "a", "an", "and", "or", "in", "of", "to", "with",
                        "is", "for", "on", "at", "by", "from", "this", "that",
                        "best", "easy", "quick", "new", "how", "make", "recipe"}

        food_keywords = [word for word, count in title_freq.most_common(50)
                        if word not in common_words and len(word) > 3 and count > 1]

        for keyword in food_keywords[:10]:
            keyword_recipes = [r for r in recipes if keyword in r["title"].lower()]
            score = len(keyword_recipes) * 10

            for recipe in keyword_recipes:
                if recipe.get("rating"):
                    score += float(recipe["rating"]) * 2

            source_urls = [r["url"] for r in keyword_recipes[:5]]

            category = _infer_category(keyword, keyword_recipes)

            cur.execute("""
                INSERT INTO trending_food (id, name, category, region, popularity_score,
                                          trend_velocity, source_urls, description, image_url, discovered_at)
                VALUES (gen_random_uuid(), %s, %s, 'global', %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (
                keyword.title(),
                category,
                min(100, score),
                min(50, score * 0.3),
                json.dumps(source_urls),
                keyword_recipes[0].get("description", "")[:500] if keyword_recipes else "",
                keyword_recipes[0].get("thumbnail_url", "") if keyword_recipes else "",
                datetime.now(timezone.utc),
            ))

            trend_id = cur.fetchone()
            if trend_id:
                tid = trend_id["id"]
                cur.execute("""
                    UPDATE recipe
                    SET food_id = %s
                    WHERE food_id IS NULL
                      AND LOWER(title) LIKE %s
                """, (tid, f"%{keyword}%"))
                trends.append({
                    "name": keyword.title(),
                    "id": str(tid),
                    "score": min(100, score),
                })

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

    return {"trends_identified": len(trends), "trends": trends}


def _infer_category(keyword: str, recipes: list) -> str:
    category_map = {
        "desserts": ["dessert", "cake", "cookie", "pie", "ice cream", "pudding", "brownie", "chocolate", "sweet", "pastry"],
        "baking": ["bake", "bread", "muffin", "scone", "croissant", "dough", "loaf"],
        "starters": ["appetizer", "starter", "soup", "salad", "dip", "finger food", "snack"],
        "main-course": ["chicken", "beef", "pork", "pasta", "curry", "steak", "roast", "grill", "stir-fry", "rice"],
        "beverages": ["drink", "smoothie", "cocktail", "juice", "tea", "coffee"],
        "snacks": ["snack", "finger", "bite", "wrap", "roll", "popcorn", "chip"],
    }

    keyword_lower = keyword.lower()
    for category, keywords in category_map.items():
        for k in keywords:
            if k in keyword_lower or keyword_lower in k:
                return category

    for recipe in recipes:
        title = recipe["title"].lower()
        for category, keywords in category_map.items():
            for k in keywords:
                if k in title:
                    return category

    return "main-course"
