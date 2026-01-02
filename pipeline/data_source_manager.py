"""
Data Source Manager
Manages multiple data sources and fetches data concurrently.

Author: Fikret Ahiskali - Concurrency & Runtime Pipeline
"""

import threading
import queue
import time
from typing import List, Dict, Any
from datasources.base_source import DataSource
from processing import log_message


class DataSourceManager:
    """
    Manages multiple data sources and fetches data concurrently using threading.
    """
    
    def __init__(self, data_sources: List[DataSource] = None, fetch_interval: int = 60):
        """
        Initialize Data Source Manager.
        
        Args:
            data_sources: List of DataSource instances to manage
            fetch_interval: Interval in seconds between fetch cycles
        """
        self.data_sources = data_sources or []
        self.fetch_interval = fetch_interval
        self.event_queue = queue.Queue()
        self.running = False
        self.threads = []
        self.lock = threading.Lock()
        
        log_message(f"DataSourceManager initialized with {len(self.data_sources)} sources", "INFO")
    
    def add_source(self, source: DataSource):
        """Add a new data source to the manager."""
        with self.lock:
            self.data_sources.append(source)
            log_message(f"Added data source: {source.__class__.__name__}", "INFO")
    
    def _fetch_from_source(self, source: DataSource):
        """
        Fetch data from a single source and put it in the queue.
        """
        source_name = source.__class__.__name__
        start_time = time.time()
        try:
            # Log mesajını sadece yavaş kaynaklar için göster (performans için)
            if 'OpenWeather' in source_name or 'Flood' in source_name:
                log_message(f"Fetching data from {source_name}...", "INFO")
            
            data = source.fetch_and_parse()
            elapsed = time.time() - start_time
            
            if data:
                self.event_queue.put({
                    'source': source_name,
                    'data': data,
                    'timestamp': time.time()
                })
                # Sadece önemli kaynaklar için detaylı log
                if elapsed > 2.0 or len(data) > 50:
                    log_message(f"✓ {source_name}: {len(data) if isinstance(data, list) else 1} items in {elapsed:.2f}s", "INFO")
            else:
                if elapsed > 1.0:
                    log_message(f"No data from {source_name} (took {elapsed:.2f}s)", "WARNING")
                
        except Exception as e:
            elapsed = time.time() - start_time
            log_message(f"✗ {source_name} failed after {elapsed:.2f}s: {str(e)}", "ERROR")
    
    def fetch_all_sources(self):
        """Fetch data from all sources concurrently using threading."""
        threads = []
        
        with self.lock:
            sources = self.data_sources.copy()
        
        if not sources:
            log_message("No data sources configured", "WARNING")
            return
        
        start_time = time.time()
        log_message(f"Starting concurrent fetch from {len(sources)} sources", "INFO")
        
        for source in sources:
            thread = threading.Thread(
                target=self._fetch_from_source,
                args=(source,),
                name=f"Fetch-{source.__class__.__name__}"
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Thread timeout'ları optimize et - hızlı API'ler için daha kısa timeout
        # Yavaş API'ler için daha uzun timeout (OpenWeather, Flood gibi)
        for thread in threads:
            # Thread ismine göre timeout belirle
            thread_name = thread.name.lower()
            if 'openweather' in thread_name or 'flood' in thread_name:
                timeout = 20  # Yavaş API'ler için 20 saniye
            elif 'eonet' in thread_name:
                timeout = 15  # EONET için 15 saniye
            else:
                timeout = 10  # Diğerleri için 10 saniye
            
            thread.join(timeout=timeout)
            if thread.is_alive():
                log_message(f"Thread {thread.name} timed out after {timeout}s", "WARNING")
        
        total_time = time.time() - start_time
        log_message(f"All fetch operations completed in {total_time:.2f}s", "INFO")
    
    def get_events(self, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """Get all events from the queue."""
        events = []
        
        try:
            while not self.event_queue.empty():
                event = self.event_queue.get(timeout=timeout)
                events.append(event)
        except queue.Empty:
            pass
        
        return events
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the manager."""
        with self.lock:
            return {
                'running': self.running,
                'source_count': len(self.data_sources),
                'queue_size': self.event_queue.qsize(),
                'fetch_interval': self.fetch_interval,
                'sources': [src.__class__.__name__ for src in self.data_sources]
            }
