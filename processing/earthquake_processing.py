from datetime import datetime

from .storage import log_message
from models import RawEarthquake, CleanedEarthquake

"""
Deprem (earthquake) verilerini temizleme ve USGS formatından
sistemin iç earthquake modeline dönüştürme fonksiyonları.

Bu dosya sadece deprem pipeline'ı içindir; diğer afet türleri
(flood, storm, wildfire, volcano, weather) burada işlenmez.
"""

# Genel deprem event'i için sistem içinde kullanacağımız zorunlu alanlar
REQUIRED_FIELDS = ["id", "event_type", "timestamp", "magnitude", "location"]

# USGS kaynağından beklediğimiz temel alanlar
USGS_REQUIRED_FIELDS = ["type", "time", "magnitude", "location"]


def clean_earthquake_event(raw_event: dict):
    """
    Tek bir ham deprem event'ini temizler.
    Eksik veya hatalı veri varsa None döndürür.

    Bu fonksiyon, bizim iç formatımıza uygun olan event'ler için kullanılır:
    id, event_type, timestamp, magnitude, location (ve opsiyonel latitude/longitude).
    """

    # 1) Zorunlu alanlar var mı?
    for field in REQUIRED_FIELDS:
        if field not in raw_event or raw_event[field] in (None, ""):
            log_message(
                f"Eksik alan: {field}. Event kaydedilmedi: {raw_event}",
                level="WARNING",
            )
            return None

    # 2) Temel alanları normalize et
    cleaned = {
        "id": raw_event["id"],
        "event_type": str(raw_event["event_type"]).lower(),
        "timestamp": str(raw_event["timestamp"]),
        "location": str(raw_event["location"]),
    }

    # 3) Magnitude'u sayıya çevir
    try:
        cleaned["magnitude"] = float(raw_event["magnitude"])
    except (ValueError, TypeError):
        log_message(
            f"Geçersiz magnitude: {raw_event.get('magnitude')}. Event kaydedilmedi: {raw_event}",
            level="WARNING",
        )
        return None

    # 4) Opsiyonel: latitude/longitude varsa ekle
    lat = raw_event.get("latitude")
    lon = raw_event.get("longitude")

    if lat is not None:
        try:
            cleaned["latitude"] = float(lat)
        except (ValueError, TypeError):
            log_message(
                f"Geçersiz latitude: {lat}. Koordinat atlandı.",
                level="WARNING",
            )

    if lon is not None:
        try:
            cleaned["longitude"] = float(lon)
        except (ValueError, TypeError):
            log_message(
                f"Geçersiz longitude: {lon}. Koordinat atlandı.",
                level="WARNING",
            )

    return cleaned


def clean_earthquake_events(raw_events):
    """
    İç formatımıza (id, event_type, timestamp, magnitude, location, ...)
    yakın olan event listesi için toplu temizleme fonksiyonu.

    Input:
      - Dictionary listesi
      - veya RawEarthquake objeleri

    Output:
      - CleanedEarthquake objeleri listesi
    """
    cleaned_list = []

    for ev in raw_events:
        # RawEarthquake obje ise:
        if isinstance(ev, RawEarthquake):
            cleaned = CleanedEarthquake.fromRaw(ev)
            cleaned_list.append(cleaned)
        else:
            # Dictionary ise:
            cleaned_dict = clean_earthquake_event(ev)
            if cleaned_dict is not None:
                cleaned = CleanedEarthquake(
                    id=cleaned_dict["id"],
                    event_type=cleaned_dict["event_type"],
                    timestamp=cleaned_dict["timestamp"],
                    magnitude=cleaned_dict["magnitude"],
                    location=cleaned_dict["location"],
                    latitude=cleaned_dict.get("latitude"),
                    longitude=cleaned_dict.get("longitude"),
                )
                cleaned_list.append(cleaned)

    log_message(f"Temizlenen event sayısı: {len(cleaned_list)}", level="INFO")
    return cleaned_list


def clean_usgs_earthquake_events(usgs_events):
    """
    USGS kaynağından gelen ham deprem event listesini alır,
    bizim sistemin kullandığı formata çevirip temizler.

    Input:
      - RawEarthquake objeleri
      - veya USGS'ten gelen dictionary formatı

    Output:
      - CleanedEarthquake objeleri listesi
    """
    cleaned_list = []

    for index, raw in enumerate(usgs_events, start=1):
        # 1) Ortak bir dictionary görünümü üret
        if isinstance(raw, RawEarthquake):
            raw_dict = raw.toDictionary()
            time_val = raw.time
        else:
            raw_dict = raw
            time_val = raw.get("time")

            # Dict için zorunlu alan kontrolü
            missing = [
                field
                for field in USGS_REQUIRED_FIELDS
                if field not in raw_dict or raw_dict[field] in (None, "")
            ]
            if missing:
                log_message(
                    f"USGS event'inde eksik alan(lar): {missing}. Event kaydedilmedi: {raw_dict}",
                    level="WARNING",
                )
                continue

        # 2) Zamanı ISO string'e çevir
        if isinstance(time_val, (int, float)):
            # ms cinsinden epoch ise:
            ts = datetime.fromtimestamp(time_val / 1000).isoformat()
        elif hasattr(time_val, "isoformat"):
            ts = time_val.isoformat()
        else:
            ts = str(time_val)

        # 3) Magnitude'u float'a çevir
        try:
            if isinstance(raw, RawEarthquake):
                magnitude = float(raw.magnitude)
            else:
                magnitude = float(raw_dict.get("magnitude"))
        except (TypeError, ValueError):
            mag_val = raw.magnitude if isinstance(raw, RawEarthquake) else raw_dict.get(
                "magnitude"
            )
            log_message(
                f"USGS event'inde geçersiz magnitude: {mag_val}. Event kaydedilmedi",
                level="WARNING",
            )
            continue

        # 4) Konum (location)
        if isinstance(raw, RawEarthquake):
            location = raw.location
        else:
            location = raw_dict.get("location")
        if not location:
            location = "Unknown"

        # 5) Latitude / Longitude
        if isinstance(raw, RawEarthquake):
            latitude = raw.latitude
            longitude = raw.longitude
        else:
            latitude = raw_dict.get("latitude")
            longitude = raw_dict.get("longitude")

        cleaned_eq = CleanedEarthquake(
            id=index,
            event_type="earthquake",
            timestamp=ts,
            location=str(location),
            magnitude=magnitude,
            latitude=latitude,
            longitude=longitude,
        )

        cleaned_list.append(cleaned_eq)

    log_message(f"USGS'ten temizlenen event sayısı: {len(cleaned_list)}", level="INFO")
    return cleaned_list

