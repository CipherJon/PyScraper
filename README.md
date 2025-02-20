# Web Scraper

This is a simple web scraper built with Python. It fetches and parses web pages, extracting specific data according to the provided configuration.

## Requirements

- Python 3.x
- `requests` library
- `beautifulsoup4` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/web-scraper.git
    cd web-scraper
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Update the `url` variable in `main.py` to the target URL.
2. Run the scraper:
    ```sh
    python main.py
    ```

## Logging

Logs are saved to `logs/scraper.log` and also printed to the console.

## Configuration

You can modify the `scraper.py` file to change the tags and classes for data extraction according to your needs.

## License

This project is licensed under the MIT License.