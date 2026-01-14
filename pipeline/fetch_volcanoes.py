from datetime import datetime
from datasources.eonet_volcano_source import EONETVolcanoSource
from processing.storage import save_events_to_json, log_message

def fetch_volcano_events(days=365, status="all"):
    api_source = EONETVolcanoSource(days=days, status=status)
    
    raw_data = api_source.fetch_raw()
    parsed_events = api_source.parse(raw_data)
    
    return parsed_events

def summarize_volcano_events(events):
    count = len(events)
    print(f"\n[!] Toplam {count} yanardağ aktivitesi tespit edildi.")

    valid_events = []
    for ev in events:
        if ev.get("time") and isinstance(ev["time"], datetime):
            valid_events.append(ev)

    def get_time(item):
        return item["time"]

    valid_events.sort(key=get_time, reverse=True)

    print("-" * 35)
    print(" SON VOLKANİK AKTİVİTELER ".center(35, "="))
    print("-" * 35)

    for entry in valid_events[:5]:
        dt = entry["time"]
        name = entry.get("title", "Bilinmeyen Bölge")
        coords = (entry.get("latitude"), entry.get("longitude"))

        friendly_time = dt.strftime("%Y-%m-%d | %H:%M:%S")

        print(f" * {friendly_time} -> {name} {coords}")
    print("-" * 35)

def main():
    log_message("Volcano data fetch sequence started.")
    
    try:
        volcano_list = fetch_volcano_events(days=365)
    except Exception as err:
        print(f"[ERROR] Veri çekme başarısız: {err}")
        log_message(f"Volcano fetch failed: {err}", level="ERROR")
        return

    if not volcano_list:
        print("[-] Gösterilebilecek yanardağ olayı bulunamadı.")
        return

    summarize_volcano_events(volcano_list)

    target_name = "volcanoes.json"
    save_events_to_json(volcano_list, filename=target_name)

    msg = f"Successfully saved {len(volcano_list)} volcano events to {target_name}"
    log_message(msg, level="INFO")
    print(f"\n[OK] Veriler data/{target_name} klasörüne aktarıldı.")

if __name__ == "__main__":
    main()