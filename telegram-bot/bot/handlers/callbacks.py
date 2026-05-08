from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.inline import trending_food_keyboard, recipe_list_keyboard
from bot.formatters.message_formatter import format_trending_message, format_recipe_list_message
import httpx
from bot import API_GATEWAY_URL

API_BASE = f"{API_GATEWAY_URL}/api/v1"


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    category = query.data.replace("cat_", "")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{API_BASE}/foods/trending", params={"category": category, "limit": 10})
            if resp.status_code == 200:
                foods = resp.json()
                if not foods:
                    await query.edit_message_text(
                        f"No trending foods found in '{category}' category."
                    )
                    return
                message = format_trending_message(foods, f"Trending {category.title()}")
                keyboard = trending_food_keyboard(foods)
                await query.edit_message_text(message, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await query.edit_message_text("Failed to fetch foods for this category.")
        except httpx.RequestError:
            await query.edit_message_text("Cannot connect to the API.")


async def region_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    region = query.data.replace("reg_", "")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{API_BASE}/foods/trending", params={"region": region, "limit": 10})
            if resp.status_code == 200:
                foods = resp.json()
                if not foods:
                    await query.edit_message_text(
                        f"No trending foods found for '{region}' region."
                    )
                    return
                message = format_trending_message(foods, f"{region.title()} Trending Foods")
                keyboard = trending_food_keyboard(foods)
                await query.edit_message_text(message, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await query.edit_message_text("Failed to fetch foods for this region.")
        except httpx.RequestError:
            await query.edit_message_text("Cannot connect to the API.")


async def food_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    food_id = query.data.replace("food_", "")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            foods_resp = await client.get(f"{API_BASE}/foods/trending", params={"limit": 1})
            if foods_resp.status_code != 200:
                await query.edit_message_text("Failed to fetch food details.")
                return

            recipes_resp = await client.get(f"{API_BASE}/foods/{food_id}/recipes")
            if recipes_resp.status_code == 200:
                recipes = recipes_resp.json()
                if not recipes:
                    await query.edit_message_text("No recipes available for this food.")
                    return

                food_name = recipes[0].get("title", "selected food") if recipes else "Food"
                message = format_recipe_list_message(food_name, recipes)
                keyboard = recipe_list_keyboard(recipes)
                await query.edit_message_text(message, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await query.edit_message_text("No recipes found.")
        except httpx.RequestError:
            await query.edit_message_text("Cannot connect to the API.")


async def recipe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    recipe_id = query.data.replace("recipe_", "")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{API_BASE}/recipes/{recipe_id}")
            if resp.status_code == 200:
                recipe = resp.json()

                from bot.formatters.message_formatter import format_recipe_detail_message
                message = format_recipe_detail_message(recipe)

                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 Extract Ingredients", callback_data=f"ing_{recipe_id}"),
                        InlineKeyboardButton("🔗 Open Recipe", url=recipe.get("url", "")),
                    ],
                    [InlineKeyboardButton("◀️ Back to Recipes", callback_data=f"back_{recipe.get('food_id', '')}")],
                ])

                await query.edit_message_text(message, parse_mode="Markdown", reply_markup=keyboard, disable_web_page_preview=True)
            else:
                await query.edit_message_text("Recipe not found.")
        except httpx.RequestError:
            await query.edit_message_text("Cannot connect to the API.")


async def ingredient_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    recipe_id = query.data.replace("ing_", "")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(f"{API_BASE}/recipes/{recipe_id}/ingredients")
            if resp.status_code == 201:
                data = resp.json()
                ingredients_resp = await client.get(f"{API_BASE}/recipes/{recipe_id}/ingredients")
                ingredients = ingredients_resp.json() if ingredients_resp.status_code == 200 else []

                from bot.formatters.message_formatter import format_ingredient_message
                message = format_ingredient_message(recipe_id, data, ingredients)
                await query.edit_message_text(message, parse_mode="Markdown")
            else:
                await query.edit_message_text("Failed to extract ingredients. Please try again.")
        except httpx.RequestError:
            await query.edit_message_text("Cannot connect to the API.")
