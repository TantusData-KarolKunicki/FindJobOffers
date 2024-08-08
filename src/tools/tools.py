# TODO: remove footer etc useless

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

def get_source_pages_iframe(url):
  page_source = ''
  opts = Options()
  opts.add_argument("--headless")
  opts.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ''Chrome/94.0.4606.81 Safari/537.36')
  
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