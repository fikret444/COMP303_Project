from scrape_news import scrape_all_risk_headlines

def main():
    news = scrape_all_risk_headlines()

    print("Total headlines:", len(news))
    print("-" * 40)

    for item in news[:15]:
        print(f"[{item['source']}] {item['title']}")

if __name__ == "__main__":
    main()
