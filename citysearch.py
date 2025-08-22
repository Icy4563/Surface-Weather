import csv
from typing import List, Tuple, Union

CSV_FILE = 'worldcities.csv'

_cities = []

def _load_data():
    global _cities
    if _cities:
        return
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['lat'] = float(row['lat'])
                row['lng'] = float(row['lng'])
                try:
                    row['population'] = int(float(row['population'])) if row['population'] else 0
                except ValueError:
                    row['population'] = 0
                _cities.append(row)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file '{CSV_FILE}' not found.")

def find_city(city_name: str, partial: bool = False):
    """
    Search for a city by name. If partial=True, matches substrings (case-insensitive).
    Returns a list of matches sorted by population (descending).
    """
    _load_data()
    name = city_name.lower()
    if partial:
        matches = [city for city in _cities if name in city['city'].lower()]
    else:
        matches = [city for city in _cities if city['city'].lower() == name]
    matches.sort(key=lambda x: x['population'], reverse=True)
    return matches

def get_coordinates(city_name: str, partial: bool = False) -> Union[Tuple[str, str, str, float, float], List[Tuple[str, str, str, float, float]]]:
    """
    Returns (city, admin_name, country, lat, lng).
    If one match -> returns a tuple
    If multiple -> returns list of tuples
    """
    results = find_city(city_name, partial=partial)
    coords = [(r['city'], r['admin_name'], r['country'], r['lat'], r['lng']) for r in results]

    if len(coords) == 1:
        return coords[0]
    return coords
