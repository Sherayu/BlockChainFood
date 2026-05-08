from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders.blog_spider import FoodBlogSpider
from crawler.spiders.recipe_site_spider import RecipeSiteSpider
from crawler.spiders.rss_spider import RSSSpider
from crawler.social.reddit_client import RedditClient
import time
import os

CRAWL_FREQUENCY_MINUTES = int(os.getenv("CRAWL_FREQUENCY_MINUTES", "60"))


def run_spiders():
    process = CrawlerProcess(get_project_settings())

    process.crawl(FoodBlogSpider)
    process.crawl(RecipeSiteSpider)
    process.crawl(RSSSpider)

    process.start()


def run_social_clients():
    reddit = RedditClient()
    reddit.fetch_trending()


def main():
    print(f"[Crawler] Starting crawler service (frequency: {CRAWL_FREQUENCY_MINUTES}min)")

    while True:
        print("[Crawler] Running spiders...")
        try:
            run_spiders()
        except Exception as e:
            print(f"[Crawler] Spider error: {e}")

        print("[Crawler] Running social API clients...")
        try:
            run_social_clients()
        except Exception as e:
            print(f"[Crawler] Social client error: {e}")

        print(f"[Crawler] Crawl cycle complete. Sleeping {CRAWL_FREQUENCY_MINUTES} minutes...")
        time.sleep(CRAWL_FREQUENCY_MINUTES * 60)


if __name__ == "__main__":
    main()
