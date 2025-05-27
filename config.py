from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl, validator, ValidationError
import csv
import os
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Define paths
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / 'config'
OUTPUT_DIR = BASE_DIR / 'output'

def ensure_output_dir() -> None:
    """Ensure the output directory exists.
    
    This function should be called explicitly when directory creation is needed,
    rather than at module import time.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOG_FILE = 'logs/scraper.log'
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5
RETRY_STATUS_FORCELIST = [500, 502, 503, 504]  # Server error status codes
RETRY_METHOD_WHITELIST = ['GET', 'POST']  # Safe methods to retry

# Request headers and proxies configuration
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

PROXIES = []

class SelectorConfig(BaseModel):
    """Configuration for a single selector."""
    type: str = Field(..., description="Type of selector (css, xpath, tag)")
    selector: str = Field(..., description="The selector string")
    output: str = Field(..., description="Output filename")
    description: Optional[str] = Field(None, description="Description of what this selector extracts")

    @property
    def is_valid(self) -> bool:
        """Check if the selector configuration is valid."""
        valid_types = {'css', 'xpath', 'tag'}
        return (
            self.type in valid_types and
            bool(self.selector) and
            self.output.endswith(('.json', '.csv'))
        )

class ScraperConfig(BaseModel):
    """Configuration for a single scraper."""
    name: str = Field(..., description="Name of the scraper")
    url: str = Field(..., description="URL to scrape")
    selectors: List[SelectorConfig] = Field(..., description="List of selectors to use")
    description: Optional[str] = Field(None, description="Description of the scraper")
    enabled: bool = Field(True, description="Whether the scraper is enabled")

    @property
    def is_valid(self) -> bool:
        """Check if the scraper configuration is valid."""
        return (
            bool(self.name) and
            bool(self.url) and
            bool(self.selectors) and
            all(selector.is_valid for selector in self.selectors)
        )

class Config(BaseModel):
    """Main configuration model."""
    scrapers: List[ScraperConfig] = Field(..., description="List of scrapers")
    output_format: str = Field("json", description="Output format (json or csv)")
    output_dir: str = Field("output", description="Output directory")
    max_retries: int = Field(3, description="Maximum number of retries for failed requests")
    retry_delay: int = Field(5, description="Delay between retries in seconds")
    user_agents: List[str] = Field(default_factory=list, description="List of user agents to rotate")
    proxies: List[str] = Field(default_factory=list, description="List of proxy servers to use")

    @property
    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return bool(self.scrapers) and all(scraper.is_valid for scraper in self.scrapers)

# Example configuration
SCRAPER_CONFIG = [
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
                "type": "css",
                "selector": "p",
                "output": "paragraphs.json"
            }
        ],
        "enabled": True
    }
]

# Output configuration
OUTPUT_CONFIG = {
    "json": {
        "indent": 2,
        "ensure_ascii": False,
        "sort_keys": True
    },
    "csv": {
        "delimiter": ",",
        "quotechar": '"',
        "encoding": "utf-8",
        "header": True,
        "quote_nonnumeric": True,
        "quoting": csv.QUOTE_NONNUMERIC,
        "escapechar": "\\",
        "lineterminator": "\n"
    }
}

def load_config(config_path: str = None) -> Config:
    """Load and validate configuration from file.
    
    Args:
        config_path: Path to the configuration file. If None, uses default path.
        
    Returns:
        Config: Validated configuration object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config validation fails
    """
    if config_path is None:
        config_path = CONFIG_DIR / 'config.json'
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        config = Config(**data)
        validate_config(config)  # Validate after loading
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {str(e)}")
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            error_messages.append(f"{loc}: {msg}")
        error_details = "\n".join(error_messages)
        logger.error(f"Configuration validation failed:\n{error_details}")
        raise ValueError(f"Invalid configuration:\n{error_details}")

def validate_config(config: Config) -> bool:
    """Validate the configuration.
    
    Args:
        config: Configuration object to validate
        
    Returns:
        bool: True if configuration is valid
        
    Raises:
        ValueError: If validation fails
    """
    try:
        # Validate each scraper
        for scraper in config.scrapers:
            if not scraper.enabled:
                continue
                
            # Validate URL
            if not scraper.url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL for scraper {scraper.name}: {scraper.url}")
            
            # Validate selectors
            if not scraper.selectors:
                raise ValueError(f"No selectors defined for scraper {scraper.name}")
            
            for selector in scraper.selectors:
                if not selector.type in ['css', 'xpath', 'tag']:
                    raise ValueError(f"Invalid selector type for scraper {scraper.name}: {selector.type}")
                if not selector.selector:
                    raise ValueError(f"Empty selector for scraper {scraper.name}")
                if not selector.output:
                    raise ValueError(f"No output filename specified for selector in scraper {scraper.name}")
        
        # Validate output format
        if config.output_format not in ['json', 'csv']:
            raise ValueError(f"Invalid output format: {config.output_format}")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {str(e)}")

def get_output_path(filename: str) -> Path:
    """Get the full output path for a file.
    
    Args:
        filename: Name of the output file
        
    Returns:
        Path: Full path to the output file
    """
    ensure_output_dir()  # Ensure output directory exists
    return OUTPUT_DIR / filename