import re


class RecipeExtractor:
    def extract_structure(self, text: str) -> dict:
        sections = self._split_sections(text)

        title = sections.get("title", "")
        ingredients = self._parse_ingredients(sections.get("ingredients", ""))
        steps = self._parse_steps(sections.get("instructions", "") or sections.get("method", ""))
        prep_time = self._extract_time(text, "prep")
        cook_time = self._extract_time(text, "cook")
        servings = self._extract_servings(text)

        return {
            "title": title,
            "ingredients": ingredients,
            "steps": steps,
            "prep_time_minutes": prep_time,
            "cook_time_minutes": cook_time,
            "servings": servings,
        }

    def _split_sections(self, text: str) -> dict:
        sections = {}
        current_section = "title"
        lines = text.split("\n")

        for line in lines:
            line_lower = line.strip().lower()
            if "ingredient" in line_lower:
                current_section = "ingredients"
            elif "instruction" in line_lower or "method" in line_lower or "direction" in line_lower:
                current_section = "instructions"
            elif "prep time" in line_lower or "cook time" in line_lower or "total time" in line_lower:
                current_section = "times"
            else:
                sections.setdefault(current_section, [])
                sections[current_section].append(line.strip())

        return sections

    def _parse_ingredients(self, text: str) -> list:
        if isinstance(text, list):
            text = "\n".join(text)

        ingredients = []
        pattern = r'^([\d\s\/\.¼½¾]+)?\s*([a-zA-Z\s]+)?\s*[-–]?\s*(.+)$'

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                quantity = match.group(1) or ""
                unit = match.group(2) or ""
                name = match.group(3) or line
                ingredients.append({
                    "name": name.strip().rstrip("."),
                    "quantity": quantity.strip(),
                    "unit": unit.strip(),
                })

        return ingredients

    def _parse_steps(self, text: str) -> list:
        if isinstance(text, list):
            text = "\n".join(text)

        steps = []
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith(("#", "//", "<!--")):
                steps.append(re.sub(r'^\d+[\.\)]\s*', '', line))

        return steps

    def _extract_time(self, text: str, time_type: str) -> int:
        pattern = rf'{time_type}[:\s]+(\d+)\s*(min|hour|hr)s?'
        match = re.search(pattern, text.lower())
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            if unit.startswith("hour") or unit == "hr":
                value *= 60
            return value
        return None

    def _extract_servings(self, text: str) -> int:
        pattern = r'(?:serves|servings|yield)[:\s]+(\d+)'
        match = re.search(pattern, text.lower())
        return int(match.group(1)) if match else None
