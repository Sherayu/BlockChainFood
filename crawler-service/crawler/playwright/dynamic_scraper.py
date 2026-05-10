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

    JS_HEAVY_SITES = [
        "https://www.seriouseats.com/recipes",
    ]

    async def scrape_listing(self, url: str, max_pages: int = 3) -> list:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            links = []
            try:
                for _ in range(max_pages):
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(3000)
                    page_links = await page.eval_on_selector_all(
                        "a[href*=recipe], a[href*=recept], article a",
                        "elements => elements.map(el => el.href).filter(h => h)",
                    )
                    links.extend(page_links)
                    next_btn = await page.query_selector("a[rel=next], .pagination a")
                    if not next_btn:
                        break
                    await next_btn.click()
                    await page.wait_for_timeout(2000)
            except Exception:
                pass
            finally:
                await browser.close()
            return list(set(links))

    async def batch_scrape(self, urls: list) -> list:
        results = []
        for url in urls:
            result = await self.scrape_recipe_page(url)
            if result and "error" not in result:
                results.append(result)
        return results

    def scrape_sync(self, url: str) -> dict:
        return asyncio.run(self.scrape_recipe_page(url))

    def batch_scrape_sync(self, urls: list) -> list:
        return asyncio.run(self.batch_scrape(urls))

    def scrape_listing_sync(self, url: str, max_pages: int = 3) -> list:
        return asyncio.run(self.scrape_listing(url, max_pages))

    def _get_source(self, url: str) -> str:
        if "seriouseats" in url:
            return "Serious Eats"
        if "foodnetwork" in url:
            return "Food Network"
        if "allrecipes" in url:
            return "AllRecipes"
        if "tasty" in url:
            return "Tasty"
        if "pinterest" in url:
            return "Pinterest"
        if "instagram" in url:
            return "Instagram"
        if "bonappetit" in url:
            return "Bon Appetit"
        if "epicurious" in url:
            return "Epicurious"
        if "food52" in url:
            return "Food52"
        if "bbcgoodfood" in url:
            return "BBC Good Food"
        return "Dynamic Source"
