

from web_search.career_link_pure import find_job_board_link_pure
from web_search.job_info import get_job_offers_technologies
from web_search.jobs_list import get_job_offers
import os

KEY_WORDS = os.environ['KEY_WORDS'].split(',')

def get_person_company_tech(linkedin, person_link):
    company_link, job_board_link, job_offers_links, company_technologies = '', '', {}, {key: 0 for key in KEY_WORDS}
    company_link = linkedin.get_person_info(person_link)['company_url']
    if company_link:
        job_board_link = find_job_board_link_pure(company_link)
        if job_board_link: 
            job_offers_links = get_job_offers(job_board_link)
            if job_offers_links:
                company_technologies = get_job_offers_technologies(job_offers_links)
    return company_technologies, person_link, company_link, job_board_link, job_offers_links


