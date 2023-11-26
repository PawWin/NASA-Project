import requests
import random
from datetime import datetime, timedelta
from flask import Flask, render_template
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from

app = Flask(__name__)

api_key = "FDlAcufYBrWHbobPQfofRn7Tm79SeoJotLOcpnjy"

#create a user database in SQLAlchemy

def get_apod_data():
    # Choosing random date from beginning of apod to today
    start_day = datetime(1995, 6, 16)  # Date of the first date of apod
    end_day = datetime.now()

    range_of_days = random.randint(0, (end_day - start_day).days)  # Range of the days I can add to start date

    random_date = start_day + timedelta(days=range_of_days)  # Random date

    # Getting requests from apod api
    response = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={api_key}&date={random_date.date()}")

    return response.json()


def planetary_candidates():
    api_url = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI"

    query_params = {
        "table": "cumulative",
        "where": "koi_prad<2 and koi_teq>180 and koi_teq<303 and koi_disposition='CANDIDATE'",
        "format": "json",
        "api_key": api_key
    }
    response = requests.get(api_url, params=query_params)

    data = response.json()
    radii = []
    equilibrium_temperatures = []

    for planet in data:
        radii.append(planet["koi_prad"])
        equilibrium_temperatures.append(planet["koi_teq"])

    plt.figure(figsize=(10, 6))
    plt.scatter(equilibrium_temperatures, radii, alpha=0.5)
    plt.xlabel('Temperatura równowagi (K)')
    plt.ylabel('Promień planety (R_earth)')
    plt.title('Promień planety względem Temperatury Równowagi')
    plt.grid(True)

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    planets_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return planets_data


def cameras_diagrams():
    max_sol = 3650
    # random_sol = random.randint(1, max_sol)
    random_sol = 2745

    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol={random_sol}&api_key={api_key}"

    response = requests.get(url)
    data = response.json()

    photos = data.get('photos', [])
    cameras = {}

    for photo in photos:
        camera_name = photo['camera']['name']
        if camera_name in cameras:
            cameras[camera_name] += 1
        else:
            cameras[camera_name] = 1

    camera_names = list(cameras.keys())
    photo_counts = list(cameras.values())

    manifest_url = f"https://api.nasa.gov/mars-photos/api/v1/manifests/curiosity?api_key={api_key}"
    manifest_response = requests.get(manifest_url)

    manifest_data = manifest_response.json()
    sol_info = manifest_data['photo_manifest']['photos'][random_sol]
    earth_date = sol_info['earth_date']

    plt.figure(figsize=(12, 6))
    plt.bar(camera_names, photo_counts)
    plt.xlabel("Nazwa aparatu")
    plt.ylabel("Liczba zdjęć")
    plt.title(f"Liczba zdjęć z różnych aparatów Mars Rover Curiosity (sol {random_sol}, data: {earth_date})")
    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    cameras_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return cameras_data


def near_earth_object():
    start_date = datetime(random.randint(2015, 2022), random.randint(1, 12), random.randint(1, 30))
    end_date = start_date + timedelta(days=7)  # Data 7 dni później

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date_str}&end_date={end_date_str}&api_key={api_key}"
    response = requests.get(url)

    data = response.json()
    neo_data = data['near_earth_objects'][start_date_str]
    neo_types = {}

    for neo in neo_data:
        if 'neo_reference_id' in neo and 'name' in neo and 'is_potentially_hazardous_asteroid' in neo:
            neo_type = "Potentially Hazardous" if neo['is_potentially_hazardous_asteroid'] else "Non-Hazardous"
            if neo_type in neo_types:
                neo_types[neo_type] += 1
            else:
                neo_types[neo_type] = 1

    labels = neo_types.keys()
    sizes = neo_types.values()

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f"Rodzaje obiektów Near Earth Object (NEO) od {start_date_str} do {end_date_str}")
    plt.axis('equal')

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    near_earth_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return near_earth_data


def asteroid():
    start_date = "2015-01-01"
    end_date = "2023-11-01"

    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

    random_datetime = start_datetime + timedelta(
        days=random.randint(0, (end_datetime - start_datetime).days))

    random_date = random_datetime.strftime("%Y-%m-%d")
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={random_date}&end_date={random_date}&api_key={api_key}"

    response = requests.get(url)

    data = response.json()
    near_earth_objects = data['near_earth_objects']

    date_counts = {}
    for date, asteroids in near_earth_objects.items():
        date_counts[date] = len(asteroids)

    dates = list(date_counts.keys())
    asteroid_counts = list(date_counts.values())

    plt.figure(figsize=(12, 6))
    plt.bar(dates, asteroid_counts)
    plt.ylabel("Liczba asteroid")
    plt.title(f"Liczba bliskich podejść asteroid w dniu {random_date}")
    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    asteroids_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return asteroids_data


def planet_masses():
    planet_names = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    planet_masses = [0.055, 0.815, 1, 0.107, 317.8, 95.2, 14.5, 17.1]

    plt.figure(figsize=(10, 6))
    plt.bar(planet_names, planet_masses, color='green')
    plt.xlabel('Planet')
    plt.ylabel('Relative Mass (Earth = 1)')
    plt.title('Relative Mass of Planets in the Solar System')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    planet_masses_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return planet_masses_data

@app.route('/')
def base():
    return render_template('base.html')

@app.route('/apod')
def display_apod():
    apod_data = get_apod_data()
    title = apod_data['title']
    explanation = apod_data['explanation']
    hd_url = apod_data['hdurl']
    return render_template('apod.html', title=title, explanation=explanation, hd_url=hd_url)

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/diagrams')
def display_diagram_main():
    return "Tu bedzie mozna wybrac konkretna strone z wykresami od Grzesia"


@app.route('/diagrams/planetary-candidates')
def display_planetary_candidates_diagrams():
    planets_data = planetary_candidates()
    return render_template('planetary-candidates.html', planets_data=planets_data)


@app.route('/diagrams/cameras')
def display_cameras_diagrams():
    cameras_data = cameras_diagrams()
    return render_template('cameras-diagrams.html', cameras_data=cameras_data)


@app.route('/diagrams/near-earth')
def display_near_earth_objects():
    near_earth_data = near_earth_object()
    return render_template('near-earth.html', near_earth_data=near_earth_data)


@app.route('/diagrams/asteroids')
def display_asteroid_diagram():
    asteroids_data = asteroid()
    return render_template('asteroid.html', asteroids_data=asteroids_data)


@app.route('/diagrams/planet-masses')
def display_planet_masses():
    planets_masses_data = planet_masses()
    return render_template('planet-masses.html', planets_masses_data=planets_masses_data)


if __name__ == "__main__":
    app.run(debug=True)


