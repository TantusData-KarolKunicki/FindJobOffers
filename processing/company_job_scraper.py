import os
import time
import urllib.parse
from collections import defaultdict
import logging

from processing.web_search.google_search import google_search
from processing.web_search.job_board_finder import JobBoardFinder
from processing.web_search.job_board_scraper import JobBoardScraper
from processing.web_search.job_offer_analyzer import JobOfferAnalyzer


class CompanyJobScraper:
    def __init__(self):
        self.KEY_WORDS = os.environ["KEY_WORDS"].split(",")
        self.IMPORTANT_PAGES = os.environ["IMPORTANT_PAGES"].split(",")
        self.BANNED_PAGES = os.environ["BANNED_PAGES"].split(",")

    def get_google_links(
        self,
        company_name: str,
        search_range: int = 3,
        subpage_search_range: int = 3,
    ):
        main_links, subpage_links = google_search(f"{company_name} jobs")

        important_links = []
        for important_page in self.IMPORTANT_PAGES:
            important_links.extend([link for link in main_links if important_page in link.lower()])

        google_links = main_links[:search_range] + subpage_links[:subpage_search_range] + important_links
        google_links = set(google_links)

        for banned_page in self.BANNED_PAGES:
            google_links = [google_link for google_link in google_links if banned_page not in google_link]
        google_links = [google_link.split("?srsltid")[0] for google_link in google_links]
        return google_links

    def get_jobs(self, links: list):
        job_offers_links = {}
        job_board_scraper = JobBoardScraper()
        """job_board_finder = JobBoardFinder()
        job_board_links = [link if is_job_board else job_board_finder.find_job_board(link)
                           for link, is_job_board in zip(links, is_job_board_list)]"""

        for link in links:
            job_offers_links.update(job_board_scraper.get_job_offers(link))

        return job_offers_links  # , job_board_links

    """def get_person_company_tech(self, linkedin: LinkedinSingleton, person_link: str):
        person_info = linkedin.get_person_info(person_link)
        companies_url = person_info['companies_url']
        companies_names = [company['company_name'] for company in person_info['present_comapnies']]
        companies_job_board_linkedin = [company['jobSearchPageUrl'] for company in person_info['companies_info']]
        companies_info, google_links = self.get_comapnies_info(
            person_link=person_link, companies_url=companies_url, companies_names=companies_names)

        return companies_info, google_links"""

    def merge_jobs_links(self, jobs_links_direct, jobs_links_google):
        jobs_links_google = {f"{key}_google": value for key, value in jobs_links_google.items()}
        jobs_links_direct = {f"{key}_direct": value for key, value in jobs_links_direct.items()}
        job_offers_links = jobs_links_direct | jobs_links_google
        # job_offers_links = {val: key for key, val in job_offers_links.items()}
        grouped_job_names = defaultdict(list)
        for job_name, link in job_offers_links.items():
            grouped_job_names[link].append(job_name)
        job_offers_links = dict(grouped_job_names)
        job_offers_links = {
            urllib.parse.quote(link, safe=":/=?"): job_names for link, job_names in job_offers_links.items()
        }
        return job_offers_links

    def get_company_tech(self, company_name="", company_link=""):
        start = time.time()
        short_company_name = company_name.split("|")[0]
        company_info, google_links = self.get_companies_info(company_name=short_company_name, company_link=company_link)
        measured_time = time.time() - start
        logging.info(f"Całkowity czas {short_company_name} = {measured_time}")
        return company_info, measured_time, google_links

    def get_companies_info(self, company_name="", company_link=""):
        companies_info = []
        job_board_link = ""
        google_links = []
        jobs_links_direct = {}
        jobs_links_google = {}
        linkedin_unique = False

        if company_name:
            google_links = self.get_google_links(company_name)
            jobs_links_google = self.get_jobs(google_links)

        if company_link:
            job_board_finder = JobBoardFinder()
            job_board_link = job_board_finder.find_job_board(company_link)
            if job_board_link not in google_links:
                jobs_links_direct = self.get_jobs([job_board_link])
                jobs_links_direct = {
                    key: val for key, val in jobs_links_direct.items() if key in jobs_links_google.keys()
                }
                if jobs_links_direct:
                    linkedin_unique = True

        job_offers_links = self.merge_jobs_links(jobs_links_direct, jobs_links_google)

        job_offer_analyzer = JobOfferAnalyzer()
        for job_offer_link, job_names in job_offers_links.items():
            technologies = job_offer_analyzer.get_job_offer_technologies(job_offer_link)

            companies_info.append(
                {
                    "company_name": company_name,
                    "company_link": company_link,
                    "job_board_link": job_board_link,
                    "linkedin_unique": linkedin_unique,
                    "job_names": ["_".join(job_name.split("_")[:-1]) for job_name in job_names],
                    "job_offer_link": job_offer_link,
                    "job_sources": [job_name.split("_")[-1] for job_name in job_names],
                    "technologies": technologies,
                }
            )
        return companies_info, google_links
