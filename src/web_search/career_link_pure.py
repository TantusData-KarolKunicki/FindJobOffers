
from url_to_llm_text.get_html_text import get_page_source
from url_to_llm_text.get_llm_input_text import get_processed_text 
import requests
import os


def find_job_board_link_pure(url):
    page_source = get_page_source(url)
    llm_text = get_processed_text(page_source, url)

    prompt_format = """In input I give you a website of company. 
                    Find link in input to a subpage where that company
                    offers jobs, careers for new employees.
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
    return link
