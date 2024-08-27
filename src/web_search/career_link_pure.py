
from xml.etree.ElementPath import find
from tools.tools import get_page_source, dumb_get_text, dumb_find_text
import requests
import os
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from minify_html import minify
from inscriptis import get_text
from langchain.prompts import PromptTemplate
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
import warnings


def get_processed_text(page_source: str, base_url: str,
                 html_parser: str ='lxml',
                 keep_images: bool =True, remove_svg_image: bool =True, remove_gif_image: bool =True, remove_image_types: list =[],
                 keep_webpage_links: bool =True,
                 remove_script_tag: bool =True, remove_style_tag: bool =True, remove_tags: list =[],
                 job_board_url = '', important_words=[]
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
    important_context = []
    for tag in soup.find_all(remove_tag):
      if job_board_url:
        important_context.extend(dumb_find_text(str(tag), context_len=50, main_url=job_board_url))
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
    def find_important_words(important_words, text):
        if important_words:
          pattern = re.compile(r'(' + '|'.join(important_words) + r')', re.IGNORECASE)
      
          # Find all matches and their positions
          matches = pattern.finditer(text)
          return any(matches)
        else:
          return False

      
    def track_important_words(important_words, text, new_text):
        important_word_status = find_important_words(important_words, text)
        new_important_word_status = find_important_words(important_words, new_text)
        if new_important_word_status != important_word_status:
          return dumb_find_text(text, context_len=50)
        else:
          return []
    body_content = soup.find('body')

    important_context.extend(track_important_words(important_words=important_words, 
                                                   text=str(soup),
                                                     new_text=str(body_content)))
    if body_content:
      try:
        minimized_body = minify(str(body_content))
        important_context.extend(track_important_words(important_words=important_words, 
                                                   text=str(body_content),
                                                     new_text=str(minimized_body)))
        text = get_text(minimized_body)
        important_context.extend(track_important_words(important_words=important_words, 
                                                   text=str(minimized_body),
                                                     new_text=str(text)))
        if text == '':
          text = dumb_get_text(str(minimized_body))
          if text == '':
            text = dumb_get_text(str(body_content))
      except:
        text = get_text(str(body_content))
        if text == '':
          text = dumb_get_text(str(body_content))
    else:
      text = soup.get_text()
    if text == '':
        text = dumb_get_text(str(soup))
    important_context = '\n\n'.join(important_context)
    text = text + important_context
    return text

  except Exception as e:
    print('Error while getting processed text: ', e)
    return ''
  
class JobBoard(BaseModel):
    job_board: str = Field(description=' The job board link')


def find_job_board_link_pure(url):
    page_source = get_page_source(url, wait=10)
    llm_text = get_processed_text(page_source, url, job_board_url=url, 
                                  important_words=['job', 'career', 'karriere'])

    prompt_format = """In input I give you a website of company. 
                    Find link in input to a subpage where that company have job board(
                    offers jobs, careers for new employees).
                    Link should exist in input I gave you. You need not use 
                    website, use only my input!\n
                    The format should be: 'Your link: <LINK>\n
                    webpage: {llm_friendly_webpage_text}"""
    if len(llm_text) > 40000:
        print('SHORTEN LLM TEXT')
        # 1k overlap
        rest_llm_text = dumb_get_text(llm_text[35000:], context_len=200, search_words=['job', 'career', 'karriere'])
        llm_text = llm_text[:36000] + rest_llm_text

    prompt = prompt_format.format(llm_friendly_webpage_text=llm_text)

    api_key = os.environ["OPENAI_API_KEY"]
    warnings.filterwarnings("ignore", category=UserWarning)
    
    
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0, seed=0, top_p=0.001,
                       max_tokens=4096, n=1, frequency_penalty=0, presence_penalty=0)
    warnings.filterwarnings("default", category=UserWarning)
    structured_llm = model.with_structured_output(JobBoard)
    

    # Run the chain with the formatted text
    response = structured_llm.invoke(prompt)
    response = response.job_board

    # Process the response to extract the link
    #response = response[response.find('Your link:'):]
    link = response[response.find('http'):]
    if link.find(']') != -1:
        link = link[:link.find(']')]
    if link.find(')') != -1:
        link = link[:link.find(')')]   
        
    return link
