from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.keyboards.inline import (
    category_keyboard, region_keyboard, trending_food_keyboard,
    recipe_list_keyboard, configure_keyboard, foods_category_keyboard,
)
from bot.formatters.message_formatter import (
    format_trending_message, format_recipe_list_message,
    format_recipe_detail_message, format_ingredient_message,
    format_configure_message, format_status_message, format_foods_message,
)
import httpx
import time
from bot import API_GATEWAY_URL

API_BASE = f"{API_GATEWAY_URL}/api/v1"


async def _log_usage(command: str, update: Update, start_time: float):
    try:
        user = update.effective_user
        args = update.message.text.split() if update.message and update.message.text else []
        params = " ".join(args[1:]) if len(args) > 1 else None
        elapsed = int((time.time() - start_time) * 1000)
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{API_BASE}/analytics/bot/log", json={
                "command": command,
                "user_id": user.id if user else 0,
                "username": user.username if user else None,
                "parameters": params,
                "response_time_ms": elapsed,
            })
    except Exception:
        pass


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    user = update.effective_user
    welcome = (
        f"🍽️ *Welcome to Food Discovery Bot, {user.first_name}!*\n\n"
        "I monitor food trends from blogs, recipe sites, and social media "
        "to bring you the hottest trending foods and recipes every day.\n\n"
        "*Commands:*\n"
        "/categories - Browse food categories\n"
        "/regions - Select cuisine regions\n"
        "/foods <category> - Browse foods by category\n"
        "/trending - Get trending foods\n"
        "/recipes <food> - Get recipes for a food\n"
        "/ingredients <recipe_id> - Extract and store ingredients\n"
        "/configure - Customize your alerts\n"
        "/status - System status\n"
        "/help - Show all commands"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")
    await _log_usage("start", update, _start)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    help_text = (
        "🤖 *Food Discovery Bot - Help*\n\n"
        "*Commands:*\n"
        "/start - Initialize the bot\n"
        "/categories - Show available food categories\n"
        "/regions - Show available cuisine regions\n"
        "/foods <category> - Browse foods by category (e.g., /foods desserts)\n"
        "/trending - List current trending foods\n"
        "/trending <category> - Filter by category (e.g., /trending desserts)\n"
        "/recipes <food_name> - Get top 5 recipes for a food\n"
        "/ingredients <recipe_id> - Extract ingredients for a recipe\n"
        "/configure - Configure alert preferences\n"
        "/status - View system status\n"
        "/help - Show this message\n\n"
        "*Inline Buttons:* Use them to navigate and select options!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")
    await _log_usage("help", update, _start)


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    await update.message.reply_text(
        "🍽️ *Select Food Categories*\n\n"
        "Choose one or more categories you're interested in:",
        parse_mode="Markdown",
        reply_markup=category_keyboard(),
    )
    await _log_usage("categories", update, _start)


async def regions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    await update.message.reply_text(
        "🌍 *Select Cuisine Regions*\n\n"
        "Choose the cuisine regions you're interested in:",
        parse_mode="Markdown",
        reply_markup=region_keyboard(),
    )
    await _log_usage("regions", update, _start)


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    category = context.args[0] if context.args else None

    params = {"limit": 10}
    if category:
        params["category"] = category

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{API_BASE}/foods/trending", params=params)
            if resp.status_code == 200:
                foods = resp.json()
                if not foods:
                    await update.message.reply_text(
                        "No trending foods found right now. The crawler may still be collecting data."
                    )
                    return

                message = format_trending_message(foods)
                keyboard = trending_food_keyboard(foods)
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                await update.message.reply_text("Failed to fetch trending foods. Please try again later.")
        except httpx.RequestError:
            await update.message.reply_text("Cannot connect to the API. Is the service running?")
    await _log_usage("trending", update, _start)


async def recipes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    if not context.args:
        await update.message.reply_text("Please specify a food name: /recipes <food_name>")
        return

    food_name = " ".join(context.args).lower()

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            foods_resp = await client.get(f"{API_BASE}/foods/trending", params={"limit": 20})
            if foods_resp.status_code != 200:
                await update.message.reply_text("Failed to fetch food data.")
                return

            foods = foods_resp.json()
            matched_food = None
            for food in foods:
                if food_name in food["name"].lower():
                    matched_food = food
                    break

            if not matched_food:
                await update.message.reply_text(
                    f"No food found matching '{food_name}'. Try /trending to see available foods."
                )
                return

            recipes_resp = await client.get(f"{API_BASE}/foods/{matched_food['id']}/recipes")
            if recipes_resp.status_code == 200:
                recipes = recipes_resp.json()
                message = format_recipe_list_message(matched_food["name"], recipes)
                keyboard = recipe_list_keyboard(recipes)
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                await update.message.reply_text("No recipes found for this food.")
        except httpx.RequestError:
            await update.message.reply_text("Cannot connect to the API.")
    await _log_usage("recipes", update, _start)


async def ingredients_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    if not context.args:
        await update.message.reply_text("Please specify a recipe ID: /ingredients <recipe_id>")
        return

    recipe_id = context.args[0]

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(f"{API_BASE}/recipes/{recipe_id}/ingredients")
            if resp.status_code == 201:
                data = resp.json()
                ingredients_resp = await client.get(f"{API_BASE}/recipes/{recipe_id}/ingredients")
                ingredients = ingredients_resp.json() if ingredients_resp.status_code == 200 else []

                message = format_ingredient_message(recipe_id, data, ingredients)
                await update.message.reply_text(message, parse_mode="Markdown")
            elif resp.status_code == 404:
                await update.message.reply_text("Recipe not found. Please check the recipe ID.")
            else:
                await update.message.reply_text("Failed to extract ingredients. Please try again.")
        except httpx.RequestError:
            await update.message.reply_text("Cannot connect to the API.")
    await _log_usage("ingredients", update, _start)


async def foods_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    category = " ".join(context.args).lower() if context.args else None

    if not category:
        await update.message.reply_text(
            "🍽️ *Browse Foods by Category*\n\n"
            "Select a category below to see available foods:",
            parse_mode="Markdown",
            reply_markup=foods_category_keyboard(),
        )
        return

    params = {"category": category, "limit": 10}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{API_BASE}/foods/trending", params=params)
            if resp.status_code == 200:
                foods = resp.json()
                if not foods:
                    await update.message.reply_text(
                        f"No foods found in category '{category}'. "
                        "Try a different category with /foods <category>."
                    )
                    return
                message = format_foods_message(category, foods)
                await update.message.reply_text(message, parse_mode="Markdown")
            else:
                await update.message.reply_text(
                    "Failed to fetch foods. Please try again later."
                )
        except httpx.RequestError:
            await update.message.reply_text("Cannot connect to the API. Is the service running?")
    await _log_usage("foods", update, _start)


async def configure_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{API_BASE}/config/alerts")
            if resp.status_code == 200:
                config = resp.json()
                message = format_configure_message(config)
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown",
                    reply_markup=configure_keyboard(),
                )
            else:
                await update.message.reply_text("Failed to fetch configuration.")
        except httpx.RequestError:
            await update.message.reply_text("Cannot connect to the API.")
    await _log_usage("configure", update, _start)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _start = time.time()
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            crawler_resp = await client.get(f"{API_BASE}/crawler/status")
            analysis_resp = await client.get(f"{API_BASE}/analysis/status")
            config_resp = await client.get(f"{API_BASE}/config/alerts")

            crawler = crawler_resp.json() if crawler_resp.status_code == 200 else {}
            analysis = analysis_resp.json() if analysis_resp.status_code == 200 else {}
            config = config_resp.json() if config_resp.status_code == 200 else {}

            message = format_status_message(crawler, analysis, config)
            await update.message.reply_text(message, parse_mode="Markdown")
        except httpx.RequestError:
            await update.message.reply_text("Cannot connect to the API.")
    await _log_usage("status", update, _start)
