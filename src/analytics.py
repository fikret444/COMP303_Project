import csv
from pathlib import Path

#Folder Path (project root'ta "data" klasörü)
DATA_DIR = Path("data")

def load_events_from_csv(filename="earthquakes.csv"):
    """
    data/ klasöründeki CSV dosyasını okur,
    her satırı dict olarak listeye ekler.
    """
    file_path = DATA_DIR / filename
    events = []

    if not file_path.exists():
        # Dosya yoksa boş liste döndür
        return events

    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # id'yi mümkünse int'e, magnitude'ü float'a çevir
            try:
                row["id"] = int(row["id"])
            except (ValueError, KeyError):
                pass

            try:
                row["magnitude"] = float(row["magnitude"])
            except (ValueError, KeyError):
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

def count_strong_earthquakes(events, threshold=5.0):
    """
    Belirli bir threshold'dan buyuk magnitude'lı event sayısını döndürür.
    """
    count = 0
    for e in events:
        mag = e.get("magnitude")
        if isinstance(mag, (int, float)) and mag >= threshold:
            count += 1
    return count