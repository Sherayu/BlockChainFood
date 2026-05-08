import logging
import httpx
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot import API_GATEWAY_URL

API_BASE = f"{API_GATEWAY_URL}/api/v1"
logger = logging.getLogger(__name__)


class AlertScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        self.scheduler.add_job(
            self.send_daily_alerts,
            trigger="cron",
            hour=8,
            minute=0,
            id="daily_alert",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("Alert scheduler started - daily alerts at 08:00 UTC")

    async def send_daily_alerts(self):
        logger.info("Running daily alert...")

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                config_resp = await client.get(f"{API_BASE}/config/alerts")
                if config_resp.status_code != 200:
                    logger.error("Failed to fetch alert config")
                    return

                config = config_resp.json()
                if not config.get("active", True):
                    logger.info("Alerts are disabled, skipping")
                    return

                categories = config.get("categories", [])
                regions = config.get("regions", [])
                frequency = config.get("frequency", "daily")

                params = {"limit": 10}
                if categories:
                    params["category"] = categories[0]

                foods_resp = await client.get(f"{API_BASE}/foods/trending", params=params)
                if foods_resp.status_code != 200:
                    logger.error("Failed to fetch trending foods")
                    return

                foods = foods_resp.json()
                if not foods:
                    logger.info("No trending foods to alert")
                    return

                for subscriber in await self._get_subscribers():
                    try:
                        await self._send_alert(subscriber, foods, config)
                    except Exception as e:
                        logger.error(f"Failed to send alert to {subscriber}: {e}")

                await client.put(f"{API_BASE}/config/alerts", json={
                    "last_sent": datetime.utcnow().isoformat(),
                })

                logger.info("Daily alert sent successfully")

            except httpx.RequestError as e:
                logger.error(f"API request failed: {e}")
            except Exception as e:
                logger.error(f"Alert scheduler error: {e}")

    async def _get_subscribers(self) -> list:
        return []

    async def _send_alert(self, user_id: int, foods: list, config: dict):
        lines = ["🌅 *Good Morning! Here's Your Daily Food Digest*\n"]

        for i, food in enumerate(foods[:5], 1):
            name = food.get("name", "Unknown")
            score = food.get("popularity_score", 0)
            category = food.get("category", "").title()

            lines.append(
                f"{i}. *{name}* 🔥 {score:.0f}/100\n"
                f"   Category: {category}\n"
            )

        lines.append("\n_Tap below to see recipes!_")

        keyboard = []
        for food in foods[:5]:
            keyboard.append([
                InlineKeyboardButton(
                    f"🍽️ {food.get('name', 'Unknown')} Recipes",
                    callback_data=f"food_{food['id']}",
                )
            ])

        keyboard.append([InlineKeyboardButton("🔕 Configure Alerts", callback_data="cfg_freq")])

        await self.bot.send_message(
            chat_id=user_id,
            text="\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
