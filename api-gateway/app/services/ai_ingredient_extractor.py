import json
import re
import httpx
from bs4 import BeautifulSoup
from typing import Optional, List
from app.config import get_settings


class AIIngredientExtractor:
    def __init__(self):
        self.settings = get_settings()
        self.timeout = self.settings.ingredient_extractor_timeout
        self.headers = {"User-Agent": self.settings.ingredient_extractor_user_agent}

    async def extract(self, url: str) -> List[dict]:
        result = await self._tier1_jsonld(url)
        if result:
            return result

        result = await self._tier2_schollz(url)
        if result:
            return result

        result = await self._tier3_gemini(url)
        if result:
            return result

        return []

    async def _tier1_jsonld(self, url: str) -> Optional[List[dict]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    return None
                soup = BeautifulSoup(resp.text, "lxml")
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        if item.get("@type") == "Recipe" or item.get("name") and item.get("recipeIngredient"):
                            raw = item.get("recipeIngredient", [])
                            if raw:
                                return [self._parse_ingredient_str(i) for i in raw]
                    for item in items:
                        if isinstance(item, dict):
                            for key in ("@graph", "itemListElement"):
                                for sub in item.get(key, []):
                                    if isinstance(sub, dict) and sub.get("@type") == "Recipe":
                                        raw = sub.get("recipeIngredient", [])
                                        if raw:
                                            return [self._parse_ingredient_str(i) for i in raw]
            return None
        except Exception:
            return None

    async def _tier2_schollz(self, url: str) -> Optional[List[dict]]:
        from urllib.parse import quote
        try:
            api_url = f"https://ingredients.schollz.now.sh/?url={quote(url)}"
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(api_url, headers=self.headers)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                raw = data.get("ingredients", data.get("recipeIngredient", []))
                if not raw and isinstance(data, list):
                    raw = data
                if raw:
                    return [self._parse_ingredient_str(i) for i in raw]
            return None
        except Exception:
            return None

    async def _tier3_gemini(self, url: str) -> Optional[List[dict]]:
        if not self.settings.gemini_api_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.settings.gemini_api_key)
            page_text = await self._fetch_page_text(url)
            if not page_text:
                return None
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = (
                "Extract the recipe ingredients from the following webpage text. "
                "Return ONLY a JSON array of objects, each with keys: name, quantity, unit. "
                "Example: [{\"name\": \"flour\", \"quantity\": \"2\", \"unit\": \"cups\"}]. "
                "If no ingredients are found, return [].\n\n" + page_text[:30000]
            )
            response = await model.generate_content_async(prompt)
            text = response.text.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [self._normalize_ingredient(i) for i in parsed if isinstance(i, dict)]
            return None
        except Exception:
            return None

    async def _fetch_page_text(self, url: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    return None
                soup = BeautifulSoup(resp.text, "lxml")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                text = soup.get_text(separator=" ")
                text = re.sub(r"\s+", " ", text).strip()
                return text[:50000]
        except Exception:
            return None

    def _parse_ingredient_str(self, raw: str) -> dict:
        raw = raw.strip()
        if not raw:
            return {"name": "", "quantity": "", "unit": "", "category": "other"}
        pattern = re.compile(
            r"^([\d\s\/\.,¼½¾⅓⅔⅛⅜⅝⅞]+)?\s*"
            r"((?:tablespoons|tablespoon|teaspoons|teaspoon|cups|cup|tbsp|tsp|ounces|ounce|oz|"
            r"pounds|pound|lbs|lb|kilograms|kilogram|kg|milliliters|milliliter|ml|"
            r"liters|liter|l|fluid ounce|fl oz|pinch|dash|slices|slice|cloves|clove|"
            r"cans|can|packages|package|pkg|bunches|bunch|pieces|piece|whole|handful|to taste"
            r"))?\s*"
            r"(.+)?$",
            re.IGNORECASE,
        )
        match = pattern.match(raw)
        if match:
            qty = match.group(1) or ""
            unit = match.group(2) or ""
            name = match.group(3) or raw
            return {"name": name.strip(), "quantity": qty.strip(), "unit": unit.strip(), "category": "other"}
        return {"name": raw, "quantity": "", "unit": "", "category": "other"}

    def _normalize_ingredient(self, item: dict) -> dict:
        return {
            "name": item.get("name", "").strip(),
            "quantity": str(item.get("quantity", "")).strip() if item.get("quantity") else "",
            "unit": item.get("unit", "").strip() if item.get("unit") else "",
            "category": item.get("category", "other"),
        }
