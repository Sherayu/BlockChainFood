from playwright.async_api import async_playwright
import asyncio
import json
from datetime import datetime, timezone
import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class DynamicScraper:
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL)

    async def scrape_recipe_page(self, url: str) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                title = await page.title()
                content = await page.content()

                ingredients = await page.eval_on_selector_all(
                    "[class*=ingredient] li, [class*=Ingredient] li",
                    "elements => elements.map(el => el.textContent.trim())",
                )

                steps = await page.eval_on_selector_all(
                    "[class*=step] li, [class*=instruction] li, [class*=direction] li",
                    "elements => elements.map(el => el.textContent.trim())",
                )

                image = await page.eval_on_selector(
                    "meta[property=og:image]",
                    "el => el.content",
                )

                description = await page.eval_on_selector(
                    "meta[name=description]",
                    "el => el.content",
                )

                result = {
                    "title": title,
                    "url": url,
                    "source": self._get_source(url),
                    "source_type": "recipe_site",
                    "description": description or "",
                    "image_url": image or "",
                    "ingredients": [{"name": i} for i in ingredients if i],
                    "steps": [s for s in steps if s],
                    "rating": 0.0,
                    "difficulty": "medium",
                    "prep_time_minutes": None,
                    "cook_time_minutes": None,
                    "servings": None,
                    "tags": [],
                    "nutrition": {},
                    "crawled_at": datetime.now(timezone.utc).isoformat(),
                }

                self.redis_client.rpush("crawl_results", json.dumps(result))
                return result

            except Exception as e:
                return {"error": str(e), "url": url}
            finally:
                await browser.close()

    def scrape_sync(self, url: str) -> dict:
        return asyncio.run(self.scrape_recipe_page(url))

    def _get_source(self, url: str) -> str:
        if "tasty" in url:
            return "Tasty"
        if "pinterest" in url:
            return "Pinterest"
        if "instagram" in url:
            return "Instagram"
        return "Dynamic Source"
