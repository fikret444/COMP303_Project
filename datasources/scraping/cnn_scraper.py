import requests
from lxml import html


CNN_URL = "https://www.cnnturk.com"


KEYWORDS = [
    "deprem", "sel", "fırtına", "yangın",
    "tehlike", "acil", "alarm",
    "yağış", "kar", "hortum",
    "heyelan", "afet"
]


def fetch_cnn_headlines():
    response = requests.get(CNN_URL, timeout=10)
    tree = html.fromstring(response.content)
    headlines = tree.xpath("//a/text()")

    clean_headlines = []
    for h in headlines:
        h = h.strip()
        if len(h) > 15:
            clean_headlines.append(h)

    return clean_headlines


def filter_danger_news(headlines):
    results = []

    for title in headlines:
        title_lower = title.lower()
        for keyword in KEYWORDS:
            if keyword in title_lower:
                results.append(title)
                break

    return results


if __name__ == "__main__":
    all_news = fetch_cnn_headlines()
    danger_news = filter_danger_news(all_news)

    print("CNN TÜRK - Riskli Haberler:")
    for news in danger_news:
        print("-", news)
