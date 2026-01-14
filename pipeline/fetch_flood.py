import json
import random
from datetime import datetime
from pathlib import Path

from datasources.flood_openmeteo_source import OpenMeteoFloodSource
from processing.storage import log_message

CITIES = [
    ("New Orleans", 29.9511, -90.0715),
    ("Houston", 29.7604, -95.3698),
    ("Miami", 25.7617, -80.1918),
    ("New York", 40.7128, -74.0060),
    ("Sacramento", 38.5816, -121.4944),
    ("Vancouver", 49.2827, -123.1207),
    ("Calgary", 51.0447, -114.0719),
    ("Montreal", 45.5019, -73.5674),
    ("Winnipeg", 49.8954, -97.1385),
    ("Toronto", 43.6510, -79.3470),
]

def fetch_flood_risk_for_all_cities():
    all_events = []

    for city_name, lat, lon in CITIES:
        print(f">> Veri alınıyor: {city_name}...")
        log_message(f"Flood query started for: {city_name}")

        try:
            src = OpenMeteoFloodSource(
                latitude=lat,
                longitude=lon,
                location_name=city_name,
                past_days=3,
                forecast_days=7,
            )

            raw_data = src.fetch_raw()
            city_events = src.parse(raw_data)
            
            if city_events:
                print(f"   [+] {city_name}: {len(city_events)} kayıt eklendi.")
                all_events.extend(city_events)
            else:
                print(f"   [!] {city_name} için veri bulunamadı.")
                
        except Exception as err:
            log_message(f"Problem fetching {city_name}: {err}", level="ERROR")
            continue

    return all_events

def filter_high_risk_events(events):
    """
    Sadece yüksek riskli olanları ayırır.
    """
    high_risk_subset = []
    for ev in events:
        is_flood = ev.get("type") == "flood_risk"
        is_high = ev.get("risk_level") == "high"
        
        if is_flood and is_high:
            high_risk_subset.append(ev)
    return high_risk_subset

def save_events_to_json(all_events, high_events, filename="flood_risk.json"):
    current_dir = Path(__file__).resolve().parent
    data_dir = current_dir.parent / "data"
    
    if not data_dir.exists():
        data_dir.mkdir(parents=True)

    file_path = data_dir / filename

    output_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_events": len(all_events),
        "total_high_risk_events": len(high_events),
        "events": all_events,
        "high_risk_events": high_events,
    }

    def handle_special_types(o):
        if hasattr(o, 'strftime'):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        return str(o)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4, default=handle_special_types)

    return file_path

def summarize_flood_risk(events):
    stats = {}

    for ev in events:
        location = ev.get("location", "Unknown City")
        risk = ev.get("risk_level", "unknown")
        
        if location not in stats:
            stats[location] = {"low": 0, "medium": 0, "high": 0, "unknown": 0, "peak_discharge": 0.0}

        if risk in stats[location]:
            stats[location][risk] += 1
        else:
            stats[location]["unknown"] += 1

        val = ev.get("river_discharge")
        if val:
            try:
                num_val = float(val)
                if num_val > stats[location]["peak_discharge"]:
                    stats[location]["peak_discharge"] = num_val
            except:
                pass

    print("\n" + "="*45)
    print(" SEL RİSKİ ÖZET RAPORU ".center(45, "#"))
    print("="*45)

    for city, data in stats.items():
        print(f"\n[*] Şehir: {city}")
        print(f"    Risk Dağılımı -> High: {data['high']}, Med: {data['medium']}, Low: {data['low']}")
        if data["peak_discharge"] > 0:
            print(f"    Maksimum Debi: {data['peak_discharge']} m3/s")
    
    print("="*45)

def main():
    log_message("Flood fetch process started.")
    
    raw_results = fetch_flood_risk_for_all_cities()
    
    if not raw_results:
        log_message("No flood data retrieved, shutting down.", level="WARNING")
        return

    high_risks = filter_high_risk_events(raw_results)
    
    target_file = save_events_to_json(raw_results, high_risks)
    print(f"\n[OK] Veriler kaydedildi: {target_file}")
    
    summarize_flood_risk(raw_results)
    log_message("Flood fetch process completed successfully.")

if __name__ == "__main__":
    main()