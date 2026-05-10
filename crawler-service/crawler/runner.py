from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from crawler.spiders.blog_spider import FoodBlogSpider
from crawler.spiders.recipe_site_spider import RecipeSiteSpider
from crawler.spiders.rss_spider import RSSSpider
from crawler.social.reddit_client import RedditClient
from crawler.playwright.dynamic_scraper import DynamicScraper
import time
import os
import json

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


def run_dynamic_scraper():
    scraper = DynamicScraper()
    for site_url in DynamicScraper.JS_HEAVY_SITES:
        print(f"[DynamicScraper] Scraping listing: {site_url}")
        try:
            links = scraper.scrape_listing_sync(site_url, max_pages=2)
            print(f"[DynamicScraper] Found {len(links)} recipe links from {site_url}")
            for link in links[:20]:
                print(f"[DynamicScraper] Scraping recipe: {link}")
                result = scraper.scrape_sync(link)
                if result and "error" not in result:
                    scraper.redis_client.rpush("crawl_results", json.dumps(result))
        except Exception as e:
            print(f"[DynamicScraper] Error scraping {site_url}: {e}")


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

        print("[Crawler] Running dynamic scraper for JS-heavy sites...")
        try:
            run_dynamic_scraper()
        except Exception as e:
            print(f"[Crawler] Dynamic scraper error: {e}")

        print(f"[Crawler] Crawl cycle complete. Sleeping {CRAWL_FREQUENCY_MINUTES} minutes...")
        time.sleep(CRAWL_FREQUENCY_MINUTES * 60)


if __name__ == "__main__":
    main()
