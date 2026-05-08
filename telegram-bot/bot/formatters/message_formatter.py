from datetime import datetime


def format_trending_message(foods: list, title: str = "🔥 Today's Trending Foods") -> str:
    lines = [f"*{title}*\n"]

    for i, food in enumerate(foods[:10], 1):
        name = food.get("name", "Unknown")
        score = food.get("popularity_score", 0)
        category = food.get("category", "").title()
        region = food.get("region", "Global").title()

        bar = _score_bar(score)
        lines.append(
            f"{i}. *{name}*\n"
            f"   {bar} `{score:.0f}/100` | {category} | {region}\n"
        )

    lines.append("\n_Tap a food to see recipes!_")
    return "\n".join(lines)


def format_recipe_list_message(food_name: str, recipes: list) -> str:
    lines = [f"🍽️ *Top Recipes for {food_name.title()}*\n"]

    if not recipes:
        lines.append("No recipes found yet. Check back soon!")
        return "\n".join(lines)

    for i, recipe in enumerate(recipes[:5], 1):
        title = recipe.get("title", "Unknown")
        rating = recipe.get("rating", 0)
        source = recipe.get("source", "Unknown")
        difficulty = recipe.get("difficulty", "medium").capitalize()
        prep = recipe.get("prep_time_minutes")
        cook = recipe.get("cook_time_minutes")

        stars = "⭐" * int(rating) if rating else ""

        time_info = ""
        if prep or cook:
            time_info = f" | Prep: {prep or '?'}min Cook: {cook or '?'}min"

        lines.append(
            f"{i}. *{title}*\n"
            f"   {stars} | {source} | {difficulty}{time_info}\n"
        )

    lines.append("\n_Tap a recipe to see details!_")
    return "\n".join(lines)


def format_recipe_detail_message(recipe: dict) -> str:
    title = recipe.get("title", "Unknown Recipe")
    source = recipe.get("source", "Unknown")
    rating = recipe.get("rating", 0)
    difficulty = recipe.get("difficulty", "medium").capitalize()
    prep = recipe.get("prep_time_minutes")
    cook = recipe.get("cook_time_minutes")
    servings = recipe.get("servings")
    description = recipe.get("description", "")
    ingredients = recipe.get("ingredients", [])
    steps = recipe.get("steps", [])

    stars = "⭐" * int(rating) if rating else "No rating"
    lines = [f"*{title}*\n", f"*Source:* {source} | {stars}"]
    lines.append(f"*Difficulty:* {difficulty}")

    time_parts = []
    if prep:
        time_parts.append(f"Prep: {prep}min")
    if cook:
        time_parts.append(f"Cook: {cook}min")
    if time_parts:
        lines.append(f"*Time:* {' | '.join(time_parts)}")
    if servings:
        lines.append(f"*Servings:* {servings}")

    if description:
        lines.append(f"\n*Description:*\n{description[:300]}")

    if ingredients:
        lines.append(f"\n*Ingredients ({len(ingredients)}):*")
        for ing in ingredients[:15]:
            name = ing.get("name", "")
            qty = ing.get("quantity", "")
            unit = ing.get("unit", "")
            if qty or unit:
                lines.append(f"• {qty} {unit} {name}".strip())
            else:
                lines.append(f"• {name}")

    if steps:
        lines.append(f"\n*Steps ({len(steps)}):*")
        for i, step in enumerate(steps[:10], 1):
            lines.append(f"{i}. {step[:200]}")

    return "\n".join(lines)


def format_ingredient_message(recipe_id: str, store_data: dict, ingredients: list) -> str:
    status = store_data.get("status", "success")
    count = store_data.get("ingredients_count", 0)

    if status == "success":
        lines = ["✅ *Ingredients Stored Successfully!*\n"]
    else:
        lines = ["⚠️ *Ingredients Extraction Issue*\n"]

    lines.append(f"*Total Ingredients:* {count}\n")

    if ingredients:
        categorized = {}
        for ing in ingredients:
            cat = ing.get("category", "other")
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(ing)

        for category, items in categorized.items():
            emoji = _category_emoji(category)
            lines.append(f"{emoji} *{category.title()}*")
            for item in items:
                name = item.get("name", "")
                qty = item.get("quantity", "")
                unit = item.get("unit", "")
                if qty or unit:
                    lines.append(f"  • {qty} {unit} {name}".strip())
                else:
                    lines.append(f"  • {name}")
            lines.append("")

    lines.append(f"📝 *Recipe ID:* `{recipe_id}`")
    return "\n".join(lines)


def format_configure_message(config: dict) -> str:
    freq = config.get("frequency", "daily")
    categories = config.get("categories", [])
    regions = config.get("regions", [])
    active = config.get("active", True)
    last_sent = config.get("last_sent", "Never")

    lines = ["⚙️ *Current Configuration*\n"]
    lines.append(f"*Frequency:* {freq}")
    lines.append(f"*Categories:* {', '.join(categories) if categories else 'All'}")
    lines.append(f"*Regions:* {', '.join(regions) if regions else 'Global'}")
    lines.append(f"*Active:* {'✅ Yes' if active else '❌ No'}")
    lines.append(f"*Last Alert:* {last_sent}\n")
    lines.append("Use the buttons below to modify settings.")

    return "\n".join(lines)


def format_status_message(crawler: dict, analysis: dict, config: dict) -> str:
    lines = ["📊 *System Status*\n"]

    lines.append("*🕷️ Crawler Service*")
    lines.append(f"Status: {crawler.get('status', 'unknown')}")
    lines.append(f"Active Spiders: {crawler.get('active_spiders', 0)}")
    lines.append(f"Pages Today: {crawler.get('pages_crawled_today', 0)}")
    lines.append(f"Crawl Queue: {crawler.get('queue_size', 0)}\n")

    lines.append("*🔬 Analysis Service*")
    lines.append(f"Status: {analysis.get('status', 'unknown')}")
    lines.append(f"Pending Tasks: {analysis.get('pending_tasks', 0)}")
    lines.append(f"Processed Today: {analysis.get('processed_today', 0)}")
    lines.append(f"Trends Identified: {analysis.get('trends_identified_today', 0)}\n")

    lines.append("*⚙️ Alert Configuration*")
    lines.append(f"Frequency: {config.get('frequency', 'daily')}")
    lines.append(f"Active: {'✅' if config.get('active', True) else '❌'}")

    return "\n".join(lines)


def _score_bar(score: float) -> str:
    filled = max(1, min(10, int(score / 10)))
    return "█" * filled + "░" * (10 - filled)


def _category_emoji(category: str) -> str:
    emojis = {
        "dairy": "🥛",
        "meat": "🥩",
        "seafood": "🐟",
        "vegetable": "🥦",
        "fruit": "🍎",
        "grain": "🌾",
        "spice": "🌶️",
        "condiment": "🫒",
        "other": "📦",
    }
    return emojis.get(category, "📦")
