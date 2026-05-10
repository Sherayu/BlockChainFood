import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from bot import TELEGRAM_BOT_TOKEN
from bot.handlers.commands import (
    start_command, help_command, categories_command,
    regions_command, trending_command, recipes_command,
    ingredients_command, configure_command, status_command, foods_command,
)
from bot.handlers.callbacks import (
    category_callback, region_callback, food_callback,
    recipe_callback, ingredient_action_callback, foods_category_callback,
)
from bot.scheduler.alert_scheduler import AlertScheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")


async def post_init(app):
    scheduler = AlertScheduler(app.bot)
    await scheduler.start()
    logger.info("Alert scheduler started")


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("categories", categories_command))
    app.add_handler(CommandHandler("regions", regions_command))
    app.add_handler(CommandHandler("trending", trending_command))
    app.add_handler(CommandHandler("recipes", recipes_command))
    app.add_handler(CommandHandler("ingredients", ingredients_command))
    app.add_handler(CommandHandler("configure", configure_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("foods", foods_command))

    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat_"))
    app.add_handler(CallbackQueryHandler(region_callback, pattern=r"^reg_"))
    app.add_handler(CallbackQueryHandler(food_callback, pattern=r"^food_\d+"))
    app.add_handler(CallbackQueryHandler(foods_category_callback, pattern=r"^foods_"))
    app.add_handler(CallbackQueryHandler(recipe_callback, pattern=r"^recipe_"))
    app.add_handler(CallbackQueryHandler(ingredient_action_callback, pattern=r"^ing_"))

    app.add_error_handler(error_handler)

    logger.info("Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
