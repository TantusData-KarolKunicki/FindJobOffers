import time

import requests
from bs4 import BeautifulSoup
from linkedin_api import Linkedin
from linkedin_api.client import ChallengeException
from numpy.random import normal

from .linkedin_strategy import LinkedinStrategy


class LinkedinApi(LinkedinStrategy):
    def __init__(self, email, password):
        self.seed_url = "https://www.linkedin.com/uas/login"
        self.login_url = "https://www.linkedin.com/checkpoint/lg/login-submit"
        self.verify_url = "https://www.linkedin.com/checkpoint/challenge/verify"
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.api = self.login()

    def login(self):
        try:
            api = Linkedin(self.email, self.password)
        except ChallengeException:
            self.login_pin(self.email, self.password)
            api = Linkedin(self.email, self.password)
        return api

    def login_pin(self, email, password):
        self.session.get(self.seed_url)
        text = self.session.get(self.seed_url).text
        soup = BeautifulSoup(text, "html.parser")
        payload = {
            "session_key": email,
            "loginCsrfParam": soup.find("input", {"name": "loginCsrfParam"})["value"],
            "session_password": password,
        }

        r = self.session.post(self.login_url, data=payload)
        soup = BeautifulSoup(r.text, "html.parser")
        self.verify_pin(soup)

    def verify_pin(self, soup):
        pin = input("Check the PIN in your inbox and enter here:\n")
        payload = {
            "csrfToken": soup.find("input", {"name": "csrfToken"})["value"],
            "pageInstance": soup.find("input", {"name": "pageInstance"})["value"],
            "resendUrl": soup.find("input", {"name": "resendUrl"})["value"],
            "challengeId": soup.find("input", {"name": "challengeId"})["value"],
            "language": "en-US",
            "displayTime": soup.find("input", {"name": "displayTime"})["value"],
            "challengeSource": soup.find("input", {"name": "challengeSource"})["value"],
            "requestSubmissionId": soup.find("input", {"name": "requestSubmissionId"})["value"],
            "challengeType": soup.find("input", {"name": "challengeType"})["value"],
            "challengeData": soup.find("input", {"name": "challengeData"})["value"],
            "challengeDetails": soup.find("input", {"name": "challengeDetails"})["value"],
            "failureRedirectUri": soup.find("input", {"name": "failureRedirectUri"})["value"],
            "pin": pin,
        }
        self.session.post(self.verify_url, data=payload)

    def get_profile(self, linkedin_name):
        self.imitate_user_sleep(4)
        profile = self.api.get_profile(linkedin_name)
        return profile

    def get_company_data(self, company_id):
        self.imitate_user_sleep(4)
        return self.api.get_company(company_id)

    def get_companies_data(self, present_comapnies):
        companies_info = [self.get_company_data(company["id"]) for company in present_comapnies]
        return companies_info

    def get_comapnies_url(self, companies_info):
        return [self.get_comapny_url(company_info) for company_info in companies_info]

    def get_person_info(self, link):
        linkedin_name = self.get_linkedin_name(link)
        # sometimes need clear linkedin api cookies, just uninstall and install library
        profile = self.get_profile(linkedin_name)
        present_comapnies = self.get_current_companies(profile)
        companies_info = self.get_companies_data(present_comapnies)
        companies_url = self.get_comapnies_url(companies_info)
        return {
            "linkedin_name": linkedin_name,
            "profile": profile,
            "present_comapnies": present_comapnies,
            "companies_info": companies_info,
            "companies_url": companies_url,
        }

    @staticmethod
    def get_linkedin_name(link):
        linkedin_name = link.split("/")[4]
        return linkedin_name

    @staticmethod
    def get_current_companies(profile):
        companies = profile["experience"]
        present_comapnies = [company for company in companies if "endDate" not in company["timePeriod"]]
        # if 2 jobs in one comapny ther's only 1 comapnyUrn
        present_comapnies = [company for company in present_comapnies if "companyUrn" in company]
        return [
            {
                "company_name": company["companyName"],
                "id": company["companyUrn"].split(":")[3],
            }
            for company in present_comapnies
        ]

    @staticmethod
    def get_comapny_url(company_data):
        if "companyPageUrl" in company_data:
            return company_data["companyPageUrl"]
        elif "callToAction" in company_data:
            if "url" in company_data["callToAction"]:
                return company_data["callToAction"]["url"]
        return ""

    @staticmethod
    def imitate_user_sleep(number=2):
        # Calculate the values 25% less and 25% more than the given number
        lower_bound = number * 0.75
        upper_bound = number * 1.25

        # Set the mean (mu) as the given number
        mu = number

        # Calculate the standard deviation (sigma)
        sigma = (upper_bound - lower_bound) / 4  # Since we want ±2σ to cover 25% less and 25% more
        # to make sure no infinity loop
        counter = 0
        while counter < 10:
            # Generate a number from the normal distribution
            random_number = normal(mu, sigma)

            # Check if the number is within the desired range
            if lower_bound <= random_number <= upper_bound:
                time.sleep(random_number)
                return
            counter += 1
        time.sleep(number + 1.03 * number)

    @staticmethod
    def show_link_data(data):
        print("#" * 30)
        print(f'Profile Name: {data["linkedin_name"]}')
        print(f'Company name: {data["company_name"]}')
        print(f'Company id: {data["comapny_id"]}')
        print(f'Company url: {data["company_url"]}')
