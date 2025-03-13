# Configuration settings for the web scraper

# URL of the target website
URL = "https://example.com"

# Logging configuration
LOG_FILE = 'logs/scraper.log'

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds (base for exponential backoff)
RETRY_STATUS_FORCELIST = [500, 502, 503, 504]  # Server error status codes
RETRY_METHOD_WHITELIST = ['GET', 'POST']  # Safe methods to retry