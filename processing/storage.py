import csv
import json
import glob
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

project_path = Path(__file__).resolve().parent.parent
veri_klasoru = project_path / "data"
log_klasoru = project_path / "logs"

veri_klasoru.mkdir(exist_ok=True)
log_klasoru.mkdir(exist_ok=True)


def eski_dosyalari_temizle():
   
    earthquake_pattern = str(veri_klasoru / "earthquakes_*.json")
    earthquake_files = glob.glob(earthquake_pattern)
    if len(earthquake_files) > 5:
        earthquake_files.sort(key=os.path.getctime, reverse=True)
        for eski_dosya in earthquake_files[5:]:
            try:
                os.remove(eski_dosya)
                log_message(f"Eski dosya başarıyla temizlendi: {os.path.basename(eski_dosya)}", "INFO")
            except OSError as hata:
                log_message(f"Eski dosya silinemedi {eski_dosya}: {hata}", "WARNING")
    
    # weather_all.json dosyasının içi 10MB üzerine çıkarsa içi temizlenecek
    weather_file = veri_klasoru / "weather_all.json"
    if weather_file.exists():
        dosya_boyutu = os.path.getsize(weather_file) / 1000000
        if dosya_boyutu > 10:
            try:
                weather_file.unlink()
                log_message(f"weather_all.json başarıyla temizlendi (boyut: {dosya_boyutu:.2f} MB)", "INFO")
            except OSError as hata:
                log_message(f"weather_all.json silinemedi: {hata}", "WARNING")

    # app.log dosyası 5MB üzerine ulaşırsa temizleyeceğiz
    log_file = log_klasoru / "app.log"
    if log_file.exists():
        dosya_boyutu = os.path.getsize(log_file) / 1000000
        if dosya_boyutu > 5:
            try:
                log_file.unlink()
                log_message(f"app.log başarıyla temizlendi (boyut: {dosya_boyutu:.2f} MB)", "INFO")
            except OSError as hata:
                log_message(f"app.log dosyası silinemedi: {hata}", "WARNING")

def veriyi_hazirla(ham_liste):
    duzenli_liste = []
    for madde in ham_liste:
        if hasattr(madde, 'toDictionary'):
            duzenli_liste.append(madde.toDictionary())
        else:
            duzenli_liste.append(madde)
    return duzenli_liste

def save_events_to_csv(events, filename="events.csv", append=True):
    if not events:
        return

    file_path = veri_klasoru / filename
    
    serializable_events = veriyi_hazirla(events)

    if not serializable_events:
        return

    basliklar = list(serializable_events[0].keys())
    file_exists = file_path.exists()
    mode = "a" if append and file_exists else "w"

    with file_path.open(mode, newline="", encoding="utf-8") as f:
        csv_yazici = csv.DictWriter(f, fieldnames=basliklar)
        if mode == "w":
            csv_yazici.writeheader()
        csv_yazici.writerows(serializable_events)

def save_events_to_json(events, filename="events.json"):
    if not events:
        return

    file_path = veri_klasoru / filename

    serializable_events = veriyi_hazirla(events)

    # datetime objelerini ISO'dan kendi insiyatifimize uymak için formatladık
    def tarih_formatla(obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return str(obj)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(serializable_events, f, ensure_ascii=False, indent=2, default=tarih_formatla)


def log_message(message, level="INFO"):
   
    log_file = log_klasoru / "app.log"
    zaman_damgasi = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%d-%m-%Y %H:%M:%S")

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{zaman_damgasi} [{level}] {message}\n")