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

# Request headers and proxies configuration
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

PROXIES = []