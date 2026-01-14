from datetime import datetime
from .storage import log_message
from models import RawEarthquake, CleanedEarthquake

# Genel veri için alınacak zorunlu alanlar
ZORUNLU_ALANLAR = ["id", "event_type", "timestamp", "magnitude", "location"]

# USGS den alacağımız zorunlu alanlar
USGS_ZORUNLU_ALANLAR = ["type", "time", "magnitude", "location"]

def clean_earthquake_event(raw_event: dict):
    try:
        cleaned = {
            "id": raw_event["id"],
            "event_type": str(raw_event.get("event_type", "earthquake")).lower(),
            "timestamp": str(raw_event["timestamp"]),
            "location": str(raw_event["location"]),
            "magnitude": float(raw_event["magnitude"])
        }
    except (KeyError, ValueError, TypeError) as e:
        log_message(f"Data mapping error: {e}", level="WARNING")
        return None

    for coord in ["latitude", "longitude"]:
        value = raw_event.get(coord)
        if value is not None:
            try:
                cleaned[coord] = float(value)
            except:
                pass 

    return cleaned

def clean_earthquake_events(raw_events):
    cleaned_list = []

    for ev in raw_events:
        if hasattr(ev, 'toDictionary'):
            data_source = ev.toDictionary()
        else:
            data_source = ev

        processed_dict = clean_earthquake_event(data_source)
        
        if processed_dict:
            new_event = CleanedEarthquake(**processed_dict)
            cleaned_list.append(new_event)

    log_message(f"Processing complete. Cleaned: {len(cleaned_list)}", level="INFO")
    return cleaned_list

def clean_usgs_earthquake_events(usgs_events):
    final_output = []
    counter = 0

    for raw in usgs_events:
        counter += 1
        
        if isinstance(raw, RawEarthquake):
            raw_dict = raw.toDictionary()
            time_val = raw.time
        else:
            raw_dict = raw
            time_val = raw.get("time")

            missing_fields = []
            for field in USGS_ZORUNLU_ALANLAR:
                if field not in raw_dict or not raw_dict[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                log_message(f"Missing USGS fields: {missing_fields}", level="WARNING")
                continue

        # Tarih formatını ISO yapmıştık ama bunu da strftime çeviriyoruz
        try:
            if isinstance(time_val, (int, float)):
                ts = datetime.fromtimestamp(time_val / 1000).strftime('%Y-%m-%d %H:%M:%S')
            elif hasattr(time_val, "strftime"):
                ts = time_val.strftime('%Y-%m-%d %H:%M:%S')
            else:
                ts = str(time_val)
        except:
            ts = "Unknown"

        try:
            magnitude = float(raw_dict.get("magnitude", 0))
            location = str(raw_dict.get("location", "Unknown"))
            
            cleaned_eq = CleanedEarthquake(
                id=counter,
                event_type="earthquake",
                timestamp=ts,
                location=location,
                magnitude=magnitude,
                latitude=raw_dict.get("latitude"),
                longitude=raw_dict.get("longitude")
            )
            final_output.append(cleaned_eq)
        except Exception as e:
            log_message(f"Conversion error in USGS: {e}", level="WARNING")
            continue

    log_message(f"USGS conversion finished. Records: {len(final_output)}", level="INFO")
    return final_output