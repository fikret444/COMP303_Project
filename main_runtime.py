"""
SDEWS Main Runtime Entry Point
Smart Disaster Early Warning System

Tüm ekip üyelerinin çalışmalarını entegre eden ana sistem.

Team Integration:
- Hakan Demircan: API & Web Scraping (datasources/)
- Erdem Kaya: Core Data Models (models/)
- Yağız Efe Hüşan: Data Processing & Storage (processing/)
- Fikret Ahıskalı: Concurrency & Runtime Pipeline (pipeline/)

Author: Fikret Ahıskalı
Date: December 2025
"""

import sys
from datasources.usgs_earthquake import USGSEarthquakeSource
from datasources.openweather_source import OpenWeatherSource
from pipeline import RuntimeSystem
from processing import log_message


def print_banner():
    """SDEWS banner'ini yazdir."""
    banner = """
    ============================================================
    
          Smart Disaster Early Warning System (SDEWS)
    
      Concurrent Data Processing & Real-time Event Pipeline
    
    ============================================================
    
    Ekip Uyeleri:
    - Hakan Demircan: API Integration & Web Scraping
    - Erdem Kaya: Core System & Data Models
    - Fikret Ahiskali: Concurrency & Runtime Pipeline
    - Yagiz Efe Husan: Data Processing, Storage & Analytics
    
    """
    print(banner)
    log_message("SDEWS System Initialization", "INFO")


def main():
    """SDEWS runtime sisteminin ana entry point'i."""
    print_banner()
    
    # Data source'lari baslat
    log_message("Data source'lar baslatiliyor...", "INFO")
    
    # 1. USGS Earthquake Source (Hakan'in calismasi)
    earthquake_source = USGSEarthquakeSource()
    log_message("[OK] USGS Earthquake Source hazir", "INFO")
    
    # 2. OpenWeather Sources - Türkiye'nin önemli şehirleri (Hakan'in calismasi)
    # include_forecast=True ile 5 günlük tahmin verileri de çekiliyor
    weather_sources = [
        OpenWeatherSource(city="Istanbul", include_forecast=True),
        OpenWeatherSource(city="Ankara", include_forecast=True),
        OpenWeatherSource(city="Izmir", include_forecast=True),
        OpenWeatherSource(city="Antalya", include_forecast=True),
        OpenWeatherSource(city="Bursa", include_forecast=True),
        OpenWeatherSource(city="Adana", include_forecast=True),
    ]
    log_message(f"[OK] {len(weather_sources)} OpenWeather Source hazir", "INFO")
    
    # Runtime sistemi olustur (Fikret'in calismasi)
    log_message("Runtime system olusturuluyor...", "INFO")
    
    # Tüm data source'ları birleştir
    all_sources = [earthquake_source] + weather_sources
    
    runtime = RuntimeSystem(
        data_sources=all_sources,
        fetch_interval=120,  # Her 2 dakikada bir veri çek
        num_consumers=3  # 3 paralel consumer thread
    )
    
    log_message("[OK] Runtime System hazir", "INFO")
    
    # Calisma modunu belirle
    continuous = "--once" not in sys.argv
    
    if continuous:
        log_message("SUREKLI MOD baslatiliyor (Ctrl+C ile durdurun)", "INFO")
        log_message("Sistemi durdurmak icin Ctrl+C'ye basin", "INFO")
    else:
        log_message("TEK CALISTIRMA MODU baslatiliyor", "INFO")
    
    try:
        # Runtime sistemini başlat
        runtime.start(continuous=continuous)
        
    except KeyboardInterrupt:
        log_message("\nKeyboard interrupt alindi", "INFO")
    except Exception as e:
        log_message(f"Beklenmeyen hata: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        # Temizlik
        runtime.stop()
        log_message("Sistem kapatildi", "INFO")


if __name__ == "__main__":
    main()
