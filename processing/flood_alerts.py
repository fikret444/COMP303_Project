# processing/flood_alerts.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from processing.storage import log_message
from processing.flood_report import load_flood_data  # flood_risk.json'u okumak için


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def build_city_alerts(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    flood_risk.json içindeki events ve high_risk_events içinden
    şehir bazlı kısa uyarı / özet üretir.

    Dönen yapı:
    {
      "New Orleans": {
         "total_events": 10,
         "high_risk_days": 10,
         "alert_level": "high",
         "message": "New Orleans için sel riski kritik seviyede. 10 günde 10 high risk günü var."
      },
      ...
    }
    """
    events: List[Dict[str, Any]] = payload.get("events", [])
    high_events: List[Dict[str, Any]] = payload.get("high_risk_events", [])

    # Şehir bazlı toplam event sayısı
    per_city_total: Dict[str, int] = {}
    for ev in events:
        city = ev.get("location", "Unknown")
        per_city_total[city] = per_city_total.get(city, 0) + 1

    # Şehir bazlı high risk event sayısı
    per_city_high: Dict[str, int] = {}
    for ev in high_events:
        city = ev.get("location", "Unknown")
        per_city_high[city] = per_city_high.get(city, 0) + 1

    alerts: Dict[str, Dict[str, Any]] = {}

    for city, total_count in per_city_total.items():
        high_count = per_city_high.get(city, 0)

        # Basit uyarı seviyesi kuralı:
        # 0 high gün      -> low
        # 1-3 high gün    -> medium
        # 4+ high gün     -> high
        if high_count == 0:
            level = "low"
            msg = (
                f"{city} için şu anda model düşük sel riski gösteriyor. "
                f"Toplam {total_count} günde high risk gün bulunmuyor."
            )
        elif high_count <= 3:
            level = "medium"
            msg = (
                f"{city} için orta seviyede sel riski mevcut. "
                f"{total_count} gün içinde {high_count} gün high risk görünmekte."
            )
        else:
            level = "high"
            msg = (
                f"{city} için sel riski YÜKSEK. "
                f"{total_count} gün içinde {high_count} gün high risk olarak işaretlenmiş."
            )

        alerts[city] = {
            "total_events": total_count,
            "high_risk_days": high_count,
            "alert_level": level,
            "message": msg,
        }

    return alerts


def print_alerts(alerts: Dict[str, Dict[str, Any]]) -> None:
    """
    Üretilen uyarıları terminale yazdırır ve app.log'a özet geçer.
    """
    if not alerts:
        print("⚠ Flood alerts: Şehir bazlı uyarı üretilemedi (boş veri).")
        log_message("Flood alerts: Şehir bazlı uyarı üretilemedi (boş veri).", level="WARNING")
        return

    print("\n🚨 Sel / Su Taşkını Uyarıları (Şehir Bazlı):")
    log_message("Flood alerts: Şehir bazlı sel uyarıları oluşturuldu.", level="INFO")

    for city, info in alerts.items():
        level = info["alert_level"]
        msg = info["message"]

        # Seviyeye göre küçük bir ikon
        if level == "high":
            icon = "🟥"
        elif level == "medium":
            icon = "🟨"
        else:
            icon = "🟩"

        print(f"\n{icon} {city} → [{level.upper()}]")
        print(f"   {msg}")

        log_message(
            f"Flood alert for {city} → level={level}, "
            f"high_days={info['high_risk_days']}, total={info['total_events']}",
            level="INFO",
        )


def main():
    # flood_risk.json'u flood_report'taki loader ile okuyalım
    payload = load_flood_data("flood_risk.json")
    if payload is None:
        return

    alerts = build_city_alerts(payload)
    print_alerts(alerts)


if __name__ == "__main__":
    main()