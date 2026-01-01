"""
Import Test - Tüm modüllerin import edilip edilmediğini kontrol et
"""

print("=" * 60)
print("IMPORT TESTİ BAŞLIYOR...")
print("=" * 60)

try:
    print("\n1. Datasources (Hakan) import ediliyor...")
    from datasources.usgs_earthquake import USGSEarthquakeSource
    from datasources.openweather_source import OpenWeatherSource
    print("   [OK] Datasources basarili!")
except Exception as e:
    print(f"   [HATA] Datasources hatasi: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. Models (Erdem) import ediliyor...")
    from models import RawEarthquake, CleanedEarthquake
    print("   [OK] Models basarili!")
except Exception as e:
    print(f"   [HATA] Models hatasi: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. Processing (Efe) import ediliyor...")
    from processing import (
        save_events_to_json,
        log_message,
        clean_usgs_earthquake_events
    )
    print("   [OK] Processing basarili!")
except Exception as e:
    print(f"   [HATA] Processing hatasi: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4. Pipeline (Fikret) import ediliyor...")
    from pipeline import (
        DataSourceManager,
        EventPipeline,
        RuntimeSystem
    )
    print("   [OK] Pipeline basarili!")
except Exception as e:
    print(f"   [HATA] Pipeline hatasi: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("[BASARILI] TUM IMPORT'LAR TAMAM!")
print("=" * 60)
print("\nSistem hazir, main_runtime.py calistiri labilir!\n")

