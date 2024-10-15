import logging
from langchain_core.exceptions import OutputParserException
from langchain_openai import ChatOpenAI

from processing.web_search.ai_output_schema import JobOffers
from processing.web_search.job_board_finder import get_processed_text
from processing.web_search.web_scraper import WebScraper


class JobBoardScraper:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-4o-mini-2024-07-18",
            temperature=0,
            seed=0,
            top_p=0.001,
            max_tokens=4096,
            n=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        self.input_max_len = 40000
        self.structured_llm = self.model.with_structured_output(JobOffers)

    def split_string_on_newline(self, input_string: str, max_length: int = 20000) -> list:
        lines = input_string.splitlines(keepends=True)
        chunks: list[str] = []
        current_chunk_lines: list[str] = []
        current_length = 0

        for line in lines:
            line_length = len(line)
            if current_length + line_length > max_length:
                chunks.append("".join(current_chunk_lines))
                current_chunk_lines = []
                current_length = 0

            current_chunk_lines.append(line)
            current_length += line_length

        if current_chunk_lines:
            chunks.append("".join(current_chunk_lines))
        return chunks

    def invoke_model(self, prompt, llm_text_limit):
        """counter = 0
        while counter <= 10:"""
        try:
            return self.structured_llm.invoke(prompt)
        except OutputParserException:
            return self.get_jobs_links(prompt, llm_text_limit // 2)
        """except LangSmithRateLimitError as e:
            print(f'Rate limit error encountered. Retrying: {e}')
            time.sleep(10)
            counter += 1"""

    def get_jobs_links(self, llm_text: str, llm_text_limit: int):
        prompt_format = (
            "In input I give you a company webpage. Find"
            "job offers and links to subpages of those job offers in input."
            "Use only my input. Links should exist on the webpage!\n"
            "webpage: {llm_friendly_webpage_text}"
        )

        # if input too long, but used in recursion with smaller llm_text_limit too cause output error
        # eg. Padentic error, cause no } at the end, cause output too long
        if len(llm_text) > llm_text_limit:
            llm_texts = self.split_string_on_newline(llm_text, llm_text_limit // 2)
            job_offers = []
            for text in llm_texts:
                prompt = prompt_format.format(llm_friendly_webpage_text=text)
                job_offers_part = self.invoke_model(prompt, llm_text_limit)
                job_offers.extend(job_offers_part.job_offers)
            return JobOffers(job_offers=job_offers)
        else:
            prompt = prompt_format.format(llm_friendly_webpage_text=llm_text)
            return self.invoke_model(prompt, llm_text_limit)

    def get_job_offers(self, job_board_link, repeat=True):
        web_scraper = WebScraper()
        source_pages = web_scraper.get_page_source(job_board_link, True, True, True)
        llm_texts = [get_processed_text(source_page, job_board_link) for source_page in source_pages]
        llm_texts = [llm_text for llm_text in llm_texts if len(llm_text) > 400]
        if len(llm_texts) > 10:
            logging.warning("Too many LLM_TEXT! job_board_link: {job_board_link}, repeat: {repeat}")
            llm_texts = llm_texts[:10]

        job_offers_list = [self.get_jobs_links(llm_text, self.input_max_len) for llm_text in llm_texts]

        # remove hallucinate links, duplicated in other location
        job_offers = {
            job_offer.job_name: job_offer.job_link
            for job_offers in job_offers_list
            for job_offer in job_offers.job_offers
            if "example" not in job_offer.job_link and "company.com" not in job_offer.job_link
        }

        # if only one link (mostly it's correct job board link)
        if len(job_offers.keys()) == 1 and repeat:
            return self.get_job_offers(next(iter(job_offers.values())), repeat=False)
        else:
            return job_offers
