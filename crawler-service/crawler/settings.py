BOT_NAME = "food_crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 4
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

ITEM_PIPELINES = {
    "crawler.pipelines.normalizer.DataNormalizerPipeline": 200,
    "crawler.pipelines.publisher.RedisPublisherPipeline": 300,
    "crawler.pipelines.crawl_logger.CrawlLogPipeline": 100,
}

DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.user_agent.RandomUserAgentMiddleware": 350,
    "crawler.middlewares.rate_limiter.RateLimitMiddleware": 500,
}

FEED_EXPORT_ENCODING = "utf-8"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
