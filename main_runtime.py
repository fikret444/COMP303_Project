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
    """SDEWS banner'ını yazdır."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║          Smart Disaster Early Warning System (SDEWS)        ║
    ║                                                              ║
    ║  Concurrent Data Processing & Real-time Event Pipeline      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Ekip Üyeleri:
    - Hakan Demircan: API Integration & Web Scraping
    - Erdem Kaya: Core System & Data Models
    - Fikret Ahıskalı: Concurrency & Runtime Pipeline
    - Yağız Efe Hüşan: Data Processing, Storage & Analytics
    
    """
    print(banner)
    log_message("SDEWS System Initialization", "INFO")


def main():
    """SDEWS runtime sisteminin ana entry point'i."""
    print_banner()
    
    # Data source'ları başlat
    log_message("Data source'lar başlatılıyor...", "INFO")
    
    # 1. USGS Earthquake Source (Hakan'ın çalışması)
    earthquake_source = USGSEarthquakeSource()
    log_message("✓ USGS Earthquake Source hazır", "INFO")
    
    # 2. OpenWeather Source (Hakan'ın çalışması)
    weather_source = OpenWeatherSource(city="Istanbul")
    log_message("✓ OpenWeather Source hazır", "INFO")
    
    # Runtime sistemi oluştur (Fikret'in çalışması)
    log_message("Runtime system oluşturuluyor...", "INFO")
    
    runtime = RuntimeSystem(
        data_sources=[earthquake_source, weather_source],
        fetch_interval=120,  # Her 2 dakikada bir veri çek
        num_consumers=3  # 3 paralel consumer thread
    )
    
    log_message("✓ Runtime System hazır", "INFO")
    
    # Çalışma modunu belirle
    continuous = "--once" not in sys.argv
    
    if continuous:
        log_message("SÜREKLI MOD başlatılıyor (Ctrl+C ile durdurun)", "INFO")
        log_message("Sistemi durdurmak için Ctrl+C'ye basın", "INFO")
    else:
        log_message("TEK ÇALIŞTIRMA MODU başlatılıyor", "INFO")
    
    try:
        # Runtime sistemini başlat
        runtime.start(continuous=continuous)
        
    except KeyboardInterrupt:
        log_message("\nKeyboard interrupt alındı", "INFO")
    except Exception as e:
        log_message(f"Beklenmeyen hata: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        # Temizlik
        runtime.stop()
        log_message("Sistem kapatıldı", "INFO")


if __name__ == "__main__":
    main()
