# src/processing.py

from datetime import datetime
from .storage import log_message

# ---------------------------------------------------
# 1) LOKAL / ÖRNEK DEPREM EVENT'LERİ İÇİN TEMİZLEME
# ---------------------------------------------------

LOCAL_EQ_REQUIRED_FIELDS = ["id", "event_type", "timestamp", "magnitude", "location"]


def clean_earthquake_events(raw_events):
    """
    Elle girdiğimiz / örnek deprem event'lerini normalize eder.

    Beklenen ham format:
    {
        "id": 1,
        "event_type": "earthquake",
        "timestamp": "2020-11-30T14:51:00Z",
        "magnitude": "6.9",
        "location": "İzmir",
    }

    Dönen format:
    - id: int
    - event_type: "earthquake"
    - timestamp: string (ISO benzeri)
    - location: string
    - magnitude: float
    """
    cleaned = []

    for ev in raw_events:
        # Zorunlu alan kontrolü
        missing = [field for field in LOCAL_EQ_REQUIRED_FIELDS if field not in ev]
        if missing:
            log_message(
                f"Eksik alan: {missing}. Event kaydedilmedi: {ev}",
                level="WARNING",
            )
            continue

        # event_type normalize
        event_type = str(ev.get("event_type", "")).lower()
        if event_type != "earthquake":
            log_message(
                f"Desteklenmeyen event_type: {event_type}. Event atlandı: {ev}",
                level="WARNING",
            )
            continue

        # magnitude float'a çevrilir
        try:
            mag = float(ev.get("magnitude"))
        except (TypeError, ValueError):
            log_message(
                f"Geçersiz magnitude: {ev.get('magnitude')}. Event kaydedilmedi: {ev}",
                level="WARNING",
            )
            continue

        # id int'e çevrilir
        try:
            ev_id = int(ev.get("id"))
        except (TypeError, ValueError):
            log_message(
                f"Geçersiz id: {ev.get('id')}. Event kaydedilmedi: {ev}",
                level="WARNING",
            )
            continue

        cleaned.append(
            {
                "id": ev_id,
                "event_type": "earthquake",
                "timestamp": str(ev.get("timestamp")),
                "location": ev.get("location"),
                "magnitude": mag,
            }
        )

    log_message(f"Temizlenen event sayısı: {len(cleaned)}", level="INFO")
    return cleaned


# ---------------------------------------------------
# 2) USGS DEPREM EVENT'LERİ İÇİN TEMİZLEME
# ---------------------------------------------------

USGS_REQUIRED_FIELDS = ["type", "source", "location", "magnitude", "time"]


def clean_usgs_earthquake_events(raw_events):
    """
    USGS'ten gelen deprem event'lerini normalize eder.

    Beklenen ham format (parse_usgs_geojson sonrası):
    {
        "type": "earthquake",
        "source": "USGS",
        "location": "...",
        "magnitude": 4.3,
        "time": datetime(...),
        "latitude": ...,
        "longitude": ...
    }

    Dönen format:
    - id: int
    - event_type: "earthquake"
    - timestamp: ISO string
    - location: string
    - magnitude: float
    - latitude / longitude: float veya None
    - source: "USGS"
    """
    cleaned = []

    for idx, ev in enumerate(raw_events, start=1):
        # Zorunlu alan kontrolü
        missing = [field for field in USGS_REQUIRED_FIELDS if field not in ev]
        if missing:
            log_message(
                f"USGS event'inde eksik alan(lar): {missing}. Event atlandı: {ev}",
                level="WARNING",
            )
            continue

        event_type = str(ev.get("type", "")).lower()
        if event_type != "earthquake":
            # Sadece deprem event'leriyle ilgileniyoruz
            continue

        # magnitude float'a çevrilir
        mag = ev.get("magnitude")
        try:
            mag = float(mag)
        except (TypeError, ValueError):
            log_message(
                f"USGS event'inde geçersiz magnitude: {mag}. Event atlandı: {ev}",
                level="WARNING",
            )
            continue

        # time -> ISO string
        t = ev.get("time")
        if isinstance(t, datetime):
            ts = t.isoformat()
        else:
            try:
                ts = datetime.fromisoformat(str(t)).isoformat()
            except Exception:
                log_message(
                    f"USGS event'inde geçersiz zaman: {t}. Event atlandı: {ev}",
                    level="WARNING",
                )
                continue

        cleaned.append(
            {
                "id": idx,
                "event_type": "earthquake",
                "timestamp": ts,
                "location": ev.get("location", "Unknown"),
                "magnitude": mag,
                "latitude": ev.get("latitude"),
                "longitude": ev.get("longitude"),
                "source": ev.get("source", "USGS"),
            }
        )

    log_message(
        f"USGS'ten temizlenen event sayısı: {len(cleaned)}", level="INFO"
    )
    return cleaned


# ---------------------------------------------------
# 3) OPENWEATHER HAVA DURUMU EVENT'LERİ İÇİN TEMİZLEME
# ---------------------------------------------------

WEATHER_REQUIRED_FIELDS = [
    "type",
    "source",
    "location",
    "temperature",
    "wind_speed",
    "time",
]


def clean_openweather_events(raw_events):
    """
    OpenWeather'dan gelen anlık hava durumu event'lerini normalize eder.

    Beklenen ham format (openweather.py / fetch_openweather):
    {
        "type": "weather",
        "source": "OpenWeatherMap",
        "location": "Ankara,TR",
        "temperature": 12.3,
        "wind_speed": 4.5,
        "time": datetime(...)
    }

    Dönen format:
    - id: int
    - type: "weather"
    - source: "OpenWeatherMap"
    - location: string
    - temperature: float
    - wind_speed: float
    - time: ISO string
    """
    cleaned = []

    for idx, ev in enumerate(raw_events, start=1):
        # Zorunlu alan kontrolü
        missing = [field for field in WEATHER_REQUIRED_FIELDS if field not in ev]
        if missing:
            log_message(
                f"OpenWeather event'inde eksik alan(lar): {missing}. Event atlandı: {ev}",
                level="WARNING",
            )
            continue

        # temperature / wind_speed sayıya çevrilir
        try:
            temp = float(ev.get("temperature"))
            wind = float(ev.get("wind_speed"))
        except (TypeError, ValueError) as e:
            log_message(
                f"OpenWeather event'inde geçersiz sayı ({e}). Event atlandı: {ev}",
                level="WARNING",
            )
            continue

        # time -> ISO string
        time_val = ev.get("time")
        if isinstance(time_val, datetime):
            time_str = time_val.isoformat()
        else:
            # zaten string ise olduğu gibi bırak
            time_str = str(time_val)

        cleaned.append(
            {
                "id": idx,
                "type": ev.get("type", "weather"),
                "source": ev.get("source", "OpenWeatherMap"),
                "location": ev.get("location"),
                "temperature": temp,
                "wind_speed": wind,
                "time": time_str,
            }
        )

    log_message(
        f"OpenWeather'dan temizlenen hava durumu event sayısı: {len(cleaned)}",
        level="INFO",
    )
    return cleaned