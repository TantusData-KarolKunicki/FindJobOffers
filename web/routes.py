import ast
import base64
import io
import os

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for

from processing.linkedin.linkedin_singleton import LinkedinSingleton

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY_FLASK", "defaultsecretkey")
matplotlib.use("Agg")
results = None


def linkedin_login():
    linkedin = LinkedinSingleton(os.environ["EMAIL_LINKEDIN"], os.environ["PASSWORD_LINKEDIN"])
    return linkedin


def create_bar_plot(data):
    filtered_data = {k: v for k, v in data.items() if v != 0}
    labels = list(filtered_data.keys())
    values = list(filtered_data.values())

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color="blue")
    plt.xlabel("Technologie")
    plt.ylabel("Wartości")
    plt.title("Technologie firmy")

    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            int(yval),
            ha="center",
            va="bottom",
        )

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode("utf8")
    plt.close()

    return plot_url


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        global results
        result_file_name = request.form["result_file_name"]
        try:
            results = pd.read_csv(f"data/{result_file_name}")
            people = list(results["person_link"])
            people = [person.split("/")[-1] for person in people]
            companies = results["company_link"]
            basic_info = list(zip(people, companies))
            session["basic_info"] = basic_info
            session["result_file_name"] = result_file_name
        except Exception as e:
            return f"Błąd: {str(e)}"

    basic_info = session.get("basic_info", None)
    if basic_info:
        return render_template("result.html", basic_info=basic_info)
    return render_template("index.html")


@app.route("/person/<person_id>")
def person_detail(person_id):
    basic_info = session.get("basic_info", None)
    if basic_info is None:
        return redirect(url_for("index"))
    global results
    if results is None:
        return "Dane nie zostały załadowane."

    person_record = results[results["person_link"].str.contains(person_id)].iloc[0]

    if not person_record.empty:
        person_link = person_record["person_link"]
        company_link = person_record["company_link"]
        job_board_link = person_record["job_board_link"]
        company_technologies = person_record["company_technologies"]
        company_technologies = ast.literal_eval(company_technologies)

        job_offers_links = person_record["job_offers_links"]
        job_offers_links = ast.literal_eval(job_offers_links)
        plot_url = create_bar_plot(company_technologies)
        # Renderowanie strony osoby
        return render_template(
            template_name_or_list="person.html",
            person_link=person_link,
            company_link=company_link,
            job_board_link=job_board_link,
            plot_url=plot_url,
            job_offers_links=job_offers_links,
        )
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(port=8000, debug=True)
