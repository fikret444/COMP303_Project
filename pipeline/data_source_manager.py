# DataSourceManager - Veri kaynaklarını paralel olarak yönetir
# Her kaynak için thread oluşturup aynı anda veri çeker

import threading
import queue
import time
from typing import List, Dict, Any
from datasources.base_source import DataSource
from processing import log_message


class DataSourceManager:
    
    TIMEOUT_SLOW = 20
    TIMEOUT_MEDIUM = 15
    TIMEOUT_FAST = 10
    
    def __init__(self, data_sources: List[DataSource] = None, fetch_interval: int = 60):
        self.data_sources = data_sources or []
        self.fetch_interval = fetch_interval
        self.event_queue = queue.Queue()
        self.lock = threading.Lock()
        
        log_message(f"DataSourceManager: {len(self.data_sources)} kaynak hazır", "INFO")
    
    def add_source(self, source: DataSource):
        with self.lock:
            self.data_sources.append(source)
            log_message(f"Kaynak eklendi: {source.__class__.__name__}", "INFO")
    
    def _get_timeout_for_source(self, source_name: str) -> int:
        source_lower = source_name.lower()
        if 'openweather' in source_lower or 'flood' in source_lower:
            return self.TIMEOUT_SLOW
        elif 'eonet' in source_lower:
            return self.TIMEOUT_MEDIUM
        else:
            return self.TIMEOUT_FAST
    
    def _fetch_from_source(self, source: DataSource):
        source_name = source.__class__.__name__
        start_time = time.time()
        
        try:
            if 'OpenWeather' in source_name or 'Flood' in source_name:
                log_message(f"{source_name} verisi çekiliyor...", "INFO")
            
            data = source.fetch_and_parse()
            elapsed = time.time() - start_time
            
            if data:
                self.event_queue.put({
                    'source': source_name,
                    'data': data,
                    'timestamp': time.time()
                })
                
                data_count = len(data) if isinstance(data, list) else 1
                if elapsed > 2.0 or data_count > 50:
                    log_message(f"✓ {source_name}: {data_count} öğe ({elapsed:.2f}s)", "INFO")
            else:
                if elapsed > 1.0:
                    log_message(f"{source_name}: Veri yok ({elapsed:.2f}s)", "WARNING")
                    
        except Exception as e:
            elapsed = time.time() - start_time
            log_message(f"✗ {source_name} hata: {str(e)} ({elapsed:.2f}s)", "ERROR")
    
    def fetch_all_sources(self):
        with self.lock:
            sources = self.data_sources.copy()
        
        if not sources:
            log_message("Veri kaynağı bulunamadı", "WARNING")
            return
        
        log_message(f"{len(sources)} kaynaktan paralel veri çekiliyor...", "INFO")
        start_time = time.time()
        
        threads = []
        for source in sources:
            thread = threading.Thread(
                target=self._fetch_from_source,
                args=(source,),
                name=f"Fetch-{source.__class__.__name__}",
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            timeout = self._get_timeout_for_source(thread.name)
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                log_message(f"⚠ {thread.name} timeout ({timeout}s)", "WARNING")
        
        total_time = time.time() - start_time
        log_message(f"Tüm veri çekme işlemleri tamamlandı ({total_time:.2f}s)", "INFO")
    
    def get_events(self, timeout: float = 1.0) -> List[Dict[str, Any]]:
        events = []
        
        try:
            while not self.event_queue.empty():
                event = self.event_queue.get(timeout=timeout)
                events.append(event)
        except queue.Empty:
            pass
        
        return events
    
    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'source_count': len(self.data_sources),
                'queue_size': self.event_queue.qsize(),
                'fetch_interval': self.fetch_interval,
                'sources': [src.__class__.__name__ for src in self.data_sources]
            }
