import time
from collections import defaultdict


class RateLimitMiddleware:
    def __init__(self):
        self.domain_times = defaultdict(list)
        self.min_interval = 2.0

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        from urllib.parse import urlparse
        domain = urlparse(request.url).netloc

        now = time.time()
        self.domain_times[domain] = [t for t in self.domain_times[domain] if now - t < 60]

        if self.domain_times[domain]:
            elapsed = now - self.domain_times[domain][-1]
            if elapsed < self.min_interval:
                wait = self.min_interval - elapsed
                time.sleep(wait)

        self.domain_times[domain].append(time.time())
        return None
