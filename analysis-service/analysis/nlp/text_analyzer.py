import re
from collections import Counter


class TextAnalyzer:
    def __init__(self):
        self.common_stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "shall", "can", "need", "dare",
            "ought", "used", "this", "that", "these", "those", "it", "its",
            "you", "your", "yours", "he", "she", "they", "we", "my", "our",
            "his", "her", "their", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "because", "as", "until",
            "while", "about", "between", "through", "during", "before", "after",
            "above", "below", "up", "down", "out", "off", "over", "under",
            "again", "further", "then", "once",
        }

        self.food_keywords = {
            "recipe", "cook", "bake", "roast", "grill", "fry", "steam", "boil",
            "saute", "season", "marinate", "chop", "dice", "mince", "slice",
            "delicious", "tasty", "flavorful", "savory", "sweet", "spicy",
            "healthy", "fresh", "homemade", "traditional", "authentic",
        }

    def extract_keywords(self, text: str, top_n: int = 10) -> list:
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        words = [w for w in words if w not in self.common_stopwords]
        word_counts = Counter(words)
        return word_counts.most_common(top_n)

    def extract_food_terms(self, text: str) -> list:
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        food_terms = [w for w in words if w in self.food_keywords or len(w) > 4]
        return list(set(food_terms))

    def is_food_related(self, text: str) -> bool:
        text_lower = text.lower()
        food_indicators = {
            "recipe", "ingredient", "cook", "bake", "kitchen", "chef",
            "dish", "meal", "dinner", "lunch", "breakfast", "dessert",
            "delicious", "flavor", "spice", "fresh", "homemade",
        }
        return any(indicator in text_lower for indicator in food_indicators)

    def extract_quantities(self, text: str) -> list:
        pattern = r'([\d\s\/\.¼½¾⅓⅔⅛⅜⅝⅞]+)\s*(cup|tablespoon|tablespoons|tbsp|teaspoon|teaspoons|tsp|ounce|oz|pound|lb|lbs|gram|g|kilogram|kg|liter|l|milliliter|ml|piece|pieces|clove|cloves|slice|slices|whole|can|bunch|pinch|dash)\s+(.+?)(?=[,;]|$)'

        matches = re.findall(pattern, text, re.IGNORECASE)
        return [
            {"quantity": m[0].strip(), "unit": m[1].strip(), "name": m[2].strip()}
            for m in matches
        ]

    def categorize_dish(self, title: str, ingredients: list) -> str:
        text = title.lower()

        dessert_words = {"dessert", "cake", "cookie", "pie", "brownie", "pudding", "ice cream", "sweet"}
        baking_words = {"bread", "muffin", "scone", "bun", "roll", "loaf", "pastry", "dough"}
        starter_words = {"appetizer", "starter", "soup", "salad", "dip", "finger food"}
        main_words = {"chicken", "steak", "pasta", "curry", "roast", "grill", "stir-fry", "casserole"}
        beverage_words = {"drink", "smoothie", "cocktail", "juice", "tea", "coffee", "shake"}

        for word in dessert_words:
            if word in text:
                return "desserts"
        for word in baking_words:
            if word in text:
                return "baking"
        for word in starter_words:
            if word in text:
                return "starters"
        for word in main_words:
            if word in text:
                return "main-course"
        for word in beverage_words:
            if word in text:
                return "beverages"

        ingredient_names = [i.get("name", "") if isinstance(i, dict) else str(i) for i in ingredients]
        ingredient_text = " ".join(ingredient_names).lower()

        if any(w in ingredient_text for w in dessert_words):
            return "desserts"
        if any(w in ingredient_text for w in main_words):
            return "main-course"

        return "main-course"
