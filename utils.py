import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import signals
from twisted.internet import reactor, task
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time

# Constants
MAX_LIMIT = 100  # Example limit per start_url
DEPTH_LIMIT = 2  # Example depth limit
DEPTH_PRIORITY = 10  # Example priority adjustment
IDLE_TIMEOUT = 6  # Idle timeout in seconds


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    # Add other headers as needed
}

class CustomCrawlerProcess(CrawlerProcess):
    def __init__(self, settings=None, install_root_handler=True):
        super().__init__(settings, install_root_handler)
        self.settings.set('DEFAULT_REQUEST_HEADERS', HEADERS, priority='cmdline')
        self.scraped_data = []
        
    def crawl(self, *args, **kwargs):
        df = super().crawl(*args, **kwargs)
        return df

    def spider_closed(self, spider, reason):
        self.logger.info(f'Spider {spider.name} closed with reason: {reason}')
        if hasattr(spider, 'scraped_data'):
            self.scraped_data = spider.scraped_data
        super().spider_closed(spider, reason)

    def close(self):
        df = pd.DataFrame(self.scraped_data)
        return df

MAX_LIMIT = 40  # Define the maximum number of URLs to scrape
DEPTH_LIMIT = 2  # Define the maximum depth limit
DEPTH_PRIORITY = 10  # Define the priority decrement per depth level
class PatternCrawler(CrawlSpider):
    name = 'pattern_crawler'

    def __init__(self, start_urls, allowed_patterns, max_depth=1, *args, **kwargs):
        super(PatternCrawler, self).__init__(*args, **kwargs)
        self.start_urls = start_urls
        self.allowed_patterns = allowed_patterns
        self.max_depth = int(max_depth)
        self.scraped_counts = {url: 0 for url in start_urls}  # Track scraped count per start_url
        self.scraped_data = []
        self.start_domains = [self.get_domain(url) for url in start_urls]
        self.last_item_time = time.time()
        self.idle_task = None

        self.rules = (
            Rule(
                LinkExtractor(allow=self.allowed_patterns, canonicalize=True),
                callback='parse_item',
                follow=True,
                process_request='process_request'
            ),
        )
        super(PatternCrawler, self)._compile_rules()

    def get_domain(self, url):
        return url.split('//')[-1].split('/')[0]

    def process_request(self, request, response):
        start_url = self.get_start_url(request.url)
        if start_url and self.scraped_counts[start_url] >= MAX_LIMIT:
            self.logger.info(f'Max URL limit ({MAX_LIMIT}) reached for {start_url}. Skipping: {request.url}')
            return None

        if not any(domain in request.url for domain in self.start_domains):
            self.logger.info('Skipping URL as it is not a subpage of the start URLs: %s', request.url)
            return None

        if self.max_depth > 0 and 'depth' in request.meta:
            current_depth = request.meta['depth']
            if current_depth >= DEPTH_LIMIT:
                self.logger.info('Request discarded due to exceeding DEPTH_LIMIT: %s', request.url)
                return None
            request.priority = request.priority - (current_depth * DEPTH_PRIORITY)

        return request

    def get_start_url(self, url):
        """Find the matching start_url for a given url."""
        for start_url in self.start_urls:
            if self.get_domain(start_url) in url:
                return start_url
        return None

    def parse_item(self, response):
        self.logger.info('Crawling URL: %s', response.url)
        title = response.css('title::text').get()
        body_html = response.css('body').get()

        if title is None or body_html is None:
            self.logger.warning('Missing title or body in URL: %s', response.url)
            return

        soup = BeautifulSoup(body_html, 'html.parser')
        body_text = soup.get_text(separator='\n', strip=True)

        start_url = self.get_start_url(response.url)
        if start_url:
            self.scraped_counts[start_url] += 1
        item = {
            'url': response.url,
            'title': title,
            'body': body_text
        }
        self.scraped_data.append(item)
        yield item
        self.last_item_time = time.time()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PatternCrawler, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        if self.idle_task is None:
            self.idle_task = task.LoopingCall(self.check_idle)
            self.idle_task.start(1.0)

    def check_idle(self):
        idle_time = time.time() - self.last_item_time
        if idle_time > IDLE_TIMEOUT:
            self.logger.info(f'Idle timeout ({IDLE_TIMEOUT}s) reached. Stopping reactor.')
            if reactor.running:
                reactor.stop()
            if self.idle_task and self.idle_task.running:
                self.idle_task.stop()
    
    def close(self, reason):
        """Convert scraped data to DataFrame and return it."""
        df = pd.DataFrame(self.scraped_data)
        self.logger.info('Scraped data converted to DataFrame')
        return df

def main():
    patterns = ["about", "contact", "privacy", "terms", "news"]
    urls = ["https://www.advancionsciences.com", "https://www.abc-group.com"]  # List of URLs to crawl
    depth = 2

    process = CustomCrawlerProcess({
        'LOG_LEVEL': 'INFO',
    })

    try:
        process.crawl(PatternCrawler, start_urls=urls, allowed_patterns=patterns, max_depth=depth)
        process.start()

        df = process.close()  # Modify the scrapper call such that the dataframe is returned as output instead of being saved.
        df.to_excel('scraped_data.xlsx')  # Save the scraped data to an Excel file
    except Exception as e:
        logging.error(f"An error occurred during crawling: {e}")

if __name__ == "__main__":
    main()
