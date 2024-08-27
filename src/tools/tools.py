# TODO: remove footer etc useless

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import os
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def dumb_find_text(text, context_len=200, search_words=['job', 'career', 'karriere'], main_url=''):
    # Define the words to search for
    
    # Create a regex pattern for case-insensitive search, allowing for partial matches
    pattern = re.compile(r'(' + '|'.join(search_words) + r')', re.IGNORECASE)
    
    # Find all matches and their positions
    matches = pattern.finditer(text)
    
    # Collect the surrounding text for each match
    results = []
    for match in matches:
        start = max(0, match.start() - context_len)
        end = min(len(text), match.end() + context_len)
        result = text[start:end]
        # dumb find url and add main_url eg '/content' -> 'example.com/content'
        if main_url:
            url_start_idx = result.find('/')
            if url_start_idx >= 0:
                result = result[:url_start_idx] + main_url + result[url_start_idx:]
        results.append(result)
    return results

def dumb_get_text(text, context_len=200, search_words=['job', 'career', 'karriere'], main_url=''):
    results = dumb_find_text(text, context_len, search_words, main_url)
    return '\n\n'.join(results)

def check_selenium_server(url):
    """Sprawdza dostępność serwera Selenium."""
    try:
        response = requests.get(url+'/status')
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    

def get_driver():
        try:
            selenium_url = os.environ['SELENIUM_URL']
            opts = Options()
            #opts.add_argument("--headless")
            opts.add_argument('--disable-cookies')
            opts.add_argument("--disable-notifications")
            opts.add_argument("--no-sandbox")
            opts.add_argument("window-size=1400,2100") 
            opts.add_argument('--disable-gpu')
            opts.add_argument('--disable-dev-shm-usage')
            
            opts.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ''Chrome/94.0.4606.81 Safari/537.36')
            if check_selenium_server(selenium_url):
                #print("Łączenie z zdalnym serwerem Selenium...")
                driver = webdriver.Remote(command_executor=selenium_url, options=opts)
            else:
                #print("Zdalny serwer Selenium niedostępny. Uruchamianie lokalnego WebDrivera...")
                driver = webdriver.Chrome(options=opts)
        except Exception as e:
            print('Error while getting selenium driver: ', e)
            raise(e)
        return driver

def get_page_source(url: str,
                    wait: float = 1.5,
                    headless: bool = True,
                    user_agent: str = "Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166"
                    ) -> str:
  """
  Get html text using selenium

  Args:
    url (str): The url from which html content is to be extracted 
    wait (float): time to implicitly wait for the website to load. default is 1.5 sec.
    headless (bool): use headless browser or not. default True
    user_agent (str): user agent. default "Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166"

  Returns (str): 
    html text
  """
  driver = get_driver()
  try:
      driver.get(url)
      driver.implicitly_wait(wait)
      time.sleep(wait)
      return driver.page_source
  except Exception as e:
      print(f'Error while getting page source {url}: ', e)
      return ''

def scroll_down(driver, wait=4):
    SCROLL_PAUSE_TIME = 0.5
      # Pobierz pełny HTML strony
    while True:
      previous_scrollY = driver.execute_script('return window.scrollY')
        #driver.execute_script('window.scrollBy( 0, 400 )' ) #Alternative scroll, a bit slower but reliable
      html = driver.find_element(By.TAG_NAME, 'html')
      html.send_keys(Keys.PAGE_DOWN)
      html.send_keys(Keys.PAGE_DOWN)
      html.send_keys(Keys.PAGE_DOWN) #Faster scroll, inelegant but works (Could translate to value scroll like above)
      time.sleep(SCROLL_PAUSE_TIME) #Give images a bit of time to load by waiting

        # Calculate new scroll height and compare with last scroll height
      if previous_scrollY == driver.execute_script('return window.scrollY'):
          break
    driver.implicitly_wait(wait)
    time.sleep(wait)

from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

def click_show_more(driver, key_phrase='SHOW MORE', wait=1):
    element_phrase = "//*[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'{0}')]".format(key_phrase)
    try:
        # Znajdź wszystkie elementy z tekstem "Show more" niezależnie od tagu
        
        prev_page_source = driver.page_source
        next_page_source = ''
        displayed = False
        while True:
            displayed = False
            elements = driver.find_elements(By.XPATH, element_phrase)
            for element in elements:
                if element.is_displayed():
                    ActionChains(driver).move_to_element(element).click(element).perform()
                    displayed = True
                    time.sleep(wait)  # Czekamy na załadowanie więcej ofert
                    
            next_page_source = driver.page_source

            if displayed and next_page_source != prev_page_source:
                prev_page_source == next_page_source
            else:
                break
                

    except Exception as e:
        print(f"Nie udało się kliknąć elementu: {e}")

def get_source_pages_iframe(url, show_more=False):
    page_source = ''
    source_pages = []
    driver = get_driver()
    try:
      # Otwórz stronę internetową
        driver.get(url)

        scroll_down(driver, 2)
        try:
            accept_all_button = driver.find_element(By.XPATH, "//*[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'accept all']")
            ActionChains(driver).click(accept_all_button).perform()
        except NoSuchElementException:
            pass
        if show_more:
            click_show_more(driver, key_phrase='SHOW MORE', wait=2)
            click_show_more(driver, key_phrase='SHOW ALL', wait=2)
      # Czekaj na załadowanie strony (np. czekaj na obecność elementu)
        source_pages = [driver.page_source]

      # Znajdź wszystkie iframe'y na stronie
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for index, iframe in enumerate(iframes):
            # Przełącz na iframe
            driver.switch_to.frame(iframe)
            try:
                # extracted function dont wait (???)
                scroll_down(driver, 5)
                iframe_source = driver.page_source
                source_pages.append(iframe_source)
            except TimeoutException:
                pass
            except WebDriverException:
                pass

            # Przełącz z powrotem do głównego dokumentu
            driver.switch_to.default_content()

    except TimeoutException:
        print("Loading took too much time!")
    except WebDriverException:
        print("Can'f find page")
    finally:
        # Zamknij przeglądarkę
        driver.quit()
    source_pages = list(set(source_pages))
    return source_pages

