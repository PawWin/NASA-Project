import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def get_largest_hazardous_neo_in_time_range(api_key, start_date, end_date):
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        neo_data = response.json()["near_earth_objects"]
        largest_hazardous_neo = find_largest_hazardous_neo(neo_data)
        return largest_hazardous_neo
    else:
        print(f"Nie udało się pobrać informacji o obiektach NEO. Kod odpowiedzi: {response.status_code}")
        return None


def find_largest_hazardous_neo(neo_data):
    largest_hazardous_neo = None
    max_diameter = 0

    for date, neo_list in neo_data.items():
        for neo in neo_list:
            if "is_potentially_hazardous_asteroid" in neo and neo["is_potentially_hazardous_asteroid"]:
                if "estimated_diameter" in neo and "kilometers" in neo["estimated_diameter"]:
                    diameter = neo["estimated_diameter"]["kilometers"]["estimated_diameter_max"]
                    if diameter > max_diameter:
                        max_diameter = diameter
                        largest_hazardous_neo = neo

    return largest_hazardous_neo


def display_neo_info(neo_info):
    if neo_info:
        print("\nInformacje o największym potencjalnie niebezpiecznym obiekcie w najbliższych 7 dniach:")
        print(f"Nazwa obiektu NEO: {neo_info['name']}")
        print(f"Data zbliżenia: {neo_info['close_approach_data'][0]['close_approach_date_full']}")
        print(
            f"Największy szacowany średnica: {neo_info['estimated_diameter']['kilometers']['estimated_diameter_max']} km")
        print(
            f"Prędkość względna: {neo_info['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']} km/h")
        print(f"Odległość minięcia: {neo_info['close_approach_data'][0]['miss_distance']['kilometers']} km")
        print(f"Ciało, wokół którego krąży: {neo_info['close_approach_data'][0]['orbiting_body']}")
    else:
        print("Brak informacji o największym potencjalnie niebezpiecznym obiekcie w podanym przedziale czasowym.")


def plot_asteroid_vs_burj_khalifa(asteroid_diameter, burj_khalifa_height):
    objects = ['Asteroid', 'Burj Khalifa']
    sizes = [asteroid_diameter, burj_khalifa_height]

    plt.bar(objects, sizes, color=['red', 'blue'])
    plt.ylabel('Size (in meters)')
    plt.title('Asteroid vs Burj Khalifa')
    plt.show()


if __name__ == "__main__":
    api_key = "FDlAcufYBrWHbobPQfofRn7Tm79SeoJotLOcpnjy"  # Twój klucz API NASA
    start_date = input("Podaj datę początkową (format YYYY-MM-DD): ")

    # Automatyczne ustawienie end_date na 7 dni później
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = start_date_obj + timedelta(days=7)
    end_date = end_date_obj.strftime('%Y-%m-%d')

    largest_hazardous_neo_info = get_largest_hazardous_neo_in_time_range(api_key, start_date, end_date)

    display_neo_info(largest_hazardous_neo_info)

    # Dodaj informacje o Burj Khalifa (wysokość około 828 metrów)
    burj_khalifa_height = 828

    # Jeśli dane o asteroidzie są dostępne, generuj wykres
    if largest_hazardous_neo_info:
        asteroid_diameter = largest_hazardous_neo_info['estimated_diameter']['kilometers'][
                                'estimated_diameter_max'] * 1000  # przelicz na metry
        plot_asteroid_vs_burj_khalifa(asteroid_diameter, burj_khalifa_height)
