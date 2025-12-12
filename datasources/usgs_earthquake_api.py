import requests
from datetime import datetime
from datasources.base_source import DataSource

class USGSEarthquakeSource(DataSource):
    URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

    def fetch_events(self):
        response = requests.get(self.URL)
        data = response.json()

        events = []

        for item in data["features"]:
            props = item["properties"]
            coords = item["geometry"]["coordinates"]

            event = {
                "type": "earthquake",
                "source": "USGS",
                "location": props["place"],
                "magnitude": props["mag"],
                "time": datetime.fromtimestamp(props["time"] / 1000),
                "latitude": coords[1],
                "longitude": coords[0],
            }

            events.append(event)

        return events
