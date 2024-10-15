import urllib.parse

from bs4 import BeautifulSoup

from processing.tools.tools import get_driver


def google_search(query):
    driver = get_driver()
    main_links = []  # Initiate empty list to capture final results
    subpage_link = []
    # Specify number of pages on google search, each page contains 10 #links
    page = 1
    query = urllib.parse.quote(query, safe=":/=?")
    url = "http://www.google.com/search?q=" + query + "&start=" + str((page - 1) * 10)
    driver.get(url)

    # main google results
    soup = BeautifulSoup(driver.page_source, "html.parser")
    search = soup.find_all("div", class_="yuRUbf")
    for h in search:
        main_links.append(h.a.get("href"))

    # link to subpages in google results check eg "clearscore jobs"
    search = soup.find_all("tr", class_=lambda value: value and value.startswith("mslg"))
    for tr in search:
        # Szukamy elementu <a> z atrybutem href
        a_tag = tr.find("a", href=True)
        if a_tag:
            subpage_link.append(a_tag["href"])  # Dodajemy link do listy

    driver.quit()
    return main_links, subpage_link
