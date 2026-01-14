# processing/flood_regional_analysis.py

from __future__ import annotations
import json
from pathlib import Path
from processing.storage import log_message

project_path = Path(__file__).resolve().parent.parent
veri_klasoru = project_path / "data"

def load_flood_data(filename: str = "flood_risk.json"):
    file_path = veri_klasoru / filename

    if not file_path.exists():
        msg = f"Flood Analysis: {filename} dosyası sistemde bulunamadı."
        log_message(msg, level="WARNING")
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        msg = f"Flood Analysis: Veri okuma sırasında bir problem oluştu: {e}"
        log_message(msg, level="ERROR")
        return None

def print_sample_events(label: str, ev_list: list, max_count: int = 5):
    if not ev_list:
        print(f"\n[-] {label} kategorisinde kayıtlı veri yok.")
        return

    print(f"\n>>> {label} Flood Event Örnekleri:")
    for ev in ev_list[:max_count]:
        city = ev.get("location", "Unknown")
        time_info = ev.get("time", "unknown time")
        discharge = ev.get("river_discharge", "N/A")
        risk = ev.get("risk_level", "unknown")
        print(f"   * {time_info} | {city} | debi: {discharge} m3/s | risk: {risk}")

def main():
    payload = load_flood_data("flood_risk.json")
    if not payload:
        return

    events = payload.get("events", [])
    generated_at = payload.get("generated_at", "bilinmiyor")

    categorized_events = {
        "high": [],
        "medium": [],
        "low": [],
        "unknown": []
    }

    per_city = {}

    for ev in events:
        risk = ev.get("risk_level", "unknown").lower()
        city = ev.get("location", "Unknown")

        if risk in categorized_events:
            categorized_events[risk].append(ev)
        else:
            categorized_events["unknown"].append(ev)

        if city not in per_city:
            per_city[city] = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
        
        if risk in per_city[city]:
            per_city[city][risk] += 1
        else:
            per_city[city]["unknown"] += 1

    print("-" * 40)
    print(" SEL BÖLGESEL ANALİZ RAPORU (ABD & Kanada)")
    print(f"Veri Tarihi : {generated_at}")
    print(f"Toplam Kayıt: {len(events)}")
    print("-" * 40)

    print(f"Kritik (High) Risk : {len(categorized_events['high'])}")
    print(f"Orta (Medium) Risk  : {len(categorized_events['medium'])}")
    print(f"Düşük (Low) Risk    : {len(categorized_events['low'])}")

    print("\n ŞEHİR BAZLI ÖZET:")
    for city, stats in per_city.items():
        print(f"   • {city:15} | H:{stats['high']} | M:{stats['medium']} | L:{stats['low']}")

    print_sample_events("YÜKSEK RİSK", categorized_events['high'])
    print_sample_events("ORTA RİSK", categorized_events['medium'])
    print_sample_events("DÜŞÜK RİSK", categorized_events['low'])

    log_message(
        f"Sel analizi raporu başarıyla üretildi. Toplam {len(events)} olay incelendi.",
        level="INFO"
    )

if __name__ == "__main__":
    main()