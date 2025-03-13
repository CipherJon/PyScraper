import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from lxml import etree
import logging
from schemas import ScrapedData, ScrapedElement
from config import MAX_RETRIES, RETRY_DELAY, RETRY_STATUS_FORCELIST, RETRY_METHOD_WHITELIST, USER_AGENTS, PROXIES
from typing import Optional, List
import random

class WebScraper:
    def __init__(self, url: str, proxies: Optional[List[str]] = None, user_agents: Optional[List[str]] = None):
        self.url = url
        self.soup = None
        self.logger = logging.getLogger(__name__)
        self.proxies = proxies or PROXIES
        self.user_agents = user_agents or USER_AGENTS
        self.current_proxy_idx = 0
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_DELAY,
            status_forcelist=RETRY_STATUS_FORCELIST,
            allowed_methods=RETRY_METHOD_WHITELIST
        )
        
        # Create HTTP adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def fetch_page(self):
        try:
            headers = {'User-Agent': random.choice(self.user_agents)} if self.user_agents else {}
            
            proxy = None
            if self.proxies:
                proxy = {'http': self.proxies[self.current_proxy_idx % len(self.proxies)]}
                self.current_proxy_idx += 1
            
            response = self.session.get(
                self.url,
                timeout=10,
                headers=headers,
                proxies=proxy
            )
            response.raise_for_status()  # Check if the request was successful
            self.soup = BeautifulSoup(response.text, 'lxml')
            self.logger.info(f"Page fetched successfully from {self.url} after {response.raw.retries.total} attempts")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch page after {getattr(e.request, 'retries', 0)} attempts: {e}")
            self.soup = None

    def extract_headlines(self):
        if self.soup is None:
            self.logger.warning("No soup object. Please fetch the page first.")
            return []

        headlines = self.soup.find_all('h1')
        self.logger.info(f"Found {len(headlines)} headlines.")
        
        validated_elements = []
        for headline in headlines:
            try:
                validated = ScrapedElement(
                    content=headline.get_text(),
                    source_url=self.url,
                    element_type='h1',
                    css_classes=headline.get('class'),
                    parent_element=str(headline.parent.name) if headline.parent else None
                )
                validated_elements.append(validated)
            except Exception as e:
                self.logger.error(f"Validation failed for headline: {e}")
        
        return ScrapedData(
            elements=validated_elements,
            page_title=self.soup.title.string if self.soup.title else '',
            scraped_url=self.url
        )

    def extract_data(self, tag, class_name=None):
        if self.soup is None:
            self.logger.warning("No soup object. Please fetch the page first.")
            return []

        elements = self.soup.find_all(tag, class_=class_name)
        self.logger.info(f"Found {len(elements)} elements with tag '{tag}' and class '{class_name}'.")
        
        validated_elements = []
        for element in elements:
            try:
                validated = ScrapedElement(
                    content=element.get_text(),
                    source_url=self.url,
                    element_type=tag,
                    css_classes=element.get('class'),
                    parent_element=str(element.parent.name) if element.parent else None
                )
                validated_elements.append(validated)
            except Exception as e:
                self.logger.error(f"Validation failed for element: {e}")
        
        return ScrapedData(
            elements=validated_elements,
            page_title=self.soup.title.string if self.soup.title else '',
            scraped_url=self.url
        )

    def extract_css(self, selector):
        """Extract elements using CSS selector"""
        if self.soup is None:
            self.logger.warning("No soup object. Please fetch the page first.")
            return []

        elements = self.soup.select(selector)
        self.logger.info(f"Found {len(elements)} elements with CSS selector '{selector}'")
        
        validated_elements = []
        for element in elements:
            try:
                validated = ScrapedElement(
                    content=element.get_text(),
                    source_url=self.url,
                    element_type=element.name,
                    css_classes=element.get('class'),
                    parent_element=str(element.parent.name) if element.parent else None,
                    css_selector=selector
                )
                validated_elements.append(validated)
            except Exception as e:
                self.logger.error(f"Validation failed for CSS element: {e}")
        
        return ScrapedData(
            elements=validated_elements,
            page_title=self.soup.title.string if self.soup.title else '',
            scraped_url=self.url
        )

    def extract_xpath(self, xpath):
        """Extract elements using XPath selector"""
        if self.soup is None:
            self.logger.warning("No soup object. Please fetch the page first.")
            return []

        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(str(self.soup), parser)
            elements = tree.xpath(xpath)
        except Exception as e:
            self.logger.error(f"XPath evaluation failed: {e}")
            return []

        self.logger.info(f"Found {len(elements)} elements with XPath '{xpath}'")
        
        validated_elements = []
        for element in elements:
            try:
                if isinstance(element, str):
                    content = element
                    element_type = 'text'
                else:
                    content = element.text
                    element_type = element.tag

                validated = ScrapedElement(
                    content=content,
                    source_url=self.url,
                    element_type=element_type,
                    xpath_selector=xpath,
                    parent_element=str(element.getparent().tag) if element.getparent() else None
                )
                validated_elements.append(validated)
            except Exception as e:
                self.logger.error(f"Validation failed for XPath element: {e}")
        
        return ScrapedData(
            elements=validated_elements,
            page_title=self.soup.title.string if self.soup.title else '',
            scraped_url=self.url
        )