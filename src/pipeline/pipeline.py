from web_search.career_link_pure import find_job_board_link_pure
from web_search.job_info import get_job_offers_technologies, get_job_offer_technologies
from web_search.jobs_list import get_job_offers
from web_search.google_search import get_google_job_links
import os
import time

def get_google_links(comapny_name):
        IMPORTANT_PAGES = os.environ['KEY_WORDS'].split(',')

        main_link, subpage_links = get_google_job_links(comapny_name)
        important_links = []
        for important_page in IMPORTANT_PAGES:
            important_links.extend([link for link in important_links if important_page in link])

        google_links = main_link[:3] + subpage_links[:3] + important_links
        google_links = set(google_links)
        return google_links

def get_comapnies_info_linkedin(company_link, google_links):
    job_board_link = ''
    job_offers_links_linkedin = {}

    start = time.time()
    job_board_link = find_job_board_link_pure(company_link)
    if job_board_link:
        if job_board_link not in google_links:
            unique = True
            job_offers_links_linkedin = get_job_offers(job_board_link)
        else:
             unique = False
             print("LINK JUZ W GOOGLE")
    print("linkedin time", time.time()-start)
    return job_board_link, job_offers_links_linkedin, unique

def get_companies_info_google(google_links):
    job_offers_links_google = {}

    start = time.time()
    for google_link in google_links:
        job_offers_links_google = job_offers_links_google | get_job_offers(google_link)
    print("google time ", time.time()-start)
    return job_offers_links_google

def get_comapnies_info(companies_names, companies_url=[], person_link=''):
    KEY_WORDS = os.environ['KEY_WORDS'].split(',')
    companies_info = []
    job_board_link = ''
    job_offers_links_linkedin = {}
    linkedin_uniqe = False
    job_offers_links_google = {}

    if not companies_url:
        companies_url = ['' for _ in companies_names]

    for company_link, comapny_name in zip(companies_url, companies_names):
        company_technologies_all = {key: 0 for key in KEY_WORDS}
        google_links = get_google_links(comapny_name)
        google_links = [google_link for google_link in google_links if 'linkedin' not in google_link]
        google_links = [google_link for google_link in google_links if 'indeed' not in google_link]
        google_links = [google_link for google_link in google_links if 'wikipedia' not in google_link]
        google_links = [google_link for google_link in google_links if 'instagram' not in google_link]
        google_links = [google_link.split('?srsltid')[0] for google_link in google_links]
        
        if company_link:
            companies_info_linkedin = get_comapnies_info_linkedin(company_link,
                                                                google_links)
            job_board_link, job_offers_links_linkedin, linkedin_uniqe = companies_info_linkedin
            job_offers_links_linkedin = {f"{key}_linkedin": value for key, value in job_offers_links_linkedin.items()}
        
        if comapny_name:
            job_offers_links_google = get_companies_info_google(google_links)
            job_offers_links_google = {f"{key}_google": value for key, value in job_offers_links_google.items()}
        
        job_offers_links = job_offers_links_linkedin | job_offers_links_google
        job_offers_links = {v: k for k, v in job_offers_links.items()}
        job_offers_links = {v: k for k, v in job_offers_links.items()}
        #if job_offers_links:
        #   company_technologies_all = get_job_offers_technologies(job_offers_links)
        
        for key, job_offer_link in job_offers_links.items():
            technologies = get_job_offer_technologies(job_offer_link)

            companies_info.append((person_link, 
                                comapny_name,
                                company_link,
                                job_board_link,
                                job_offer_link,
                                technologies,
                                key.split("_")[-1],
                                linkedin_uniqe
                                ))
    return companies_info

def get_person_company_tech(linkedin, person_link):
    start = time.time()
    person_info = linkedin.get_person_info(person_link)
    companies_url = person_info['companies_url']
    companies_names = [company['company_name'] for company in person_info['present_comapnies']]
    companies_job_board_linkedin = [company['jobSearchPageUrl'] for company in person_info['companies_info']]
    print("companies_url ", time.time()-start)
    companies_info = get_comapnies_info(person_link=person_link, 
                                        companies_url=companies_url, 
                                        companies_names=companies_names)

    return companies_info

def get_direct_company_tech(companies_names):
    start = time.time()
    companies_info = get_comapnies_info(companies_names=companies_names)
    print('Całkowity czas ', time.time()-start)
    return companies_info
