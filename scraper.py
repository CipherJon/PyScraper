import requests
from bs4 import BeautifulSoup
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
            self.soup = BeautifulSoup(response.text, 'html.parser')
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