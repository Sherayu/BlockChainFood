import time
from collections import defaultdict
from twisted.internet import reactor, defer


class RateLimitMiddleware:
    def __init__(self):
        self.domain_times = defaultdict(list)
        self.min_interval = 2.0
        self.pending = defaultdict(list)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def _release_request(self, domain, d):
        self.domain_times[domain].append(time.time())
        reactor.callFromThread(d.callback, None)

    def process_request(self, request, spider):
        from urllib.parse import urlparse
        domain = urlparse(request.url).netloc

        now = time.time()
        self.domain_times[domain] = [t for t in self.domain_times[domain] if now - t < 60]

        if self.domain_times[domain]:
            elapsed = now - self.domain_times[domain][-1]
            if elapsed < self.min_interval:
                wait = self.min_interval - elapsed
                d = defer.Deferred()
                reactor.callLater(wait, self._release_request, domain, d)
                return d

        self.domain_times[domain].append(time.time())
        return None
