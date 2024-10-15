import logging
import time
import urllib.parse
import os

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from processing.tools.tools import get_driver


class WebScraper:
    def __init__(self):
        self.driver = None

    def generate_page_num_xpath(self, num):
        return """
        //*[
            contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'page {num}')
            or
            contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'page {num}')
            or
            contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'page {num}')
        ]
        """

    def generate_next_page_xpath(self):
        return """
        //body//*[
            not(ancestor::header) and
            (
                contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next page')
                or
                contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next page')
                or
                contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')
                or
                translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'next'
            )
        ]
        """

    def generate_search_jobs_xpath(self):
        return """
            //body//input[
                (contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search jobs')
                or
                contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search jobs'))
                and not(ancestor::header)
                and not(ancestor::*[@id='mapsearch'])
            ]
            |
            //body//a[
                contains(@class, 'button')
                and
                contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search jobs')
                and
                not(ancestor::header)
                and
                not(ancestor::*[@id='mapsearch'])
            ]
        """

    def sort_priority(self, element):
        tag_name = element.tag_name
        element_class = element.get_attribute("class")
        element_type = element.get_attribute("type")

        tag_priority = {
            "button": 0,
            "a": 1 if "button" == element_class else (2 if "submit" in element_type else 5),
            "input": 3 if element_type == "submit" else 4,
            "div": 7,
        }

        return tag_priority.get(tag_name, 6)

    def scroll_down(self, wait=1, max_retries=3):
        SCROLL_PAUSE_TIME = 0.5
        attempts = 0

        while attempts < max_retries:
            try:
                while True:
                    previous_scrollY = self.driver.execute_script("return window.scrollY")
                    html = self.driver.find_element(By.TAG_NAME, "html")
                    html.send_keys(Keys.PAGE_DOWN)
                    html.send_keys(Keys.PAGE_DOWN)
                    html.send_keys(Keys.PAGE_DOWN)
                    time.sleep(SCROLL_PAUSE_TIME)
                    if previous_scrollY == self.driver.execute_script("return window.scrollY"):
                        break

                self.driver.implicitly_wait(wait)
                time.sleep(wait)
                break
            except WebDriverException:
                attempts += 1
                if attempts < max_retries:
                    self.driver.refresh()
                    time.sleep(wait)
                else:
                    raise

    def click_show_more(self, key_phrase="SHOW MORE", wait=1, url=""):
        MAX_SHOW_MORE = 10
        element_phrase = """
        //*[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{0} {1}')
        or
        translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')=
                                                                                concat('{0}', ' ', number(), ' ', '{1}')
        or
        contains(translate(@aria-label, 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{0} {1}')]
        """.format(
            key_phrase.split()[0], key_phrase.split()[1]
        )

        try:
            prev_page_source = self.driver.page_source
            counter = 0
            while counter < MAX_SHOW_MORE:
                displayed = False
                elements = self.driver.find_elements(By.XPATH, element_phrase)
                for element in elements:
                    if element.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            element,
                        )
                        time.sleep(0.5)
                        ActionChains(self.driver).move_to_element(element).click(element).perform()
                        displayed = True
                        time.sleep(wait)
                counter += 1

                next_page_source = self.driver.page_source
                if not displayed or next_page_source == prev_page_source:
                    break
                prev_page_source = next_page_source
        except Exception:
            logging.debug(
                "Nie udało się kliknąć elementu. url: {url}, current url: {driver.current_url}, key_phrase: {key_phrase}"
            )

    def search_jobs_button(self):
        xpath_expression = self.generate_search_jobs_xpath()
        try:
            elements = self.driver.find_elements(By.XPATH, xpath_expression)
            sorted_elements = sorted(elements, key=self.sort_priority)
            element = next((elem for elem in sorted_elements if elem.is_displayed()), None)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                element,
            )
            time.sleep(1)
            original_window_handles = self.driver.window_handles
            ActionChains(self.driver).move_to_element(element).click(element).perform()
            time.sleep(2)
            new_window_handles = self.driver.window_handles
            if len(new_window_handles) > len(original_window_handles):
                self.driver.switch_to.window(new_window_handles[-1])
                source_pages = self.scrap_page(pagination=True)
                self.driver.switch_to.window(original_window_handles[0])
            else:
                source_pages = self.scrap_page(pagination=True)
        except Exception:
            source_pages = []
        return source_pages

    def handle_pagination(self, pagination="num_bar", pagination_num=1):
        PAGINATION_LIMIT = int(os.environ["PAGINATION_LIMIT"])
        if pagination_num >= PAGINATION_LIMIT:
            return [], False

        if pagination == "next":
            xpath_expression = self.generate_next_page_xpath()
        elif pagination == "num_bar":
            xpath_expression = self.generate_page_num_xpath(pagination_num + 1)

        try:
            element = next(
                (el for el in self.driver.find_elements(By.XPATH, xpath_expression) if el.tag_name != "div"),
                None,
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                element,
            )
            time.sleep(1)
            ActionChains(self.driver).move_to_element(element).click(element).perform()
            time.sleep(1)
            source_pages = [self.driver.page_source]
            source_pages.extend(self.get_iframes())
            next_page, _ = self.handle_pagination(pagination, pagination_num + 1)
            source_pages.extend(next_page)
            return source_pages, True
        except Exception:
            return [], False

    def click_cookies(self):
        # cookies by OneTrust
        try:
            element = self.driver.find_element(By.XPATH, "//button[@id='onetrust-accept-btn-handler']")
            ActionChains(self.driver).click(element).perform()
        except Exception:
            pass

        # cookies by TrustArc
        try:
            WebDriverWait(self.driver, 1).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (
                        By.XPATH,
                        '//iframe[@title="TrustArc Cookie Consent Manager"]',
                    )
                )
            )
            WebDriverWait(self.driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Agree and Proceed']"))
            ).click()
        except Exception:
            pass

        # Other cookies
        phrases = ["accept all", "reject all"]
        for phrase in phrases:
            try:
                accept_all_button = self.driver.find_element(
                    By.XPATH,
                    (
                        "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '"
                        + phrase
                        + "')]"
                    ),
                )
                ActionChains(self.driver).click(accept_all_button).perform()
                break
            except Exception:
                pass

    def prepare_driver(self, url, show_more=False, cookies=False):
        self.driver.get(url)
        time.sleep(1)
        self.scroll_down()
        if cookies:
            self.click_cookies()
            time.sleep(1)
        if show_more:
            self.click_show_more(key_phrase="SHOW MORE", url=url)

    def get_iframes(self):
        source_pages = []
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                self.driver.switch_to.frame(iframe)
                self.scroll_down()
                source_pages.append(self.driver.page_source)
            except Exception:
                pass
            finally:
                self.driver.switch_to.default_content()
        return source_pages

    def scrap_page(self, url="", pagination=False, search_job_button=False):
        source_pages = []
        try:
            source_pages = [self.driver.page_source]
            if pagination:
                next_pages, _ = self.handle_pagination("num_bar", 1)
                source_pages.extend(next_pages)
            if search_job_button:
                source_pages.extend(self.search_jobs_button())
        except WebDriverException as e:
            logging.error(
                f"Error scraping page {url}. pagination: {pagination}, search_job_button: {search_job_button}, error: {e}"
            )
        finally:
            self.driver.quit()
        return source_pages

    def get_page_source(self, url, show_more=False, pagination=False, search_job_button=False):
        url = urllib.parse.quote(url, safe=":/=?")
        source_pages = []
        self.driver = get_driver()

        try:
            self.prepare_driver(url=url, show_more=show_more, cookies=True)
        except TimeoutException as e:
            logging.error(
                f"Error too long load page {url}. show_more: {show_more}, pagination: {pagination}, search_job_button: {search_job_button}, error: {e}"
            )
        except WebDriverException as e:
            logging.error(
                f"Error cant find page page {url}. show_more: {show_more}, pagination: {pagination}, search_job_button: {search_job_button}, error: {e}"
            )
            pass

        source_pages = self.scrap_page(url=url, pagination=pagination, search_job_button=search_job_button)

        source_pages = list(set(source_pages))
        return source_pages
