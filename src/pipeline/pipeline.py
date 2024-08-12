from web_search.career_link_pure import find_job_board_link_pure
from web_search.job_info import get_job_offers_technologies
from web_search.jobs_list import get_job_offers
import os
import time


def get_person_company_tech(linkedin, person_link):
    KEY_WORDS = os.environ['KEY_WORDS'].split(',')
    company_link, job_board_link, job_offers_links, company_technologies = '', '', {}, {key: 0 for key in KEY_WORDS}
    start = time.time()
    company_link = linkedin.get_person_info(person_link)['company_url']
    print("company_link ", time.time()-start)
    if company_link:
        start = time.time()
        job_board_link = find_job_board_link_pure(company_link)
        print("job_board_link ", time.time()-start)
        if job_board_link:
            start = time.time()
            job_offers_links = get_job_offers(job_board_link)
            print("job_offers_links ", time.time()-start)
            if job_offers_links:
                start = time.time()
                company_technologies = get_job_offers_technologies(job_offers_links)
                print("company_technologies ", time.time()-start)
    return company_technologies, person_link, company_link, job_board_link, job_offers_links


