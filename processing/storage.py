import csv
import json
import glob
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Project root'u bul (src klasörünün bir üstü)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Folder Path
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"

# Create if folders don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


def cleanup_old_files():
    """
    Eski dosyaları temizle:
    - earthquakes_*.json dosyalarından en son 5'ini tut, diğerlerini sil
    - weather_all.json 10 MB'dan büyükse temizle
    - app.log 5 MB'dan büyükse temizle
    """
    # Eski earthquake dosyalarını temizle (en son 5'ini tut)
    earthquake_pattern = str(DATA_DIR / "earthquakes_*.json")
    earthquake_files = glob.glob(earthquake_pattern)
    if len(earthquake_files) > 5:
        # En son oluşturulan 5 dosyayı tut
        earthquake_files.sort(key=os.path.getctime, reverse=True)
        for old_file in earthquake_files[5:]:
            try:
                os.remove(old_file)
                log_message(f"Eski dosya temizlendi: {os.path.basename(old_file)}", "INFO")
            except Exception as e:
                log_message(f"Eski dosya silinemedi {old_file}: {e}", "WARNING")
    
    # weather_all.json boyut kontrolü (10 MB'dan büyükse temizle)
    weather_file = DATA_DIR / "weather_all.json"
    if weather_file.exists():
        size_mb = weather_file.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            try:
                weather_file.unlink()
                log_message(f"weather_all.json temizlendi (boyut: {size_mb:.2f} MB)", "INFO")
            except Exception as e:
                log_message(f"weather_all.json silinemedi: {e}", "WARNING")
    
    # app.log boyut kontrolü (5 MB'dan büyükse temizle)
    log_file = LOGS_DIR / "app.log"
    if log_file.exists():
        size_mb = log_file.stat().st_size / (1024 * 1024)
        if size_mb > 5:
            try:
                log_file.unlink()
                log_message(f"app.log temizlendi (boyut: {size_mb:.2f} MB)", "INFO")
            except Exception as e:
                log_message(f"app.log silinemedi: {e}", "WARNING")


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