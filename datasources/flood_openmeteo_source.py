# datasources/flood_openmeteo_source.py

import requests
from datetime import datetime
from typing import List, Optional

from datasources.base_source import DataSource, DataSourceError, Event


class OpenMeteoFloodSource(DataSource):
    """
    Open-Meteo Global Flood API üzerinden, belirli bir koordinat için
    nehir debisi (river_discharge) verisi alır ve basit bir 'flood_risk'
    event listesi üretir.

    ⚠ Bu model GERÇEK sel tahmini değildir; proje kapsamında, debi
    değerine göre basit bir risk sınıflaması yapıyoruz.
    """

    BASE_URL = "https://flood-api.open-meteo.com/v1/flood"

    def __init__(
        self,
        latitude: float,
        longitude: float,
        past_days: int = 3,
        forecast_days: int = 7,
        location_name: Optional[str] = None,
    ):
        """
        latitude, longitude : Koordinatlar
        past_days          : Kaç gün geriye dönük veri
        forecast_days      : Kaç gün ileriye dönük tahmin
        location_name      : (Opsiyonel) İnsan okuyabilir lokasyon adı, örn. "New York"
        """
        self.latitude = latitude
        self.longitude = longitude
        self.past_days = past_days
        self.forecast_days = forecast_days
        self.location_name = location_name

    def fetch_raw(self):
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "river_discharge",
            "past_days": self.past_days,
            "forecast_days": self.forecast_days,
            "timezone": "auto",
        }

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DataSourceError(f"Open-Meteo Flood fetch failed: {e}")

    def parse(self, raw) -> List[Event]:
        """
        Open-Meteo flood çıktısını sadeleştirip şu formata çeviriyoruz:

        {
            "type": "flood_risk",
            "source": "Open-Meteo Flood",
            "time": datetime,
            "location": "New York" veya "41.0,-74.0",
            "latitude": ...,
            "longitude": ...,
            "river_discharge": float,
            "risk_level": "low" | "medium" | "high"
        }
        """

        daily = raw.get("daily", {})
        times = daily.get("time", [])
        discharges = daily.get("river_discharge", [])

        events: List[Event] = []

        # İnsan okuyabilir lokasyon ismi, yoksa "lat,lon" stringi
        location_str = (
            self.location_name
            if self.location_name
            else f"{self.latitude:.3f},{self.longitude:.3f}"
        )

        for t_str, discharge in zip(times, discharges):
            # Tarihi datetime'a çevir
            try:
                t = datetime.fromisoformat(t_str)
            except Exception:
                t = None

            # Basit, projelik risk sınıflaması (gerçek tahmin DEĞİL):
            # 0–500 m³/s   -> low
            # 500–2000     -> medium
            # 2000+        -> high
            if discharge is None:
                risk = "unknown"
            elif discharge < 200:
                risk = "low"
            elif discharge < 800:
                risk = "medium"
            else:
                risk = "high"

            events.append({
                "type": "flood_risk",
                "source": "Open-Meteo Flood",
                "time": t,
                "location": location_str,
                "latitude": raw.get("latitude"),
                "longitude": raw.get("longitude"),
                "river_discharge": discharge,
                "risk_level": risk,
            })

        return events


# Bu dosyayı tek başına test etmek için:
if __name__ == "__main__":
    # Örnek: New York civarı
    src = OpenMeteoFloodSource(
        latitude=40.7128,
        longitude=-74.0060,
        location_name="New York",
    )
    raw = src.fetch_raw()
    events = src.parse(raw)
    print(f"{len(events)} flood_risk event üretildi (New York).")
    for ev in events[:5]:
        print(ev)


