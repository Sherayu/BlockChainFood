from datetime import datetime, timezone


class PopularityScorer:
    def __init__(self):
        self.time_weight = 0.3
        self.engagement_weight = 0.4
        self.source_weight = 0.2
        self.diversity_weight = 0.1

        self.source_trust = {
            "recipe_site": 1.0,
            "blog": 0.8,
            "rss": 0.7,
            "social_reddit": 0.6,
            "social_pinterest": 0.5,
            "social_twitter": 0.4,
            "aggregator": 0.7,
        }

    def score(self, item: dict) -> float:
        time_score = self._calculate_time_score(item.get("crawled_at", ""))
        engagement_score = self._calculate_engagement_score(item)
        source_score = self._calculate_source_score(item.get("source_type", ""))
        diversity_score = self._calculate_diversity_score(item)

        total = (
            time_score * self.time_weight
            + engagement_score * self.engagement_weight
            + source_score * self.source_weight
            + diversity_score * self.diversity_weight
        )

        return round(min(100, total * 100), 2)

    def _calculate_time_score(self, crawled_at: str) -> float:
        try:
            if isinstance(crawled_at, str):
                crawled = datetime.fromisoformat(crawled_at.replace("Z", "+00:00"))
            else:
                crawled = crawled_at

            hours_ago = (datetime.now(timezone.utc) - crawled).total_seconds() / 3600
            return max(0, 1 - (hours_ago / 48))
        except (ValueError, TypeError):
            return 0.5

    def _calculate_engagement_score(self, item: dict) -> float:
        rating = item.get("rating", 0) or 0
        ingredients_count = len(item.get("ingredients", []) or [])
        steps_count = len(item.get("steps", []) or [])

        score = 0
        if rating > 0:
            score += min(1, rating / 5) * 0.5
        score += min(1, ingredients_count / 15) * 0.25
        score += min(1, steps_count / 10) * 0.25

        return score

    def _calculate_source_score(self, source_type: str) -> float:
        return self.source_trust.get(source_type, 0.5)

    def _calculate_diversity_score(self, item: dict) -> float:
        tags = item.get("tags", []) or []
        ingredients = item.get("ingredients", []) or []
        return min(1, (len(tags) + len(ingredients)) / 30)
