# src/main.py

"""
Bu modül projeyi çalıştırmak için giriş noktasıdır.

Şu anda tek yaptığı şey:
- USGS'ten deprem verisini çekip
- temizleyip
- JSON'a kaydedip
- analitik özet üreten fetch_usgs_quakes pipeline'ını çalıştırmak.
"""

from .fetch_usgs_quakes import main as run_usgs_pipeline


def main():
    # Tüm işi yapan pipeline'ı çağırıyoruz
    run_usgs_pipeline()


if __name__ == "__main__":
    main()