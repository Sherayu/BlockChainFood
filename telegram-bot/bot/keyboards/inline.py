from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def category_keyboard() -> InlineKeyboardMarkup:
    categories = [
        ("🍰 Desserts", "cat_desserts"),
        ("🥗 Starters", "cat_starters"),
        ("🍛 Main Course", "cat_main-course"),
        ("🥖 Baking", "cat_baking"),
        ("☕ Beverages", "cat_beverages"),
        ("🍿 Snacks", "cat_snacks"),
    ]

    keyboard = []
    for i in range(0, len(categories), 2):
        row = []
        for emoji, data in categories[i:i+2]:
            row.append(InlineKeyboardButton(emoji, callback_data=data))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def region_keyboard() -> InlineKeyboardMarkup:
    regions = [
        ("🇮🇳 Indian", "reg_indian"),
        ("🌏 South Asian", "reg_south-asian"),
        ("🌮 Mexican", "reg_mexican"),
        ("🍝 Italian", "reg_italian"),
        ("🥟 East Asian", "reg_east-asian"),
        ("🥙 Mediterranean", "reg_mediterranean"),
        ("🌍 Global", "reg_global"),
    ]

    keyboard = []
    for i in range(0, len(regions), 2):
        row = []
        for flag, data in regions[i:i+2]:
            row.append(InlineKeyboardButton(flag, callback_data=data))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def trending_food_keyboard(foods: list) -> InlineKeyboardMarkup:
    keyboard = []
    for food in foods[:10]:
        display = f"{food.get('name', 'Unknown')} (🔥 {food.get('popularity_score', 0):.0f})"
        keyboard.append([
            InlineKeyboardButton(display, callback_data=f"food_{food['id']}")
        ])
    return InlineKeyboardMarkup(keyboard)


def recipe_list_keyboard(recipes: list) -> InlineKeyboardMarkup:
    keyboard = []
    for i, recipe in enumerate(recipes[:5], 1):
        rating = recipe.get("rating", 0)
        stars = "⭐" * int(rating) if rating else ""
        title = recipe.get("title", f"Recipe {i}")
        display = f"{i}. {title[:40]} {stars}".strip()
        keyboard.append([
            InlineKeyboardButton(display, callback_data=f"recipe_{recipe['id']}")
        ])
    return InlineKeyboardMarkup(keyboard)


def foods_category_keyboard() -> InlineKeyboardMarkup:
    categories = [
        ("🍰 Desserts", "foods_desserts"),
        ("🥗 Starters", "foods_starters"),
        ("🍛 Main Course", "foods_main-course"),
        ("🥖 Baking", "foods_baking"),
        ("☕ Beverages", "foods_beverages"),
        ("🍿 Snacks", "foods_snacks"),
    ]
    keyboard = []
    for i in range(0, len(categories), 2):
        row = []
        for emoji, data in categories[i:i+2]:
            row.append(InlineKeyboardButton(emoji, callback_data=data))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def configure_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🕐 Change Frequency", callback_data="cfg_freq")],
        [InlineKeyboardButton("🍽️ Change Categories", callback_data="cfg_cat")],
        [InlineKeyboardButton("🌍 Change Regions", callback_data="cfg_reg")],
        [InlineKeyboardButton("🔕 Toggle Alerts", callback_data="cfg_toggle")],
        [InlineKeyboardButton("✅ Done", callback_data="cfg_done")],
    ]
    return InlineKeyboardMarkup(keyboard)
