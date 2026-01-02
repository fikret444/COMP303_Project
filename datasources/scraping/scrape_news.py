# datasources/scraping/scrape_news.py
import requests
from datetime import datetime
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# US-only keywords (English)
# ------------------------------------------------------------
KEYWORDS = [
    "earthquake", "aftershock", "seismic", "tremor",
    "flood", "flash flood", "river flood", "inundation",
    "storm", "severe storm", "hurricane", "tropical storm", "tornado",
    "wildfire", "brush fire", "forest fire", "evacuation",
    "volcano", "eruption", "ash", "lava",
    "warning", "watch", "alert", "emergency", "advisory",
]


# ------------------------------------------------------------
# US-based RSS feeds (official / stable)
# ------------------------------------------------------------
FEEDS = [
    # FEMA: Disaster / emergency updates (US)
    ("FEMA", "https://www.fema.gov/feeds/disasters.rss"),

    # USGS: Latest earthquakes (global feed but USGS is US-based; we keyword-filter)
    ("USGS", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.atom"),

    # NHC: Hurricanes / tropical storms (US)
    ("NOAA NHC", "https://www.nhc.noaa.gov/index-at.xml"),

    # NWS: Weather stories (US)
    ("NWS", "https://www.weather.gov/rss_page.php?site_name=nws"),
]


def _download(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text


def _normalize_space(s: str) -> str:
    return " ".join((s or "").split()).strip()


def _has_keyword(text: str) -> bool:
    low = (text or "").lower()
    return any(k in low for k in KEYWORDS)


def _dedupe_by_key(items, key_fn):
    seen = set()
    out = []
    for it in items:
        k = key_fn(it)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def _parse_rss_or_atom(xml_text: str, source_name: str):
    """
    Parses RSS or Atom feeds into:
    {"source":..., "title":..., "link":...}
    """
    items = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return items

    tag = root.tag.lower()

    # ---- Atom ----
    if "feed" in tag:
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
        for entry in root.findall(f"{ns}entry"):
            title_el = entry.find(f"{ns}title")
            link_el = entry.find(f"{ns}link")
            title = _normalize_space(title_el.text if title_el is not None else "")
            link = ""
            if link_el is not None:
                link = link_el.attrib.get("href", "") or ""
            if title and link:
                items.append({"source": source_name, "title": title, "link": link})
        return items

    # ---- RSS ----
    channel = root.find("channel")
    if channel is None:
        # sometimes RSS has namespaces; quick fallback:
        for child in root:
            if child.tag.lower().endswith("channel"):
                channel = child
                break

    if channel is None:
        return items

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")

        title = _normalize_space(title_el.text if title_el is not None else "")
        link = _normalize_space(link_el.text if link_el is not None else "")

        if title and link:
            items.append({"source": source_name, "title": title, "link": link})

    return items


def filter_risk_items(items):
    """
    Keep items that match risk keywords in title (US-only feeds already)
    """
    out = []
    for it in items:
        title = it.get("title", "")
        if not title or not _has_keyword(title):
            continue
        out.append(it)

    out = _dedupe_by_key(out, key_fn=lambda x: x["link"])
    out = _dedupe_by_key(out, key_fn=lambda x: x["title"])
    return out


def scrape_all_risk_headlines():
    now = datetime.now().isoformat(timespec="seconds")
    merged = []

    for source, url in FEEDS:
        try:
            xml_text = _download(url)
            merged.extend(_parse_rss_or_atom(xml_text, source))
        except Exception as e:
            merged.append({
                "source": source,
                "title": f"({source} feed failed: {e})",
                "link": url
            })

    filtered = filter_risk_items(merged)

    # shape events for your API response
    events = []
    for it in filtered[:60]:
        events.append({
            "type": "news_risk",
            "source": it["source"],
            "title": it["title"],
            "time": now,
            "url": it["link"]
        })

    return events


# Optional alias if you used scrape_news() before
def scrape_news():
    return scrape_all_risk_headlines()


if __name__ == "__main__":
    # quick local test
    data = scrape_all_risk_headlines()
    print(f"Fetched {len(data)} US risk headlines.")
    for x in data[:10]:
        print("-", x["source"], ":", x["title"])
