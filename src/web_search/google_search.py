from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup
from tools.tools import get_driver


def get_google_job_links(company_name):
    driver = get_driver()

    query = f'{company_name} jobs'
    main_links = [] # Initiate empty list to capture final results
    subpage_link = []
    # Specify number of pages on google search, each page contains 10 #links
    n_pages = 1 
    for page in range(1, n_pages+1):
        url = "http://www.google.com/search?q=" + query + "&start=" + str((page - 1) * 10)
        driver.get(url)

        # main google results
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        search = soup.find_all('div', class_="yuRUbf")
        for h in search:
            main_links.append(h.a.get('href'))

        # link to subpages in google results check eg "clearscore jobs"
        search = soup.find_all('tr', class_=lambda value: value and value.startswith('mslg'))
        for tr in search:
            # Szukamy elementu <a> z atrybutem href
            a_tag = tr.find('a', href=True)
            if a_tag:
                subpage_link.append(a_tag['href'])  # Dodajemy link do listy

    driver.quit()
    return main_links, subpage_link




