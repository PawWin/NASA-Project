import requests
import random
from datetime import datetime, timedelta
from flask import Flask, render_template

app = Flask(__name__)

api_key = "FDlAcufYBrWHbobPQfofRn7Tm79SeoJotLOcpnjy"


def get_apod_data():
    # Choosing random date from beginning of apod to today
    start_day = datetime(1995, 6, 16)  # Date of the first date of apod
    end_day = datetime.now()

    range_of_days = random.randint(0, (end_day - start_day).days)  # Range of the days I can add to start date

    random_date = start_day + timedelta(days=range_of_days)  # Random date

    # Getting requests from apod api
    response = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={api_key}&date={random_date.date()}")

    return response.json()


@app.route('/')
def display_apod():
    apod_data = get_apod_data()
    title = apod_data['title']
    explanation = apod_data['explanation']
    hd_url = apod_data['hdurl']
    return render_template('apod.html', title=title, explanation=explanation, hd_url=hd_url)


if __name__ == "__main__":
    app.run(debug=True)
