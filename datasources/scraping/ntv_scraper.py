import requests
from lxml import html


NTV_URL = "https://www.ntv.com.tr"


KEYWORDS = [
    "deprem", "sel", "fırtına", "yangın",
    "tehlike", "acil", "alarm",
    "yağış", "kar", "hortum",
    "heyelan", "afet"
]


def fetch_ntv_headlines():
    response = requests.get(NTV_URL, timeout=10)
    tree = html.fromstring(response.content)

    # NTV headlines are usually in <a> and <h3>
    headlines = tree.xpath("//h3/text() | //a/text()")

    clean_headlines = []
    for h in headlines:
        h = h.strip()
        if len(h) > 15:
            clean_headlines.append(h)

    return clean_headlines


def filter_danger_news(headlines):
    results = []

    for title in headlines:
        for keyword in KEYWORDS:
            if keyword in title.lower():
                results.append(title)
                break

    return results


if __name__ == "__main__":
    all_news = fetch_ntv_headlines()
    danger_news = filter_danger_news(all_news)

    print("NTV - Riskli Haberler:")
    for news in danger_news:
        print("-", news)
