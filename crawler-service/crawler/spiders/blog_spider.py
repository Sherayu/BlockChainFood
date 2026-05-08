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
        image = response.css("meta[property=og:image]::attr(content)").get()

        ingredients = []
        for ing in response.css("[class*=ingredient] li, [class*=Ingredient] li"):
            text = ing.css("::text").get()
            if text:
                ingredients.append({"name": text.strip(), "quantity": "", "unit": ""})

        steps = []
        for step in response.css("[class*=step] li, [class*=instruction] li, [class*=direction] li"):
            text = step.css("::text").get()
            if text:
                steps.append(text.strip())

        yield {
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
        tags = response.css("[class*=tag]::text, meta[property=article:tag]::attr(content)").getall()
        return [t.strip() for t in tags if t.strip()]
