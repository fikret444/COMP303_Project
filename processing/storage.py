import csv
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Project root'u bul (src klasörünün bir üstü)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Folder Path
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"

# Create if folders don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


def save_events_to_csv(events, filename="events.csv", append=True):
    """
    İstersen ileride kullanırsın diye bırakıyoruz.
    Şu an USGS pipeline'ında kullanılmıyor.
    
    Accepts both objects (with toDictionary method) and dictionaries.
    """
    if not events:
        return

    file_path = DATA_DIR / filename

    # Convert objects to dictionaries if needed
    serializable_events = []
    for event in events:
        # Check if it's an object with toDictionary method
        if hasattr(event, 'toDictionary'):
            serializable_events.append(event.toDictionary())
        else:
            # Already a dictionary
            serializable_events.append(event)

    if not serializable_events:
        return

    fieldnames = list(serializable_events[0].keys())
    file_exists = file_path.exists()
    mode = "a" if append and file_exists else "w"

    with file_path.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        writer.writerows(serializable_events)


def save_events_to_json(events, filename="events.json"):
    """
    Event listesini data/ klasöründe JSON dosyasına kaydeder.
    Örn: data/earthquakes_tr.json
    
    Accepts both objects (with toDictionary method) and dictionaries.
    """
    if not events:
        return

    file_path = DATA_DIR / filename

    # Convert objects to dictionaries if needed
    serializable_events = []
    for event in events:
        # Check if it's an object with toDictionary method
        if hasattr(event, 'toDictionary'):
            serializable_events.append(event.toDictionary())
        else:
            # Already a dictionary
            serializable_events.append(event)

    # datetime objelerini ISO string'e çevir
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(serializable_events, f, ensure_ascii=False, indent=2, default=json_serializer)


def log_message(message, level="INFO"):
    """
    logs/app.log içine zaman damgası + seviye + mesaj yazar.
    Zaman damgası Europe/Istanbul (Türkiye saati) kullanır.
    """
    log_file = LOGS_DIR / "app.log"
    now = datetime.now(ZoneInfo("Europe/Istanbul")).isoformat()

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{now} [{level}] {message}\n")