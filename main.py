import logging
import json
import csv
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Union, Optional
from logging_config import setup_logging
from scraper import WebScraper
from config import Config, ScraperConfig, SelectorConfig, SCRAPER_CONFIG, OUTPUT_DIR

class DataValidationError(Exception):
    """Exception raised for data validation errors."""
    pass

class SelectorConfigError(Exception):
    """Exception raised for selector configuration errors."""
    pass

def load_config() -> Config:
    """Load and validate the scraper configuration.
    
    Returns:
        Config: The validated configuration object
        
    Raises:
        ValueError: If configuration is invalid
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Convert the dictionary configuration to Pydantic model
        config = Config(scrapers=SCRAPER_CONFIG)
        logger.info("Configuration loaded and validated successfully")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise ValueError(f"Invalid configuration: {str(e)}")

def validate_selector_config(selector_config: Dict[str, Any], selector_name: str) -> bool:
    """Validate selector configuration.
    
    Args:
        selector_config: The selector configuration to validate
        selector_name: Name of the selector for logging purposes
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Check if selector_config is a dictionary
        if not isinstance(selector_config, dict):
            logger.error(f"Invalid selector configuration for {selector_name}: not a dictionary")
            return False
            
        # Check required keys
        required_keys = {'type', 'selector', 'output'}
        if not all(key in selector_config for key in required_keys):
            missing_keys = required_keys - set(selector_config.keys())
            logger.error(f"Missing required keys in selector {selector_name}: {missing_keys}")
            return False
            
        # Validate selector type
        valid_types = {'css', 'xpath', 'h1', 'h2', 'h3', 'p', 'div', 'span', 'a'}
        if selector_config['type'] not in valid_types:
            logger.error(f"Invalid selector type '{selector_config['type']}' for {selector_name}")
            return False
            
        # Check for empty selector
        if not selector_config['selector']:
            logger.error(f"Empty selector string for {selector_name}")
            return False
            
        # Validate output filename
        output = selector_config['output']
        if not output.endswith(('.json', '.csv')):
            logger.error(f"Invalid output filename for {selector_name}: must end with .json or .csv")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating selector {selector_name}: {str(e)}")
        return False

def validate_data(data: Union[Dict[str, Any], List[Dict[str, Any]]], format: str) -> None:
    """Validate data structure before saving.
    
    Args:
        data: The data to validate
        format: The output format ('json' or 'csv')
    
    Raises:
        DataValidationError: If data validation fails
    """
    if format == 'csv':
        if not isinstance(data, list):
            raise DataValidationError("CSV format requires data to be a list of dictionaries")
        if not data:
            raise DataValidationError("Cannot write empty data to CSV")
        if not all(isinstance(item, dict) for item in data):
            raise DataValidationError("All items in data must be dictionaries")
        if not all(item for item in data):
            raise DataValidationError("Data contains empty dictionaries")
        # Ensure all dictionaries have the same keys
        first_keys = set(data[0].keys())
        if not all(set(item.keys()) == first_keys for item in data):
            raise DataValidationError("All dictionaries must have the same keys")
    elif format == 'json':
        if not isinstance(data, (dict, list)):
            raise DataValidationError("JSON format requires data to be a dictionary or list")
    else:
        raise DataValidationError(f"Unsupported format: {format}")

def save_data(data: Union[Dict[str, Any], List[Dict[str, Any]]], output_path: str, format: str = 'json') -> None:
    """Save scraped data to a file.
    
    Args:
        data: The data to save (dictionary or list of dictionaries)
        output_path: Path where the file should be saved
        format: Output format ('json' or 'csv')
        
    Raises:
        DataValidationError: If data validation fails
        ValueError: If format is unsupported
        IOError: If file operations fail
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Validate data
        validate_data(data, format)
        
        # Create output directory if path contains directory component
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Only create directory if path has directory component
            os.makedirs(output_dir, exist_ok=True)
        
        # Save data based on format
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:  # csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                
        logger.info(f"Data saved successfully to {output_path}")
        
    except DataValidationError as e:
        logger.error(f"Data validation error: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data format: {str(e)}")
        raise
    except IOError as e:
        logger.error(f"Error saving data to {output_path}: {str(e)}")
        raise

def get_output_format_from_extension(filename: str) -> str:
    """Get the output format based on file extension.
    
    Args:
        filename: The output filename
        
    Returns:
        str: The output format ('json' or 'csv')
        
    Raises:
        ValueError: If the file extension is not supported
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.json':
        return 'json'
    elif ext == '.csv':
        return 'csv'
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def process_scraper_config(config: ScraperConfig) -> None:
    """Process a single scraper configuration."""
    logger = logging.getLogger(__name__)
    logger.info(f"Processing scraper: {config.name}")
    
    try:
        # Initialize scraper
        scraper = WebScraper(config.url)
        
        # Process each selector configuration
        for selector_name, selector_config in config.selectors.items():
            try:
                # Fetch page if not already fetched
                if scraper.soup is None:
                    scraper.fetch_page()
                
                # Extract data based on selector type
                if selector_config.type == 'css':
                    data = scraper.extract_css(selector_config.selector)
                elif selector_config.type == 'xpath':
                    data = scraper.extract_xpath(selector_config.selector)
                else:
                    data = scraper.extract_data(selector_config.type, selector_config.selector)
                
                if data and data.elements:
                    # Create output path and determine format
                    output_path = os.path.join(OUTPUT_DIR, selector_config.output)
                    output_format = get_output_format_from_extension(selector_config.output)
                    save_data(data.to_dict(), output_path, output_format)
                    logger.info(f"Saved {len(data.elements)} elements to {output_path}")
                else:
                    logger.warning(f"No data found for selector: {selector_name}")
                
            except Exception as e:
                logger.error(f"Error processing selector {selector_name}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error processing scraper {config.name}: {str(e)}")
        raise

def main():
    """Main function to run the scraper."""
    try:
        # Initialize logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Load and validate configuration
        config = load_config()
        
        # Process each scraper configuration
        for scraper_config in config.scrapers:
            try:
                logger.info(f"Starting scraper: {scraper_config.name}")
                process_scraper_config(scraper_config)
            except Exception as e:
                logger.error(f"Error processing scraper {scraper_config.name}: {str(e)}")
                continue
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()