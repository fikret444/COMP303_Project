from datasources.usgs_earthquake import USGSEarthquakeSource

# Whole Americas bounding box (minLon, minLat, maxLon, maxLat)
AMERICA_BBOX = [-170.0, -56.0, -34.0, 72.0]


def get_earthquakes(bbox=None):
    if bbox is None:
        bbox = AMERICA_BBOX

    src = USGSEarthquakeSource(bbox=bbox)
    return src.fetch_and_parse()


if __name__ == "__main__":
    quakes = get_earthquakes()

    print("First 10 earthquakes:")
    for q in quakes[:10]:
        print(q)

    try:
        as_dict = [q.toDictionary() for q in quakes[:5]]
        print(as_dict)
    except Exception:
        print(quakes[:5])
