
import logging
import re
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import signals
from twisted.internet import reactor
import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    # Add other headers as needed
}

class CustomCrawlerProcess(CrawlerProcess):
    def __init__(self, settings=None, install_root_handler=True):
        super().__init__(settings, install_root_handler)
        self.settings.set('DEFAULT_REQUEST_HEADERS', HEADERS, priority='cmdline')

MAX_LIMIT = 40  # Define the maximum number of URLs to scrape
DEPTH_LIMIT = 2  # Define the maximum depth limit
DEPTH_PRIORITY = 10  # Define the priority decrement per depth level

class PatternCrawler(CrawlSpider):
    name = 'pattern_crawler'

    def __init__(self, start_urls, allowed_patterns, max_depth=1, *args, **kwargs):
        super(PatternCrawler, self).__init__(*args, **kwargs)
        self.start_urls = start_urls  # Accept a list of start URLs
        self.allowed_patterns = allowed_patterns
        self.max_depth = int(max_depth)
        self.scraped_count = 0  # Initialize scraped URL counter
        self.scraped_data = []  # List to store scraped data

        # Extract domains for subpage check
        self.start_domains = [self.get_domain(url) for url in start_urls]

        self.rules = (
            Rule(
                LinkExtractor(allow=self.allowed_patterns, canonicalize=True),  # Enable canonicalization
                callback='parse_item',
                follow=True,
                process_request='process_request'
            ),
        )
        super(PatternCrawler, self)._compile_rules()

    def get_domain(self, url):
        """Extract the domain from the start URL."""
        return url.split('//')[-1].split('/')[0]

    def process_request(self, request, response):
        """Process each request to filter URLs based on domain, MAX_LIMIT, and adjust priority."""
        if self.scraped_count >= MAX_LIMIT:
            self.logger.info('Max URL limit reached. Stopping further requests.')
            if reactor.running:
                reactor.stop()
            return None

        # Check if the request URL is a subpage of any of the start URL's domains
        if not any(domain in request.url for domain in self.start_domains):
            self.logger.info('Skipping URL as it is not a subpage of the start URLs: %s', request.url)
            return None

        # Check if max_depth is exceeded
        if self.max_depth > 0 and 'depth' in request.meta:
            current_depth = request.meta['depth']
            if current_depth >= DEPTH_LIMIT:
                self.logger.info('Request discarded due to exceeding DEPTH_LIMIT: %s', request.url)
                return None
            # Adjust request priority based on depth
            request.priority = request.priority - (current_depth * DEPTH_PRIORITY)

        return request

    def parse_item(self, response):
        """Parse the item and increment the scraped URL counter."""
        self.logger.info('Crawling URL: %s', response.url)
        title = response.css('title::text').get()
        body_html = response.css('body').get()

        if title is None or body_html is None:
            self.logger.warning('Missing title or body in URL: %s', response.url)
            return

        # Use BeautifulSoup to clean the HTML body into simple text
        soup = BeautifulSoup(body_html, 'html.parser')
        body_text = soup.get_text(separator='\n', strip=True)

        self.scraped_count += 1  # Increment the scraped URL counter
        item = {
            'url': response.url,
            'title': title,
            'body': body_text
        }
        self.scraped_data.append(item)  # Append scraped data to the list
        yield item

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PatternCrawler, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """Shutdown the reactor when spider is idle."""
        self.logger.info('Spider idle. Stopping reactor.')
        if reactor.running:
            reactor.stop()

    def close(self, reason):
        """Convert scraped data to DataFrame and save to CSV."""
        df = pd.DataFrame(self.scraped_data)
        df.to_csv('scraped_data.csv', index=False)  # Save DataFrame to CSV
        self.logger.info('Scraped data saved to scraped_data.csv')

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
    except Exception as e:
        logging.error(f"An error occurred during crawling: {e}")

if __name__ == "__main__":
    main()
