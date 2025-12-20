"""
Runtime System Test
Basit test ve demo için kullanılır.

Author: Fikret Ahıskalı
"""

import time
from datasources.usgs_earthquake import USGSEarthquakeSource
from datasources.openweather_source import OpenWeatherSource
from pipeline import DataSourceManager, EventPipeline, RuntimeSystem


def test_data_sources():
    """Data source'ları test et."""
    print("\n" + "=" * 60)
    print("TEST: Data Sources")
    print("=" * 60)
    
    # USGS test
    print("\n1. USGS Earthquake Source testi...")
    usgs = USGSEarthquakeSource()
    data = usgs.fetch_and_parse()
    print(f"   ✓ {len(data) if isinstance(data, list) else 1} deprem verisi alındı")
    
    # OpenWeather test
    print("\n2. OpenWeather Source testi...")
    weather = OpenWeatherSource(city="Istanbul")
    data = weather.fetch_and_parse()
    print(f"   ✓ Hava durumu verisi alındı: {data.get('city', 'Unknown')}")
    
    print("\n✅ Data source testleri başarılı!\n")


def test_pipeline():
    """Pipeline sistemini test et."""
    print("\n" + "=" * 60)
    print("TEST: Pipeline System")
    print("=" * 60)
    
    # DataSourceManager test
    print("\n1. DataSourceManager testi...")
    earthquake_source = USGSEarthquakeSource()
    manager = DataSourceManager(data_sources=[earthquake_source], fetch_interval=10)
    
    print("   - Concurrent fetch başlatılıyor...")
    manager.fetch_all_sources()
    
    events = manager.get_events()
    print(f"   ✓ {len(events)} event batch alındı")
    
    # EventPipeline test
    print("\n2. EventPipeline testi...")
    pipeline = EventPipeline(num_consumers=2)
    pipeline.start_consumers()
    print("   ✓ 2 consumer thread başlatıldı")
    
    # Mock event ekle
    if events:
        pipeline.add_events(events[0])
        print("   ✓ Event pipeline'a eklendi")
        
        time.sleep(2)
        pipeline.wait_for_completion()
        
        results = pipeline.get_results()
        print(f"   ✓ {len(results)} sonuç işlendi")
    
    pipeline.stop_consumers()
    print("   ✓ Consumer'lar durduruldu")
    
    print("\n✅ Pipeline testleri başarılı!\n")


def test_runtime_once():
    """RuntimeSystem'i tek seferlik test et."""
    print("\n" + "=" * 60)
    print("TEST: RuntimeSystem (Single Run)")
    print("=" * 60)
    
    earthquake_source = USGSEarthquakeSource()
    
    runtime = RuntimeSystem(
        data_sources=[earthquake_source],
        fetch_interval=60,
        num_consumers=2
    )
    
    print("\n✓ RuntimeSystem başlatıldı")
    print("  Tek döngü çalıştırılıyor...\n")
    
    runtime.start(continuous=False)
    
    status = runtime.get_status()
    print(f"\n✓ Döngü tamamlandı")
    print(f"  - İşlenen event: {status['pipeline']['processed_count']}")
    
    print("\n✅ RuntimeSystem testi başarılı!\n")


def run_all_tests():
    """Tüm testleri çalıştır."""
    print("\n" + "═" * 60)
    print("SDEWS SYSTEM TESTS")
    print("Fikret Ahıskalı - Concurrency & Runtime Pipeline")
    print("═" * 60)
    
    try:
        test_data_sources()
        test_pipeline()
        test_runtime_once()
        
        print("\n" + "=" * 60)
        print("✅ TÜM TESTLER BAŞARILI!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test hatası: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
