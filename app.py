import requests
import random
import numpy as np
from datetime import datetime, timedelta

from flask import Flask, render_template

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import MultipleLocator

from io import BytesIO
import base64

import folium

import astropy.units as u
from astropy.coordinates import Longitude
from sunpy.coordinates import HeliocentricEarthEcliptic, get_body_heliographic_stonyhurst, get_horizons_coord
from sunpy.time import parse_time

app = Flask(__name__)

api_key = "FDlAcufYBrWHbobPQfofRn7Tm79SeoJotLOcpnjy"


@app.route('/')
def base():
    return render_template('base.html')


@app.route('/apod')
def apod():
    start_day = datetime(1995, 6, 16)
    end_day = datetime.now()

    range_of_days = random.randint(0, (end_day - start_day).days)

    random_date = start_day + timedelta(days=range_of_days)

    response = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={api_key}&date={random_date.date()}")

    apod_data = response.json()
    title = apod_data['title']
    explanation = apod_data['explanation']
    hd_url = apod_data['hdurl']
    return render_template('apod.html', title=title, explanation=explanation, hd_url=hd_url)


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/login')
def login():
    return render_template('login-sprint.html')


@app.route('/diagrams')
def display_diagram_main():
    return "Tu bedzie mozna wybrac konkretna strone z wykresami od Grzesia"


@app.route('/planetary-candidates')
def display_planetary_candidates():
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

    return render_template('planetary-candidates.html', planets_data=planets_data)


@app.route('/cameras')
def display_cameras_diagrams():
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

    return render_template('cameras-diagrams.html', cameras_data=cameras_data)


@app.route('/near-earth')
def display_near_earth_objects():
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

    return render_template('near-earth.html', near_earth_data=near_earth_data)


@app.route('/asteroids')
def display_asteroid_diagram():
    obstime = parse_time('now')

    hee_frame = HeliocentricEarthEcliptic(obstime=obstime)

    def get_first_orbit(coord):
        lon = coord.transform_to(hee_frame).spherical.lon
        shifted = Longitude(lon - lon[0])
        ends = np.flatnonzero(np.diff(shifted) < 0)
        if ends.size > 0:
            return coord[:ends[0]]
        return coord

    planets = ['mercury', 'venus', 'earth', 'mars']
    times = obstime + np.arange(700) * u.day
    planet_coords = {planet: get_first_orbit(get_body_heliographic_stonyhurst(planet, times)) for planet in planets}

    def coord_to_heexy(coord):
        coord = coord.transform_to(hee_frame)
        coord.representation_type = 'cartesian'
        return coord.y.to_value('AU'), coord.x.to_value('AU')

    mpl.rcParams.update({'figure.facecolor': 'black',
                         'axes.edgecolor': 'white',
                         'axes.facecolor': 'black',
                         'axes.labelcolor': 'white',
                         'axes.titlecolor': 'white',
                         'lines.linewidth': 1,
                         'xtick.color': 'white',
                         'xtick.direction': 'in',
                         'xtick.top': True,
                         'ytick.color': 'white',
                         'ytick.direction': 'in',
                         'ytick.right': True})

    fig = plt.figure()
    ax = fig.add_subplot()

    ax.set_xlim(-2.15, 2.15)
    ax.set_xlabel('Y (HEE)')
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    ax.set_ylim(1.8, -1.8)
    ax.set_ylabel('X (HEE)')
    ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.yaxis.set_minor_locator(MultipleLocator(0.1))

    ax.set_title(obstime.strftime('%d-%b-%Y %H:%M UT'))
    ax.set_aspect('equal')

    ax.plot([0, 0], [0, 2], linestyle='dotted', color='gray')

    for planet, coord in planet_coords.items():
        ax.plot(*coord_to_heexy(coord), linestyle='dashed', color='gray')

        colors = {'mercury': 'brown', 'venus': 'orange', 'earth': 'blue', 'mars': 'red'}

        x, y = coord_to_heexy(coord[0])
        ax.plot(x, y, 'o', markersize=10, color=colors[planet])
        ax.text(x + 0.1, y, planet, color=colors[planet])

        ax.plot(0, 0, 'o', markersize=15, color='yellow')
        ax.text(0.12, 0, 'Sun', color='yellow')

    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams.update({'axes.titlecolor': 'black'})

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    asteroids_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return render_template('asteroid.html', asteroids_data=asteroids_data)


@app.route('/planet-masses')
def display_planet_masses():
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
    planets_masses_data = base64.b64encode(buffer.read()).decode()
    buffer.close()

    return render_template('planet-masses.html', planets_masses_data=planets_masses_data)


@app.route('/world-map')
def world_map():
    categories_icons = {'Volcanoes': ['red', 'volcano', 0], 'Sea and Lake Ice': ['blue', 'icicles', 0],
                        'Severe Storms': ['purple', 'tornado', 0], 'Wildfires': ['orange', 'fire', 0],
                        'Dust and Haze': ['yellow', 'smog', 0], 'Temperature Extremes': ['pink', 'temperature-high', 0],
                        'Floods': ['darkblue', 'house-flood-water', 0], 'Earthquakes': ['brown', 'house-crack', 0],
                        'Manmade': ['black', 'industry', 0], 'Drought': ['beige', 'sun', 0],
                        'Snow': ['lightblue', 'snowflake', 0], 'Landslides': ['lightred', 'hill-rockslide', 0],
                        'Water Color': ['green', 'water', 0]}

    url = "https://eonet.gsfc.nasa.gov/api/v2.1/events?status=open"

    mymap = folium.Map(location=[0, 0], zoom_start=2)

    response = requests.get(url)
    data = response.json()

    for event in data['events']:
        if event['geometries'][0]['type'] == 'Point':
            latitude = event['geometries'][0]['coordinates'][1]
            longitude = event['geometries'][0]['coordinates'][0]
            event_name = event['title']
            event_date = event['geometries'][0]['date']
            folium.Marker(location=[latitude, longitude], popup=f"{event_name} ({event_date}),",
                          icon=folium.Icon(color=categories_icons[event['categories'][0]['title']][0],
                                           icon=categories_icons[event['categories'][0]['title']][1],
                                           prefix='fa')).add_to(mymap)

    map_html = mymap.get_root().render()

    for cat in data['events']:
        if cat['categories'][0]['title'] in categories_icons:
            categories_icons[cat['categories'][0]['title']][2] += 1


    return render_template('world_map.html', map_html=map_html,
                           icons_data=categories_icons)


@app.route('/near-earth-asteroids')
def near_earth():
    start_date = "2015-09-01"

    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = start_date_obj + timedelta(days=7)
    end_date = end_date_obj.strftime('%Y-%m-%d')

    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    response = requests.get(url)

    neo_data = response.json()["near_earth_objects"]

    largest_hazardous_neo = None
    max_diameter = 0

    for date, neo_list in neo_data.items():
        for neo in neo_list:
            if neo["is_potentially_hazardous_asteroid"]:
                diameter = neo["estimated_diameter"]["kilometers"]["estimated_diameter_max"]
                if diameter > max_diameter:
                    max_diameter = diameter
                    largest_hazardous_neo = neo

    example_city_area = 25.0
    burj_khalifa_height = 0.828
    asteroid_area = np.pi * (max_diameter / 2.0) ** 2

    if max_diameter <= 2:
        object_to_scale = "fa solid fa-building fa-fade"
        compared_object_data = ["Burj Khalifa", f"{burj_khalifa_height}km"]
        scale = max_diameter / burj_khalifa_height
        icon_size = round(scale * 10.0, 2)
    else:
        object_to_scale = "fa solid fa-city fa-fade"
        compared_object_data = ["Averaged sized city: Siemianowice", f"{example_city_area}km2"]
        scale = asteroid_area / example_city_area
        icon_size = round(scale * 10.0, 2)

    neo_postprocess_data = {'name': largest_hazardous_neo['name'], 'area': asteroid_area,
                            'diameter': max_diameter,
                            'distance': largest_hazardous_neo['close_approach_data'][0]['miss_distance']['kilometers'],
                            'velocity': largest_hazardous_neo['close_approach_data'][0]['relative_velocity']['kilometers_per_hour'],
                            'date': largest_hazardous_neo['close_approach_data'][0]['close_approach_date_full']}

    return render_template('near-earth-asteroids.html',
                           icon_size=icon_size,
                           object_to_scale=object_to_scale,
                           neo_postprocess_data=neo_postprocess_data,
                           compared_object_data=compared_object_data,)


if __name__ == "__main__":
    app.run(debug=True)


