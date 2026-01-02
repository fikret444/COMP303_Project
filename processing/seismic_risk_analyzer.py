"""
Sismik Risk Analiz Uzmanı
Sismik boşluk (seismic gap) teorisi ve tarihsel deprem verileri ışığında risk analizi

Author: SDEWS Team
Date: January 2025
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import glob
import os
from .storage import log_message, DATA_DIR

# Amerika kıtalarındaki önemli fay hatları ve ortalama tekrarlanma aralıkları (yıl)
# Kaynak: Bilimsel literatür ve USGS verileri
FAULT_LINE_DATA = {
    # Kuzey Amerika - San Andreas Fay Hattı
    "san_andreas": {
        "name": "San Andreas Fay Hattı",
        "region": "California, USA",
        "bbox": {"min_lat": 32.0, "max_lat": 40.0, "min_lon": -125.0, "max_lon": -115.0},
        "avg_recurrence_interval": 150,  # Ortalama 150 yılda bir büyük deprem
        "last_major_earthquake": "1906-04-18",  # 1906 San Francisco depremi (M7.9)
        "magnitude_threshold": 7.0
    },
    # Kuzey Amerika - Cascadia Subduction Zone
    "cascadia": {
        "name": "Cascadia Subduction Zone",
        "region": "Pacific Northwest, USA/Canada",
        "bbox": {"min_lat": 40.0, "max_lat": 50.0, "min_lon": -130.0, "max_lon": -120.0},
        "avg_recurrence_interval": 500,  # Ortalama 500 yılda bir mega deprem
        "last_major_earthquake": "1700-01-26",  # 1700 Cascadia depremi (M9.0)
        "magnitude_threshold": 8.0
    },
    # Güney Amerika - Nazca Plate Subduction
    "nazca_subduction": {
        "name": "Nazca Plate Subduction Zone",
        "region": "Chile, Peru, Ecuador",
        "bbox": {"min_lat": -40.0, "max_lat": 5.0, "min_lon": -85.0, "max_lon": -65.0},
        "avg_recurrence_interval": 100,  # Ortalama 100 yılda bir büyük deprem
        "last_major_earthquake": "2010-02-27",  # 2010 Chile depremi (M8.8)
        "magnitude_threshold": 7.5
    },
    # Güney Amerika - Caribbean Plate Boundary
    "caribbean_boundary": {
        "name": "Caribbean Plate Boundary",
        "region": "Caribbean, Central America",
        "bbox": {"min_lat": 10.0, "max_lat": 20.0, "min_lon": -90.0, "max_lon": -60.0},
        "avg_recurrence_interval": 50,  # Ortalama 50 yılda bir büyük deprem
        "last_major_earthquake": "2010-01-12",  # 2010 Haiti depremi (M7.0)
        "magnitude_threshold": 7.0
    },
    # Güney Amerika - Andean Volcanic Belt
    "andean": {
        "name": "Andean Volcanic Belt",
        "region": "Andes Mountains",
        "bbox": {"min_lat": -40.0, "max_lat": 10.0, "min_lon": -80.0, "max_lon": -65.0},
        "avg_recurrence_interval": 80,  # Ortalama 80 yılda bir büyük deprem
        "last_major_earthquake": "2015-09-16",  # 2015 Chile depremi (M8.3)
        "magnitude_threshold": 7.0
    },
    # Kuzey Amerika - New Madrid Seismic Zone
    "new_madrid": {
        "name": "New Madrid Seismic Zone",
        "region": "Central United States",
        "bbox": {"min_lat": 35.0, "max_lat": 38.0, "min_lon": -92.0, "max_lon": -88.0},
        "avg_recurrence_interval": 500,  # Ortalama 500 yılda bir mega deprem
        "last_major_earthquake": "1812-02-07",  # 1812 New Madrid depremi (M7.5-8.0)
        "magnitude_threshold": 7.0
    },
    # Güney Amerika - Puerto Rico Trench
    "puerto_rico_trench": {
        "name": "Puerto Rico Trench",
        "region": "Caribbean Sea",
        "bbox": {"min_lat": 15.0, "max_lat": 20.0, "min_lon": -70.0, "max_lon": -60.0},
        "avg_recurrence_interval": 200,  # Ortalama 200 yılda bir büyük deprem
        "last_major_earthquake": "1946-08-04",  # 1946 Dominican Republic depremi (M8.1)
        "magnitude_threshold": 7.5
    }
}


class SeismicRiskAnalyzer:
    """
    Sismik Risk Analiz Uzmanı
    Sismik boşluk teorisi ve tarihsel verilerle risk analizi yapar
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the analyzer with data directory"""
        self.data_dir = data_dir or DATA_DIR
        self.fault_lines = FAULT_LINE_DATA
        
    def get_historical_earthquakes(self, bbox: Dict[str, float], min_magnitude: float = 7.0, years_back: int = 200) -> List[Dict]:
        """
        Belirli bir bölgede gerçekleşmiş tarihsel depremleri topla
        
        Args:
            bbox: Bounding box dict with min_lat, max_lat, min_lon, max_lon
            min_magnitude: Minimum deprem büyüklüğü
            years_back: Kaç yıl geriye gidilecek
            
        Returns:
            List of earthquake dictionaries
        """
        historical_quakes = []
        cutoff_date = datetime.now() - timedelta(days=years_back * 365)
        
        # Tüm earthquake dosyalarını oku
        pattern = str(self.data_dir / "earthquakes_*.json")
        earthquake_files = glob.glob(pattern)
        
        for file_path in earthquake_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    earthquakes = json.load(f)
                    
                if not isinstance(earthquakes, list):
                    continue
                    
                for eq in earthquakes:
                    # Bounding box kontrolü
                    lat = eq.get('latitude')
                    lon = eq.get('longitude')
                    
                    if lat is None or lon is None:
                        continue
                        
                    if not (bbox['min_lat'] <= lat <= bbox['max_lat'] and 
                           bbox['min_lon'] <= lon <= bbox['max_lon']):
                        continue
                    
                    # Magnitude kontrolü
                    magnitude = eq.get('magnitude', 0)
                    if magnitude < min_magnitude:
                        continue
                    
                    # Tarih kontrolü
                    timestamp = eq.get('timestamp')
                    if timestamp:
                        try:
                            if isinstance(timestamp, str):
                                eq_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            else:
                                continue
                            
                            if eq_date < cutoff_date:
                                continue
                                
                            historical_quakes.append({
                                'timestamp': timestamp,
                                'magnitude': magnitude,
                                'latitude': lat,
                                'longitude': lon,
                                'location': eq.get('location', 'Unknown')
                            })
                        except:
                            continue
                            
            except Exception as e:
                log_message(f"Error reading earthquake file {file_path}: {e}", "WARNING")
                continue
        
        # Tarihe göre sırala (en yeni en başta)
        historical_quakes.sort(key=lambda x: x['timestamp'], reverse=True)
        return historical_quakes
    
    def analyze_fault_line(self, fault_id: str) -> Dict:
        """
        Belirli bir fay hattı için sismik risk analizi yap
        
        Args:
            fault_id: Fault line identifier (e.g., "san_andreas")
            
        Returns:
            Risk analiz sonucu dictionary
        """
        if fault_id not in self.fault_lines:
            return {
                'error': f'Unknown fault line: {fault_id}',
                'risk_level': 'UNKNOWN'
            }
        
        fault_data = self.fault_lines[fault_id]
        bbox = fault_data['bbox']
        
        # Tarihsel depremleri topla
        historical_quakes = self.get_historical_earthquakes(
            bbox=bbox,
            min_magnitude=fault_data['magnitude_threshold'],
            years_back=500
        )
        
        # Son büyük depremi bul
        last_major_date_str = fault_data.get('last_major_earthquake')
        last_major_date = datetime.fromisoformat(last_major_date_str) if last_major_date_str else None
        
        # Eğer tarihsel verilerde daha yeni bir deprem varsa onu kullan
        if historical_quakes:
            most_recent = historical_quakes[0]
            try:
                recent_date = datetime.fromisoformat(most_recent['timestamp'].replace('Z', '+00:00'))
                if last_major_date is None or recent_date > last_major_date:
                    last_major_date = recent_date
                    last_major_date_str = most_recent['timestamp']
            except:
                pass
        
        # Ortalama tekrarlanma aralığı
        avg_interval = fault_data['avg_recurrence_interval']
        
        # Zaman aşımı hesabı
        now = datetime.now()
        if last_major_date:
            time_elapsed = (now - last_major_date).days / 365.25  # Yıl cinsinden
        else:
            time_elapsed = avg_interval  # Eğer veri yoksa, ortalama aralığa eşit kabul et
        
        # Risk puanlaması
        time_ratio = time_elapsed / avg_interval if avg_interval > 0 else 1.0
        
        if time_ratio >= 1.2:
            risk_level = "YÜKSEK RİSKLİ"
            risk_score = min(100, int(50 + (time_ratio - 1.2) * 100))
            risk_description = "Sismik boşluk tespit edildi. Ortalama tekrarlanma aralığını aşmış durumda."
        elif time_ratio >= 0.9:
            risk_level = "ORTA-YÜKSEK RİSKLİ"
            risk_score = int(40 + (time_ratio - 0.9) * 33)
            risk_description = "Ortalama tekrarlanma aralığına yaklaşıyor. Dikkatli izleme önerilir."
        elif time_ratio >= 0.7:
            risk_level = "ORTA RİSKLİ"
            risk_score = int(25 + (time_ratio - 0.7) * 75)
            risk_description = "Normal aralıkta. Rutin izleme yeterli."
        else:
            risk_level = "DÜŞÜK RİSKLİ"
            risk_score = int(time_ratio * 35)
            risk_description = "Son depremden bu yana yeterli süre geçmemiş. Düşük risk."
        
        # Son büyük depremler listesi (en fazla 5)
        recent_major_quakes = historical_quakes[:5] if len(historical_quakes) > 0 else []
        
        return {
            'fault_id': fault_id,
            'fault_name': fault_data['name'],
            'region': fault_data['region'],
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_description': risk_description,
            'time_elapsed_years': round(time_elapsed, 2),
            'avg_recurrence_interval_years': avg_interval,
            'time_ratio': round(time_ratio, 3),
            'last_major_earthquake_date': last_major_date_str if last_major_date else None,
            'magnitude_threshold': fault_data['magnitude_threshold'],
            'recent_major_earthquakes': recent_major_quakes,
            'total_historical_quakes_found': len(historical_quakes),
            'analysis_date': datetime.now().isoformat(),
            'disclaimer': 'Bu analiz istatistiksel verilere dayalı bir olasılık değerlendirmesidir; kesin bir tarih veya zaman bildirmez. Lütfen resmi kurumların (AFAD, USGS vb.) açıklamalarını takip edin.'
        }
    
    def analyze_region(self, latitude: float, longitude: float, radius_km: float = 100) -> Dict:
        """
        Belirli bir koordinat etrafındaki bölge için risk analizi yap
        
        Args:
            latitude: Bölge enlemi
            longitude: Bölge boylamı
            radius_km: Analiz yarıçapı (km)
            
        Returns:
            Risk analiz sonucu
        """
        # Yaklaşık bounding box hesapla (1 derece ≈ 111 km)
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * abs(abs(latitude) / 90.0) if latitude != 0 else 1)
        
        bbox = {
            'min_lat': latitude - lat_offset,
            'max_lat': latitude + lat_offset,
            'min_lon': longitude - lon_offset,
            'max_lon': longitude + lon_offset
        }
        
        # Bu bölgedeki tüm fay hatlarını bul
        relevant_faults = []
        for fault_id, fault_data in self.fault_lines.items():
            fault_bbox = fault_data['bbox']
            # Bounding box'ların kesişip kesişmediğini kontrol et
            if not (bbox['max_lat'] < fault_bbox['min_lat'] or bbox['min_lat'] > fault_bbox['max_lat'] or
                   bbox['max_lon'] < fault_bbox['min_lon'] or bbox['min_lon'] > fault_bbox['max_lon']):
                relevant_faults.append(fault_id)
        
        # Eğer yakın bir fay hattı varsa onu analiz et
        if relevant_faults:
            # En yakın fay hattını bul (basit yaklaşım: ilk eşleşen)
            primary_fault = relevant_faults[0]
            result = self.analyze_fault_line(primary_fault)
            result['analysis_type'] = 'fault_line'
            result['query_location'] = {'latitude': latitude, 'longitude': longitude, 'radius_km': radius_km}
            return result
        
        # Eğer yakın fay hattı yoksa, bölgesel analiz yap
        historical_quakes = self.get_historical_earthquakes(
            bbox=bbox,
            min_magnitude=6.0,
            years_back=100
        )
        
        if not historical_quakes:
            return {
                'analysis_type': 'region',
                'query_location': {'latitude': latitude, 'longitude': longitude, 'radius_km': radius_km},
                'risk_level': 'BİLİNMEYEN',
                'risk_score': 0,
                'risk_description': 'Bu bölge için yeterli tarihsel veri bulunamadı.',
                'total_historical_quakes_found': 0,
                'analysis_date': datetime.now().isoformat(),
                'disclaimer': 'Bu analiz istatistiksel verilere dayalı bir olasılık değerlendirmesidir; kesin bir tarih veya zaman bildirmez. Lütfen resmi kurumların (AFAD, USGS vb.) açıklamalarını takip edin.'
            }
        
        # Son depremi bul
        most_recent = historical_quakes[0]
        try:
            recent_date = datetime.fromisoformat(most_recent['timestamp'].replace('Z', '+00:00'))
            now = datetime.now()
            time_elapsed = (now - recent_date).days / 365.25
            
            # Bölgesel ortalama için 50 yıl varsayalım (genel tahmin)
            avg_interval = 50.0
            time_ratio = time_elapsed / avg_interval
            
            if time_ratio >= 1.0:
                risk_level = "ORTA-YÜKSEK RİSKLİ"
                risk_score = min(80, int(50 + (time_ratio - 1.0) * 30))
                risk_description = f"Son büyük depremden {round(time_elapsed, 1)} yıl geçti. Bölgesel ortalama aralığa yaklaşıyor."
            elif time_ratio >= 0.7:
                risk_level = "ORTA RİSKLİ"
                risk_score = int(30 + (time_ratio - 0.7) * 66)
                risk_description = "Normal aralıkta. Rutin izleme yeterli."
            else:
                risk_level = "DÜŞÜK RİSKLİ"
                risk_score = int(time_ratio * 42)
                risk_description = "Son depremden bu yana yeterli süre geçmemiş. Düşük risk."
        except:
            risk_level = "BİLİNMEYEN"
            risk_score = 0
            risk_description = "Tarihsel veri analiz edilemedi."
            time_elapsed = 0
            time_ratio = 0
        
        return {
            'analysis_type': 'region',
            'query_location': {'latitude': latitude, 'longitude': longitude, 'radius_km': radius_km},
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_description': risk_description,
            'time_elapsed_years': round(time_elapsed, 2),
            'recent_major_earthquakes': historical_quakes[:5],
            'total_historical_quakes_found': len(historical_quakes),
            'analysis_date': datetime.now().isoformat(),
            'disclaimer': 'Bu analiz istatistiksel verilere dayalı bir olasılık değerlendirmesidir; kesin bir tarih veya zaman bildirmez. Lütfen resmi kurumların (AFAD, USGS vb.) açıklamalarını takip edin.'
        }
    
    def get_all_fault_lines(self) -> List[Dict]:
        """Tüm fay hatlarının listesini döndür"""
        return [
            {
                'fault_id': fault_id,
                'name': data['name'],
                'region': data['region'],
                'bbox': data['bbox']
            }
            for fault_id, data in self.fault_lines.items()
        ]


    def detect_earthquake_swarms_from_data(self, earthquakes: List[Dict], min_count: int = 3, 
                                           max_magnitude: float = 5.0, cluster_radius_km: float = 100.0, 
                                           min_days: int = 0, max_days: int = 1) -> List[Dict]:
        """
        Deprem sürülerini (swarm) tespit et - Verilen deprem verilerinden
        Son 1 gün içindeki depremleri analiz eder (USGS'ten çekilen verilerle uyumlu)
        
        Args:
            earthquakes: Analiz edilecek deprem listesi (dashboard'dan gelen veriler)
            min_count: Minimum deprem sayısı (varsayılan: 3)
            max_magnitude: Maksimum deprem büyüklüğü (varsayılan: 5.0)
            cluster_radius_km: Küme yarıçapı km cinsinden (varsayılan: 100)
            min_days: Minimum zaman aralığı gün cinsinden (varsayılan: 0 - aynı gün içindeki depremler)
            max_days: Maksimum zaman aralığı gün cinsinden (varsayılan: 1 - son 24 saat)
            
        Returns:
            List of swarm dictionaries with risk analysis
        """
        from datetime import timedelta
        import math
        
        swarms = []
        cutoff_date = datetime.now() - timedelta(days=max_days)
        
        # Verilen deprem verilerini işle
        all_earthquakes = []
        
        for eq in earthquakes:
            lat = eq.get('latitude')
            lon = eq.get('longitude')
            magnitude = eq.get('magnitude', 0)
            timestamp = eq.get('timestamp')
            
            if lat is None or lon is None or magnitude is None:
                continue
            
            # Büyüklük filtresi
            if magnitude > max_magnitude:
                continue
            
            # Tarih filtresi
            eq_date = None
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        # Farklı timestamp formatlarını dene
                        clean_timestamp = timestamp.replace('Z', '').strip()
                        try:
                            if '.' in clean_timestamp:
                                # Mikrosaniye varsa
                                parts = clean_timestamp.split('.')
                                eq_date = datetime.strptime(parts[0], '%Y-%m-%dT%H:%M:%S')
                            else:
                                eq_date = datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
                        except:
                            try:
                                eq_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            except:
                                eq_date = datetime.now()
                    else:
                        eq_date = datetime.now()
                    
                    # Zaman kontrolü - gelecek tarihleri atla
                    if eq_date > datetime.now():
                        eq_date = datetime.now()
                    
                    # Eğer çok eski değilse ekle (max_days kontrolü)
                    if eq_date >= cutoff_date:
                        all_earthquakes.append({
                            'latitude': lat,
                            'longitude': lon,
                            'magnitude': magnitude,
                            'timestamp': timestamp,
                            'location': eq.get('location', 'Unknown'),
                            'datetime': eq_date
                        })
                except Exception as e:
                    log_message(f"Tarih parse hatası: {timestamp}, {e}", "WARNING")
                    # Hata olsa bile depremi ekle (bugünkü tarihle) - swarm tespiti için önemli
                    all_earthquakes.append({
                        'latitude': lat,
                        'longitude': lon,
                        'magnitude': magnitude,
                        'timestamp': timestamp or datetime.now().isoformat(),
                        'location': eq.get('location', 'Unknown'),
                        'datetime': datetime.now()
                    })
            else:
                # Timestamp yoksa, bugünkü tarihle ekle
                all_earthquakes.append({
                    'latitude': lat,
                    'longitude': lon,
                    'magnitude': magnitude,
                    'timestamp': datetime.now().isoformat(),
                    'location': eq.get('location', 'Unknown'),
                    'datetime': datetime.now()
                })
        
        log_message(f"Haritada gösterilen {len(earthquakes)} depremden {len(all_earthquakes)} deprem analiz ediliyor (min_count: {min_count}, max_magnitude: {max_magnitude}, radius: {cluster_radius_km}km)", "INFO")
        
        if len(all_earthquakes) < min_count:
            log_message(f"Yeterli deprem yok: {len(all_earthquakes)} < {min_count}", "INFO")
            return swarms
        
        # Haversine formülü ile mesafe hesaplama (km)
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Dünya yarıçapı km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        # Depremleri kümele (clustering)
        processed = set()
        
        for i, eq1 in enumerate(all_earthquakes):
            if i in processed:
                continue
                
            cluster = [eq1]
            processed.add(i)
            
            # Bu depreme yakın diğer depremleri bul
            for j, eq2 in enumerate(all_earthquakes):
                if j in processed or i == j:
                    continue
                
                distance = haversine_distance(
                    eq1['latitude'], eq1['longitude'],
                    eq2['latitude'], eq2['longitude']
                )
                
                if distance <= cluster_radius_km:
                    cluster.append(eq2)
                    processed.add(j)
            
            # Eğer küme yeterince büyükse, swarm olarak işaretle
            if len(cluster) >= min_count:
                # Zaman aralığını kontrol et
                cluster_dates = [eq['datetime'] for eq in cluster]
                time_span = (max(cluster_dates) - min(cluster_dates)).days
                
                # Zaman aralığı kontrolü - son 1 gün içindeki depremler için
                # time_span 0 olabilir (aynı saat içinde) veya 1 günden az olabilir
                if time_span <= max_days:  # Son 1 gün içindeki depremler
                    # Küme merkezini hesapla
                    center_lat = sum(eq['latitude'] for eq in cluster) / len(cluster)
                    center_lon = sum(eq['longitude'] for eq in cluster) / len(cluster)
                    
                    # İstatistikler
                    magnitudes = [eq['magnitude'] for eq in cluster]
                    avg_magnitude = sum(magnitudes) / len(magnitudes)
                    max_magnitude_cluster = max(magnitudes)
                    min_magnitude_cluster = min(magnitudes)
                    
                    # Risk analizi
                    earthquake_count = len(cluster)
                    risk_score = min(100, int(
                        20 +  # Base score
                        (earthquake_count - min_count) * 5 +  # Her ekstra deprem +5
                        (avg_magnitude - 2.0) * 10 +  # Ortalama büyüklük etkisi
                        (time_span / max_days) * 20 if max_days > 0 else 0  # Zaman aralığı etkisi
                    ))
                    
                    if risk_score >= 70:
                        risk_level = "YÜKSEK RİSKLİ"
                    elif risk_score >= 50:
                        risk_level = "ORTA-YÜKSEK RİSKLİ"
                    elif risk_score >= 30:
                        risk_level = "ORTA RİSKLİ"
                    else:
                        risk_level = "DÜŞÜK RİSKLİ"
                    
                    swarms.append({
                        'swarm_id': f"swarm_{len(swarms) + 1}",
                        'center_latitude': center_lat,
                        'center_longitude': center_lon,
                        'earthquake_count': earthquake_count,
                        'avg_magnitude': round(avg_magnitude, 2),
                        'max_magnitude': max_magnitude_cluster,
                        'min_magnitude': min_magnitude_cluster,
                        'time_span_days': time_span,
                        'cluster_radius_km': cluster_radius_km,
                        'risk_level': risk_level,
                        'risk_score': risk_score,
                        'risk_description': f"{earthquake_count} adet küçük deprem {time_span} gün içinde {cluster_radius_km} km yarıçapında tespit edildi. Bu bir deprem sürüsü (swarm) olabilir.",
                        'earthquakes': sorted(cluster, key=lambda x: x['datetime'], reverse=True)[:10],  # En fazla 10 deprem
                        'first_earthquake_date': min(cluster_dates).isoformat(),
                        'last_earthquake_date': max(cluster_dates).isoformat(),
                        'analysis_date': datetime.now().isoformat(),
                        'disclaimer': 'Bu analiz istatistiksel verilere dayalı bir olasılık değerlendirmesidir; kesin bir tarih veya zaman bildirmez. Lütfen resmi kurumların (AFAD, USGS vb.) açıklamalarını takip edin.'
                    })
        
        # Risk skoruna göre sırala (en yüksek risk en üstte)
        swarms.sort(key=lambda x: x['risk_score'], reverse=True)
        
        log_message(f"Toplam {len(swarms)} deprem sürüsü tespit edildi (haritada gösterilen depremlerden)", "INFO")
        if len(swarms) > 0:
            log_message(f"İlk swarm: {swarms[0]['earthquake_count']} deprem, risk: {swarms[0]['risk_level']}, merkez: ({swarms[0]['center_latitude']:.2f}, {swarms[0]['center_longitude']:.2f})", "INFO")
        
        return swarms

    def detect_earthquake_swarms(self, min_count: int = 3, max_magnitude: float = 5.0, 
                                 cluster_radius_km: float = 100.0, min_days: int = 0, 
                                 max_days: int = 1) -> List[Dict]:
        """
        Deprem sürülerini (swarm) tespit et - birbirine yakın küçük depremler
        Son 1 gün içindeki depremleri analiz eder (USGS'ten çekilen verilerle uyumlu)
        
        Args:
            min_count: Minimum deprem sayısı (varsayılan: 3)
            max_magnitude: Maksimum deprem büyüklüğü (varsayılan: 5.0)
            cluster_radius_km: Küme yarıçapı km cinsinden (varsayılan: 100)
            min_days: Minimum zaman aralığı gün cinsinden (varsayılan: 0 - aynı gün içindeki depremler)
            max_days: Maksimum zaman aralığı gün cinsinden (varsayılan: 1 - son 24 saat)
            
        Returns:
            List of swarm dictionaries with risk analysis
        """
        from datetime import timedelta
        import math
        
        swarms = []
        cutoff_date = datetime.now() - timedelta(days=max_days)
        min_date = datetime.now() - timedelta(days=min_days)
        
        # Amerika kıtaları filtresi - USGS'ten çekilen depremler zaten bu bölgede
        # Bbox: [minLon, minLat, maxLon, maxLat] = [-180, -60, -30, 85]
        americas_bbox = {'min_lon': -180, 'min_lat': -60, 'max_lon': -30, 'max_lat': 85}
        
        # Tüm deprem verilerini topla (sadece Amerika kıtaları)
        all_earthquakes = []
        pattern = str(self.data_dir / "earthquakes_*.json")
        earthquake_files = glob.glob(pattern)
        
        for file_path in earthquake_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    earthquakes = json.load(f)
                    
                if not isinstance(earthquakes, list):
                    continue
                    
                for eq in earthquakes:
                    lat = eq.get('latitude')
                    lon = eq.get('longitude')
                    magnitude = eq.get('magnitude', 0)
                    timestamp = eq.get('timestamp')
                    
                    if lat is None or lon is None or magnitude is None:
                        continue
                    
                    # Amerika kıtaları filtresi - Sadece haritada gösterilen depremler
                    if not (americas_bbox['min_lat'] <= lat <= americas_bbox['max_lat'] and
                           americas_bbox['min_lon'] <= lon <= americas_bbox['max_lon']):
                        continue
                    
                    # Büyüklük filtresi
                    if magnitude > max_magnitude:
                        continue
                    
                    # Tarih filtresi
                    eq_date = None
                    if timestamp:
                        try:
                            if isinstance(timestamp, str):
                                # Farklı timestamp formatlarını dene
                                try:
                                    # ISO format: "2026-01-02T22:08:46.058000" veya "2026-01-02T22:08:46.058000Z"
                                    clean_timestamp = timestamp.replace('Z', '').strip()
                                    if '.' in clean_timestamp:
                                        # Mikrosaniye varsa
                                        eq_date = datetime.strptime(clean_timestamp.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                                    else:
                                        eq_date = datetime.strptime(clean_timestamp, '%Y-%m-%dT%H:%M:%S')
                                except:
                                    try:
                                        eq_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    except:
                                        # Parse edilemezse bugünkü tarih kullan
                                        eq_date = datetime.now()
                            else:
                                eq_date = datetime.now()
                            
                            # Zaman kontrolü - gelecek tarihleri atla
                            if eq_date > datetime.now():
                                eq_date = datetime.now()
                            
                            # Eğer çok eski değilse ekle (max_days kontrolü)
                            if eq_date >= cutoff_date:
                                all_earthquakes.append({
                                    'latitude': lat,
                                    'longitude': lon,
                                    'magnitude': magnitude,
                                    'timestamp': timestamp,
                                    'location': eq.get('location', 'Unknown'),
                                    'datetime': eq_date
                                })
                        except Exception as e:
                            log_message(f"Tarih parse hatası: {timestamp}, {e}", "WARNING")
                            # Hata olsa bile depremi ekle (bugünkü tarihle)
                            all_earthquakes.append({
                                'latitude': lat,
                                'longitude': lon,
                                'magnitude': magnitude,
                                'timestamp': timestamp or datetime.now().isoformat(),
                                'location': eq.get('location', 'Unknown'),
                                'datetime': datetime.now()
                            })
                    else:
                        # Timestamp yoksa, bugünkü tarihle ekle
                        all_earthquakes.append({
                            'latitude': lat,
                            'longitude': lon,
                            'magnitude': magnitude,
                            'timestamp': datetime.now().isoformat(),
                            'location': eq.get('location', 'Unknown'),
                            'datetime': datetime.now()
                        })
                            
            except Exception as e:
                log_message(f"Error reading earthquake file {file_path}: {e}", "WARNING")
                continue
        
        log_message(f"Toplam {len(all_earthquakes)} deprem analiz ediliyor (min_count: {min_count}, max_magnitude: {max_magnitude}, radius: {cluster_radius_km}km)", "INFO")
        
        if len(all_earthquakes) < min_count:
            log_message(f"Yeterli deprem yok: {len(all_earthquakes)} < {min_count}", "INFO")
            return swarms
        
        # Haversine formülü ile mesafe hesaplama (km)
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # Dünya yarıçapı km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        # Depremleri kümele (clustering)
        processed = set()
        
        for i, eq1 in enumerate(all_earthquakes):
            if i in processed:
                continue
                
            cluster = [eq1]
            processed.add(i)
            
            # Bu depreme yakın diğer depremleri bul
            for j, eq2 in enumerate(all_earthquakes):
                if j in processed or i == j:
                    continue
                
                distance = haversine_distance(
                    eq1['latitude'], eq1['longitude'],
                    eq2['latitude'], eq2['longitude']
                )
                
                if distance <= cluster_radius_km:
                    cluster.append(eq2)
                    processed.add(j)
            
            # Eğer küme yeterince büyükse, swarm olarak işaretle
            if len(cluster) >= min_count:
                # Zaman aralığını kontrol et
                cluster_dates = [eq['datetime'] for eq in cluster]
                time_span = (max(cluster_dates) - min(cluster_dates)).days
                
                # Zaman aralığı kontrolü - son 1 gün içindeki depremler için
                # time_span 0 olabilir (aynı saat içinde) veya 1 günden az olabilir
                if time_span <= max_days:  # Son 1 gün içindeki depremler
                    # Küme merkezini hesapla
                    center_lat = sum(eq['latitude'] for eq in cluster) / len(cluster)
                    center_lon = sum(eq['longitude'] for eq in cluster) / len(cluster)
                    
                    # İstatistikler
                    magnitudes = [eq['magnitude'] for eq in cluster]
                    avg_magnitude = sum(magnitudes) / len(magnitudes)
                    max_magnitude_cluster = max(magnitudes)
                    min_magnitude_cluster = min(magnitudes)
                    
                    # Risk analizi
                    earthquake_count = len(cluster)
                    risk_score = min(100, int(
                        20 +  # Base score
                        (earthquake_count - min_count) * 5 +  # Her ekstra deprem +5
                        (avg_magnitude - 2.0) * 10 +  # Ortalama büyüklük etkisi
                        (time_span / max_days) * 20  # Zaman aralığı etkisi
                    ))
                    
                    if risk_score >= 70:
                        risk_level = "YÜKSEK RİSKLİ"
                    elif risk_score >= 50:
                        risk_level = "ORTA-YÜKSEK RİSKLİ"
                    elif risk_score >= 30:
                        risk_level = "ORTA RİSKLİ"
                    else:
                        risk_level = "DÜŞÜK RİSKLİ"
                    
                    swarms.append({
                        'swarm_id': f"swarm_{len(swarms) + 1}",
                        'center_latitude': center_lat,
                        'center_longitude': center_lon,
                        'earthquake_count': earthquake_count,
                        'avg_magnitude': round(avg_magnitude, 2),
                        'max_magnitude': max_magnitude_cluster,
                        'min_magnitude': min_magnitude_cluster,
                        'time_span_days': time_span,
                        'cluster_radius_km': cluster_radius_km,
                        'risk_level': risk_level,
                        'risk_score': risk_score,
                        'risk_description': f"{earthquake_count} adet küçük deprem {time_span} gün içinde {cluster_radius_km} km yarıçapında tespit edildi. Bu bir deprem sürüsü (swarm) olabilir.",
                        'earthquakes': sorted(cluster, key=lambda x: x['datetime'], reverse=True)[:10],  # En fazla 10 deprem
                        'first_earthquake_date': min(cluster_dates).isoformat(),
                        'last_earthquake_date': max(cluster_dates).isoformat(),
                        'analysis_date': datetime.now().isoformat(),
                        'disclaimer': 'Bu analiz istatistiksel verilere dayalı bir olasılık değerlendirmesidir; kesin bir tarih veya zaman bildirmez. Lütfen resmi kurumların (AFAD, USGS vb.) açıklamalarını takip edin.'
                    })
        
        # Risk skoruna göre sırala (en yüksek risk en üstte)
        swarms.sort(key=lambda x: x['risk_score'], reverse=True)
        
        log_message(f"Toplam {len(swarms)} deprem sürüsü tespit edildi", "INFO")
        if len(swarms) > 0:
            log_message(f"İlk swarm: {swarms[0]['earthquake_count']} deprem, risk: {swarms[0]['risk_level']}", "INFO")
        
        return swarms


def analyze_seismic_risk(fault_id: Optional[str] = None, latitude: Optional[float] = None, 
                        longitude: Optional[float] = None, radius_km: float = 100) -> Dict:
    """
    Convenience function for seismic risk analysis
    
    Args:
        fault_id: Fault line identifier (e.g., "san_andreas")
        latitude: Region latitude (if analyzing by location)
        longitude: Region longitude (if analyzing by location)
        radius_km: Analysis radius in km (default 100)
        
    Returns:
        Risk analysis result dictionary
    """
    analyzer = SeismicRiskAnalyzer()
    
    if fault_id:
        return analyzer.analyze_fault_line(fault_id)
    elif latitude is not None and longitude is not None:
        return analyzer.analyze_region(latitude, longitude, radius_km)
    else:
        return {
            'error': 'Either fault_id or (latitude, longitude) must be provided',
            'risk_level': 'UNKNOWN'
        }

