import requests
from datetime import datetime
from datasources.base_source import DataSource, DataSourceError
from models import RawEarthquake


class USGSEarthquakeSource(DataSource):
    URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

    def __init__(self, bbox=None):
        self.bbox = bbox  # [minLon, minLat, maxLon, maxLat]

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
            
            lat = coords[1]
            lon = coords[0]

            if self.bbox and len(self.bbox) == 4:
                min_lon, min_lat, max_lon, max_lat = self.bbox
                if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
                    continue
                if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
                    continue

            raw_eq = RawEarthquake(
                type="earthquake",
                source="USGS",
                location=props.get("place"),
                magnitude=props.get("mag"),
                time=datetime.fromtimestamp((props.get("time", 0) / 1000)),
                latitude=lat,
                longitude=lon
            )
            
            events.append(raw_eq)

        return events
