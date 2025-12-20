import csv
import json
from pathlib import Path

# Proje kök klasörü (SDEWS)
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def load_events_from_csv(filename="earthquakes.csv"):
    """
    Eski CSV pipeline'ı için; USGS hattında şu an kullanılmıyor.
    """
    file_path = DATA_DIR / filename
    events = []

    if not file_path.exists():
        return events

    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                if "id" in row:
                    row["id"] = int(row["id"])
            except (ValueError, TypeError):
                pass

            try:
                if "magnitude" in row:
                    row["magnitude"] = float(row["magnitude"])
            except (ValueError, TypeError):
                pass

            events.append(row)

    return events


def load_events_from_json(filename="earthquakes_tr.json"):
    """
    USGS pipeline'ı için: Türkiye içindeki depremleri JSON'dan okur.
    """
    file_path = DATA_DIR / filename
    events = []

    if not file_path.exists():
        return events

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for row in data:
        try:
            if "id" in row:
                row["id"] = int(row["id"])
        except (ValueError, TypeError):
            pass

        try:
            if "magnitude" in row:
                row["magnitude"] = float(row["magnitude"])
        except (ValueError, TypeError):
            pass

        events.append(row)

    return events


def compute_basic_stats(events):
    """
    Event listesi için basit istatistikler döndürür:
    kaç event, max/min/ortalama magnitude gibi.
    """
    if not events:
        return None

    magnitudes = []
    for e in events:
        mag = e.get("magnitude")
        if isinstance(mag, (int, float)):
            magnitudes.append(mag)

    if not magnitudes:
        return None

    total_events = len(events)
    max_mag = max(magnitudes)
    min_mag = min(magnitudes)
    avg_mag = sum(magnitudes) / len(magnitudes)

    return {
        "total_events": total_events,
        "max_magnitude": max_mag,
        "min_magnitude": min_mag,
        "avg_magnitude": avg_mag,
    }


def count_strong_earthquakes(events, threshold=2.5):
    """
    Belirli bir eşik değerinin (threshold) üzerindeki
    deprem sayısını döndürür.
    Örn: threshold=5.0 -> 5.0 ve üzeri depremleri say.
    """
    count = 0
    for e in events:
        mag = e.get("magnitude")
        if isinstance(mag, (int, float)) and mag >= threshold:
            count += 1
    return count


def filter_events_in_bbox(events, min_lat, max_lat, min_lon, max_lon):
    """
    Verilen enlem/boylam dikdörtgeni (bounding box) içindeki event'leri döndürür.
    Örn: Türkiye veya belirli bir şehir için filtreleme.
    """
    filtered = []

    for e in events:
        lat = e.get("latitude")
        lon = e.get("longitude")

        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue

        if (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon):
            filtered.append(e)

    return filtered