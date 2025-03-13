import unittest
from scraper import WebScraper
from schemas import ScrapedData
from schemas import ScrapedData

class TestWebScraper(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com"
        self.scraper = WebScraper(self.url)

    def test_fetch_page(self):
        self.scraper.fetch_page()
        self.assertIsNotNone(self.scraper.soup)

    def test_extract_headlines(self):
        self.scraper.fetch_page()
        result = self.scraper.extract_headlines()
        self.assertIsInstance(result, ScrapedData)
        self.assertIsInstance(result.elements, list)

    def test_extract_data(self):
        self.scraper.fetch_page()
        result = self.scraper.extract_data('p', 'specific-class')
        self.assertIsInstance(result, ScrapedData)
        self.assertIsInstance(result.elements, list)

if __name__ == '__main__':
    unittest.main()