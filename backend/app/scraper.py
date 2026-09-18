"""Optional Selenium scraper for live interview topics.

Disabled by default (ENABLE_SCRAPER=false) because it needs Chrome installed
and adds several seconds of latency. Results are cached per role.
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

SOURCE_URL = "https://github.com/topics/interview-questions"
PAGE_LOAD_TIMEOUT = 10


@lru_cache(maxsize=16)
def fetch_interview_topics(role: str) -> tuple[str, ...]:
    """Scrape repository titles about interview questions and turn them into prompts.

    Blocking — call it through `asyncio.to_thread`. Returns an empty tuple on failure.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as ec
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError:
        logger.warning("selenium is not installed; skipping scraper")
        return ()

    options = Options()
    for arg in ("--headless=new", "--disable-gpu", "--no-sandbox"):
        options.add_argument(arg)

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.get(SOURCE_URL)
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            ec.presence_of_element_located((By.TAG_NAME, "h3"))
        )
        titles = [el.text.strip() for el in driver.find_elements(By.TAG_NAME, "h3")[:5]]
        topics = tuple(
            f"As a {role}, walk me through the core concepts behind '{title}'. What would break first in production?"
            for title in titles
            if title
        )
        logger.info("Scraped %d topics for role %r", len(topics), role)
        return topics
    except Exception as exc:
        logger.warning("Scraping failed, falling back to question bank: %s", exc)
        return ()
    finally:
        if driver is not None:
            driver.quit()
