import csv
import json
from pathlib import Path
from datetime import datetime

project_path = Path(__file__).resolve().parent.parent
veri_klasoru = project_path / "data"

def _veri_tipini_duzelt(event_dict):
    try:
        if "id" in event_dict:
            event_dict["id"] = int(event_dict["id"])
    except:
        pass

    try:
        if "magnitude" in event_dict:
            event_dict["magnitude"] = float(event_dict["magnitude"])
    except:
        pass
    
    return event_dict

def load_events_from_csv(filename="earthquakes.csv"):
    file_path = veri_klasoru / filename
    events = []

    if not file_path.exists():
        return events

    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(_veri_tipini_duzelt(row))

    return events

def load_events_from_json(filename="earthquakes_tr.json"):
    file_path = veri_klasoru / filename
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    events = []
    for item in data:
        events.append(_veri_tipini_duzelt(item))
        
    return events

def compute_basic_stats(events):
    if not events:
        return None

    magnitudes = []
    for e in events:
        mag = getattr(e, 'magnitude', None) if not isinstance(e, dict) else e.get("magnitude")
        
        if isinstance(mag, (int, float)):
            magnitudes.append(mag)

    if not magnitudes:
        return {"total_events": len(events), "status": "No magnitude data found"}

    stats = {
        "total_events": len(events),
        "max_magnitude": max(magnitudes),
        "min_magnitude": min(magnitudes),
        "avg_magnitude": round(sum(magnitudes) / len(magnitudes), 2),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return stats
# 2.5 ve üzeri depremleri göndermemizi sağlayan fonsiyon
def count_strong_earthquakes(events, threshold=2.5):
    count = 0
    for e in events:
        # dict/obje umursamadan direkt magnitude değerini çeker
        mag = e.get("magnitude") if isinstance(e, dict) else getattr(e, "magnitude", 0)
        
        if isinstance(mag, (int, float)) and mag >= threshold:
            count += 1
    return count

def filter_events_in_bbox(events, min_lat, max_lat, min_lon, max_lon):
    """
    Belirli koordinatlar arasındaki depremleri filtreler.
    """
    filtered = []

    for e in events:
        if isinstance(e, dict):
            lat, lon = e.get("latitude"), e.get("longitude")
        else:
            lat, lon = getattr(e, "latitude", None), getattr(e, "longitude", None)

        # Koordinat olması şart yoksa atlayacak hatta sayı yoksa da atlamalı
        if not all(isinstance(x, (int, float)) for x in [lat, lon]):
            continue

        if (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon):
            filtered.append(e)

    return filtered