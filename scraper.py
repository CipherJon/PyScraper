import requests
from bs4 import BeautifulSoup
import logging

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

        headlines = self.soup.find_all('h1')  # Adjust the tag and class based on the website structure
        self.logger.info(f"Found {len(headlines)} headlines.")
        return [headline.get_text() for headline in headlines]

    def extract_data(self, tag, class_name=None):
        if self.soup is None:
            self.logger.warning("No soup object. Please fetch the page first.")
            return []

        elements = self.soup.find_all(tag, class_=class_name)
        self.logger.info(f"Found {len(elements)} elements with tag '{tag}' and class '{class_name}'.")
        return [element.get_text() for element in elements]