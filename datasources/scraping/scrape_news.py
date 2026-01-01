import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin


KEYWORDS = [
    "deprem", "sel", "fırtına", "yangın",
    "heyelan", "çığ", "tsunami",
    "acil", "alarm", "uyarı",
    "sağanak", "kar", "dolu",
    "su kesintisi", "baraj", "taşkın"
]

BLOCKED_PATH_HINTS = [
    "/spor", "/magazin", "/yasam", "/kultur", "/sanat",
    "/ekonomi", "/finans", "/video", "/galeri", "/teknoloji", "/otomobil"
]


def download(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.text


def has_keyword(title):
    title = (title or "").lower()
    return any(k in title for k in KEYWORDS)


def blocked(link):
    link = (link or "").lower()
    return any(b in link for b in BLOCKED_PATH_HINTS)


def dedupe_by_url(items):
    seen = set()
    out = []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        out.append(it)
    return out


def scrape_ntv():
    base = "https://www.ntv.com.tr"
    html = download(base)
    soup = BeautifulSoup(html, "html.parser")

    items = []
    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        if len(title) < 10:
            continue

        link = urljoin(base, a["href"])
        items.append({"source": "NTV", "title": title, "url": link})

    return items


def scrape_cnnturk():
    base = "https://www.cnnturk.com"
    pages = [
        "https://www.cnnturk.com/son-dakika-haberleri/",
        "https://www.cnnturk.com/son-dakika-depremler/",
        "https://www.cnnturk.com/turkiye/",
    ]

    items = []
    for page in pages:
        html = download(page)
        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            # CNN Turk sometimes keeps titles in "title" attribute
            title = a.get("title") or a.get_text(" ", strip=True)
            if len(title) < 10:
                continue

            link = urljoin(base, a["href"])
            items.append({"source": "CNN TURK", "title": title.strip(), "url": link})

    return items


def scrape_all_risk_headlines():
    now = datetime.now().isoformat(timespec="seconds")

    try:
        merged = scrape_ntv() + scrape_cnnturk()
    except Exception:
        merged = []

    # filter: keyword + not blocked
    filtered = []
    for it in merged:
        if has_keyword(it["title"]) and not blocked(it["url"]):
            filtered.append(it)

    filtered = dedupe_by_url(filtered)

    events = []
    for it in filtered[:60]:
        events.append({
            "type": "news_risk",
            "source": it["source"],
            "title": it["title"],
            "time": now,
            "url": it["url"]
        })

    return events


# alias (your app uses scrape_all_risk_headlines, but this helps if you call scrape_news)
def scrape_news():
    return scrape_all_risk_headlines()
