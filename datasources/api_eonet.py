from datasources.eonet_source import EONETSource


def get_eonet_events(status="open", days=30, limit=50, category_ids=None, bbox=None):
    src = EONETSource(
        status=status,
        days=days,
        limit=limit,
        category_ids=category_ids,
        bbox=bbox
    )
    return src.fetch_and_parse()
if __name__ == "__main__":
    turkey_bbox = [25.0,42.5,45.0,35.5]

    events = get_eonet_events(
        status="open",
        days=30,
        limit=30,
        category_ids=["wildfires", "floods", "severeStorms"],
        bbox=turkey_bbox
    )

    for e in events[:10]:
        print(e)
    as_dict = [e.toDictionary() for e in events[:5]]
    print(as_dict)

