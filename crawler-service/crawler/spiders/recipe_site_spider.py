import scrapy
from datetime import datetime, timezone
from urllib.parse import urljoin
import json
import re


class RecipeSiteSpider(scrapy.Spider):
    name = "recipe_sites"
    allowed_domains = [
        "allrecipes.com", "foodnetwork.com",
        "bbcgoodfood.com", "tasty.co",
    ]

    start_urls = [
        "https://www.allrecipes.com/recipes",
        "https://www.foodnetwork.com/recipes",
        "https://www.bbcgoodfood.com/recipes",
        "https://tasty.co/recipes",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        for href in response.css("a::attr(href)").getall():
            url = urljoin(response.url, href)
            if self._is_recipe_page(url):
                yield scrapy.Request(url, callback=self.parse_recipe)

        next_page = response.css("a[rel=next]::attr(href), .pagination a::attr(href)").get()
        if next_page:
            yield scrapy.Request(urljoin(response.url, next_page))

    def parse_recipe(self, response):
        schema_data = self._extract_schema(response)
        if schema_data:
            return self._process_schema(schema_data, response.url)

        return self._extract_from_html(response)

    def _is_recipe_page(self, url):
        if re.search(r'/(recipe|recept)/\d+/', url) or re.search(r'/recipe/', url):
            return True
        return False

    def _extract_schema(self, response):
        for script in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Recipe":
                            return item
                elif isinstance(data, dict) and data.get("@type") == "Recipe":
                    return data
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def _process_schema(self, data, url):
        ingredients = []
        for ing in data.get("recipeIngredient", []):
            parts = self._parse_ingredient(ing)
            ingredients.append(parts)

        steps = []
        for step_data in data.get("recipeInstructions", []):
            if isinstance(step_data, dict):
                steps.append(step_data.get("text", ""))
            elif isinstance(step_data, str):
                steps.append(step_data)

        return {
            "title": data.get("name", ""),
            "url": url,
            "source": self._get_source(url),
            "source_type": "recipe_site",
            "description": data.get("description", ""),
            "image_url": self._extract_image(data),
            "ingredients": ingredients,
            "steps": steps,
            "rating": data.get("aggregateRating", {}).get("ratingValue", 0.0) if isinstance(data.get("aggregateRating"), dict) else 0.0,
            "difficulty": self._infer_difficulty(data),
            "prep_time_minutes": self._parse_time(data.get("prepTime")),
            "cook_time_minutes": self._parse_time(data.get("cookTime")),
            "servings": self._parse_servings(data.get("recipeYield")),
            "tags": data.get("keywords", "").split(",") if data.get("keywords") else [],
            "nutrition": data.get("nutrition", {}),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

    def _extract_from_html(self, response):
        title = response.css("h1::text").get()
        if not title:
            title = response.css("title::text").get()
        if not title:
            return

        ingredients = []
        for li in response.css("[class*=ingredient] li, .ingredients-list li, .recipe-ingredients li"):
            text = li.css("::text").get()
            if text:
                parts = self._parse_ingredient(text.strip())
                ingredients.append(parts)

        steps = []
        for li in response.css("[class*=instruction] li, [class*=step] li, .recipe-method li"):
            text = li.css("::text").get()
            if text:
                steps.append(text.strip())

        return {
            "title": title.strip(),
            "url": response.url,
            "source": self._get_source(response.url),
            "source_type": "recipe_site",
            "description": response.css("meta[name=description]::attr(content)").get() or "",
            "image_url": response.css("meta[property=og:image]::attr(content)").get() or "",
            "ingredients": ingredients,
            "steps": steps,
            "rating": 0.0,
            "difficulty": "medium",
            "prep_time_minutes": None,
            "cook_time_minutes": None,
            "servings": None,
            "tags": [],
            "nutrition": {},
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

    def _parse_ingredient(self, text):
        pattern = r'^([\d\s\/\.]+)?\s*([a-zA-Z\s]+)?\s*[-–]?\s*(.+)$'
        match = re.match(pattern, text.strip())
        if match:
            quantity = match.group(1) or ""
            unit = ""
            name = match.group(3) or text.strip()
            return {"name": name.strip(), "quantity": quantity.strip(), "unit": unit.strip()}
        return {"name": text.strip(), "quantity": "", "unit": ""}

    def _get_source(self, url):
        if "allrecipes" in url:
            return "AllRecipes"
        if "foodnetwork" in url:
            return "Food Network"
        if "bbcgoodfood" in url:
            return "BBC Good Food"
        if "tasty" in url:
            return "Tasty"
        return "Unknown"

    def _extract_image(self, data):
        image = data.get("image")
        if isinstance(image, list):
            return image[0] if image else ""
        if isinstance(image, dict):
            return image.get("url", "")
        return image or ""

    def _infer_difficulty(self, data):
        prep = self._parse_time(data.get("prepTime")) or 0
        cook = self._parse_time(data.get("cookTime")) or 0
        total = prep + cook
        if total > 120:
            return "hard"
        if total > 45:
            return "medium"
        return "easy"

    def _parse_time(self, time_str):
        if not time_str:
            return None
        import re
        match = re.search(r'(\d+)', str(time_str))
        return int(match.group(1)) if match else None

    def _parse_servings(self, servings):
        if not servings:
            return None
        if isinstance(servings, list):
            servings = servings[0]
        try:
            return int(servings)
        except (ValueError, TypeError):
            return None
