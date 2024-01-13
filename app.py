import requests
import random
import numpy as np
from datetime import datetime, timedelta
import json

from config import app, db, bcrypt, User, Image
from flask import render_template, request, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import MultipleLocator

from io import BytesIO
import base64
import forms
import folium

import astropy.units as u
from astropy.coordinates import Longitude
from sunpy.coordinates import HeliocentricEarthEcliptic, get_body_heliographic_stonyhurst
from sunpy.time import parse_time


api_keys = json.loads(open('api_key.txt', 'r').read())
api_key = api_keys['api_key']
api_key2 = base64.b64encode(api_keys['api_key2'].encode()).decode()


@app.route('/')
def base():
    return render_template('base.html')


@app.route('/apod', methods=['GET', 'POST'])
def apod():
    start_day = datetime(1995, 6, 16)
    end_day = datetime.now()

    range_of_days = random.randint(0, (end_day - start_day).days)

    random_date = start_day + timedelta(days=range_of_days)

    response = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={api_key}&date={random_date.date()}")

    if response.status_code == 200:
        apod_data = response.json()
        title = apod_data['title']
        explanation = apod_data['explanation']
        hd_url = apod_data['hdurl']
        if forms.ImageForm().validate_on_submit():
            image_link = hd_url
            image = Image(user_id=current_user.id, image_link=image_link)
            db.session.add(image)
            db.session.commit()
        return render_template('apod.html', title=title, explanation=explanation, hd_url=hd_url, image_form=forms.ImageForm())
    else:
        return render_template('responsemissing.html')


@app.route('/planetary-candidates')
def planetary_candidates_chart():
    api_url = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI"

    query_params = {
        "table": "cumulative",
        "where": "koi_prad<2 and koi_teq>180 and koi_teq<303 and koi_disposition='CANDIDATE'",
        "format": "json",
        "api_key": api_key
    }
    response = requests.get(api_url, params=query_params)

    if response.status_code == 200:
        data = response.json()
        radii = []
        equilibrium_temperatures = []

        for planet in data:
            radii.append(planet["koi_prad"])
            equilibrium_temperatures.append(planet["koi_teq"])

        plt.figure(figsize=(10, 6))
        plt.scatter(equilibrium_temperatures, radii, alpha=0.5)
        plt.xlabel('Equilibrium temperature (K)')
        plt.ylabel('Radius of the planet (R_earth)')
        plt.title('Radius of the planet relative to the Equilibrium Temperature')
        plt.grid(True)

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        planets_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return render_template('planetary-candidates.html', planets_data=planets_data)
    else:
        return render_template('responsemissing.html')


@app.route('/cameras')
def cameras_diagrams_chart():
    max_sol = 3650
    # random_sol = random.randint(1, max_sol)
    random_sol = 120

    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol={random_sol}&api_key={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
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
        plt.xlabel("Camera name")
        plt.ylabel("Number of photos")
        plt.title(f"Number of photos from different Mars Rover Curiosity cameras(sol {random_sol}, date: {earth_date})")
        plt.xticks(rotation=45)
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        cameras_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return render_template('cameras-diagrams.html', cameras_data=cameras_data)
    else:
        return render_template('responsemissing.html')


@app.route('/near-earth')
def near_earth_objects_chart():
    start_date = datetime(random.randint(2015, 2022), random.randint(1, 12), random.randint(1, 30))
    end_date = start_date + timedelta(days=7)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date_str}&end_date={end_date_str}&api_key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
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
        plt.title(f"Dangerous and not dangerous Near Earth Object (NEO) from {start_date_str} to {end_date_str}")
        plt.axis('equal')

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        near_earth_data = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return render_template('near-earth.html', near_earth_data=near_earth_data)
    else:
        return render_template('responsemissing.html')


@app.route('/planet-position')
def planets_position_chart():
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

    return render_template('planet-position.html', asteroids_data=asteroids_data)


@app.route('/planet-masses')
def planet_masses_chart():
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

  
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Creating a new user when the register form validates
    if forms.RegistrationForm().validate_on_submit():
        # Creating a new user in the database
        register_form = forms.RegistrationForm()
        hashed_password = bcrypt.generate_password_hash(register_form.password.data).decode('utf-8')
        user = User(username=register_form.username.data,
                    email=register_form.email.data,
                    password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            return redirect(url_for('login'))
        # Signing in the user after creating them
        user = User.query.filter_by(email=forms.RegistrationForm().email.data).first()
        if user and bcrypt.check_password_hash(user.password, forms.RegistrationForm().password.data):
            login_user(user)
            # Taking the user to the authenticated side of the site
            return redirect(url_for('login'))

    if forms.LoginForm().validate_on_submit():
        user = User.query.filter_by(email=forms.LoginForm().email.data).first()
        if user and bcrypt.check_password_hash(user.password, forms.LoginForm().password.data):
            login_user(user, remember=forms.LoginForm().remember.data)
            #print(current_user.get_all_image_links())
            return redirect(url_for('login'))

    if (request.method == "POST") & (request.form.get('post_header') == 'log out'):
        logout_user()
        return redirect(url_for('login'))

    return render_template('login.html',
                           login_form=forms.LoginForm(),
                           register_form=forms.RegistrationForm(),user=current_user)


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

    if response.status_code == 200:
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
    else:
        return render_template('responsemissing.html')


@app.route('/near-earth-asteroids-date', methods=['GET', 'POST'])
def pick_date():
    form = forms.DateSelectForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            selected_date = request.form.get('selected_date')
        return redirect(url_for('near_earth', selected_date=selected_date))
    return render_template('pick-date.html', form=form)


@app.route('/near-earth-asteroids/<selected_date>')
def near_earth(selected_date):
    start_date = selected_date

    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&api_key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
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

        if largest_hazardous_neo is not None:
            example_city_area = 25.0
            burj_khalifa_height = 0.828
            asteroid_area = np.pi * (max_diameter / 2.0) ** 2

            if max_diameter <= 2:
                object_to_scale = "fa solid fa-building"
                compared_object_data = ["Burj Khalifa", f"{burj_khalifa_height} km"]
                scale = max_diameter / burj_khalifa_height
                icon_size = round(scale * 10.0, 2)

                plt.figure(figsize=(6, 6))
                plt.pie([burj_khalifa_height, max_diameter],
                        labels=['Burj Khalifa', largest_hazardous_neo['name']],
                        autopct='%1.1f%%', startangle=140)
                plt.axis('equal')

                buffer = BytesIO()
                plt.savefig(buffer, format="png")
                buffer.seek(0)
                comparison_diagram = base64.b64encode(buffer.read()).decode()
                buffer.close()
            else:
                object_to_scale = "fa solid fa-city"
                compared_object_data = ["Averaged sized city: Siemianowice", f"{example_city_area} km2"]
                scale = asteroid_area / example_city_area
                icon_size = round(scale * 10.0, 2)

                plt.figure(figsize=(6, 6))
                plt.pie([example_city_area, asteroid_area],
                        labels=['Siemianowice Slaskie', largest_hazardous_neo['name']],
                        autopct='%1.1f%%', startangle=140)
                plt.axis('equal')

                buffer = BytesIO()
                plt.savefig(buffer, format="png")
                buffer.seek(0)
                comparison_diagram = base64.b64encode(buffer.read()).decode()
                buffer.close()

            neo_postprocess_data = {'name': largest_hazardous_neo['name'], 'area': round(asteroid_area,2),
                                    'diameter': round(max_diameter,2),
                                    'distance': round(float(largest_hazardous_neo['close_approach_data'][0]['miss_distance']['kilometers']),2),
                                    'velocity': round(float(largest_hazardous_neo['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']),2),
                                    'date': largest_hazardous_neo['close_approach_data'][0]['close_approach_date_full']}

            return render_template('near-earth-asteroids.html',
                                   icon_size=icon_size,
                                   object_to_scale=object_to_scale,
                                   neo_postprocess_data=neo_postprocess_data,
                                   compared_object_data=compared_object_data,
                                   comparison_diagram=comparison_diagram)
        else:
            return render_template('dangerous-object-missing.html')
    else:
        return render_template('responsemissing.html')


@app.route('/pick-constelation', methods=['GET', 'POST'])
def pick_constellation():
    form = forms.PickConstellationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            constellation = request.form.get('constellation')
        return redirect(url_for('constellations', constellation=constellation))
    return render_template('pick-constellation.html', form=form)


@app.route('/constellations/<constellation>')
def constellations(constellation):
    constellation_description = {'Andromeda': 'Andromeda is a constellation rich in Greek mythology and can be best observed during autumn nights. The name Andromeda refers to the princess from Greek mythology, known for her beauty. According to the myth, Andromeda was chained to a rock as a sacrifice to a sea monster, but was eventually saved by the hero Perseus. The constellation is often depicted as a woman with outstretched arms, seemingly in a pose of distress. Its most notable feature is the Andromeda Galaxy, the closest spiral galaxy to the Milky Way, visible to the naked eye in dark sky conditions. To locate the Andromeda Galaxy, look for a faint, elongated smudge near the constellations',
                                 'Aquila': 'Aquila was the eagle that in Greek mythology actually bore Ganymede (Aquarius) up to Mt. Olympus. The eagle was also the thunderbolt carrier for Zeus. This constellation lies in the Milky Way band, and its most prominent star is Altair, which is actually one of the closest naked eye stars to the earth. The top portion of Aquila forms a shallow inverted “V,” with Altair nearly the point. This represents the head and wings of the eagle. A line then descends from Altair, which forms the body of the eagle',
                                 'Aries': 'While many constellations have gone through various iterations of mythological stories, Aries has always been the ram. This constellation is one of 12 constellations that form the zodiac — the constellations that straddle the sun’s path across the sky (known in scienctific terms as the ecliptic). In ancient times, that gave the constellations of the zodiac special significance. In Greek mythology, Aries is the ram whose fleece became the Golden Fleece. The Golden Fleece is a symbol of kingship and authority, and plays a significant role in the tale of Jason and the Argonauts. Jason is sent to find the fleece in order to rightfully claim his throne as king, and with some help from Medea (his future wife), finds his prize. It’s one of the oldest stories in antiquity, and was current in Homer’s time.',
                                 'Aquarius': 'While one of the biggest, most famous, and oldest named constellations, Aquarius is faint and often hard to find/see. In Greek mythology, Aquarius represented Ganymede, a very handsome young man. Zeus recognized the lad’s good looks, and invited Ganymede to Mt. Olympus to be the cupbearer of the gods. For his service he was granted eternal youth, as well as a place in the night sky.',
                                 'Canis Major': 'Canis Major represents the famed Greek dog Laelaps. There are a few origin stories, but the common theme is that he was so fast he was elevated to the skies by Zeus. Laelaps is also considered to be one of Orion’s hunting dogs, trailing behind him in the night sky in pursuit of Taurus the bull. Canis Major is notable because it contains the brightest star in the night sky, Sirius. Tradition notes that the first appearance of Canis Major in the dawn sky comes in late summer, ushering in the dog days of the season. In the night sky, it almost looks a stick figure, with Sirius at the head, and another bright star, Adhara, at its rear end',
                                 'Cancer': 'Cancer, the Crab, is a small and faint constellation located between Gemini and Leo. In Greek mythology, Cancer is associated with the crab that Hera sent to distract Hercules during his battle with the Hydra. Despite its modest appearance, Cancer is home to a rich cluster of stars known as the Beehive Cluster, or Messier 44. This cluster is a group of young stars surrounded by a faint nebula, best observed through binoculars or a small telescope. Cancer is best seen during late winter and early spring, when it climbs high in the night sky.',
                                 'Capricorn': 'Capricornus, often simply referred to as Capricorn, is one of the oldest recognized constellations, dating back to ancient Mesopotamia. In Greek mythology, Capricorn is associated with the god Pan, who transformed into a fish-tailed goat to escape the monster Typhon. Capricorn is depicted as a creature with the upper body of a goat and the tail of a fish. Its brightest star, Deneb Algedi, marks the goats tail. Capricorn is best viewed in late summer and early autumn, when it appears low on the southern horizon.',
                                 'Cassiopeia': 'Cassiopeia, in Greek mythology, was a vain queen who often boasted about her beauty. She was the mother of Princess Andromeda, and in contrast to other figures being placed in the sky in honor, Cassiopeia was forced to the heavenly realms as punishment. As the story goes, she boasted that her beauty (or her daughter’s, depending on the story) was greater than that of the sea nymphs. This was quite an offense, and she was banned to the sky for all to gawk at.',
                                 'Cygnus': 'Multiple personas take on the form of the swan in Greek mythology. At one point Zeus morphed into a swan to seduce Leda, mother of both Gemini and Helen of Troy. Another tale says that Orpheus was murdered and then placed into the sky as a swan next to his lyre (the constellation Lyra, also in the drawing above). The constellation may also have gotten its name from the tale of Phaethon and Cycnus. Phaethon was the son of Helios (the sun god), and took his father’s sun chariot for a ride one day. Phaethon couldn’t control the reins, however, and Zeus had to shoot down the chariot with Phaethon in it, killing him. Phaethon’s brother, Cycnus (now spelled Cygnus), spent many days grieving and collecting the bones, which so touched the gods that they turned him into a swan and gave him a place in the sky.',
                                 'Gemini': 'Gemini represents the twins Castor and Pollux. While the twins’ mother was Leda, Castor’s father was the mortal king of Sparta, while Pollux’s father was King Zeus (He seduced Leda in the form of a swan, remember? These stories tend to all tie together!). When Castor was killed, the immortal Pollux begged Zeus to give Castor immortality, which he did by placing the brothers in the night sky for all time. Castor and Pollux also happen to be the names of the brightest stars in the constellation, and represent the heads of the twins. Each star then has a line forming their bodies, giving the constellation a rough “U” shape. The twins sit next to Orion, making them fairly easy to find in winter.',
                                 'Leo': 'Leo has been a great lion in the night sky across almost all mythological traditions. In Greek lore, Leo is the monstrous lion that was killed by Hercules as part of his twelve labors. The lion could not be killed by mortal weapons, as its fur was impervious to attack, and its claws sharper than any human sword. Eventually Hercules tracked him down and strangled the great beast, albeit losing a finger in the process. Because Leo actually looks somewhat like its namesake, it is the easiest constellation in the zodiac to find. A distinctive backwards question mark forms the head and chest, then moves to the left to form a triangle and the lion’s rear end. Regulus is Leo’s brightest star, and sits in the bottom right of the constellation, representing the lion’s front right leg.',
                                 'Libra': 'Libra, the Scales, is a relatively faint constellation located between Virgo and Scorpius. In Greek mythology, Libra is associated with the goddess Themis, who is often depicted holding the scales of justice. Libra is best viewed in the evening sky during late spring and early summer. Its most recognizable feature is the nearby bright star Spica in the constellation Virgo. Libras faint stars make it a challenging constellation to spot, but its association with themes of balance and justice add a layer of intrigue',
                                 'Lyra': 'Lyra is associated with the myth of Orpheus the great musician. Orpheus was given the harp by Apollo, and it’s said that his music was more beautiful than that of any mortal man. His music could soothe anger and bring joy to weary hearts. Wandering the land in depression after his wife died, he was killed and his lyre (harp) was thrown into a river. Zeus sent an eagle to retrieve the lyre, and it was then placed in the night sky. Lyra sort of forms a lopsided square with a tail to its brightest star, Vega, which is one of the brightest stars in the sky. It is small, and almost directly overhead in the summer months, but the bright Vega makes it fairly easy to find.',
                                 'Orion': 'Orion is one of the largest and most recognizable of the constellations. It is viewable around the world, and has been mentioned by Homer, Virgil, and even the Bible, making it perhaps the most famous constellation. Orion was a massive, supernaturally gifted hunter who was the son of Poseidon. It was said he regularly hunted with Artemis (Goddess of the Hunt) on the island of Crete, and that he was killed either by her bow, or by the sting of the great scorpion who later became the constellation Scorpius.',
                                 'Pisces': 'The two fish of the sky represent Aphrodite and her son Eros, who turned themselves into fish and tied themselves together with rope in order to escape Typhon, the largest and most vile monster in all of Greek mythology.It’s not likely you’ll find Pisces in the middle of a city, as none of its individual stars are really worth noting or particularly bright. It forms a large “V” with the right fish forming a small “O” on the end, and the left fish forming a small triangle on the end',
                                 'Sagittarius': 'Sagittarius, the Archer, is a prominent constellation in the southern sky, best viewed during the summer months. In Greek mythology, Sagittarius is associated with the centaur Chiron, known for his wisdom and skill in archery. The constellation is depicted as a centaur drawing a bow, aiming an arrow towards the heart of the nearby Scorpius constellation. Sagittarius is home to the center of our Milky Way galaxy, making it a region rich in star clusters, nebulae, and other celestial wonders. Its most notable feature is the Teapot asterism, a group of stars that resemble a teapot when connected by imaginary lines.',
                                 'Scorpius': 'There are a variety of myths associated with the scorpion, almost all of them involving Orion the hunter. Orion once boasted that he could kill all the animals on the earth. He encountered the scorpion, and after a long, fierce fight, Orion was defeated. It was such a hard-fought battle that it caught the eye of Zeus, and the scorpion was raised to the night sky for all eternity. With many bright stars, Scorpius is fairly easy to find in the night sky. Antares, the brightest star in the constellation, is said to be the heart of the scorpion. That will be the easiest star to locate, but is sometimes confused with Mars because of its red-orange coloring. To the right of the heart are 3-5 stars that form the head. To the left are a long line of stars that curve into a sideways or upside-down question mark.',
                                 'Taurus': 'Taurus is a large and prominent fixture in the winter sky. As one of the oldest recognized constellations, it has mythologies dating back to the early Bronze Age. There are several Greek myths involving Taurus. Two of them include Zeus, who either disguised himself as a bull or disguised his mistress as a bull in multiple escapades of infidelity. Another myth has the bull being the 7th labor of Hercules after the beast wreaked havoc in the countryside.',
                                 'Ursa Major': 'The Big Dipper is popularly thought of as a constellation itself, but is in fact an asterism within the constellation of Ursa Major. It is said to be the most universally recognized star pattern, partially because it’s always visible in the northern hemisphere. It has great significance in the mythologies of multiple cultures around the world. The Greek myth of Ursa Major also tells the story of Ursa Minor (below). Zeus was smitten for a young nymph named Callisto. Hera, Zeus’s wife, was jealous, and transformed Callisto into a bear. While in animal form, Callisto encountered her son Arcas. Being the man that he was, he was inclined to shoot the bear, but Zeus wouldn’t let that happen, and so turned Arcas into a bear as well, and placed mother (Ursa Major) and son (Ursa Minor) permanently in the night sky.',
                                 'Ursa Minor': 'Ursa Minor is famous for containing Polaris, the North Star. Many people erroneously think that the North Star is directly over their heads, but that’s only true at the North Pole. For most people in the Northern Hemisphere, it will be dipped into the night sky. Ursa Minor is better known as the Little Dipper. It’s visualized as a baby bear, with an unusually long tail. It can be distinguished from the Big Dipper not only by size, but by the emphasized curvature of the tail. When you’ve found the North Star at the end of the bear’s tail using the Big Dipper, it’s then easy to identify the rest of the constellation.',
                                 'Virgo': 'Virgo, often referred to as the Maiden, is one of the largest constellations in the sky and is best viewed in the spring months. Its origins trace back to ancient Babylonian and Greek civilizations, where it was associated with various goddesses and figures. In Greek mythology, Virgo is often linked to the goddess of justice, Dike, or the harvest goddess, Demeter. One prominent myth tells the tale of Demeters daughter, Persephone, who was abducted by Hades. During her search for Persephone, Demeters grief caused crops to wither and die, leading to famine. As a result, Virgo is sometimes associated with the changing of the seasons and the cycle of growth and harvest. Virgo is distinguished by its bright star Spica, one of the brightest stars in the night sky. Spica is often referred to as the "ear of wheat" that the Maiden holds, symbolizing fertility and abundanc.'
                                 }
    constellation_id = {'Andromeda': 'and', 'Aquila': 'aql', 'Aries': 'ari', 'Aquarius': 'aqr', 'Canis Major': 'cma',
                        'Cancer': 'cnc', 'Capricorn': 'cap', 'Cassiopeia': 'cas', 'Cygnus': 'cyg', 'Gemini': 'gem',
                        'Leo': 'leo', 'Libra': 'lib', 'Lyra': 'lyr', 'Orion': 'ori', 'Pisces': 'psc', 'Sagittarius': 'sgr',
                        'Scorpius': 'sco', 'Taurus': 'tau', 'Ursa Major': 'uma', 'Ursa Minor': 'umi', 'Virgo': 'vir'}
    constellation_best_viewed = {'Andromeda': 'October', 'Aquila': 'September',
                                'Aries': 'December', 'Aquarius': 'October',
                                'Canis Major': 'February', 'Cancer': 'March',
                                'Capricorn': 'September', 'Cassiopeia': 'November',
                                'Cygnus': 'September', 'Gemini': 'February',
                                'Leo': 'April', 'Libra': 'June',
                                'Lyra': 'August', 'Orion': 'January',
                                'Pisces': 'November', 'Sagittarius': 'August',
                                'Scorpius': 'July', 'Taurus': 'January',
                                'Ursa Major': 'April', 'Ursa Minor': 'June',
                                'Virgo': 'May'}

    headers = {
        'Authorization': f'Basic {api_key2}',
        'Content-Type': 'application/json'
    }
    payload = json.dumps({
        'style': 'navy',
        'observer': {
            'latitude': 50.270908,
            'longitude': 19.039993,
            'date': '2021-01-01',
        },
        'view': {
            'type': 'constellation',
            'parameters': {
                'constellation': f'{constellation_id[constellation]}'
            }
        }
    })

    response = requests.post('https://api.astronomyapi.com/api/v2/studio/star-chart', headers=headers, data=payload)

    if response.status_code == 200:
        constellation_info = {'name': constellation, 'description': constellation_description[constellation],
                              'picture': response.json()['data']['imageUrl'],
                              'best viewed' : constellation_best_viewed[constellation]}

        return render_template('constellations.html', constellation_info=constellation_info)
    else:
        return render_template('responsemissing.html')


@app.route('/mercury')
def mercury():
    return render_template('mercury.html')


@app.route('/venus')
def venus():
    return render_template('venus.html')


@app.route('/earth')
def earth():
    return render_template('Earth.html')


@app.route('/mars')
def mars():
    return render_template('mars.html')


@app.route('/jupiter')
def jupiter():
    return render_template('jupiter.html')


@app.route('/saturn')
def saturn():
    return render_template('saturn.html')


@app.route('/uranus')
def uranus():
    return render_template('uranus.html')


@app.route('/neptune')
def neptune():
    return render_template('neptune.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/gallery', methods=['GET', 'POST'])
@login_required
def gallery():
    return render_template('gallery.html', images=current_user.get_all_image_links())


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
