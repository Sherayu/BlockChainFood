import scrapy
from datetime import datetime, timezone
from urllib.parse import urljoin


class FoodBlogSpider(scrapy.Spider):
    name = "food_blogs"
    allowed_domains = ["seriouseats.com", "bonappetit.com", "epicurious.com", "food52.com"]

    start_urls = [
        "https://www.seriouseats.com/recipes",
        "https://www.bonappetit.com/recipes",
        "https://www.epicurious.com/recipes-menus",
        "https://food52.com/recipes",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": False,
        "ITEM_PIPELINES": {
            "crawler.pipelines.normalizer.DataNormalizerPipeline": 200,
            "crawler.pipelines.publisher.RedisPublisherPipeline": 300,
        },
    }

    def parse(self, response):
        recipe_links = response.css("a[href*=recipe]::attr(href)").getall()
        recipe_links += response.css("a[href*=recept]::attr(href)").getall()
        recipe_links += response.css("article a::attr(href)").getall()

        seen = set()
        for link in recipe_links:
            url = urljoin(response.url, link)
            if url not in seen and self._is_recipe_url(url):
                seen.add(url)
                yield scrapy.Request(url, callback=self.parse_recipe)

    def parse_recipe(self, response):
        title = response.css("h1::text").get()
        if not title:
            title = response.css("title::text").get()
        if not title:
            return

        description = response.css("meta[name=description]::attr(content)").get()
        image = response.css("meta[property='og:image']::attr(content)").get()

        ingredients = []
        sel_list = [
            "[class*=ingredient] li",
            "[class*=Ingredient] li",
            "[itemprop=recipeIngredient]",
            "[data-testid*=ingredient] li",
        ]
        for sel in sel_list:
            for ing in response.css(sel):
                text = ing.css("::text").get()
                if text:
                    ingredients.append({"name": text.strip(), "quantity": "", "unit": ""})
            if ingredients:
                break

        steps = []
        step_sel_list = [
            "[class*=step] li",
            "[class*=instruction] li",
            "[class*=direction] li",
            "[itemprop=recipeInstructions] li",
        ]
        for sel in step_sel_list:
            for step in response.css(sel):
                text = step.css("::text").get()
                if text:
                    steps.append(text.strip())
            if steps:
                break

        item = {
            "title": title.strip(),
            "url": response.url,
            "source": self._get_source_name(response.url),
            "source_type": "blog",
            "description": description.strip() if description else "",
            "image_url": image if image else "",
            "ingredients": ingredients,
            "steps": steps,
            "rating": self._extract_rating(response),
            "difficulty": self._extract_difficulty(response),
            "prep_time_minutes": self._extract_prep_time(response),
            "cook_time_minutes": self._extract_cook_time(response),
            "servings": self._extract_servings(response),
            "tags": self._extract_tags(response),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

        if not ingredients:
            dynamic = self._try_playwright(response.url)
            if dynamic and dynamic.get("ingredients"):
                item["ingredients"] = dynamic["ingredients"]
                item["steps"] = dynamic.get("steps", item["steps"])
                item["image_url"] = dynamic.get("image_url", item["image_url"])
                item["description"] = dynamic.get("description", item["description"])

        yield item

    def _try_playwright(self, url):
        try:
            from crawler.playwright.dynamic_scraper import DynamicScraper
            scraper = DynamicScraper()
            result = scraper.scrape_sync(url)
            if result and "error" not in result:
                return result
        except Exception:
            pass
        return None

    def _is_recipe_url(self, url):
        skip_patterns = ["/about", "/contact", "/privacy", "/terms", "/login", "/signup", "/category"]
        return not any(p in url for p in skip_patterns)

    def _get_source_name(self, url):
        if "seriouseats" in url:
            return "Serious Eats"
        if "bonappetit" in url:
            return "Bon Appetit"
        if "epicurious" in url:
            return "Epicurious"
        if "food52" in url:
            return "Food52"
        return "Unknown Blog"

    def _extract_rating(self, response):
        rating_text = response.css("[class*=rating]::text").get()
        if rating_text:
            try:
                return float(rating_text.strip())
            except ValueError:
                pass
        return 0.0

    def _extract_difficulty(self, response):
        text = response.css("[class*=difficulty]::text").get()
        if text:
            text = text.strip().lower()
            if text in ("easy", "medium", "hard"):
                return text
        return "medium"

    def _extract_prep_time(self, response):
        return None

    def _extract_cook_time(self, response):
        return None

    def _extract_servings(self, response):
        return None

    def _extract_tags(self, response):
        tags = response.css("[class*=tag]::text, meta[property='article:tag']::attr(content)").getall()
        return [t.strip() for t in tags if t.strip()]
