import warnings
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from url_to_llm_text.get_llm_input_text import get_processed_text
from tools.tools import get_source_pages_iframe


class JobOffer(BaseModel):
    job_name: str = Field(description="Job position name")
    job_link: str = Field(description="The link to the job offer")


class JobOffers(BaseModel):
    job_offers: List[JobOffer] = Field(...)

def get_jobs_links(llm_text):
    model = ChatOpenAI(model="gpt-4o-2024-05-13", temperature=0, seed=0, top_p=0.001,
                       max_tokens=4096, n=1, frequency_penalty=0, presence_penalty=0)
    structured_llm = model.with_structured_output(JobOffers)

    prompt_format = """In input I give you a company webpage. Find jobs offers and links to subpage of that jobs offers in input.
                  Use only my input. Links should exist in webpage!\n

                  webpage: {llm_friendly_webpage_text}"""
    if len(llm_text) > 40000:
        print('SHORT LLM TEXT')
        llm_text = llm_text[:40000]
    prompt = prompt_format.format(llm_friendly_webpage_text=llm_text)
    job_offers = structured_llm.invoke(prompt)
    return job_offers

def get_job_offers(job_board_link, repeat=True):
    source_pages = get_source_pages_iframe(job_board_link)
    llm_texts = [get_processed_text(source_page, job_board_link) for source_page in source_pages]

    warnings.filterwarnings("ignore", category=UserWarning)
    job_offers_links = [get_jobs_links(llm_text) for llm_text in llm_texts]
    warnings.filterwarnings("default", category=UserWarning)

    job_offers_links = [link.job_offers for link in job_offers_links]
    job_offers_links = [item for sublist in job_offers_links for item in sublist]
    # remove hallucinate links
    job_offers_links = {link.job_name: link.job_link for link in job_offers_links
                  if 'example' not in link.job_link
                  and 'company.com' not in link.job_link}
    # remove duplicated links
    clear_job_offers_links = {}
    for key, value in job_offers_links.items():
        if value not in clear_job_offers_links.values():
            clear_job_offers_links[key] = value
    # it was not job board but was one link to job board
    # TODO: Fix that to do when only 1 job offer or job board + other link
    # TODO: should disable links used to find source_code
    if len(clear_job_offers_links.keys()) == 1 and repeat:
        return get_job_offers(next(iter(clear_job_offers_links.values())), repeat=False)
    else:
        return clear_job_offers_links


    
    