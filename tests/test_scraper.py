import unittest
from unittest.mock import patch, Mock
from scraper import WebScraper, ScraperError, FetchError, ParseError
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

class TestWebScraper(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com"
        self.scraper = WebScraper(self.url)
        self.mock_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Headline</h1>
                <div class="content">Test Content</div>
                <p class="text">Test Paragraph</p>
            </body>
        </html>
        """

    @patch('requests.Session')
    def test_fetch_page_success(self, mock_session):
        # Setup mock response
        mock_response = Mock()
        mock_response.text = self.mock_html
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status = Mock()
        mock_session.return_value.get.return_value = mock_response

        # Test fetch
        self.scraper.fetch_page()
        self.assertIsNotNone(self.scraper.soup)
        self.assertEqual(self.scraper.soup.title.string, "Test Page")

    @patch('requests.Session')
    def test_fetch_page_network_error(self, mock_session):
        # Setup mock to raise exception
        mock_session.return_value.get.side_effect = requests.exceptions.RequestException("Network error")

        # Test fetch with error
        with self.assertRaises(FetchError):
            self.scraper.fetch_page()

    @patch('requests.Session')
    def test_fetch_page_invalid_content(self, mock_session):
        # Setup mock response with invalid content type
        mock_response = Mock()
        mock_response.headers = {'content-type': 'application/json'}
        mock_session.return_value.get.return_value = mock_response

        # Test fetch with invalid content
        with self.assertRaises(FetchError):
            self.scraper.fetch_page()

    def test_extract_headlines(self):
        # Setup soup
        self.scraper.soup = BeautifulSoup(self.mock_html, 'lxml')
        
        # Test extraction
        result = self.scraper.extract_headlines()
        self.assertEqual(len(result.elements), 1)
        self.assertEqual(result.elements[0].content, "Test Headline")

    def test_extract_data(self):
        # Setup soup
        self.scraper.soup = BeautifulSoup(self.mock_html, 'lxml')
        
        # Test extraction
        result = self.scraper.extract_data('div', 'content')
        self.assertEqual(len(result.elements), 1)
        self.assertEqual(result.elements[0].content, "Test Content")

    def test_extract_css(self):
        # Setup soup
        self.scraper.soup = BeautifulSoup(self.mock_html, 'lxml')
        
        # Test extraction
        result = self.scraper.extract_css('.text')
        self.assertEqual(len(result.elements), 1)
        self.assertEqual(result.elements[0].content, "Test Paragraph")

    def test_extract_xpath(self):
        # Setup soup
        self.scraper.soup = BeautifulSoup(self.mock_html, 'lxml')
        
        # Test extraction
        result = self.scraper.extract_xpath('//h1')
        self.assertEqual(len(result.elements), 1)
        self.assertEqual(result.elements[0].content, "Test Headline")

    def test_no_soup_error(self):
        # Test error when soup is None
        with self.assertRaises(ParseError):
            self.scraper.extract_headlines()

    def test_cache_operations(self):
        # Setup soup
        self.scraper.soup = BeautifulSoup(self.mock_html, 'lxml')
        
        # Test cache TTL
        self.scraper.set_cache_ttl(10)
        self.assertEqual(self.scraper._cache_ttl, timedelta(minutes=10))
        
        # Test cache clear
        self.scraper.clear_cache()
        self.assertEqual(len(self.scraper._cache), 0)

    def test_create_scraped_element_none(self):
        # Test handling of None element
        with self.assertRaises(ParseError):
            self.scraper._create_scraped_element(None, 'div')

    def test_create_scraped_element_string(self):
        # Test handling of string element
        element = self.scraper._create_scraped_element("Test String", 'text')
        self.assertEqual(element.content, "Test String")
        self.assertEqual(element.element_type, 'text')

if __name__ == '__main__':
    unittest.main()