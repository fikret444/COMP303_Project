# processing/wildfire_alerts.py

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from processing.storage import log_message
from processing.wildfire_report import load_wildfire_data  # wildfires.json'u okumak için


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def _safe_parse_time(t: Any) -> Optional[datetime]:
    if not t:
        return None
    if isinstance(t, datetime):
        return t
    if isinstance(t, str):
        try:
            s = t.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            return None
    return None


def build_city_alerts(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    wildfires.json içindeki events listesinden şehir bazlı wildfire riski üretir.
    Eventlerde city alanı bekleniyor (sizde mevcut).
    """
    events: List[Dict[str, Any]] = payload.get("events", []) or []
    if not events:
        return {}

    now = datetime.now()
    recent_window = now - timedelta(days=14)  # wildfire için 14 gün daha mantıklı

    per_city_total: Dict[str, int] = {}
    per_city_recent: Dict[str, int] = {}
    per_city_titles: Dict[str, List[str]] = {}

    for ev in events:
        city = ev.get("city") or ev.get("location") or "Unknown"
        per_city_total[city] = per_city_total.get(city, 0) + 1

        t = _safe_parse_time(ev.get("time"))
        if t and t >= recent_window:
            per_city_recent[city] = per_city_recent.get(city, 0) + 1

        title = (ev.get("title") or "").strip()
        if title:
            per_city_titles.setdefault(city, [])
            if len(per_city_titles[city]) < 5:
                per_city_titles[city].append(title)

    alerts: Dict[str, Dict[str, Any]] = {}

    for city, total_count in per_city_total.items():
        recent_count = per_city_recent.get(city, 0)
        titles = per_city_titles.get(city, [])

        # Basit seviye kuralı:
        # - recent >= 2 veya total >= 5 -> high
        # - recent == 1 veya total 2-4 -> medium
        # - aksi -> low
        if recent_count >= 2 or total_count >= 5:
            level = "high"
            msg = (
                f"{city} için yangın riski YÜKSEK. "
                f"Toplam {total_count} wildfire event; son 14 günde {recent_count} event."
            )
        elif recent_count == 1 or total_count >= 2:
            level = "medium"
            msg = (
                f"{city} için orta seviyede yangın riski var. "
                f"Toplam {total_count} event; son 14 günde {recent_count} event."
            )
        else:
            level = "low"
            msg = (
                f"{city} için düşük seviyede yangın riski görünüyor. "
                f"Toplam {total_count} event; son 14 günde {recent_count} event."
            )

        alerts[city] = {
            "total_events": total_count,
            "recent_events": recent_count,
            "alert_level": level,
            "message": msg,
            "sample_titles": titles,
        }

    return alerts


def print_alerts(alerts: Dict[str, Dict[str, Any]]) -> None:
    if not alerts:
        print("⚠ Wildfire alerts: Şehir bazlı uyarı üretilemedi (boş veri).")
        log_message("Wildfire alerts: Şehir bazlı uyarı üretilemedi (boş veri).", level="WARNING")
        return

    print("\n🔥 Orman Yangını Uyarıları (Şehir Bazlı):")
    log_message("Wildfire alerts: Şehir bazlı wildfire uyarıları oluşturuldu.", level="INFO")

    for city, info in alerts.items():
        level = info["alert_level"]
        msg = info["message"]

        icon = "🟥" if level == "high" else ("🟨" if level == "medium" else "🟩")

        print(f"\n{icon} {city} → [{level.upper()}]")
        print(f"   {msg}")

        titles = info.get("sample_titles", [])
        if titles:
            print("   Örnek başlıklar:")
            for t in titles[:3]:
                print(f"    - {t}")

        log_message(
            f"Wildfire alert for {city} → level={level}, recent={info['recent_events']}, total={info['total_events']}",
            level="INFO",
        )


def main():
    payload = load_wildfire_data("wildfires.json")
    if payload is None:
        return

    alerts = build_city_alerts(payload)
    print_alerts(alerts)


if __name__ == "__main__":
    main()
