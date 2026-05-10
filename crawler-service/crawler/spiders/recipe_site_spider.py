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
        "seriouseats.com",
    ]

    start_urls = [
        "https://www.allrecipes.com/recipes",
        "https://www.foodnetwork.com/recipes",
        "https://www.bbcgoodfood.com/recipes",
        "https://tasty.co/recipes",
        "https://www.seriouseats.com/recipes",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "ROBOTSTXT_OBEY": False,
        "ITEM_PIPELINES": {
            "crawler.pipelines.normalizer.DataNormalizerPipeline": 200,
            "crawler.pipelines.publisher.RedisPublisherPipeline": 300,
        },
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
        if re.search(r'/(recipe|recept|recipes)/', url):
            return True
        return False

    def _extract_schema(self, response):
        for script in response.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    atype = item.get("@type")
                    if atype == "Recipe" or (isinstance(atype, list) and "Recipe" in atype):
                        return item
                for item in items:
                    if isinstance(item, dict):
                        for key in ("@graph", "itemListElement", "mainEntity"):
                            for sub in item.get(key, []):
                                if isinstance(sub, dict):
                                    satype = sub.get("@type")
                                    if satype == "Recipe" or (isinstance(satype, list) and "Recipe" in satype):
                                        return sub
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
        ingredient_selectors = [
            "[class*=ingredient] li",
            "[class*=Ingredient] li",
            ".ingredients-list li",
            ".recipe-ingredients li",
            "[data-testid*=ingredient] li",
            ".recipe__ingredients li",
            ".recipe-ingredients__item",
            "[itemprop=recipeIngredient]",
        ]
        for sel in ingredient_selectors:
            for li in response.css(sel):
                text = li.css("::text").get()
                if text:
                    parts = self._parse_ingredient(text.strip())
                    ingredients.append(parts)
            if ingredients:
                break

        steps = []
        step_selectors = [
            "[class*=instruction] li",
            "[class*=step] li",
            "[class*=direction] li",
            ".recipe-method li",
            "[itemprop=recipeInstructions] li",
            "[class*=recipeStep]",
            "[class*=cooking-step]",
        ]
        for sel in step_selectors:
            for li in response.css(sel):
                text = li.css("::text").get()
                if text:
                    steps.append(text.strip())
            if steps:
                break

        return {
            "title": title.strip(),
            "url": response.url,
            "source": self._get_source(response.url),
            "source_type": "recipe_site",
            "description": response.css("meta[name=description]::attr(content)").get() or "",
            "image_url": response.css("meta[property='og:image']::attr(content)").get() or "",
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
        text = text.strip()
        if not text:
            return {"name": "", "quantity": "", "unit": ""}
        pattern = re.compile(
            r"^([\d\s\/\.,¼½¾⅓⅔⅛⅜⅝⅞]+)?\s*"
            r"(tablespoons|tablespoon|teaspoons|teaspoon|cups?|tbsp|tsp|ounces?|oz|"
            r"pounds?|lbs?|grams?|g|kilograms?|kg|milliliters?|ml|liters?|l|"
            r"fluid ounce|fl oz|pinch|dash|slices?|cloves?|"
            r"cans?|packages?|pkg|bunches?|pieces?|whole|handful|to taste"
            r")?\s*"
            r"[-–]?\s*(.+)?$",
            re.IGNORECASE,
        )
        match = pattern.match(text)
        if match:
            qty = match.group(1) or ""
            unit = match.group(2) or ""
            name = match.group(3) or text
            return {"name": name.strip(), "quantity": qty.strip(), "unit": unit.strip()}
        return {"name": text, "quantity": "", "unit": ""}

    def _get_source(self, url):
        if "allrecipes" in url:
            return "AllRecipes"
        if "foodnetwork" in url:
            return "Food Network"
        if "bbcgoodfood" in url:
            return "BBC Good Food"
        if "tasty" in url:
            return "Tasty"
        if "seriouseats" in url:
            return "Serious Eats"
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
