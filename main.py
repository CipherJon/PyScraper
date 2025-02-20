import logging
from logging_config import setup_logging
from scraper import WebScraper

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    url = "https://example.com"  # Replace with the target URL
    scraper = WebScraper(url)
    scraper.fetch_page()
    
    # Extract headlines
    headlines = scraper.extract_headlines()
    for idx, headline in enumerate(headlines, start=1):
        logger.info(f"Headline {idx}: {headline}")

    # Extract other data (example: paragraphs with a specific class)
    paragraphs = scraper.extract_data('p', 'specific-class')
    for idx, paragraph in enumerate(paragraphs, start=1):
        logger.info(f"Paragraph {idx}: {paragraph}")

if __name__ == "__main__":
    main()