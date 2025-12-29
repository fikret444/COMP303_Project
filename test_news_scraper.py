"""
News Scraper Test
Haber scraping fonksiyonunu test eder.
"""

try:
    from datasources.scraping.scrape_news import scrape_all_risk_headlines
except ImportError as e:
    print(f"Import hatası: {e}")
    print("News scraper modülü bulunamadı veya bağımlılıklar eksik.")
    exit(1)

def main():
    print("=" * 60)
    print("NEWS SCRAPER TESTİ")
    print("=" * 60)
    print("\nHaberler çekiliyor...\n")
    
    try:
        news = scrape_all_risk_headlines()

        print(f"Toplam haber sayısı: {len(news)}")
        print("-" * 60)

        if news:
            for i, item in enumerate(news[:15], 1):
                print(f"{i}. [{item.get('source', 'Unknown')}] {item.get('title', 'No title')}")
                if item.get('url'):
                    print(f"   URL: {item.get('url')}")
                print()
        else:
            print("Hiç haber bulunamadı.")
            
    except Exception as e:
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
