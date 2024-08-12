import csv
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os
from linkedin.linkedin_adapter import LinkedinAdapter
from pipeline.pipeline import get_person_company_tech

def process_link(link):
    try:
        company_technologies, person_link, company_link, job_board_link, job_offers_links = get_person_company_tech(linkedin=linkedin, person_link=link)
        with lock:
            with open(results_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([company_technologies, person_link, company_link, job_board_link, job_offers_links])
    except Exception as e:
        # Można tutaj dodać logowanie błędów lub zwiększyć licznik błędów
        print(f"Error processing link {link}: {e}")
        with lock:
            global errors
            errors += 1
import os

# Wczytanie zmiennych z pliku config/flask.env
load_dotenv(os.path.join('config', 'flask.env'))
#load_dotenv()

file_path = 'data/dataset_small.csv'
results_file = 'data/results_small.csv'
NUM_THREADS = int(os.environ['NUM_THREADS'])

df = pd.read_csv(file_path)
dataset_linkedin_links = list(df['Lead Linkedin Url'])
linkedin = LinkedinAdapter(os.environ['EMAIL_LINKEDIN'], os.environ['PASSWORD_LINKEDIN'])

with open(results_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['company_technologies', 'person_link', 'company_link', 'job_board_link', 'job_offers_links'])

errors = 0
lock = threading.Lock()
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    executor.map(process_link, dataset_linkedin_links)
