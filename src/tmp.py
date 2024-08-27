from pipeline.pipeline import get_person_company_tech
from web_search.jobs_list import get_job_offers
from web_search.career_link_pure import find_job_board_link_pure
from linkedin.linkedin_adapter import LinkedinAdapter
import os 
from dotenv import load_dotenv
from pprint import pprint
from pipeline.pipeline import get_person_company_tech
from web_search.google_search import get_google_job_links

load_dotenv(load_dotenv('../config/flask.env'))
linkedin = LinkedinAdapter(os.environ['EMAIL_LINKEDIN'], os.environ['PASSWORD_LINKEDIN'])

#result = linkedin.get_person_info('https://www.linkedin.com/in/idan-zalzberg-a2300013/')


result = get_person_company_tech(linkedin, 'https://www.linkedin.com/in/kontaurov')
#result = find_job_board_link_pure('http://www.manning.com/')
#result = get_job_offers('http://www.manning.com/careers')
#pprint(result)
# Użycie funkcji

"""
company_name = 'clearscore'
links = get_google_job_links(company_name)
pprint(links)
"""