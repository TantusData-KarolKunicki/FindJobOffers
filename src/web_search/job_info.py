import re
from collections import defaultdict
import os
from url_to_llm_text.get_llm_input_text import get_processed_text
from tools.tools import get_source_pages_iframe


def find_key_words(text):
    KEY_WORDS = os.environ['KEY_WORDS'].split(',')
    appearances = defaultdict(int)

    for word in KEY_WORDS:
        pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
        matches = pattern.findall(text)
        appearances[word] = len(matches)

    appearances = dict(appearances)
    return appearances


def get_technologies(job_offer_link):
    KEY_WORDS = os.environ['KEY_WORDS'].split(',')
    source_pages = get_source_pages_iframe(job_offer_link)
    llm_texts = [get_processed_text(source_page, job_offer_link) for source_page in source_pages]
    appearances = [find_key_words(llm_text) for llm_text in llm_texts]
    appearances_sum = {key: sum(d[key] for d in appearances) for key in KEY_WORDS}
    return appearances_sum


def get_job_offers_technologies(job_offers_links):
    KEY_WORDS = os.environ['KEY_WORDS'].split(',')
    appearances_key_words = [get_technologies(job_offer_link) for job_offer_link in job_offers_links.values()]
    appearances_key_words = {key: sum(d[key] for d in appearances_key_words) for key in KEY_WORDS}
    return appearances_key_words