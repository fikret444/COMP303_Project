"""
Sismik Acil Durum Operatörü - Deprem Simülasyonu
Deprem erken uyarı sistemi simülasyonu

Author: Fikret Ahıskalı
Date: January 2025
"""

import random
import math
from datetime import datetime

# 24 Sabit Sensör Konumu (Amerika kıtalarında çok geniş dağılım)
SENSOR_LOCATIONS = [
    # Kuzey Amerika - Doğu
    {'id': 'sensor_1', 'name': 'New York Sensörü', 'latitude': 40.7, 'longitude': -74.0},
    {'id': 'sensor_2', 'name': 'Montreal Sensörü', 'latitude': 45.5, 'longitude': -73.5},
    {'id': 'sensor_3', 'name': 'Boston Sensörü', 'latitude': 42.3, 'longitude': -71.0},
    {'id': 'sensor_4', 'name': 'Miami Sensörü', 'latitude': 25.7, 'longitude': -80.2},
    {'id': 'sensor_5', 'name': 'Atlanta Sensörü', 'latitude': 33.7, 'longitude': -84.4},
    # Kuzey Amerika - Merkez
    {'id': 'sensor_6', 'name': 'Chicago Sensörü', 'latitude': 41.8, 'longitude': -87.6},
    {'id': 'sensor_7', 'name': 'Dallas Sensörü', 'latitude': 32.7, 'longitude': -96.8},
    {'id': 'sensor_8', 'name': 'Denver Sensörü', 'latitude': 39.7, 'longitude': -104.9},
    {'id': 'sensor_9', 'name': 'Kansas City Sensörü', 'latitude': 39.1, 'longitude': -94.5},
    # Kuzey Amerika - Batı
    {'id': 'sensor_10', 'name': 'Los Angeles Sensörü', 'latitude': 34.0, 'longitude': -118.2},
    {'id': 'sensor_11', 'name': 'San Francisco Sensörü', 'latitude': 37.7, 'longitude': -122.4},
    {'id': 'sensor_12', 'name': 'Seattle Sensörü', 'latitude': 47.6, 'longitude': -122.3},
    {'id': 'sensor_13', 'name': 'Phoenix Sensörü', 'latitude': 33.4, 'longitude': -112.0},
    {'id': 'sensor_14', 'name': 'Alaska Sensörü', 'latitude': 61.2, 'longitude': -149.8},
    # Meksika ve Orta Amerika
    {'id': 'sensor_15', 'name': 'Mexico City Sensörü', 'latitude': 19.4, 'longitude': -99.1},
    {'id': 'sensor_16', 'name': 'Guatemala Sensörü', 'latitude': 14.6, 'longitude': -90.5},
    # Güney Amerika - Kuzey
    {'id': 'sensor_17', 'name': 'Bogota Sensörü', 'latitude': 4.7, 'longitude': -74.0},
    {'id': 'sensor_18', 'name': 'Caracas Sensörü', 'latitude': 10.5, 'longitude': -66.9},
    # Güney Amerika - Merkez
    {'id': 'sensor_19', 'name': 'Brasilia Sensörü', 'latitude': -15.8, 'longitude': -47.8},
    {'id': 'sensor_20', 'name': 'Sao Paulo Sensörü', 'latitude': -23.5, 'longitude': -46.6},
    {'id': 'sensor_21', 'name': 'Lima Sensörü', 'latitude': -12.0, 'longitude': -77.0},
    # Güney Amerika - Güney
    {'id': 'sensor_22', 'name': 'Buenos Aires Sensörü', 'latitude': -34.6, 'longitude': -58.4},
    {'id': 'sensor_23', 'name': 'Santiago Sensörü', 'latitude': -33.4, 'longitude': -70.6},
    {'id': 'sensor_24', 'name': 'Montevideo Sensörü', 'latitude': -34.9, 'longitude': -56.1}
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    İki koordinat arasındaki mesafeyi hesapla (Haversine formülü)
    Sonuç: km cinsinden
    """
    R = 6371  # Dünya yarıçapı km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def generate_random_epicenter(user_lat, user_lon):
    """
    Kullanıcıya yakın bir yerde rastgele deprem merkez üssü üret
    En yakın sensöre 200-800 km mesafede
    """
    # Kullanıcıya en yakın sensörü bul
    closest_sensor_to_user = None
    min_user_distance = float('inf')
    for sensor in SENSOR_LOCATIONS:
        distance = haversine_distance(user_lat, user_lon, sensor['latitude'], sensor['longitude'])
        if distance < min_user_distance:
            min_user_distance = distance
            closest_sensor_to_user = sensor
    
    # Deprem merkez üssünü seçilen sensöre yakın bir yerde oluştur (200-800 km mesafede)
    min_distance_from_sensor = 200  # Minimum 200 km
    max_distance_from_sensor = 800  # Maksimum 800 km
    
    angle = random.uniform(0, 2 * math.pi)
    distance_from_sensor = random.uniform(min_distance_from_sensor, max_distance_from_sensor)
    
    lat_offset = (distance_from_sensor / 111.0) * math.cos(angle)
    lon_offset = (distance_from_sensor / (111.0 * math.cos(math.radians(closest_sensor_to_user['latitude'])))) * math.sin(angle)
    
    epicenter_lat = closest_sensor_to_user['latitude'] + lat_offset
    epicenter_lon = closest_sensor_to_user['longitude'] + lon_offset
    
    # Amerika kıtaları sınırları içinde tut
    americas_bbox = {'min_lon': -180, 'min_lat': -60, 'max_lon': -30, 'max_lat': 85}
    epicenter_lat = max(americas_bbox['min_lat'], min(americas_bbox['max_lat'], epicenter_lat))
    epicenter_lon = max(americas_bbox['min_lon'], min(americas_bbox['max_lon'], epicenter_lon))
    
    return epicenter_lat, epicenter_lon


def find_detecting_sensors(epicenter_lat, epicenter_lon):
    """
    Depremi algılayan sensörleri bul
    Maksimum algılama mesafesi: 500 km
    """
    MAX_DETECTION_DISTANCE = 500  # km
    detecting_sensors = []
    
    for sensor in SENSOR_LOCATIONS:
        distance = haversine_distance(
            epicenter_lat, epicenter_lon,
            sensor['latitude'], sensor['longitude']
        )
        if distance <= MAX_DETECTION_DISTANCE:
            detecting_sensors.append({
                'sensor': sensor,
                'distance': distance
            })
    
    # Eğer hiç sensör algılamadıysa, en yakın sensörü bul
    if not detecting_sensors:
        min_distance = float('inf')
        closest_sensor = None
        for sensor in SENSOR_LOCATIONS:
            distance = haversine_distance(
                epicenter_lat, epicenter_lon,
                sensor['latitude'], sensor['longitude']
            )
            if distance < min_distance:
                min_distance = distance
                closest_sensor = sensor
        detecting_sensors = [{'sensor': closest_sensor, 'distance': min_distance}]
    
    # Mesafeye göre sırala (en yakın ilk)
    detecting_sensors.sort(key=lambda x: x['distance'])
    closest_sensor = detecting_sensors[0]['sensor']
    min_distance = detecting_sensors[0]['distance']
    
    return closest_sensor, min_distance, detecting_sensors


def calculate_wave_analysis(distance_km):
    """
    P-dalga ve S-dalga varış sürelerini hesapla
    """
    P_WAVE_SPEED = 6.0  # P dalgası hızı (km/s)
    S_WAVE_SPEED = 3.5   # S dalgası hızı (km/s)
    P_DETECTION_TIME = 5.0  # P dalgasının algılanma süresi (saniye)
    
    p_wave_arrival_time = (distance_km / P_WAVE_SPEED)
    s_wave_arrival_time = (distance_km / S_WAVE_SPEED)
    early_warning_time = max(0, s_wave_arrival_time - P_DETECTION_TIME)
    
    return {
        'p_wave_speed_km_s': P_WAVE_SPEED,
        's_wave_speed_km_s': S_WAVE_SPEED,
        'p_wave_arrival_time_seconds': round(p_wave_arrival_time, 1),
        's_wave_arrival_time_seconds': round(s_wave_arrival_time, 1),
        'p_detection_time_seconds': P_DETECTION_TIME,
        'early_warning_time_seconds': round(early_warning_time, 1)
    }


def get_severity_and_actions(magnitude):
    """
    Deprem büyüklüğüne göre şiddet ve kritik aksiyonları belirle
    """
    if magnitude >= 7.0:
        severity = "ÇOK ŞİDDETLİ"
        critical_actions = [
            "Hemen güvenli bir yere sığının (masa altı, kapı kasası)",
            "Pencere ve camlardan uzak durun",
            "Bina dışındaysanız açık alana geçin, binalardan ve elektrik direklerinden uzak durun"
        ]
    elif magnitude >= 6.0:
        severity = "ŞİDDETLİ"
        critical_actions = [
            "Güvenli bir yere sığının (masa altı, sağlam mobilya yanı)",
            "Başınızı ve boynunuzu koruyun",
            "Sallanma durana kadar yerinizden kalkmayın"
        ]
    else:
        severity = "ORTA ŞİDDETLİ"
        critical_actions = [
            "Güvenli bir yere sığının",
            "Sallanmayı bekleyin",
            "Paniğe kapılmayın, sakin kalın"
        ]
    return severity, critical_actions


def simulate_earthquake(user_lat, user_lon, epicenter_lat=None, epicenter_lon=None):
    """
    Deprem simülasyonu üret ve erken uyarı hesaplamaları yap
    
    Args:
        user_lat: Kullanıcı konumu (latitude)
        user_lon: Kullanıcı konumu (longitude)
        epicenter_lat: Kullanıcı tarafından seçilen deprem merkez üssü (latitude) - opsiyonel
        epicenter_lon: Kullanıcı tarafından seçilen deprem merkez üssü (longitude) - opsiyonel
    
    Returns:
        Dictionary containing:
        - epicenter: {latitude, longitude}
        - magnitude: Deprem büyüklüğü (4.0-8.5)
        - sensor: Ana detection yapan sensör
        - all_sensors: Tüm 24 sensör konumu
        - detecting_sensors: Depremi algılayan tüm sensörler
        - user_location: {latitude, longitude}
        - distance_km: Sensörden depreme mesafe
        - wave_analysis: P-dalga ve S-dalga analizi
        - severity: Şiddet seviyesi
        - critical_actions: Kritik güvenlik aksiyonları
        - timestamp: Simülasyon zamanı
    """
    # Deprem merkez üssünü belirle
    if epicenter_lat is None or epicenter_lon is None:
        epicenter_lat, epicenter_lon = generate_random_epicenter(user_lat, user_lon)
    
    # Deprem büyüklüğü üret (4.0-8.5 arası)
    magnitude = round(random.uniform(4.0, 8.5), 1)
    
    # Depremi algılayan sensörleri bul
    closest_sensor, min_distance, all_detecting_sensors = find_detecting_sensors(epicenter_lat, epicenter_lon)
    
    # Dalga analizi yap
    wave_analysis = calculate_wave_analysis(min_distance)
    
    # Şiddet ve kritik aksiyonları belirle
    severity, critical_actions = get_severity_and_actions(magnitude)
    
    return {
        'epicenter': {
            'latitude': epicenter_lat,
            'longitude': epicenter_lon
        },
        'magnitude': magnitude,
        'sensor': {  # Ana detection sensörü
            'id': closest_sensor['id'],
            'name': closest_sensor['name'],
            'latitude': closest_sensor['latitude'],
            'longitude': closest_sensor['longitude'],
            'distance_to_epicenter_km': round(min_distance, 1)
        },
        'all_sensors': SENSOR_LOCATIONS,  # Tüm sensör konumları
        'detecting_sensors': [  # Detection yapan tüm sensörler
            {
                'id': ds['sensor']['id'],
                'name': ds['sensor']['name'],
                'latitude': ds['sensor']['latitude'],
                'longitude': ds['sensor']['longitude'],
                'distance_to_epicenter_km': round(ds['distance'], 1)
            }
            for ds in all_detecting_sensors
        ],
        'user_location': {
            'latitude': user_lat,
            'longitude': user_lon
        },
        'distance_km': round(min_distance, 1),  # Sensörden depreme mesafe
        'wave_analysis': wave_analysis,
        'severity': severity,
        'critical_actions': critical_actions,
        'timestamp': datetime.now().isoformat()
    }

