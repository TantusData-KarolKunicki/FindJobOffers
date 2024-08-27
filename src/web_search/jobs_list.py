import warnings
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from url_to_llm_text.get_llm_input_text import get_processed_text
from tools.tools import get_source_pages_iframe
from langchain_core.exceptions import OutputParserException


class JobOffer(BaseModel):
    job_name: str = Field(description="Job position name")
    job_link: str = Field(description="The link to the job offer")


class JobOffers(BaseModel):
    job_offers: List[JobOffer] = Field(...)


def split_string_on_newline(input_string: str, max_length: int = 20000) -> list:
    lines = input_string.splitlines(keepends=True)
    chunks = []
    current_chunk_lines = []
    current_length = 0

    for line in lines:
        line_length = len(line)
        if current_length + line_length > max_length:
            chunks.append(''.join(current_chunk_lines))
            current_chunk_lines = []  # Resetujemy linię
            current_length = 0  # Resetujemy długość

        current_chunk_lines.append(line)
        current_length += line_length

    if current_chunk_lines:
        chunks.append(''.join(current_chunk_lines))
    return chunks


def get_jobs_links(llm_text, llm_text_limit=40000):
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0, seed=0, top_p=0.001,
                       max_tokens=4096, n=1, frequency_penalty=0, presence_penalty=0)
    structured_llm = model.with_structured_output(JobOffers)

    prompt_format = """In input I give you a company webpage. Find jobs offers and links to subpage of that jobs offers in input.
                  Use only my input. Links should exist in webpage!\n

                  webpage: {llm_friendly_webpage_text}"""
    
    if len(llm_text) > llm_text_limit:
        llm_texts = split_string_on_newline(llm_text, llm_text_limit//2)
        job_offers = []
        for text in llm_texts:
            prompt = prompt_format.format(llm_friendly_webpage_text=text)
            try:
                job_offers_part = structured_llm.invoke(prompt)
            except OutputParserException as e:
                job_offers_part = get_jobs_links(text, len(text)//2+1)
            job_offers.extend(job_offers_part)
        job_offers = [offer for key, offers in job_offers for offer in offers]
        job_offers = JobOffers(job_offers=job_offers)
    else:
        
        prompt = prompt_format.format(llm_friendly_webpage_text=llm_text)
        try:
            job_offers = structured_llm.invoke(prompt)
        except OutputParserException as e:
            job_offers = get_jobs_links(llm_text, llm_text_limit//2)
    return job_offers

def get_job_offers(job_board_link, repeat=True):
    source_pages = get_source_pages_iframe(job_board_link, True)
    llm_texts = [get_processed_text(source_page, job_board_link) for source_page in source_pages]
    llm_texts = [llm_text for llm_text in llm_texts if len(llm_text) > 400]
    if len(llm_texts) > 10:
        print("TOO MANY LLM_TEXT")
        llm_texts = llm_texts[:10]
    warnings.filterwarnings("ignore", category=UserWarning)
    job_offers_links = [get_jobs_links(llm_text) for llm_text in llm_texts]
    warnings.filterwarnings("default", category=UserWarning)

    job_offers_links = [link.job_offers for link in job_offers_links]
    job_offers_links = [item for sublist in job_offers_links for item in sublist]
    # remove hallucinate links, duplicated in other location
    job_offers_links = {link.job_name: link.job_link for link in job_offers_links
                  if 'example' not in link.job_link
                  and 'company.com' not in link.job_link}
    # remove duplicated links

    # not work when job offer on job board
    """for key, value in job_offers_links.items():
        if value not in clear_job_offers_links.values():
            clear_job_offers_links[key] = value"""
    # it was not job board but was one link to job board
    # TODO: Fix that to do when only 1 job offer or job board + other link
    if len(job_offers_links.keys()) == 1 and repeat:
        return get_job_offers(next(iter(job_offers_links.values())), repeat=False)
    else:
        return job_offers_links


    
    