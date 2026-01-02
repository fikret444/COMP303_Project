from datasources.eonet_source import EONETSource


# Whole Americas bounding box: [minLon, minLat, maxLon, maxLat]
AMERICA_BBOX = [-170.0, -56.0, -34.0, 72.0]


def get_eonet_events(status="open", days=30, limit=50, category_ids=None, bbox=None):
    if bbox is None:
        bbox = AMERICA_BBOX

    src = EONETSource(
        status=status,
        days=days,
        limit=limit,
        category_ids=category_ids,
        bbox=bbox
    )
    return src.fetch_and_parse()


if __name__ == "__main__":
    events = get_eonet_events(
        status="open",
        days=30,
        limit=30,
        category_ids=["wildfires", "floods", "severeStorms"],
        bbox=AMERICA_BBOX
    )

    for e in events[:10]:
        print(e)

    try:
        as_dict = [e.toDictionary() for e in events[:5]]
        print(as_dict)
    except Exception:
        print(events[:5])
