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
from datasources.eonet_source import EONETSource
from datasources.eonet_wildfire_source import EONETWildfireSource
from datasources.eonet_storm_source import EONETStormSource
from datasources.eonet_volcano_source import EONETVolcanoSource
from datasources.flood_openmeteo_source import OpenMeteoFloodSource
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
    
    # 1. USGS Earthquake Source - Sadece Kuzey ve Güney Amerika kıtaları (Hakan'in calismasi)
    # Amerika kıtaları için bbox: [minLon, minLat, maxLon, maxLat]
    # longitude -180 to -30, latitude -60 to 85
    americas_bbox = [-180, -60, -30, 85]
    earthquake_source = USGSEarthquakeSource(bbox=americas_bbox)
    log_message("[OK] USGS Earthquake Source hazir (Amerika kıtaları filtresi aktif)", "INFO")
    
    # 2. OpenWeather Sources - Amerika kıtalarındaki önemli şehirler (Hakan'in calismasi)
    # include_forecast=True ile 5 günlük tahmin verileri de çekiliyor
    # Kuzey Amerika: ABD ve Kanada'nın önemli şehirleri
    # Güney Amerika: Brezilya, Arjantin, Şili, Peru, Kolombiya'nın önemli şehirleri
    weather_sources = [
        # Kuzey Amerika - ABD
        OpenWeatherSource(city="New York", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Los Angeles", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Chicago", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Houston", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Miami", country_code="US", include_forecast=True),
        OpenWeatherSource(city="San Francisco", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Seattle", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Denver", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Washington", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Boston", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Atlanta", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Phoenix", country_code="US", include_forecast=True),
        OpenWeatherSource(city="Dallas", country_code="US", include_forecast=True),
        # Kuzey Amerika - Kanada ve Meksika
        OpenWeatherSource(city="Toronto", country_code="CA", include_forecast=True),
        OpenWeatherSource(city="Mexico City", country_code="MX", include_forecast=True),
        # Güney Amerika
        OpenWeatherSource(city="São Paulo", country_code="BR", include_forecast=True),
        OpenWeatherSource(city="Buenos Aires", country_code="AR", include_forecast=True),
        OpenWeatherSource(city="Rio de Janeiro", country_code="BR", include_forecast=True),
        OpenWeatherSource(city="Lima", country_code="PE", include_forecast=True),
        OpenWeatherSource(city="Bogotá", country_code="CO", include_forecast=True),
        OpenWeatherSource(city="Santiago", country_code="CL", include_forecast=True),
    ]
    log_message(f"[OK] {len(weather_sources)} OpenWeather Source hazir (Amerika kıtaları)", "INFO")
    
    # 3. EONET Source - Sadece Kuzey ve Güney Amerika kıtaları (Hakan'in calismasi)
    # Amerika kıtaları için bbox: [minLon, minLat, maxLon, maxLat]
    # longitude -180 to -30, latitude -60 to 85
    # Performans: days=30 ve limit=100 yeterli (daha hızlı)
    americas_bbox = [-180, -60, -30, 85]
    eonet_source = EONETSource(status="open", days=30, limit=100, bbox=americas_bbox)
    log_message("[OK] EONET Source hazir (Amerika kıtaları filtresi aktif)", "INFO")
    
    # 4. EONET Wildfire Source - Orman yangınları (Efe'nin calismasi)
    # EONETWildfireSource string formatında bbox bekliyor: "minLon,maxLat,maxLon,minLat"
    # Amerika kıtaları için: "-180,85,-30,-60"
    # Performans: days=90 yeterli (365 yerine - daha hızlı)
    americas_bbox_str = "-180,85,-30,-60"
    wildfire_source = EONETWildfireSource(days=90, status="all", bbox=americas_bbox_str)
    log_message("[OK] EONET Wildfire Source hazir (Amerika kıtaları)", "INFO")
    
    # 5. EONET Storm Source - Fırtınalar (Efe'nin calismasi)
    # Performans: days=60 yeterli (365 yerine - daha hızlı)
    storm_source = EONETStormSource(days=60, status="all", bbox=americas_bbox_str)
    log_message("[OK] EONET Storm Source hazir (Amerika kıtaları)", "INFO")
    
    # 6. EONET Volcano Source - Volkanlar (Yeni)
    # Performans: days=90 yeterli (365 yerine - daha hızlı)
    volcano_source = EONETVolcanoSource(days=90, status="all", bbox=americas_bbox_str)
    log_message("[OK] EONET Volcano Source hazir (Amerika kıtaları)", "INFO")
    
    # 7. OpenMeteo Flood Sources - Sel riski (Efe'nin calismasi)
    # Flood source'ları şehir bazlı çalışıyor, önemli şehirler için ekliyoruz
    flood_cities = [
        ("New Orleans", 29.9511, -90.0715),
        ("Houston", 29.7604, -95.3698),
        ("Miami", 25.7617, -80.1918),
        ("New York", 40.7128, -74.0060),
        ("Sacramento", 38.5816, -121.4944),
        ("Vancouver", 49.2827, -123.1207),
        ("Calgary", 51.0447, -114.0719),
        ("Montreal", 45.5019, -73.5674),
        ("Winnipeg", 49.8954, -97.1385),
        ("Toronto", 43.6510, -79.3470),
    ]
    flood_sources = [
        OpenMeteoFloodSource(latitude=lat, longitude=lon, location_name=city, past_days=3, forecast_days=7)
        for city, lat, lon in flood_cities
    ]
    log_message(f"[OK] {len(flood_sources)} OpenMeteo Flood Source hazir", "INFO")
    
    # Runtime sistemi olustur (Fikret'in calismasi)
    log_message("Runtime system olusturuluyor...", "INFO")
    
    # Tüm data source'ları birleştir
    all_sources = [earthquake_source] + weather_sources + [eonet_source] + [wildfire_source] + [storm_source] + [volcano_source] + flood_sources
    
    runtime = RuntimeSystem(
        data_sources=all_sources,
        fetch_interval=120,  # Her 2 dakikada bir veri çek
        num_consumers=5  # 5 paralel consumer thread (daha hızlı işleme için artırıldı)
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
