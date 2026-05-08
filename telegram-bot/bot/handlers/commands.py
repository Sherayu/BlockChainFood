from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.keyboards.inline import (
    category_keyboard, region_keyboard, trending_food_keyboard,
    recipe_list_keyboard, configure_keyboard,
)
from bot.formatters.message_formatter import (
    format_trending_message, format_recipe_list_message,
    format_recipe_detail_message, format_ingredient_message,
    format_configure_message, format_status_message,
)
import httpx
from bot import API_GATEWAY_URL

API_BASE = f"{API_GATEWAY_URL}/api/v1"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome = (
        f"🍽️ *Welcome to Food Discovery Bot, {user.first_name}!*\n\n"
        "I monitor food trends from blogs, recipe sites, and social media "
        "to bring you the hottest trending foods and recipes every day.\n\n"
        "*Commands:*\n"
        "/categories - Browse food categories\n"
        "/regions - Select cuisine regions\n"
        "/trending - Get trending foods\n"
        "/recipes <food> - Get recipes for a food\n"
        "/ingredients <recipe_id> - Extract and store ingredients\n"
        "/configure - Customize your alerts\n"
        "/status - System status\n"
        "/help - Show all commands"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Food Discovery Bot - Help*\n\n"
        "*Commands:*\n"
        "/start - Initialize the bot\n"
        "/categories - Show available food categories\n"
        "/regions - Show available cuisine regions\n"
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


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍽️ *Select Food Categories*\n\n"
        "Choose one or more categories you're interested in:",
        parse_mode="Markdown",
        reply_markup=category_keyboard(),
    )


async def regions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 *Select Cuisine Regions*\n\n"
        "Choose the cuisine regions you're interested in:",
        parse_mode="Markdown",
        reply_markup=region_keyboard(),
    )


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def recipes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def ingredients_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def configure_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
