# TODO: remove footer etc useless

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
import os
import time


def check_selenium_server(url):
    """Sprawdza dostępność serwera Selenium."""
    try:
        response = requests.get(url+'/status')
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    
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
  try:
      selenium_url = os.environ['SELENIUM_URL']
      opts = Options()
      opts.add_argument("--headless")
      opts.add_argument("--no-sandbox")
      opts.add_argument("window-size=1400,2100") 
      opts.add_argument('--disable-gpu')
      opts.add_argument('--disable-dev-shm-usage')
      
      opts.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ''Chrome/94.0.4606.81 Safari/537.36')
      if check_selenium_server(selenium_url):
          print("Łączenie z zdalnym serwerem Selenium...")
          driver = webdriver.Remote(command_executor=selenium_url, options=opts)
      else:
          print("Zdalny serwer Selenium niedostępny. Uruchamianie lokalnego WebDrivera...")
          driver = webdriver.Chrome(options=opts)
      driver.get(url)
      driver.implicitly_wait(wait)

      return driver.page_source
  except Exception as e:
      print('Error while getting page source: ', e)
      return ''

def get_source_pages_iframe(url):
  page_source = ''
  selenium_url = os.environ['SELENIUM_URL']
  opts = Options()
  opts.add_argument("--headless")
  opts.add_argument("--no-sandbox")
  opts.add_argument("window-size=1400,2100") 
  opts.add_argument('--disable-gpu')
  opts.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ''Chrome/94.0.4606.81 Safari/537.36')
  if check_selenium_server(selenium_url):
      print("Łączenie z zdalnym serwerem Selenium...")
      driver = webdriver.Remote(command_executor=selenium_url, options=opts)
  else:
      print("Zdalny serwer Selenium niedostępny. Uruchamianie lokalnego WebDrivera...")
      driver = webdriver.Chrome(options=opts)

  try:
      # Otwórz stronę internetową
      driver.get(url)
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
      driver.implicitly_wait(2)
      # Czekaj na załadowanie strony (np. czekaj na obecność elementu)
      source_pages = [driver.page_source]

      # Znajdź wszystkie iframe'y na stronie
      iframes = driver.find_elements(By.TAG_NAME, 'iframe')
      for index, iframe in enumerate(iframes):
          # Przełącz na iframe
          driver.switch_to.frame(iframe)

          # Pobierz HTML zawartości iframe
          iframe_source = driver.page_source
          source_pages.append(iframe_source)

          # Przełącz z powrotem do głównego dokumentu
          driver.switch_to.default_content()

  except TimeoutException:
      print("Loading took too much time!")
  # written to handle when webpage at url does not exist
  except WebDriverException:
     return []
  finally:
      # Zamknij przeglądarkę
      driver.quit()
  source_pages = list(set(source_pages))
  return source_pages