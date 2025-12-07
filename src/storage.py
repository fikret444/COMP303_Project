import csv
from pathlib import Path
from datetime import datetime

# Project root'u bul (src klasörünün bir üstü)
ROOT_DIR = Path(__file__).resolve().parent.parent

#Folder Path
DATA_DIR = Path("data")
LOGS_DIR = Path("logs")

#Create if folders doesn't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

def save_events_to_csv(events, filename="events.csv"):
    """
    events: list[dict] bekliyoruz
    Hepsini data/ klasöründeki bir CSV dosysasına ekler.
    """
    if not events:
        #If the list is empty, don't do anything
        return

    file_path = DATA_DIR / filename

    #İlk event'in key'lerini kolon adı olarak kabul edeceğiz
    fieldnames = list(events[0].keys())

    #Check if the file already exists
    file_exists = file_path.exists()

    with file_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        #If the file is new, write the column names
        if not file_exists:
            writer.writeheader()

        #Write all events line by line
        writer.writerows(events)

def log_message(message, level="INFO"):
    """
    logs/app.log içine zaman damgası + seviye + mesaj yazar.
    """
    log_file = LOGS_DIR / "app.log"
    now = datetime.utcnow().isoformat()

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{now} [{level}] {message}\n")