import requests
from datetime import datetime
from typing import List, Optional

from datasources.base_source import DataSource, DataSourceError, Event

class OpenMeteoFloodSource(DataSource):

    API_ENDPOINT = "https://flood-api.open-meteo.com/v1/flood"

    def __init__(
        self,
        latitude: float,
        longitude: float,
        past_days: int = 3,
        forecast_days: int = 7,
        location_name: Optional[str] = None,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.past_days = past_days
        self.forecast_days = forecast_days
        self.location_name = location_name

    def fetch_raw(self):
        query_params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "river_discharge",
            "past_days": self.past_days,
            "forecast_days": self.forecast_days,
            "timezone": "auto",
        }

        try:
            response = requests.get(self.API_ENDPOINT, params=query_params, timeout=12)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise DataSourceError(f"Network error during Open-Meteo flood fetch: {error}")
        except Exception as general_error:
            raise DataSourceError(f"Unexpected error in flood source: {general_error}")

    def parse(self, raw) -> List[Event]:
        daily_stats = raw.get("daily", {})
        time_series = daily_stats.get("time", [])
        discharge_values = daily_stats.get("river_discharge", [])

        flood_events: List[Event] = []

        if self.location_name:
            label = self.location_name
        else:
            label = f"{self.latitude},{self.longitude}"

        for iso_date, flow_rate in zip(time_series, discharge_values):
            try:
                event_date = datetime.fromisoformat(iso_date)
            except (ValueError, TypeError):
                event_date = None

            if flow_rate is None:
                current_risk = "unknown"
            elif flow_rate < 200:
                current_risk = "low"
            elif flow_rate < 800:
                current_risk = "medium"
            else:
                current_risk = "high"

            flood_events.append({
                "type": "flood_risk",
                "source": "Open-Meteo Flood",
                "time": event_date,
                "location": label,
                "latitude": raw.get("latitude"),
                "longitude": raw.get("longitude"),
                "river_discharge": flow_rate,
                "risk_level": current_risk,
            })

        return flood_events

if __name__ == "__main__":
    test_source = OpenMeteoFloodSource(
        latitude=40.71,
        longitude=-74.00,
        location_name="New York Test"
    )
    try:
        data = test_source.fetch_raw()
        results = test_source.parse(data)
        print(f"Success: {len(results)} events generated.")
        for item in results[:3]:
            print(f"[{item['time']}] Discharge: {item['river_discharge']} - Risk: {item['risk_level']}")
    except DataSourceError as ds_err:
        print(f"Test failed: {ds_err}")