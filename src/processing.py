from .storage import log_message

# Deprem event'i için zorunlu alanlar
REQUIRED_FIELDS = ["id", "event_type", "timestamp", "magnitude", "location"]

def clean_earthquake_event(raw_event):
    """
    Tek bir ham deprem event'ini temizler.
    Eksik veya hatalı veri varsa None döndürür.
    """

    # 1) Zorunlu alanlar var mı?
    for field in REQUIRED_FIELDS:
        if field not in raw_event:
            log_message(
                f"Eksik alan: {field}. Event kaydedilmedi: {raw_event}",
                level="WARNING"
            )
            return None

    # 2) Yeni bir dict oluştur (fazla alanları almıyoruz)
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
            level="WARNING"
        )
        return None

    return cleaned


def clean_earthquake_events(raw_events):
    """
    Birden çok ham event'i alır, temizleyip
    sadece başarılı olanları liste olarak döndürür.
    """
    cleaned_list = []

    for ev in raw_events:
        cleaned = clean_earthquake_event(ev)
        if cleaned is not None:
            cleaned_list.append(cleaned)

    log_message(f"Temizlenen event sayısı: {len(cleaned_list)}", level="INFO")
    return cleaned_list