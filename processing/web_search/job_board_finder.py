import logging
from langchain_openai import ChatOpenAI

from processing.tools.process_html import get_processed_text
from processing.tools.tools import dumb_get_text
from processing.web_search.ai_output_schema import JobBoard
from processing.web_search.web_scraper import WebScraper


class JobBoardFinder:
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
        self.structured_llm = self.model.with_structured_output(JobBoard)

    def get_prompt(self, url):
        prompt_format = (
            "In input I give you a website of company. "
            "Find link in input to a subpage where that company has "
            "job board(offers jobs, careers for new employees).\n"
            "Link should exist in input I gave you. You need not use "
            "website, use only my input!\n"
            "The format should be: 'Your link: <LINK>\n"
            "webpage: {llm_friendly_webpage_text}"
        )

        web_scraper = WebScraper()
        page_source = web_scraper.get_page_source(url)
        llm_text = get_processed_text(
            page_source,
            url,
            job_board_url=url,
            important_words=["job", "career", "karriere"],
        )
        if len(llm_text) > 40000:
            logging.warning("SHORTEN LLM TEXT!!! url: {url}")
            # 1k overlap
            rest_llm_text = dumb_get_text(
                llm_text[35000:],
                context_len=200,
                search_words=["job", "career", "karriere"],
            )
            llm_text = llm_text[:36000] + rest_llm_text
        return prompt_format.format(llm_friendly_webpage_text=llm_text)

    def get_response(self, prompt):
        response = self.structured_llm.invoke(prompt)
        response = response.job_board

        # Process the response to extract the link
        # fix most model errors

        link = response[response.find("http") :]
        if link.find("]") != -1:
            link = link[: link.find("]")]
        if link.find(")") != -1:
            link = link[: link.find(")")]
        return link

    def find_job_board(self, url):
        prompt = self.get_prompt(url)
        return self.get_response(prompt)
