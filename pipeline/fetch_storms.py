# pipeline/fetch_storms.py

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from datasources.eonet_storm_source import EONETStormSource
from processing.storage import log_message


# ABD + Kanada için takip etmek istediğimiz şehirler (genişletilmiş liste)
CITIES: List[Tuple[str, float, float]] = [
    # ABD – Doğu ve Güney kıyıları
    ("New York", 40.71, -74.00),
    ("Boston", 42.36, -71.06),
    ("Washington DC", 38.90, -77.04),
    ("Miami", 25.76, -80.19),
    ("Tampa", 27.95, -82.46),
    ("New Orleans", 29.95, -90.07),
    ("Houston", 29.76, -95.37),

    # ABD – Batı kıyısı
    ("Los Angeles", 34.05, -118.24),
    ("San Diego", 32.72, -117.16),
    ("San Francisco", 37.77, -122.41),
    ("Seattle", 47.61, -122.33),

    # ABD – İç bölgeler (örnek, fırtına hattı)
    ("Chicago", 41.88, -87.63),
    ("Dallas", 32.78, -96.80),
    ("Atlanta", 33.75, -84.39),

    # KANADA – Batı ve iç bölgeler
    ("Vancouver", 49.28, -123.12),
    ("Victoria", 48.43, -123.37),
    ("Calgary", 51.05, -114.07),
    ("Edmonton", 53.55, -113.49),
    ("Regina", 50.45, -104.61),
    ("Saskatoon", 52.13, -106.67),
    ("Winnipeg", 49.90, -97.14),

    # KANADA – Doğu ve Atlantik kıyısı
    ("Toronto", 43.65, -79.38),
    ("Ottawa", 45.42, -75.69),
    ("Montreal", 45.50, -73.56),
    ("Quebec City", 46.81, -71.21),
    ("Halifax", 44.65, -63.57),
    ("St. John's", 47.56, -52.71),
]

# Bir event'in bir şehre atanması için maksimum mesafe (km)
CITY_MATCH_THRESHOLD_KM = 1000.0


# --- Mesafe hesabı (haversine) ---

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    İki koordinasyon arasındaki yaklaşık mesafeyi km cinsinden hesaplar.
    Haversine formülü.
    """
    R = 6371.0  # Dünya yarıçapı (km)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def assign_city(lat: Optional[float], lon: Optional[float]) -> Optional[str]:
    """
    Verilen lat/lon için CITIES listesindeki en yakın şehri bulur.
    Eğer en yakın şehir CITY_MATCH_THRESHOLD_KM'den uzaktaysa None döner.
    """
    if lat is None or lon is None:
        return None

    best_city = None
    best_dist = None

    for city_name, city_lat, city_lon in CITIES:
        dist = haversine_km(lat, lon, city_lat, city_lon)
        if (best_dist is None) or (dist < best_dist):
            best_dist = dist
            best_city = city_name

    if best_dist is not None and best_dist <= CITY_MATCH_THRESHOLD_KM:
        return best_city

    return None


# --- JSON kaydetme ---

def save_storms_to_json(events: List[Dict[str, Any]], filename: str = "storms.json") -> Path:
    """
    Storm event'lerini proje kökündeki data/ klasörüne JSON olarak kaydeder.
    """
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"
    data_dir.mkdir(exist_ok=True)

    file_path = data_dir / filename

    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d T%H:%M:%S")
        return str(obj)

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d T%H:%M:%S"),
        "total_events": len(events),
        "events": events,
    }

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=default_serializer)

    return file_path


# --- Özet yazdırma ---

def summarize_storms(events: List[Dict[str, Any]]) -> None:
    """
    Şehir bazlı kaç fırtına olayı olduğunu özetler.
    """
    per_city: Dict[str, int] = {}
    no_city = 0

    for ev in events:
        city = ev.get("city")
        if city is None:
            no_city += 1
        else:
            per_city[city] = per_city.get(city, 0) + 1

    print("\n📊 Fırtına (severeStorms) Özet – Şehir Bazlı")
    log_message("Storm: Şehir bazlı fırtına özeti oluşturuldu.", level="INFO")

    if not per_city and no_city == 0:
        print("   Hiç olay bulunamadı.")
        log_message("Storm: Hiç event bulunamadı.", level="WARNING")
        return

    for city, count in per_city.items():
        print(f"   • {city}: {count} olay")
        log_message(f"Storm summary for {city}: {count} event", level="INFO")

    if no_city > 0:
        print(f"\n   (Şehre atanamayan {no_city} event var – koordinatlar şehir listesine uzak.)")
        log_message(
            f"Storm: Şehre atanamayan event sayısı = {no_city}",
            level="INFO",
        )


# --- main ---

def main():
    # 1) EONET'ten severeStorms olaylarını çek
    # ABD + Kanada kutusu içinde, son 365 günde, open + closed
    src = EONETStormSource(
        days=365,
        status="all",
        bbox=EONETStormSource.DEFAULT_NA_BBOX,
    )

    print("🌪 NASA EONET severeStorms verisi çekiliyor...")
    log_message("Storm: NASA EONET severeStorms verisi çekiliyor...", level="INFO")

    raw = src.fetch_raw()
    events = src.parse(raw)
    print(f"   → Toplam {len(events)} storm event alındı.")
    log_message(f"Storm: Toplam {len(events)} storm event alındı.", level="INFO")

    # 2) Event'leri en yakın şehre ata
    for ev in events:
        lat = ev.get("latitude")
        lon = ev.get("longitude")
        city = assign_city(lat, lon)
        ev["city"] = city  # None olabilir

    # 3) JSON'a kaydet
    file_path = save_storms_to_json(events, filename="storms.json")
    print(f"💾 Fırtına event'leri {file_path} dosyasına kaydedildi.")
    log_message(f"Storm: Event'ler {file_path} dosyasına kaydedildi.", level="INFO")

    # 4) Özet yazdır
    summarize_storms(events)


if __name__ == "__main__":
    main()

