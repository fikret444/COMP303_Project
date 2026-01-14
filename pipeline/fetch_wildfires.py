import json
import math
from datetime import datetime
from pathlib import Path

from datasources.eonet_wildfire_source import EONETWildfireSource
from processing.storage import log_message

MONITORED_CITIES = [
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

# Şehir eşleştirme eşiği (km cinsinden)
DISTANCE_THRESHOLD = 1000.0

def get_distance_km(lat1, lon1, lat2, lon2):
    earth_radius = 6371.0 

    r_lat1, r_lat2 = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    step1 = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(r_lat1) * math.cos(r_lat2) * math.sin(delta_lon / 2) ** 2)
    
    step2 = 2 * math.atan2(math.sqrt(step1), math.sqrt(1 - step1))
    return earth_radius * step2

def find_matching_city(lat, lon):
    if lat is None or lon is None:
        return None

    target_city = None
    closest_distance = float('inf')

    for name, c_lat, c_lon in MONITORED_CITIES:
        d = get_distance_km(lat, lon, c_lat, c_lon)
        if d < closest_distance:
            closest_distance = d
            target_city = name

    if closest_distance <= DISTANCE_THRESHOLD:
        return target_city
    
    return None

def save_data(wildfire_events, filename="wildfires.json"):
    root = Path(__file__).resolve().parent.parent
    data_folder = root / "data"
    data_folder.mkdir(exist_ok=True)

    dest_path = data_folder / filename

    def wildfire_encoder(obj):
        if hasattr(obj, 'isoformat'):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return str(obj)

    container = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_events": len(wildfire_events),
        "events": wildfire_events
    }

    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(container, f, indent=4, ensure_ascii=False, default=wildfire_encoder)
    
    return dest_path

def display_summary(events):
    distribution = {}
    outer_zone = 0

    for item in events:
        loc = item.get("city")
        if loc:
            distribution[loc] = distribution.get(loc, 0) + 1
        else:
            outer_zone += 1

    print("\n" + "🔥" * 15)
    print(" ORMAN YANGINLARI ANALİZİ ")
    print("🔥" * 15)

    if not distribution and outer_zone == 0:
        print("[!] Herhangi bir yangın kaydı bulunamadı.")
        return

    sorted_cities = sorted(distribution.items(), key=lambda x: x[1], reverse=True)

    for city, count in sorted_cities:
        print(f" -> {city}: {count} yangın")

    if outer_zone > 0:
        print(f"\n[Not] Şehir merkezlerinden uzak {outer_zone} olay saptandı.")

    log_message(f"Wildfire stats updated. Impacted cities: {len(distribution)}")

def main():
    wf_source = EONETWildfireSource(days=365, status="all")
    
    print(">>> NASA EONET sisteminden yangın verileri çekiliyor...")
    log_message("Wildfire fetch process started.")

    try:
        raw_output = wf_source.fetch_raw()
        all_fires = wf_source.parse(raw_output)
        print(f"[+] Toplam {len(all_fires)} yangın olayı sisteme yüklendi.")
    except Exception as e:
        print(f"[Hata] Veri çekilemedi: {e}")
        log_message(f"Wildfire API error: {e}", level="ERROR")
        return

    for fire in all_fires:
        matched = find_matching_city(fire.get("latitude"), fire.get("longitude"))
        fire["city"] = matched

    output_file = save_data(all_fires)
    print(f"[Kayıt] Dosya oluşturuldu: {output_file}")
    
    display_summary(all_fires)
    log_message("Wildfire pipeline finished.")

if __name__ == "__main__":
    main()