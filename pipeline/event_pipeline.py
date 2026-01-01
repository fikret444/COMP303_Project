"""
Event Pipeline
Producer-Consumer pattern implementation for event processing.

Author: Fikret Ahiskali - Concurrency & Runtime Pipeline
"""

import threading
import queue
import time
from typing import Dict, Any, Callable, List
from processing import (
    log_message,
    clean_usgs_earthquake_events,
    save_events_to_json,
    compute_basic_stats
)


class EventPipeline:
    """
    Event processing pipeline using Producer-Consumer pattern.
    """
    
    def __init__(self, num_consumers: int = 3, max_queue_size: int = 100):
        """Initialize Event Pipeline."""
        self.input_queue = queue.Queue(maxsize=max_queue_size)
        self.output_queue = queue.Queue()
        self.num_consumers = num_consumers
        self.consumer_threads = []
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        self.lock = threading.Lock()
        
        self.processors = {
            'USGSEarthquakeSource': self._process_earthquake_events,
            'OpenWeatherSource': self._process_weather_events,
            'default': self._process_generic_events
        }
        
        log_message(f"EventPipeline initialized with {num_consumers} consumers", "INFO")
    
    def _process_earthquake_events(self, events: List[Any], source_name: str) -> Dict[str, Any]:
        """Process earthquake events from USGS. Accepts RawEarthquake objects or dictionaries."""
        try:
            # clean_usgs_earthquake_events now returns CleanedEarthquake objects
            cleaned_events = clean_usgs_earthquake_events(events)
            
            if cleaned_events:
                filename = f"earthquakes_{int(time.time())}.json"
                save_events_to_json(cleaned_events, filename)
                
                # Convert objects to dictionaries for stats computation if needed
                stats_events = [ev.toDictionary() if hasattr(ev, 'toDictionary') else ev for ev in cleaned_events]
                stats = compute_basic_stats(stats_events)
                
                return {
                    'success': True,
                    'source': source_name,
                    'event_count': len(cleaned_events),
                    'stats': stats,
                    'filename': filename
                }
            else:
                return {'success': False, 'source': source_name, 'error': 'No valid events'}
                
        except Exception as e:
            log_message(f"Error processing earthquake events: {str(e)}", "ERROR")
            return {'success': False, 'source': source_name, 'error': str(e)}
    
    def _process_weather_events(self, events: List[Any], source_name: str) -> Dict[str, Any]:
        """Process weather events from OpenWeather. Accepts Weather objects or dictionaries."""
        try:
            # events zaten bir liste, direkt kaydet
            if not events:
                return {'success': False, 'source': source_name, 'error': 'No weather events'}
            
            # Tüm weather verilerini tek bir dosyada topla
            from pathlib import Path
            from processing.storage import DATA_DIR
            from models import Weather
            import json
            
            # Thread-safe birleştirme için lock kullan
            with self.lock:
                weather_file = DATA_DIR / "weather_all.json"
                
                # Mevcut weather dosyasını oku (varsa)
                all_weather = []
                if weather_file.exists():
                    try:
                        with open(weather_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            if isinstance(existing_data, list):
                                # Convert dictionaries to Weather objects
                                for item in existing_data:
                                    if isinstance(item, dict):
                                        all_weather.append(Weather.fromDict(item))
                                    else:
                                        all_weather.append(item)
                    except:
                        pass
                
                # Yeni verileri ekle veya güncelle
                # Current weather verilerini şehir bazında güncelle
                # Forecast verilerini ise ekle (aynı şehir için birden fazla forecast olabilir)
                city_current_dict = {}
                forecast_list = []
                
                # Mevcut verileri ayır
                for item in all_weather:
                    # Handle both objects and dictionaries
                    item_dict = item.toDictionary() if hasattr(item, 'toDictionary') else item
                    if item_dict.get('type') == 'weather_forecast':
                        forecast_list.append(item)
                    else:
                        city = item_dict.get('location')
                        if city:
                            city_current_dict[city] = item
                
                # Yeni verileri işle
                for event in events:
                    # Convert to dictionary for checking
                    event_dict = event.toDictionary() if hasattr(event, 'toDictionary') else event
                    event_type = event_dict.get('type', 'weather')
                    city = event_dict.get('location')
                    
                    if event_type == 'weather_forecast':
                        # Forecast verilerini ekle
                        forecast_list.append(event)
                    elif city:
                        # Current weather verilerini güncelle
                        city_current_dict[city] = event
                
                # Tüm verileri birleştir
                all_weather = list(city_current_dict.values()) + forecast_list
                
                # Güncellenmiş veriyi kaydet
                save_events_to_json(all_weather, "weather_all.json")
            
            return {
                'success': True,
                'source': source_name,
                'event_count': len(events),
                'total_cities': len(city_current_dict),
                'data': events[0].toDictionary() if events and hasattr(events[0], 'toDictionary') else (events[0] if events else None),
                'filename': 'weather_all.json'
            }
            
        except Exception as e:
            log_message(f"Error processing weather events: {str(e)}", "ERROR")
            return {'success': False, 'source': source_name, 'error': str(e)}
    
    def _process_generic_events(self, events: Any, source_name: str) -> Dict[str, Any]:
        """Generic processor for unknown event types."""
        try:
            filename = f"{source_name}_{int(time.time())}.json"
            save_events_to_json(events if isinstance(events, list) else [events], filename)
            
            return {'success': True, 'source': source_name, 'filename': filename}
            
        except Exception as e:
            log_message(f"Error in generic processor: {str(e)}", "ERROR")
            return {'success': False, 'source': source_name, 'error': str(e)}
    
    def _consumer_worker(self, worker_id: int):
        """Consumer worker thread function."""
        log_message(f"Consumer worker {worker_id} started", "INFO")
        
        while self.running:
            try:
                event_data = self.input_queue.get(timeout=1.0)
                
                if event_data is None:
                    self.input_queue.task_done()
                    break
                
                source_name = event_data.get('source', 'unknown')
                data = event_data.get('data')
                
                log_message(f"Worker {worker_id} processing event from {source_name}", "INFO")
                
                processor = self.processors.get(source_name, self.processors['default'])
                result = processor(data, source_name)
                
                self.output_queue.put(result)
                
                with self.lock:
                    if result.get('success'):
                        self.processed_count += 1
                    else:
                        self.error_count += 1
                
                self.input_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                log_message(f"Worker {worker_id} error: {str(e)}", "ERROR")
                with self.lock:
                    self.error_count += 1
        
        log_message(f"Consumer worker {worker_id} stopped", "INFO")
    
    def start_consumers(self):
        """Start consumer worker threads."""
        if self.running:
            log_message("Consumers already running", "WARNING")
            return
        
        self.running = True
        self.processed_count = 0
        self.error_count = 0
        
        log_message(f"Starting {self.num_consumers} consumer workers", "INFO")
        
        for i in range(self.num_consumers):
            thread = threading.Thread(
                target=self._consumer_worker,
                args=(i,),
                name=f"Consumer-{i}",
                daemon=True
            )
            thread.start()
            self.consumer_threads.append(thread)
    
    def stop_consumers(self):
        """Stop consumer worker threads gracefully."""
        if not self.running:
            log_message("Consumers not running", "WARNING")
            return
        
        log_message("Stopping consumer workers...", "INFO")
        self.running = False
        
        for _ in range(self.num_consumers):
            self.input_queue.put(None)
        
        for thread in self.consumer_threads:
            thread.join(timeout=5)
        
        self.consumer_threads.clear()
        log_message("All consumer workers stopped", "INFO")
    
    def add_events(self, events: Dict[str, Any], block: bool = True, timeout: float = None):
        """Add events to the processing queue (Producer)."""
        try:
            self.input_queue.put(events, block=block, timeout=timeout)
            log_message(f"Added events from {events.get('source')} to processing queue", "INFO")
        except queue.Full:
            log_message("Processing queue is full, event dropped", "WARNING")
    
    def get_results(self, timeout: float = 0.1) -> List[Dict[str, Any]]:
        """Get processed results from output queue."""
        results = []
        
        try:
            while not self.output_queue.empty():
                result = self.output_queue.get(timeout=timeout)
                results.append(result)
        except queue.Empty:
            pass
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        with self.lock:
            return {
                'running': self.running,
                'processed_count': self.processed_count,
                'error_count': self.error_count,
                'input_queue_size': self.input_queue.qsize(),
                'output_queue_size': self.output_queue.qsize(),
                'num_consumers': self.num_consumers
            }
    
    def wait_for_completion(self, timeout: float = None):
        """Wait for all events in queue to be processed."""
        try:
            self.input_queue.join()
            log_message("All events processed", "INFO")
        except Exception as e:
            log_message(f"Error waiting for completion: {str(e)}", "ERROR")
