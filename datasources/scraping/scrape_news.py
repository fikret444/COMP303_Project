import requests
from datetime import datetime
from urllib.parse import urljoin

# Try lxml first, fallback to BeautifulSoup4
try:
    from lxml import html
    USE_LXML = True
except ImportError:
    try:
        from bs4 import BeautifulSoup
        USE_LXML = False
    except ImportError:
        USE_LXML = None
        print("Warning: Neither lxml nor beautifulsoup4 is available. News scraping will not work.")


KEYWORDS = [
    "deprem", "sel", "fırtına", "yangın",
    "heyelan", "çığ", "tsunami",
    "acil", "alarm", "uyarı",
    "sağanak", "kar", "dolu",
    "su kesintisi", "baraj", "taşkın"
]

# categories we WANT (based on URL path)
ALLOWED_PATH_HINTS = [
    "/turkiye", "/gundem", "/son-dakika", "/yerel", "/hava", "/cevre", "/saglik"
]

# categories we DO NOT want (based on URL path, not titles)
BLOCKED_PATH_HINTS = [
    "/spor", "/sporskor", "/magazin", "/yasam", "/kultur", "/sanat", "/astroloji",
    "/ekonomi", "/finans", "/video", "/galeri", "/teknoloji", "/otomobil"
]


def _download(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.text


def _normalize_space(s: str) -> str:
    return " ".join((s or "").split()).strip()


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


def _has_keyword(text: str) -> bool:
    low = (text or "").lower()
    return any(k in low for k in KEYWORDS)


def _blocked_by_path(link: str) -> bool:
    low = (link or "").lower()
    return any(b in low for b in BLOCKED_PATH_HINTS)


def _allowed_by_path(link: str) -> bool:
    low = (link or "").lower()
    return any(a in low for a in ALLOWED_PATH_HINTS)


# -------------------------
# NTV
# -------------------------
def scrape_ntv_candidates():
    base = "https://www.ntv.com.tr"
    html_content = _download(base)
    
    if USE_LXML:
        tree = html.fromstring(html_content)
        anchors = tree.xpath("//a[@href and (.//h2 or .//p)]")
        
        items = []
        for a in anchors:
            href = a.get("href") or ""
            link = urljoin(base, href)
            
            # Prefer h2 title, else p text
            t = a.xpath(".//h2/text()")
            if t:
                title = t[0]
            else:
                p = a.xpath(".//p/text()")
                title = p[0] if p else ""
            
            title = _normalize_space(title)
            if len(title) < 10:
                continue
            
            items.append({"source": "NTV", "title": title, "link": link})
    elif USE_LXML is False:
        # BeautifulSoup4 fallback
        soup = BeautifulSoup(html_content, 'html.parser')
        items = []
        
        # Find all links with h2 or p inside
        for a in soup.find_all('a', href=True):
            h2 = a.find('h2')
            p = a.find('p')
            
            if h2:
                title = _normalize_space(h2.get_text())
            elif p:
                title = _normalize_space(p.get_text())
            else:
                continue
            
            if len(title) < 10:
                continue
            
            link = urljoin(base, a.get('href', ''))
            items.append({"source": "NTV", "title": title, "link": link})
    else:
        return []
    
    # dedupe by link first
    items = _dedupe_by_key(items, key_fn=lambda x: x["link"])
    return items


# -------------------------
# CNN TÜRK (use listing pages)
# -------------------------
CNN_LIST_URLS = [
    "https://www.cnnturk.com/son-dakika-haberleri/",
    "https://www.cnnturk.com/son-dakika-depremler/",
    "https://www.cnnturk.com/turkiye/",
]

def scrape_cnnturk_candidates():
    base = "https://www.cnnturk.com"
    items = []

    for url in CNN_LIST_URLS:
        html_content = _download(url)
        
        if USE_LXML:
            tree = html.fromstring(html_content)
            # Prefer anchor title + href, and avoid header/menu
            anchors = tree.xpath("//a[@href and @title and not(ancestor::header)]")
            
            for a in anchors:
                title = _normalize_space(a.get("title") or "")
                if len(title) < 10:
                    continue
                
                link = urljoin(base, a.get("href") or "")
                items.append({"source": "CNN TURK", "title": title, "link": link})
        elif USE_LXML is False:
            # BeautifulSoup4 fallback
            soup = BeautifulSoup(html_content, 'html.parser')
            # Avoid header links
            header = soup.find('header')
            if header:
                header.decompose()
            
            for a in soup.find_all('a', href=True, title=True):
                title = _normalize_space(a.get('title', ''))
                if len(title) < 10:
                    continue
                
                link = urljoin(base, a.get('href', ''))
                items.append({"source": "CNN TURK", "title": title, "link": link})
        else:
            continue

    items = _dedupe_by_key(items, key_fn=lambda x: x["link"])
    return items


# -------------------------
# Strong filter (no blacklist titles)
# -------------------------
def filter_risk_items(items):
    """
    Keep items that:
    - match risk keywords in title
    - NOT blocked by URL category
    - Prefer allowed categories (if present)
    """
    out = []

    for it in items:
        title = it["title"]
        link = it["link"]

        if not _has_keyword(title):
            continue

        if _blocked_by_path(link):
            continue

        # if site provides category hints, require allowed
        # (NTV/CNN usually does. If it doesn't, we don't force it.)
        if any(h in link.lower() for h in ALLOWED_PATH_HINTS):
            if not _allowed_by_path(link):
                continue

        out.append(it)

    # dedupe by title (in case same news appears twice)
    out = _dedupe_by_key(out, key_fn=lambda x: x["title"])
    return out


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

    # shape events for your API response
    events = []
    for it in filtered[:60]:
        events.append({
            "type": "news_risk",
            "source": it["source"],
            "title": it["title"],
            "time": now,
            "url": it["link"]  # now it's the real article link
        })

    return events


# Optional alias if you used scrape_news() before
def scrape_news():
    return scrape_all_risk_headlines()
