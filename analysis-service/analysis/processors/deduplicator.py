import hashlib
import json


class Deduplicator:
    def __init__(self):
        self.seen_hashes = set()

    def is_duplicate(self, item: dict) -> bool:
        content_hash = self._compute_hash(item)
        if content_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(content_hash)
        return False

    def _compute_hash(self, item: dict) -> str:
        content = item.get("title", "") + item.get("url", "")
        return hashlib.md5(content.encode()).hexdigest()
