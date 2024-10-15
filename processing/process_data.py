import pandas as pd
import os
import csv
import threading
from concurrent.futures import ThreadPoolExecutor
from processing.company_job_scraper import CompanyJobScraper
import yappi
import ast
from collections import defaultdict
from pathlib import Path
import logging


def load_raw_data(dataset_name):
    folder_path = "data/raw/" + dataset_name
    df = pd.DataFrame()
    df_list = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            df_list.append(df)
    combined_df = pd.concat(df_list, ignore_index=True)

    return combined_df


def get_comapnies_name(dataset_name):

    df_raw = load_raw_data(dataset_name)

    company_column_name = ""
    if "Company" in df_raw.columns:
        company_column_name = "Company"
    elif "Company Name" in df_raw.columns:
        company_column_name = "Company Name"
    else:
        raise Exception("Neither 'Company' nor 'Company Name' column found.")
    logging.info(f"NaN num: {sum(df_raw[company_column_name].isna())}")
    companies_names = df_raw[company_column_name].dropna()
    logging.info(f"Number of companies: {len(companies_names)}")
    companies_names = companies_names.unique()
    logging.info(f"Number of unique companies: {len(companies_names)}")
    return companies_names.tolist()


def process_raw(dataset_name, version, override=False, limit=None):
    NUM_THREADS = int(os.environ["NUM_THREADS"])
    headers = [
        "company_name",
        "company_link",
        "job_board_link",
        "linkedin_unique",
        "job_names",
        "job_offer_link",
        "job_sources",
        "technologies",
    ]
    result_file_path = Path(f"data/processed/{dataset_name}/v{version}/")
    results_file = result_file_path / f"{dataset_name}_v{version}.csv"
    results_file_time = result_file_path / f"{dataset_name}_v{version}_time.csv"
    results_file_companies = result_file_path / f"{dataset_name}_v{version}_companies.csv"
    if (
        not override
        and os.path.exists(results_file_companies)
        and os.path.exists(results_file_time)
        and os.path.exists(results_file)
    ):
        logging.info("Continue proccesing raw data")
        df_results_file_companies = pd.read_csv(results_file_companies)
        df_results_file_time = pd.read_csv(results_file_time)
        companies_names = df_results_file_companies[
            ~df_results_file_companies["company_name"].isin(df_results_file_time["company_name"])
        ]
        companies_names = companies_names["company_name"].tolist()
    else:
        logging.info("Start from strach processing raw data")
        companies_names = get_comapnies_name(dataset_name)
        if limit:
            companies_names = companies_names[:limit]
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

        results_file_time.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file_time, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["company_name", "time", "google_links"])

        results_file_companies.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file_companies, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["company_name"])
            for company_name in companies_names:
                writer.writerow([company_name])

    errors = 0
    lock = threading.Lock()

    def process_link_by_thread(link):
        threading.current_thread().name = f"Thread {link}"
        process_link(link)

    def process_link(company_name):
        try:
            comapny_jobs_scraper = CompanyJobScraper()
            company_info, measured_time, google_links = comapny_jobs_scraper.get_company_tech(company_name=company_name)
            with lock:
                for info in company_info:
                    # Upewnij się, że info jest słownikiem z kluczami pasującymi do headers
                    with open(results_file, mode="a", newline="", encoding="utf-8") as file:
                        writer = csv.DictWriter(file, fieldnames=headers)
                        writer.writerow(info)
                with open(results_file_time, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([company_name, measured_time, google_links])
        except Exception as e:
            logging.error(f"Error processing link {company_name}: {e}")
            with lock:
                global errors
                errors += 1

    yappi.start()
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Mapowanie funkcji process_link na listę linków
        executor.map(process_link_by_thread, companies_names)
    yappi.stop()
    logging.info(f"Total number of errors while processing {dataset_name} v{version}: {errors}")


def get_agg_data(dataset_name, version):
    result_file_path = Path(f"data/processed/{dataset_name}/v{version}")
    result_file = result_file_path / f"{dataset_name}_v{version}.csv"
    result_file_time = result_file_path / f"{dataset_name}_v{version}_time.csv"

    df_raw = load_raw_data(dataset_name)
    df_comapny_info = pd.read_csv(result_file)
    df_time = pd.read_csv(result_file_time)

    def aggregate_dicts(dict_list):
        aggregated_dict = defaultdict(int)
        for d in dict_list:
            for key, value in d.items():
                aggregated_dict[key] += value
        return dict(aggregated_dict)

    aggregated_df = (
        df_comapny_info.groupby("company_name")
        .agg(
            {
                "company_link": "first",
                "linkedin_unique": "first",
                "job_board_link": "first",
                "technologies": lambda x: aggregate_dicts(x.apply(ast.literal_eval)),
            }
        )
        .reset_index()
    )

    aggregated_df["job_offers"] = list(
        df_comapny_info.groupby("company_name")[["job_names", "job_sources", "job_offer_link"]].apply(
            lambda x: list(zip(x["job_names"], x["job_sources"], x["job_offer_link"]))
        )
    )

    merged_df = pd.merge(df_time, aggregated_df, on="company_name", how="left")

    df_raw = df_raw.groupby("Company").agg({"Name": lambda x: list(x), "Profile URL": lambda x: list(x)}).reset_index()
    df_raw.columns = ["company_name", "contact_names", "contact_profiles"]

    merged_df = pd.merge(
        merged_df, df_raw[["company_name", "contact_names", "contact_profiles"]], how="left", on="company_name"
    )

    merged_df = merged_df.sort_values(by="company_name")
    merged_df.to_csv(result_file_path / f"{dataset_name}_agg.csv", index=False)
    merged_df.to_excel(result_file_path / f"{dataset_name}_agg.xlsx", index=False)
    return merged_df
