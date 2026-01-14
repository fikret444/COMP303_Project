import json
import math
from datetime import datetime
from pathlib import Path

from datasources.eonet_storm_source import EONETStormSource
from processing.storage import log_message

CITIES = [
    ("New York", 40.71, -74.00), ("Boston", 42.36, -71.06),
    ("Washington DC", 38.90, -77.04), ("Miami", 25.76, -80.19),
    ("Tampa", 27.95, -82.46), ("New Orleans", 29.95, -90.07),
    ("Houston", 29.76, -95.37), ("Los Angeles", 34.05, -118.24),
    ("San Diego", 32.72, -117.16), ("San Francisco", 37.77, -122.41),
    ("Seattle", 47.61, -122.33), ("Chicago", 41.88, -87.63),
    ("Dallas", 32.78, -96.80), ("Atlanta", 33.75, -84.39),
    ("Vancouver", 49.28, -123.12), ("Victoria", 48.43, -123.37),
    ("Calgary", 51.05, -114.07), ("Edmonton", 53.55, -113.49),
    ("Regina", 50.45, -104.61), ("Saskatoon", 52.13, -106.67),
    ("Winnipeg", 49.90, -97.14), ("Toronto", 43.65, -79.38),
    ("Ottawa", 45.42, -75.69), ("Montreal", 45.50, -73.56),
    ("Quebec City", 46.81, -71.21), ("Halifax", 44.65, -63.57),
    ("St. John's", 47.56, -52.71),
]

# Belirli mesafe sınırları koyuyoruz km cinsinden. (Amerika'da normalde mil cinsinde)
DISTANCE_LIMIT = 1000.0

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formülü ile iki nokta arası mesafe.
    """
    radius = 6371.0  # Dünyanın yarıçapı

    p1, p2 = math.radians(lat1), math.radians(lat2)
    diff_lat = math.radians(lat2 - lat1)
    diff_lon = math.radians(lon2 - lon1)

    calc_a = (math.sin(diff_lat / 2) ** 2 + 
              math.cos(p1) * math.cos(p2) * math.sin(diff_lon / 2) ** 2)
    
    calc_c = 2 * math.atan2(math.sqrt(calc_a), math.sqrt(1 - calc_a))
    return radius * calc_c

def find_nearest_city(lat, lon):
    if lat is None or lon is None:
        return None

    closest_name = None
    min_dist = float('inf')

    for name, c_lat, c_lon in CITIES:
        d = calculate_distance(lat, lon, c_lat, c_lon)
        if d < min_dist:
            min_dist = d
            closest_name = name

    if min_dist <= DISTANCE_LIMIT:
        return closest_name
    return None

def save_to_json(storm_data, filename="storms.json"):
    base_path = Path(__file__).resolve().parent.parent
    data_path = base_path / "data"
    data_path.mkdir(exist_ok=True)

    output_file = data_path / filename

    def json_fixer(obj):
        if hasattr(obj, 'isoformat'):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return str(obj)

    bundle = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_events": len(storm_data),
        "events": storm_data
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=4, ensure_ascii=False, default=json_fixer)
    
    return output_file

def print_summary(events):
    city_counts = {}
    unassigned = 0

    for item in events:
        c = item