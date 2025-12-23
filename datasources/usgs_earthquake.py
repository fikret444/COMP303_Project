import requests
from datetime import datetime
from datasources.base_source import DataSource, DataSourceError
from models import RawEarthquake


class USGSEarthquakeSource(DataSource):
    URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

    def fetch_raw(self):
        try:
            r = requests.get(self.URL, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DataSourceError(f"USGS fetch failed: {e}")

    def parse(self, raw):
        events = []
        for item in raw.get("features", []):
            props = item.get("properties", {})
            coords = item.get("geometry", {}).get("coordinates", [None, None])

            # Create RawEarthquake object instead of dictionary
            raw_eq = RawEarthquake(
                type="earthquake",
                source="USGS",
                location=props.get("place"),
                magnitude=props.get("mag"),
                time=datetime.fromtimestamp((props.get("time", 0) / 1000)),
                latitude=coords[1],
                longitude=coords[0]
            )
            
            events.append(raw_eq)

        return events
