
from url_to_llm_text.get_html_text import get_page_source
from url_to_llm_text.get_llm_input_text import get_processed_text 
import requests
import os
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from minify_html import minify
from inscriptis import get_text

def dump_get_text(text):
    # Define the words to search for
    search_words = ['job', 'career', 'karriere']
    
    # Create a regex pattern for case-insensitive search, allowing for partial matches
    pattern = re.compile(r'(' + '|'.join(search_words) + r')', re.IGNORECASE)
    
    # Find all matches and their positions
    matches = pattern.finditer(text)
    
    # Collect the surrounding text for each match
    results = []
    for match in matches:
        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 200)
        results.append(text[start:end])
    
    # Join all results into a single string
    return '\n\n'.join(results)

def get_processed_text(page_source: str, base_url: str,
                 html_parser: str ='lxml',
                 keep_images: bool =True, remove_svg_image: bool =True, remove_gif_image: bool =True, remove_image_types: list =[],
                 keep_webpage_links: bool =True,
                 remove_script_tag: bool =True, remove_style_tag: bool =True, remove_tags: list =[]
                 ) -> str:
  """
  process html text. This helps the LLM to easily extract/scrape data especially image links and web links.

  Args:
    page_source (str): html source text
    base_url (str): url of the html source.
    html_parser (str): which beautifulsoup html parser to use, defaults to 'lxml'
    keep_images (bool): keep image links. If False will remove image links from the text saving tokens to be processed by LLM. Default True
    remove_svg_image (bool): remove .svg image. usually not useful while scraping. default True
    remove_gif_image (bool): remove .gif image. usually not useful while scraping. default True
    remove_image_types (list): add any image extensions which you want to remove inside a list. eg: [.png]. Default []
    keep_webpage_links (bool): keep webpage links. if scraping job does not require links then can remove them to reduce input token count to LLM. Default True
    remove_script_tag (bool): True
    remove_style_tag (bool): =True
    remove_tags (list): = list of tags to be remove. Default []

  Returns (str):
    LLM ready input web page text
  """
  try:
    soup = BeautifulSoup(page_source, html_parser)
    
    # -------remove tags----------
    remove_tag = []
    if remove_script_tag:
      remove_tag.append('script')
    if remove_style_tag:
      remove_tag.append('style')
    remove_tag.extend(remove_tags)
    remove_tag = list(set(remove_tag))
    for tag in soup.find_all(remove_tag):
      try:
        tag.extract()
      except Exception as e:
        print('Error while removing tag: ', e)
        continue
    
    # --------process image links--------
    remove_image_type = []
    if remove_svg_image:
      remove_image_type.append('.svg')
    if remove_gif_image:
      remove_image_type.append('.gif')
    remove_image_type.extend(remove_image_types)
    remove_image_type = list(set(remove_image_type))
    for image in (images := soup.find_all('img')):
      try:
        if not keep_images:
          image.replace_with('')
        else:
          image_link = image.get('src')
          type_replaced = False
          if type(image_link)==str:
            if remove_image_type!=[]:
              for image_type in remove_image_type:
                if not type_replaced and image_type in image_link:
                  image.replace_with('')
                  type_replaced=True
            if not type_replaced:
              image.replace_with('\n' + urljoin(base_url, image_link) + ' ')
      except Exception as e:
          print('Error while getting image link: ', e)
          continue
    # ----------process website links-----------
    for link in (urls := soup.find_all('a', href=True)):
      try:
        if not keep_webpage_links:
          link.replace_with('')
        else:
          link.replace_with(link.text + ': ' + urljoin(base_url, link['href']) + ' ')
      except Exception as e:
          print('Error while getting webpage link: ', e)
          continue

    # -----------change text structure-----------
    body_content = soup.find('body')
    if body_content:
      try:
        minimized_body = minify(str(body_content))
        text = get_text(minimized_body)
        if text == '':
          text = dump_get_text(str(minimized_body))
          if text == '':
            text = dump_get_text(str(body_content))
      except:
        text = get_text(str(body_content))
        if text == '':
          text = dump_get_text(str(body_content))
    else:
      text = soup.get_text()
    if text == '':
        text = dump_get_text(str(soup))
    return text

  except Exception as e:
    print('Error while getting processed text: ', e)
    return ''

def find_job_board_link_pure(url):
    page_source = get_page_source(url)
    llm_text = get_processed_text(page_source, url)

    prompt_format = """In input I give you a website of company. 
                    Find link in input to a subpage where that company have job board(
                    offers jobs, careers for new employees).
                    Link should exist in input I gave you. You need not use 
                    website, use only my input!\n
                    The format should be: 'Your link: <LINK>\n
                    webpage: {llm_friendly_webpage_text}"""
    if len(llm_text) > 40000:
        print('SHORT LLM TEXT')
    prompt = prompt_format.format(llm_friendly_webpage_text=llm_text[:40000])

    api_key = os.environ["OPENAI_API_KEY"]
    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
    }
    payload = {
      "model": "gpt-4o-2024-05-13",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": prompt
            }
      ]}],
      'seed': 0,
      "temperature": 0,
      "top_p": 0.001,
      "max_tokens": 1024,
      "n": 1,
      "frequency_penalty": 0, "presence_penalty": 0
    }

    response = requests.post("https://api.openai.com/v1/chat/completions",
                              headers=headers, json=payload)
    response = response.json()['choices'][0]['message']['content']
    
    response = response[response.find('Your link:'):]
    

    link = response[response.find('http'):]
    if link.find(']') != -1:
        link = link[:link.find(']')]
    if link.find(')') != -1:
        link = link[:link.find(')')]   
    return link
