import re


class IngredientParser:
    CATEGORY_KEYWORDS = {
        "dairy": ["milk", "cream", "butter", "cheese", "yogurt", "paneer", "ghee", "curd", "mayonnaise"],
        "meat": ["chicken", "beef", "pork", "lamb", "mutton", "bacon", "ham", "turkey", "duck", "sausage", "steak"],
        "seafood": ["fish", "shrimp", "prawn", "salmon", "tuna", "crab", "lobster", "mussel", "clam", "tilapia"],
        "vegetable": ["onion", "garlic", "tomato", "potato", "carrot", "broccoli", "spinach", "pepper",
                      "mushroom", "cucumber", "lettuce", "cabbage", "celery", "zucchini", "eggplant",
                      "bell pepper", "green bean", "pea", "corn", "avocado"],
        "fruit": ["apple", "banana", "orange", "lemon", "lime", "berry", "mango", "pineapple",
                  "watermelon", "grape", "cherry", "peach", "plum", "strawberry", "blueberry",
                  "raspberry", "coconut", "date", "fig"],
        "grain": ["rice", "flour", "pasta", "bread", "oat", "quinoa", "barley", "wheat", "corn",
                  "noodle", "spaghetti", "couscous", "lentil", "bean", "chickpea", "soy", "tofu"],
        "spice": ["salt", "pepper", "cumin", "turmeric", "chili", "cinnamon", "paprika", "ginger",
                  "garlic powder", "oregano", "basil", "thyme", "rosemary", "cardamom", "clove",
                  "nutmeg", "coriander", "mustard", "vanilla", "bay leaf", "curry powder",
                  "red pepper", "black pepper", "cayenne"],
        "condiment": ["oil", "vinegar", "sauce", "syrup", "honey", "ketchup", "mustard",
                      "soy sauce", "olive oil", "vegetable oil", "sesame oil", "fish sauce",
                      "worcestershire", "balsamic", "salsa", "jam", "pickle"],
    }

    def parse(self, ingredient_text: str) -> dict:
        text = ingredient_text.strip()
        if not text:
            return {}

        quantity, unit, name = self._split_ingredient(text)
        category = self._categorize(name)

        return {
            "name": name,
            "quantity": quantity,
            "unit": unit,
            "category": category,
        }

    def _split_ingredient(self, text: str) -> tuple:
        fraction_map = {
            "¼": "0.25", "½": "0.5", "¾": "0.75",
            "⅓": "0.333", "⅔": "0.667",
            "⅛": "0.125", "⅜": "0.375", "⅝": "0.625", "⅞": "0.875",
        }

        for frac, decimal in fraction_map.items():
            text = text.replace(frac, decimal)

        pattern = r'^([\d\s\/\.\+\-]+)?\s*([a-zA-Z]+)?\s*[-–]\s*(.+)$'
        match = re.match(pattern, text)

        if match:
            quantity = match.group(1) or ""
            unit = match.group(2) or ""
            name = match.group(3).strip().rstrip(".")
            return quantity.strip(), unit.strip(), name

        parts = text.split(None, 2)
        if len(parts) >= 2 and self._looks_like_number(parts[0]):
            quantity = parts[0]
            unit = parts[1] if len(parts) > 2 else ""
            name = parts[2] if len(parts) > 2 else parts[1]
            return quantity, unit, name.rstrip(".")

        return "", "", text.rstrip(".")

    def _looks_like_number(self, s: str) -> bool:
        return bool(re.match(r'^[\d\.\/]+$', s))

    def _categorize(self, name: str) -> str:
        name_lower = name.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_lower or name_lower in keyword:
                    return category
        return "other"
