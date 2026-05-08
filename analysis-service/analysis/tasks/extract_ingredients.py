from celery import shared_task
import psycopg2
import psycopg2.extras
import os
import json
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fooduser:foodpass123@localhost:5432/food_discovery")


@shared_task(bind=True, max_retries=3)
def extract_ingredients_task(self, recipe_id: str):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    stored = []

    try:
        cur.execute("SELECT * FROM recipe WHERE id = %s", (recipe_id,))
        recipe = cur.fetchone()

        if not recipe:
            return {"error": f"Recipe {recipe_id} not found"}

        raw_ingredients = recipe.get("ingredients") or []
        if isinstance(raw_ingredients, str):
            raw_ingredients = json.loads(raw_ingredients)

        for item in raw_ingredients:
            name = item.get("name", "")
            if not name:
                continue

            category = _categorize_ingredient(name)

            cur.execute("""
                INSERT INTO stored_ingredient (id, recipe_id, name, quantity, unit, category, notes, stored_at)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                recipe_id,
                name,
                item.get("quantity", ""),
                item.get("unit", ""),
                category,
                "",
                datetime.now(timezone.utc),
            ))

            ing_id = cur.fetchone()
            if ing_id:
                stored.append({"id": str(ing_id["id"]), "name": name, "category": category})

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

    return {
        "recipe_id": recipe_id,
        "ingredients_count": len(stored),
        "status": "success" if stored else "failed",
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "ingredients": stored,
    }


def _categorize_ingredient(name: str) -> str:
    name_lower = name.lower()

    dairy = ["milk", "cream", "butter", "cheese", "yogurt", "paneer", "ghee", "curd"]
    meat = ["chicken", "beef", "pork", "lamb", "mutton", "bacon", "ham", "turkey", "duck", "sausage"]
    seafood = ["fish", "shrimp", "prawn", "salmon", "tuna", "crab", "lobster", "mussel", "clam"]
    vegetable = ["onion", "garlic", "tomato", "potato", "carrot", "broccoli", "spinach", "pepper",
                 "mushroom", "cucumber", "lettuce", "cabbage", "celery", "zucchini", "eggplant"]
    fruit = ["apple", "banana", "orange", "lemon", "lime", "berry", "mango", "pineapple",
             "watermelon", "grape", "avocado", "cherry", "peach", "plum", "strawberry"]
    grain = ["rice", "flour", "pasta", "bread", "oat", "quinoa", "barley", "wheat", "corn",
             "noodle", "spaghetti", "couscous", "lentil", "bean", "chickpea"]
    spice = ["salt", "pepper", "cumin", "turmeric", "chili", "cinnamon", "paprika", "ginger",
             "garlic powder", "oregano", "basil", "thyme", "rosemary", "cardamom", "clove",
             "nutmeg", "coriander", "mustard", "vanilla", "bay leaf"]

    for item in dairy:
        if item in name_lower:
            return "dairy"
    for item in meat:
        if item in name_lower:
            return "meat"
    for item in seafood:
        if item in name_lower:
            return "seafood"
    for item in vegetable:
        if item in name_lower:
            return "vegetable"
    for item in fruit:
        if item in name_lower:
            return "fruit"
    for item in grain:
        if item in name_lower:
            return "grain"
    for item in spice:
        if item in name_lower:
            return "spice"

    return "other"
