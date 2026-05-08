import scrapy
from datetime import datetime, timezone
from urllib.parse import urljoin
import feedparser
import hashlib


class RSSSpider(scrapy.Spider):
    name = "rss_feeds"

    feed_urls = [
        "https://www.seriouseats.com/feed",
        "https://www.bonappetit.com/feed",
        "https://www.epicurious.com/feed",
        "https://food52.com/feed",
        "https://www.bbcgoodfood.com/feed",
        "https://www.allrecipes.com/rss/allrecipes.xml",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 5,
        "CONCURRENT_REQUESTS": 1,
    }

    def start_requests(self):
        for feed_url in self.feed_urls:
            yield scrapy.Request(feed_url, callback=self.parse_feed, priority=10)

    def parse_feed(self, response):
        feed = feedparser.parse(response.text)
        source = self._get_source_name(response.url)

        for entry in feed.entries[:20]:
            link = entry.get("link", "")
            title = entry.get("title", "")
            if not title or not link:
                continue

            yield scrapy.Request(
                url=link,
                callback=self.parse_article,
                meta={
                    "source": source,
                    "feed_title": title,
                    "feed_summary": entry.get("summary", ""),
                    "feed_published": entry.get("published", ""),
                    "feed_tags": [t.get("term", "") for t in entry.get("tags", []) if isinstance(t, dict)],
                },
                priority=5,
            )

    def parse_article(self, response):
        title = response.meta.get("feed_title") or response.css("h1::text").get() or ""
        if not title:
            return

        description = response.meta.get("feed_summary") or response.css("meta[name=description]::attr(content)").get() or ""
        image = response.css("meta[property=og:image]::attr(content)").get() or ""

        ingredients = []
        for ing in response.css("[class*=ingredient] li, [class*=Ingredient] li"):
            text = ing.css("::text").get()
            if text:
                ingredients.append({"name": text.strip(), "quantity": "", "unit": ""})

        steps = []
        for step in response.css("[class*=step] li, [class*=instruction] li"):
            text = step.css("::text").get()
            if text:
                steps.append(text.strip())

        tags = response.meta.get("feed_tags", [])
        tags += response.css("[class*=tag]::text, meta[property=article:tag]::attr(content)").getall()

        yield {
            "title": title.strip(),
            "url": response.url,
            "source": response.meta.get("source", "RSS Feed"),
            "source_type": "rss",
            "description": description.strip() if description else "",
            "image_url": image,
            "ingredients": ingredients,
            "steps": steps,
            "rating": 0.0,
            "difficulty": "medium",
            "prep_time_minutes": None,
            "cook_time_minutes": None,
            "servings": None,
            "tags": list(set(tags)) if tags else [],
            "nutrition": {},
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_source_name(self, url):
        if "seriouseats" in url:
            return "Serious Eats"
        if "bonappetit" in url:
            return "Bon Appetit"
        if "epicurious" in url:
            return "Epicurious"
        if "food52" in url:
            return "Food52"
        if "bbcgoodfood" in url:
            return "BBC Good Food"
        if "allrecipes" in url:
            return "AllRecipes"
        return "Unknown RSS"
