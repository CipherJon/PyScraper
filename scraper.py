import requests
from bs4 import BeautifulSoup
from lxml import etree
import logging
from schemas import ScrapedData, ScrapedElement

class WebScraper:
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.logger = logging.getLogger(__name__)

    def fetch_page(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Check if the request was successful
            self.soup = BeautifulSoup(response.text, 'lxml')
            self.logger.info(f"Page fetched successfully from {self.url}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching the page: {e}")
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