import logging
import os
import re
from typing import List

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def dumb_find_text(
    text,
    context_len=200,
    search_words=["job", "career", "karriere"],
    main_url="",
) -> List[str]:
    # Create a regex pattern for case-insensitive search, allowing for partial matches
    pattern = re.compile(r"(" + "|".join(search_words) + r")", re.IGNORECASE)
    matches = pattern.finditer(text)

    # Collect the surrounding text for each match
    results = []
    for match in matches:
        start = max(0, match.start() - context_len)
        end = min(len(text), match.end() + context_len)
        result = text[start:end]
        # dumb find url and add main_url eg '/content' -> 'example.com/content'
        if main_url:
            url_start_idx = result.find("/")
            if url_start_idx >= 0:
                result = result[:url_start_idx] + main_url + result[url_start_idx:]
        results.append(result)
    return results


def dumb_get_text(
    text,
    context_len=200,
    search_words=["job", "career", "karriere"],
    main_url="",
):
    results = dumb_find_text(text, context_len, search_words, main_url)
    return "\n\n".join(results)


def check_selenium_server(url):
    """Sprawdza dostępność serwera Selenium."""
    try:
        response = requests.get(url + "/status")
        return response.status_code == 200
    except requests.ConnectionError:
        return False


def get_driver():
    class IgnoreChromeDriverWarning(logging.Filter):
        def filter(self, record):
            print(record.getMessage())
            # Filter out the specific ChromeDriver warning message
            return "chromedriver version" not in record.getMessage().lower()

    logging.getLogger().addFilter(IgnoreChromeDriverWarning())
    try:
        selenium_url = os.environ["SELENIUM_URL"]
        opts = Options()
        if os.environ["HEADLESS"] == "true":
            opts.add_argument("--headless")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--no-sandbox")
        opts.add_argument("window-size=1400,2100")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--mute-audio")

        # opts.add_argument('--log-level=3')

        opts.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/94.0.4606.81 Safari/537.36"
        )
        if check_selenium_server(selenium_url):
            # print("Łączenie z zdalnym serwerem Selenium...")
            driver = webdriver.Remote(command_executor=selenium_url, options=opts)
        else:
            # print("Zdalny serwer Selenium niedostępny. Uruchamianie lokalnego WebDrivera...")
            driver = webdriver.Chrome(options=opts)
    except Exception as e:
        logging.error(f"Error while getting selenium driver: {e}")
        raise (e)
    return driver
