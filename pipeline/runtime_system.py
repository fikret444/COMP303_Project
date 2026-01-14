import time
import signal
import sys
from typing import List
from datasources.base_source import DataSource
from .data_source_manager import DataSourceManager
from .event_pipeline import EventPipeline
from processing import log_message


class RuntimeSystem:

    def __init__(self, data_sources: List[DataSource] = None, fetch_interval: int = 60, num_consumers: int = 3):
        self.source_manager = DataSourceManager(data_sources=data_sources, fetch_interval=fetch_interval)
        self.pipeline = EventPipeline(num_consumers=num_consumers)
        self.running = False
        self.start_time = None
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        log_message("RuntimeSystem initialized", "INFO")
    
    def _signal_handler(self, signum, frame):
        log_message(f"Received signal {signum}, shutting down...", "INFO")
        self.stop()
        sys.exit(0)
    
    def add_data_source(self, source: DataSource):
        self.source_manager.add_source(source)
    
    def start(self):
        if self.running:
            log_message("Runtime sistemi zaten çalışıyor", "WARNING")
            return
        
        self.running = True
        self.start_time = time.time()
        
        log_message("=" * 60, "INFO")
        log_message("SDEWS Runtime System Başlatılıyor", "INFO")
        log_message("=" * 60, "INFO")
        
        self.pipeline.start_consumers()
        
        try:
            self.source_manager.fetch_all_sources()
            events = self.source_manager.get_events()
            
            if events:
                for event in events:
                    self.pipeline.add_events(event)
                
                log_message(f"{len(events)} event batch pipeline'a eklendi", "INFO")
                self.pipeline.wait_for_completion(timeout=60.0)
                
                results = self.pipeline.get_results()
                self._display_results(results)
            else:
                log_message("Bu döngüde veri çekilemedi", "INFO")
            
        except Exception as e:
            log_message(f"Veri çekme-işleme döngüsünde hata: {str(e)}", "ERROR")
        finally:
            self.running = False
            self.pipeline.stop_consumers()
            self.stop()
    
    def _display_results(self, results: List[dict]):
        log_message("=" * 60, "INFO")
        log_message("PROCESSING RESULTS", "INFO")
        log_message("=" * 60, "INFO")
        
        for i, result in enumerate(results, 1):
            source = result.get('source', 'Unknown')
            success = result.get('success', False)
            
            if success:
                log_message(f"Result #{i} - {source}: SUCCESS", "INFO")
                
                if 'event_count' in result:
                    log_message(f"  Events processed: {result['event_count']}", "INFO")
                
                if 'stats' in result and result['stats']:
                    stats = result['stats']
                    log_message(f"  Statistics:", "INFO")
                    log_message(f"    - Total events: {stats.get('total_events', 0)}", "INFO")
                    log_message(f"    - Max magnitude: {stats.get('max_magnitude', 0):.2f}", "INFO")
                    log_message(f"    - Avg magnitude: {stats.get('avg_magnitude', 0):.2f}", "INFO")
                
                if 'filename' in result:
                    log_message(f"  Saved to: {result['filename']}", "INFO")
            else:
                error = result.get('error', 'Unknown error')
                log_message(f"Result #{i} - {source}: FAILED - {error}", "ERROR")
            
            log_message("-" * 60, "INFO")
    
    def stop(self):
        if not self.running:
            return
        
        log_message("RuntimeSystem durduruluyor...", "INFO")
        self.running = False
        self.pipeline.stop_consumers()
        
        log_message("=" * 60, "INFO")
        log_message("SDEWS Runtime System Durduruldu", "INFO")
        log_message("=" * 60, "INFO")
    
    def get_status(self) -> dict:
        return {
            'running': self.running,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'source_manager': self.source_manager.get_status(),
            'pipeline': self.pipeline.get_statistics()
        }
