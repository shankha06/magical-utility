import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import argparse

class PatternCrawler(CrawlSpider):
    name = 'pattern_crawler'

    def __init__(self, start_url, allowed_patterns, max_depth=0, *args, **kwargs):
        super(PatternCrawler, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_patterns = allowed_patterns
        self.max_depth = int(max_depth)

        self.rules = (
            Rule(
                LinkExtractor(allow=lambda link: any(pattern in link for pattern in self.allowed_patterns)),
                callback='parse_item',
                follow=True,
                process_request='process_request'
            ),
        )
        super(PatternCrawler, self)._compile_rules()

    def process_request(self, request, response):
        if self.max_depth > 0 and 'depth' in request.meta and request.meta['depth'] >= self.max_depth:
            return None
        return request

    def parse_item(self, response):
        self.logger.info('Crawling URL: %s', response.url)
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'body': response.css('body').get()
        }

def main():
    parser = argparse.ArgumentParser(description='Crawl subpages with specific patterns.')
    parser.add_argument('start_url', help='The starting URL for crawling.')
    parser.add_argument('patterns', nargs='+', help='List of patterns to match in URLs.')
    parser.add_argument('--depth', type=int, default=0, help='Maximum crawling depth (0 for unlimited).')
    args = parser.parse_args()

    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'LOG_LEVEL': 'INFO',
        'DEPTH_LIMIT': 0, #Scrapy's depth limit is managed by the spider, not the settings.
    })

    process.crawl(PatternCrawler, start_url=args.start_url, allowed_patterns=args.patterns, max_depth=args.depth)
    process.start()

if __name__ == '__main__':
    main()