import os
import re
from collections import defaultdict

from processing.web_search.job_board_finder import get_processed_text
from processing.web_search.web_scraper import WebScraper


class JobOfferAnalyzer:
    def __init__(self):
        self.key_words = os.environ["KEY_WORDS"].split(",")

    def find_key_words(self, text):
        appearances = defaultdict(int)
        for word in self.key_words:
            pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            matches = pattern.findall(text)
            appearances[word] = len(matches)
        return dict(appearances)

    def get_job_offer_technologies(self, job_offer_link):
        web_scraper = WebScraper()
        source_pages = web_scraper.get_page_source(job_offer_link)
        llm_texts = [get_processed_text(source_page, job_offer_link) for source_page in source_pages]
        appearances = [self.find_key_words(llm_text) for llm_text in llm_texts]
        appearances_sum = {key: sum(d.get(key, 0) for d in appearances) for key in self.key_words}
        return appearances_sum
