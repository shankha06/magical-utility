from pathlib import Path
import tempfile
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import signals
from twisted.internet import reactor, task, error
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
from fake_useragent import UserAgent

from urllib.parse import urlparse
import tldextract

# Constants
MAX_LIMIT = 10  # Example limit per start_url
DEPTH_LIMIT = 4  # Example depth limit
DEPTH_PRIORITY = 10  # Example priority adjustment
IDLE_TIMEOUT = 6  # Idle timeout in seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    # Add other headers as needed
}


def extract_domain(url):
    """
    Extracts the domain from a given URL using urlparse and tldextract.

    Args:
        url (str): The URL to extract the domain from.

    Returns:
        str: The extracted domain, or None if extraction fails.
    """
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = "https://" + url
            parsed_url = urlparse(url)
        if not parsed_url.netloc:
            return None  # Handle cases with invalid URLs

        extracted = tldextract.extract(parsed_url.netloc)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        else:
            return (
                None  # handle cases where tldextract fails to extract domain and suffix
            )

    except Exception as e:
        print(f"Error extracting domain from URL: {e}")
        return None


class PatternCrawler(CrawlSpider):
    name = "pattern_crawler"

    def __init__(self, start_urls, output_file, max_depth=1, *args, **kwargs):
        super(PatternCrawler, self).__init__(*args, **kwargs)
        self.start_urls = start_urls
          # Track scraped count per start_url
        self.scraped_data = []
        self.start_domains = [self.get_domain(url) for url in start_urls]
        self.scraped_counts = {
            url: 0 for url in self.start_domains
        }
        self.last_item_time = time.time()
        self.idle_task = None
        self.output_file = output_file
        self.total_scraped = 0
        self.depth = DEPTH_LIMIT
        self.rules = (Rule(LinkExtractor(), callback="parse_item", follow=False, process_request="process_request"),)
        super(PatternCrawler, self)._compile_rules()

    def get_domain(self, url):
        return extract_domain(url)

    def process_request(self, request, response):
        request_domain = self.get_domain(request.url)
        if self.total_scraped >= MAX_LIMIT*0.75*len(self.start_domains):
            try:
                if reactor.running:
                    reactor.stop()
            except error.ReactorNotRunning:
                pass

        if request_domain not in self.start_domains: #check domain is in start domain list
            self.logger.info(
                "Skipping URL as it is not a subpage of the start URLs: %s", request.url
            )
            return None
        
        if self.scraped_counts[request_domain] >= MAX_LIMIT:
            self.logger.info(
                f"Max URL limit ({MAX_LIMIT}) reached for {request_domain}. Skipping: {request.url}"
            )
            return None

        current_depth = request.url.count("/") - 2
        if current_depth >= DEPTH_LIMIT:
            return None
        request.priority = request.priority - (current_depth * 10)
        self.logger.info(f"Requesting URL: {request.url} at depth - {current_depth}, domain count - {self.scraped_counts[request_domain]}")

        return request

    def parse_item(self, response):
        title = response.css("title::text").get()
        body_html = response.css("body").get()

        if title is None or body_html is None:
            self.logger.warning("Missing title or body in URL: %s", response.url)
            return

        soup = BeautifulSoup(body_html, "html.parser")
        body_text = soup.get_text(separator="\n", strip=True)
        self.total_scraped +=1
        start_url = self.get_domain(response.url)
        if start_url and start_url in self.start_domains:
            self.scraped_counts[start_url] += 1
        # self.logger.info(f"Crawling URL: {response.url} at depth - {response.meta["depth"]}, domain count - {self.scraped_counts[start_url]}" )
        item = {"url": response.url, "title": title, "body": body_text}
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
            self.logger.info(
                f"Idle timeout ({IDLE_TIMEOUT}s) reached. Stopping reactor."
            )
            if reactor.running:
                reactor.stop()
            if self.idle_task and self.idle_task.running:
                self.idle_task.stop()

    def close(self, reason):
        """Convert scraped data to DataFrame and return it."""
        df = pd.DataFrame(self.scraped_data)
        self.logger.info("Scraped data converted to DataFrame")
        df.to_excel(self.output_file, index=False)


def main():
    ua = UserAgent()
    urls = [
        "https://www.advancionsciences.com",
        "https://www.abc-group.com",
        "https://www.rsmus.com/",  # RSM US LLP
        "https://www.gt.com/",  # Grant Thornton LLP
        "https://www.bakertilly.com/",  # Baker Tilly
        "https://www.bdo.com/global", #BDO
        "https://www.plante Moran.com/", #Plante Moran
        "https://www.crowe.com/", #Crowe
        "https://www.claconnect.com/", #CLA (CliftonLarsonAllen)
        "https://www.forvis.com/", #Forvis
        "https://www.armstrongworldindustries.com/", #Armstrong World Industries
        "https://www.jeld-wen.com/", #Jeld-Wen
        "https://www.sensata.com/", #Sensata Technologies
        "https://www.aaon.com/", #AAON
        "https://www.brinkman.com/", #Brinkman Construction
        "https://www.schneiderresources.com/", #Schneider Resources
        "https://www.heniff.com/", #Heniff Transportation Systems
        "https://www.milliken.com/", #Milliken & Company
        "https://www.penske.com/", #Penske Corporation
        "https://www.crowncork.com/", #Crown Holdings, Inc.
        "https://www.cbre.com/", #CBRE Group, Inc.
        "https://www.jll.com/", #Jones Lang LaSalle Incorporated
        "https://www.colliers.com/", #Colliers International
        "https://www.cushmanwakefield.com/", #Cushman & Wakefield
        "https://www.hubinternational.com/", #Hub International
        "https://www.ajg.com/", #Arthur J. Gallagher & Co.
        "https://www.marshmclennan.com/", #Marsh McLennan
        "https://www.lockton.com/", #Lockton Companies
        "https://www.assuredpartners.com/", #AssuredPartners
        "https://www.acrisure.com/", #Acrisure
        "https://www.ryan.com/", #Ryan, LLC
        "https://www.alvarezandmarsal.com/", #Alvarez & Marsal
        "https://www.protiviti.com/", #Protiviti
        "https://www.fti consulting.com/", #FTI Consulting
        "https://www.alixpartners.com/", #AlixPartners
        "https://www.ghclongpoint.com/", #GHCLongPoint
        "https://www.lincolninternational.com/", #Lincoln International
        "https://www.airdri.com/", #Airdri
        "https://www.atlasmachinery.com/", #Atlas Machinery
        "https://www.bakerpetroleum.com/", #Baker Petroleum
        "https://www.centuryprinting.com/", #Century Printing
        "https://www.davisstandard.com/", #Davis-Standard
        "https://www.eliteamc.com/", #Elite AMC Management
        "https://www.fivestarchemicals.com/", #Five Star Chemicals
        "https://www.gulfcoastfilters.com/", #Gulf Coast Filters
        "https://www.hytrol.com/", #Hytrol Conveyor Company
        "https://www.intercon1.com/", #Intercon 1
        "https://www.keymarkcorp.com/", #Keymark Corporation
        "https://www.lewiscontractors.com/", #Lewis Contractors
        "https://www.mccormickdistilling.com/", #McCormick Distilling Company
        "https://www.nationalgypsum.com/", #National Gypsum
        "https://www.ocv.com/", #OCV Control Valves
        "https://www.pattersonpump.com/", #Patterson Pump Company
        "https://www.qualitydie.com/", #Quality Die Company
        "https://www.reynoldsamerican.com/", #Reynolds American Inc.
        "https://www.steelcase.com/", #Steelcase
        "https://www.textron.com/", #Textron
        "https://www.usg.com/", #USG Corporation
        "https://www.valmont.com/", #Valmont Industries
        "https://www.williamsbakery.com/", #Williams Bakery
        "https://www.xerium.com/", #Xerium Technologies
        "https://www.yorklabel.com/", #York Label
        "https://www.zurn.com/", #Zurn Water Solutions
    ]  # List of URLs to crawl
    DEPTH = 2


    process = CrawlerProcess(
        {
            "DEPTH_LIMIT": DEPTH,
            "DEPTH_PRIORITY": 10,
            "LOG_LEVEL": "INFO",
            "USER_AGENT": ua.random,
            "COOKIES_ENABLED": False,
            "ROBOTSTXT_OBEY": False,

            "DEFAULT_REQUEST_HEADERS": HEADERS,

            "CONCURRENT_REQUESTS": 100,
            "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
            # "CONCURRENT_REQUESTS_PER_IP": 10,
            "DOWNLOAD_DELAY": 2,
            "DOWNLOAD_MAXSIZE": 3355443,
            "DOWNLOAD_TIMEOUT": 60,  # Timeout for each download in seconds
            "RETRY_ENABLED": False,

            "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
            "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
            "SCHEDULER_PRIORITY_QUEUE": "scrapy.pqueues.DownloaderAwarePriorityQueue",
            
            "CLOSESPIDER_PAGECOUNT_NO_ITEM": 30,
            "CLOSESPIDER_ITEMCOUNT": MAX_LIMIT*0.9*len(urls),
            "REDIRECT_PRIORITY_ADJUST": -1,
            "RANDOMIZE_DOWNLOAD_DELAY": True,
            "MEMUSAGE_ENABLED": True,
            "REACTOR_THREADPOOL_MAXSIZE": 100,
            "ROBOTSTXT_PARSER": "scrapy.robotstxt.PythonRobotParser",
            "ROBOTSTXT_USER_AGENT": ua.random,
            "HTTPCACHE_ALWAYS_STORE": True,
            "FAKEUSERAGENT_PROVIDERS" : [
                'scrapy_fake_useragent.providers.FakeUserAgentProvider',  # This is the first provider we'll try
                'scrapy_fake_useragent.providers.FakerProvider',  # If FakeUserAgentProvider fails, we'll use faker to generate a user-agent string for us
                'scrapy_fake_useragent.providers.FixedUserAgentProvider',  # Fall back to USER_AGENT value
            ],
            # "ROTATING_PROXY_LIST" : [
            #     'proxy1.com:8000',
            #     'proxy2.com:8031',
            #     'proxy3.com:8032',
            # ],
            # "DOWNLOADER_MIDDLEWARES": {
            #     # ...
            #     'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            #     'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
            #     # ...
            # }
        }
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_location = Path(temp_dir) / "scraped_data.xlsx"
        try:
            process.crawl(
                PatternCrawler,
                start_urls=urls,
                max_depth=DEPTH,
                output_file=temp_location,
            )
            process.start()

            extracted_data = pd.read_excel(temp_location)
            extracted_data["domain"] = extracted_data["url"].apply(extract_domain)
            print(extracted_data.groupby("domain").size())
            print(extracted_data.shape)
        except Exception as e:
            logging.error(f"An error occurred during crawling: {e}")


if __name__ == "__main__":
    main()