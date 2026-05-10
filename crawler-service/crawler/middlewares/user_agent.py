import random
from fake_useragent import UserAgent


class RandomUserAgentMiddleware:
    def __init__(self):
        self.fallback = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        ]
        try:
            self.ua = UserAgent()
            self.has_ua = True
        except Exception:
            self.has_ua = False

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        if self.has_ua:
            try:
                request.headers["User-Agent"] = self.ua.random
                return None
            except Exception:
                pass
        request.headers["User-Agent"] = random.choice(self.fallback)
        return None
