import requests
from datetime import datetime
from datasources.base_source import DataSource


class USGSEarthquakeSource(DataSource):

    URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

    def fetch_raw(self):
        response = requests.get(self.URL, timeout=10)
        return response.json()

    def parse(self, raw):
        events = []

        for item in raw.get("features", []):
            props = item.get("properties", {})
            coords = item.get("geometry", {}).get("coordinates", [])

            if not props or len(coords) < 2:
                continue

            events.append({
                "type": "earthquake",
                "source": "USGS",
                "location": props.get("place"),
                "magnitude": props.get("mag"),
                "time": datetime.fromtimestamp(props["time"] / 1000),
                "latitude": coords[1],
                "longitude": coords[0],
                "depth": coords[2] if len(coords) > 2 else None
            })

        return events
