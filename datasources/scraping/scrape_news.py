import requests
from datetime import datetime
from urllib.parse import urljoin

try:
    from lxml import html
    PARSER = "lxml"
except ImportError:
    try:
        from bs4 import BeautifulSoup
        PARSER = "bs4"
    except ImportError:
        PARSER = None


KEYWORDS = [
    "deprem", "sel", "fırtına", "yangın", "heyelan", "çığ", "tsunami",
    "acil", "alarm", "uyarı", "sağanak", "kar", "dolu",
    "su kesintisi", "baraj", "taşkın"
]

ALLOWED_PATH_HINTS = ["/turkiye", "/gundem", "/son-dakika", "/yerel", "/hava", "/cevre", "/saglik"]
BLOCKED_PATH_HINTS = ["/spor", "/sporskor", "/magazin", "/yasam", "/kultur", "/sanat", "/astroloji",
                      "/ekonomi", "/finans", "/video", "/galeri", "/teknoloji", "/otomobil"]


def _download(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    return r.text


def _clean(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _has_keyword(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in KEYWORDS)


def _allowed(link: str) -> bool:
    low = (link or "").lower()
    if any(b in low for b in BLOCKED_PATH_HINTS):
        return False
    if any(a in low for a in ALLOWED_PATH_HINTS):
        return True
    return True


def _dedupe(items, key):
    seen, out = set(), []
    for it in items:
        k = it.get(key)
        if k and k not in seen:
            seen.add(k)
            out.append(it)
    return out


def _extract_candidates(base_url: str, page_url: str, source_name: str):
    if PARSER is None:
        return []

    html_text = _download(page_url)
    items = []

    if PARSER == "lxml":
        tree = html.fromstring(html_text)

        anchors = tree.xpath("//a[@href]")
        for a in anchors:
            href = a.get("href") or ""
            link = urljoin(base_url, href)

            title = a.get("title") or ""
            if not title:
                t = a.xpath(".//h2/text()") or a.xpath(".//p/text()")
                title = t[0] if t else ""

            title = _clean(title)
            if len(title) >= 10:
                items.append({"source": source_name, "title": title, "link": link})

    else:
        soup = BeautifulSoup(html_text, "html.parser")
        for a in soup.find_all("a", href=True):
            link = urljoin(base_url, a.get("href", ""))

            title = a.get("title", "")
            if not title:
                h2 = a.find("h2")
                p = a.find("p")
                title = h2.get_text() if h2 else (p.get_text() if p else "")

            title = _clean(title)
            if len(title) >= 10:
                items.append({"source": source_name, "title": title, "link": link})

    return _dedupe(items, "link")


def scrape_ntv_candidates():
    return _extract_candidates("https://www.ntv.com.tr", "https://www.ntv.com.tr", "NTV")


CNN_LIST_URLS = [
    "https://www.cnnturk.com/son-dakika-haberleri/",
    "https://www.cnnturk.com/son-dakika-depremler/",
    "https://www.cnnturk.com/turkiye/",
]


def scrape_cnnturk_candidates():
    items = []
    for url in CNN_LIST_URLS:
        items.extend(_extract_candidates("https://www.cnnturk.com", url, "CNN TURK"))
    return _dedupe(items, "link")


def filter_risk_items(items):
    out = []
    for it in items:
        title, link = it["title"], it["link"]
        if _has_keyword(title) and _allowed(link):
            out.append(it)
    return _dedupe(out, "title")


def scrape_all_risk_headlines():
    now = datetime.now().isoformat(timespec="seconds")
    merged = []

    try:
        merged.extend(scrape_ntv_candidates())
    except Exception as e:
        merged.append({"source": "NTV", "title": f"(NTV scrape failed: {e})", "link": "https://www.ntv.com.tr"})

    try:
        merged.extend(scrape_cnnturk_candidates())
    except Exception as e:
        merged.append({"source": "CNN TURK", "title": f"(CNN scrape failed: {e})", "link": "https://www.cnnturk.com"})

    filtered = filter_risk_items(merged)

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


def scrape_news():
    return scrape_all_risk_headlines()
