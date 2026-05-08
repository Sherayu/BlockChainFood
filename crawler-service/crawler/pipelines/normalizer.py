import re
from datetime import datetime, timezone


class DataNormalizerPipeline:
    def process_item(self, item, spider):
        item["title"] = self._clean_text(item.get("title", ""))
        item["description"] = self._clean_text(item.get("description", ""))
        item["ingredients"] = self._normalize_ingredients(item.get("ingredients", []))
        item["tags"] = self._normalize_tags(item.get("tags", []))
        item["source_type"] = item.get("source_type", spider.name)

        if not item.get("crawled_at"):
            item["crawled_at"] = datetime.now(timezone.utc).isoformat()

        return item

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\n\r\t]+', ' ', text)
        return text.strip()

    def _normalize_ingredients(self, ingredients: list) -> list:
        normalized = []
        for ing in ingredients:
            if isinstance(ing, str):
                normalized.append({"name": ing.strip(), "quantity": "", "unit": ""})
            elif isinstance(ing, dict):
                normalized.append({
                    "name": ing.get("name", "").strip(),
                    "quantity": ing.get("quantity", "").strip(),
                    "unit": ing.get("unit", "").strip(),
                    "category": ing.get("category", "other"),
                })
        return normalized

    def _normalize_tags(self, tags: list) -> list:
        seen = set()
        clean = []
        for tag in tags:
            tag = tag.strip().lower() if isinstance(tag, str) else str(tag).lower()
            tag = re.sub(r'[^a-z0-9\s-]', '', tag)
            if tag and tag not in seen:
                seen.add(tag)
                clean.append(tag)
        return clean
