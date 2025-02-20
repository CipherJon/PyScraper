import unittest
from scraper import WebScraper

class TestWebScraper(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com"
        self.scraper = WebScraper(self.url)

    def test_fetch_page(self):
        self.scraper.fetch_page()
        self.assertIsNotNone(self.scraper.soup)

    def test_extract_headlines(self):
        self.scraper.fetch_page()
        headlines = self.scraper.extract_headlines()
        self.assertIsInstance(headlines, list)

    def test_extract_data(self):
        self.scraper.fetch_page()
        paragraphs = self.scraper.extract_data('p', 'specific-class')
        self.assertIsInstance(paragraphs, list)

if __name__ == '__main__':
    unittest.main()