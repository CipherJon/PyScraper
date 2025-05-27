# PolyScraper

A flexible and robust web scraping framework built with Python, designed for efficient and maintainable data extraction.

## Features

- **Multiple Selector Support**: Extract data using CSS selectors, XPath, or HTML tags
- **Robust Error Handling**: Comprehensive error handling and logging
- **Caching System**: Built-in caching to reduce redundant requests
- **Proxy Support**: Rotate through multiple proxies
- **User Agent Rotation**: Automatic user agent rotation to avoid detection
- **Configurable Output**: Save data in JSON or CSV format
- **Type Safety**: Built with Pydantic for robust data validation
- **Extensible**: Easy to extend with new selectors and data processors

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PolyScraper.git
cd PolyScraper
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from scraper import WebScraper
from config import Config, ScraperConfig, SelectorConfig

# Create a scraper instance
scraper = WebScraper("https://example.com")

# Fetch the page
scraper.fetch_page()

# Extract data using different selectors
headlines = scraper.extract_headlines()
css_elements = scraper.extract_css("div.content")
xpath_elements = scraper.extract_xpath("//div[@class='content']")
```

### Configuration

Create a configuration file in `config/config.json`:

```json
{
    "scrapers": [
        {
            "name": "Example Scraper",
            "url": "https://example.com",
            "selectors": [
                {
                    "type": "css",
                    "selector": "h1",
                    "output": "headlines.json"
                },
                {
                    "type": "xpath",
                    "selector": "//div[@class='content']",
                    "output": "content.json"
                }
            ],
            "enabled": true
        }
    ],
    "output_format": "json",
    "output_dir": "output"
}
```

### Running the Scraper

```bash
python main.py
```

## Project Structure

```
PolyScraper/
├── config/
│   └── config.json
├── output/
├── tests/
│   └── test_scraper.py
├── main.py
├── scraper.py
├── schemas.py
├── config.py
└── requirements.txt
```

## Configuration Options

### Scraper Configuration

- `name`: Name of the scraper
- `url`: Target URL to scrape
- `selectors`: List of selectors to use
- `enabled`: Whether the scraper is enabled

### Selector Configuration

- `type`: Type of selector (css, xpath, tag)
- `selector`: The selector string
- `output`: Output filename
- `description`: Optional description

### Global Configuration

- `output_format`: Output format (json or csv)
- `output_dir`: Output directory
- `max_retries`: Maximum number of retries
- `retry_delay`: Delay between retries
- `user_agents`: List of user agents
- `proxies`: List of proxy servers

## Error Handling

The scraper includes comprehensive error handling for:
- Network errors
- Parsing errors
- Validation errors
- Configuration errors

All errors are logged with appropriate context and severity levels.

## Caching

The scraper implements a caching system to:
- Reduce redundant requests
- Improve performance
- Respect rate limits
- Save bandwidth

Cache TTL is configurable (default: 5 minutes).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Testing

Run tests using pytest:
```bash
pytest tests/ -v
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- BeautifulSoup4 for HTML parsing
- Pydantic for data validation
- Requests for HTTP handling
- lxml for XPath support
