# PyScraper

A configurable web scraping framework with schema validation and logging.

## Features

- Modular scraping components
- Configuration-driven operation
- BeautifulSoup/Requests based scraping
- Pydantic schema validation
- Rotating file logging
- pytest test suite

## Requirements

- Python 3.9+
- See [requirements.txt](requirements.txt)

## Installation

```bash
git clone https://github.com/yourusername/polyscraper.git
cd polyscraper

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Edit `config.py`:
```python
# Configure target URLs and scraping parameters
SCRAPER_CONFIG = [
    {
        "url": "https://example.com",
        "selectors": {
            "title": "h1",
            "content": ".main-article"
        }
    }
]
```

2. Modify validation schemas in `schemas.py` for data validation:
```python
from pydantic import BaseModel

class ScrapedData(BaseModel):
    title: str
    content: str
    timestamp: datetime
```

## Usage

Run with default configuration:
```bash
python main.py
```

Run with custom config:
```bash
python main.py --config custom_config.py
```

## Project Structure
```
polyscraper/
├── config.py        # Main configuration
├── schemas.py       # Data validation models
├── scraper.py       # Core scraping logic
├── main.py          # Entry point
├── logging_config.py # Logging setup
└── tests/           # Test cases
```

## Logging

- Rotating logs in `logs/scraper.log`
- Configure handlers in `logging_config.py`:
```python
LOG_CONFIG = {
    "version": 1,
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/scraper.log",
            "maxBytes": 1048576,
            "backupCount": 3
        }
    }
}
```

## Testing

Run test suite with:
```bash
pytest tests/ -v
```

## License

MIT License - See [LICENSE](LICENSE)
