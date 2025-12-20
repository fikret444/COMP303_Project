from datetime import datetime
from .storage import log_message

# Genel deprem event'i için sistem içinde kullanacağımız zorunlu alanlar
REQUIRED_FIELDS = ["id", "event_type", "timestamp", "magnitude", "location"]

# USGS kaynağından beklediğimiz temel alanlar
USGS_REQUIRED_FIELDS = ["type", "time", "magnitude", "location"]


def clean_earthquake_event(raw_event):
    """
    Tek bir ham deprem event'ini temizler.
    Eksik veya hatalı veri varsa None döndürür.
    Bu fonksiyon, bizim iç formatımıza uygun olan event'ler için kullanılır:
    id, event_type, timestamp, magnitude, location.
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
    """
    cleaned_list = []

    for ev in raw_events:
        cleaned = clean_earthquake_event(ev)
        if cleaned is not None:
            cleaned_list.append(cleaned)

    log_message(f"Temizlenen event sayısı: {len(cleaned_list)}", level="INFO")
    return cleaned_list


def clean_usgs_earthquake_events(usgs_events):
    """
    USGS kaynağından gelen ham deprem event listesini alır,
    bizim sistemin kullandığı formata çevirip temizler.

    Geri dönen her event şu formatta olur:
    {
        "id": int,
        "event_type": "earthquake",
        "timestamp": "ISO-8601 string",
        "magnitude": float,
        "location": str,
        "latitude": float (opsiyonel),
        "longitude": float (opsiyonel),
    }
    """
    cleaned_list = []

    for index, raw in enumerate(usgs_events, start=1):
        # 1) USGS zorunlu alanları var mı?
        missing = [
            field
            for field in USGS_REQUIRED_FIELDS
            if field not in raw or raw[field] in (None, "")
        ]
        if missing:
            log_message(
                f"USGS event'inde eksik alan(lar): {missing}. Event kaydedilmedi: {raw}",
                level="WARNING",
            )
            continue

        # 2) Zamanı ISO string'e çevir
        time_val = raw.get("time")
        if isinstance(time_val, (int, float)):
            # ms cinsinden epoch gelmişse
            ts = datetime.fromtimestamp(time_val / 1000).isoformat()
        elif hasattr(time_val, "isoformat"):
            ts = time_val.isoformat()
        else:
            ts = str(time_val)

        # 3) Magnitude'u float'a çevir
        try:
            magnitude = float(raw.get("magnitude"))
        except (TypeError, ValueError):
            log_message(
                f"USGS event'inde geçersiz magnitude: {raw.get('magnitude')}. Event kaydedilmedi: {raw}",
                level="WARNING",
            )
            continue

        cleaned = {
            "id": index,
            "event_type": str(raw.get("type", "earthquake")).lower(),
            "timestamp": ts,
            "location": str(raw.get("location", "Unknown")),
            "magnitude": magnitude,
        }

        # 4) Opsiyonel: latitude / longitude varsa ekle
        lat = raw.get("latitude")
        lon = raw.get("longitude")

        if lat is not None:
            try:
                cleaned["latitude"] = float(lat)
            except (TypeError, ValueError):
                log_message(
                    f"USGS event'inde geçersiz latitude: {lat}. Koordinat atlandı.",
                    level="WARNING",
                )

        if lon is not None:
            try:
                cleaned["longitude"] = float(lon)
            except (TypeError, ValueError):
                log_message(
                    f"USGS event'inde geçersiz longitude: {lon}. Koordinat atlandı.",
                    level="WARNING",
                )

        cleaned_list.append(cleaned)

    log_message(f"USGS'ten temizlenen event sayısı: {len(cleaned_list)}", level="INFO")
    return cleaned_list