import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from lxml import etree
import logging
from schemas import ScrapedData, ScrapedElement
from config import MAX_RETRIES, RETRY_DELAY, RETRY_STATUS_FORCELIST, RETRY_METHOD_WHITELIST, USER_AGENTS, PROXIES
from typing import Optional, List, Dict, Any, Union
import random
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta

class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass

class FetchError(ScraperError):
    """Exception raised when page fetch fails."""
    pass

class ParseError(ScraperError):
    """Exception raised when parsing fails."""
    pass

class WebScraper:
    def __init__(self, url: str, proxies: Optional[List[str]] = None, user_agents: Optional[List[str]] = None):
        self.url = url
        self.soup = None
        self.logger = logging.getLogger(__name__)
        self.proxies = proxies or PROXIES
        self.user_agents = user_agents or USER_AGENTS
        self.current_proxy_idx = 0
        self._session = None
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = timedelta(minutes=5)  # Cache TTL of 5 minutes
        
    @property
    def session(self) -> requests.Session:
        """Lazy initialization of session with retry strategy."""
        if self._session is None:
            retry_strategy = Retry(
                total=MAX_RETRIES,
                backoff_factor=RETRY_DELAY,
                status_forcelist=RETRY_STATUS_FORCELIST,
                allowed_methods=RETRY_METHOD_WHITELIST
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session = requests.Session()
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)
        return self._session

    def _get_cache_key(self) -> str:
        """Generate a cache key for the current request.
        
        Returns:
            str: A unique cache key
        """
        # Create a string with URL and proxy index for hashing
        config_str = f"{self.url}:{self.current_proxy_idx}"
        return hashlib.md5(config_str.encode()).hexdigest()

    def _get_cached_response(self) -> Optional[BeautifulSoup]:
        """Get cached response if available and not expired."""
        cache_key = self._get_cache_key()
        if cache_key in self._cache:
            timestamp, soup = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                self.logger.info(f"Using cached response for {self.url}")
                return soup
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None

    def _cache_response(self, soup: BeautifulSoup) -> None:
        """Cache the response with current timestamp."""
        cache_key = self._get_cache_key()
        self._cache[cache_key] = (datetime.now(), soup)
        self.logger.debug(f"Cached response for {self.url}")

    def _get_random_headers(self) -> Dict[str, str]:
        """Get random headers for request."""
        return {
            'User-Agent': random.choice(self.user_agents) if self.user_agents else '',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy from the list."""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_idx % len(self.proxies)]
        self.current_proxy_idx += 1
        return {'http': proxy, 'https': proxy}

    def fetch_page(self) -> None:
        """Fetch and parse the webpage with proper caching."""
        try:
            # Check cache first
            cached_soup = self._get_cached_response()
            if cached_soup is not None:
                self.soup = cached_soup
                return

            headers = self._get_random_headers()
            proxy = self._get_proxy()
            
            response = self.session.get(
                self.url,
                timeout=10,
                headers=headers,
                proxies=proxy,
                verify=True  # SSL verification
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                raise FetchError(f"Unexpected content type: {content_type}")
            
            self.soup = BeautifulSoup(response.text, 'lxml')
            self._cache_response(self.soup)
            self.logger.info(f"Page fetched successfully from {self.url}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch page: {str(e)}")
            raise FetchError(f"Failed to fetch page: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching page: {str(e)}")
            raise FetchError(f"Unexpected error: {str(e)}")

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        self.logger.info("Cache cleared")

    def set_cache_ttl(self, minutes: int) -> None:
        """Set the cache TTL in minutes."""
        self._cache_ttl = timedelta(minutes=minutes)
        self.logger.info(f"Cache TTL set to {minutes} minutes")

    def _validate_soup(self) -> None:
        """Validate that soup object exists."""
        if self.soup is None:
            raise ParseError("No soup object. Please fetch the page first.")

    def _create_scraped_element(self, element: Any, element_type: str, 
                              selector: Optional[str] = None) -> ScrapedElement:
        """Create a ScrapedElement with proper error handling.
        
        Args:
            element: The element to process (can be None)
            element_type: Type of the element
            selector: Optional selector used to find the element
            
        Returns:
            ScrapedElement: The created element
            
        Raises:
            ParseError: If element processing fails
        """
        try:
            if element is None:
                raise ParseError("Cannot create ScrapedElement from None element")

            # Get content safely
            content = ""
            if hasattr(element, 'get_text'):
                content = element.get_text(strip=True)
            elif isinstance(element, str):
                content = element
            else:
                content = str(element)

            # Get CSS classes safely
            css_classes = None
            if hasattr(element, 'get') and callable(getattr(element, 'get')):
                css_classes = element.get('class', [])

            # Get parent element safely
            parent_element = None
            if hasattr(element, 'parent') and element.parent is not None:
                parent_element = str(element.parent.name)

            return ScrapedElement(
                content=content,
                source_url=self.url,
                element_type=element_type,
                css_classes=css_classes,
                parent_element=parent_element,
                css_selector=selector
            )
        except Exception as e:
            self.logger.error(f"Error creating ScrapedElement: {str(e)}")
            raise ParseError(f"Failed to create ScrapedElement: {str(e)}")

    def extract_headlines(self) -> ScrapedData:
        """Extract headlines with improved error handling."""
        self._validate_soup()
        
        try:
            headlines = self.soup.find_all('h1')
            self.logger.info(f"Found {len(headlines)} headlines.")
            
            validated_elements = [
                self._create_scraped_element(h, 'h1')
                for h in headlines
            ]
            
            return ScrapedData(
                elements=validated_elements,
                page_title=self.soup.title.string if self.soup.title else '',
                scraped_url=self.url
            )
        except Exception as e:
            self.logger.error(f"Error extracting headlines: {str(e)}")
            raise ParseError(f"Failed to extract headlines: {str(e)}")

    def extract_data(self, tag: str, class_name: Optional[str] = None) -> ScrapedData:
        """Extract data with improved error handling."""
        self._validate_soup()
        
        try:
            elements = self.soup.find_all(tag, class_=class_name)
            self.logger.info(f"Found {len(elements)} elements with tag '{tag}' and class '{class_name}'.")
            
            validated_elements = [
                self._create_scraped_element(e, tag)
                for e in elements
            ]
            
            return ScrapedData(
                elements=validated_elements,
                page_title=self.soup.title.string if self.soup.title else '',
                scraped_url=self.url
            )
        except Exception as e:
            self.logger.error(f"Error extracting data: {str(e)}")
            raise ParseError(f"Failed to extract data: {str(e)}")

    def extract_css(self, selector: str) -> ScrapedData:
        """Extract elements using CSS selector with improved error handling."""
        self._validate_soup()
        
        try:
            elements = self.soup.select(selector)
            self.logger.info(f"Found {len(elements)} elements with CSS selector '{selector}'")
            
            validated_elements = [
                self._create_scraped_element(e, e.name, selector)
                for e in elements
            ]
            
            return ScrapedData(
                elements=validated_elements,
                page_title=self.soup.title.string if self.soup.title else '',
                scraped_url=self.url
            )
        except Exception as e:
            self.logger.error(f"Error extracting CSS elements: {str(e)}")
            raise ParseError(f"Failed to extract CSS elements: {str(e)}")

    def extract_xpath(self, xpath: str) -> ScrapedData:
        """Extract elements using XPath with improved error handling."""
        self._validate_soup()
        
        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(str(self.soup), parser)
            elements = tree.xpath(xpath)
            
            self.logger.info(f"Found {len(elements)} elements with XPath '{xpath}'")
            
            validated_elements = []
            for element in elements:
                if isinstance(element, str):
                    element_type = 'text'
                    content = element
                else:
                    element_type = element.tag
                    # Get text content from the element
                    content = ''.join(element.itertext()).strip()
                validated_elements.append(
                    self._create_scraped_element(content, element_type, xpath)
                )
            
            return ScrapedData(
                elements=validated_elements,
                page_title=self.soup.title.string if self.soup.title else '',
                scraped_url=self.url
            )
        except Exception as e:
            self.logger.error(f"Error extracting XPath elements: {str(e)}")
            raise ParseError(f"Failed to extract XPath elements: {str(e)}")

    def __del__(self):
        """Cleanup session on object destruction."""
        if self._session:
            self._session.close()