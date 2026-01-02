"""
Runtime System
Main runtime orchestrator that integrates all pipeline components.

Author: Fikret Ahiskali - Concurrency & Runtime Pipeline
"""

import time
import signal
import sys
from typing import List
from datasources.base_source import DataSource
from .data_source_manager import DataSourceManager
from .event_pipeline import EventPipeline
from processing import log_message


class RuntimeSystem:
    """
    Main runtime system that orchestrates the entire SDEWS pipeline.
    """
    
    def __init__(
        self,
        data_sources: List[DataSource] = None,
        fetch_interval: int = 60,
        num_consumers: int = 3
    ):
        """Initialize Runtime System."""
        self.source_manager = DataSourceManager(
            data_sources=data_sources,
            fetch_interval=fetch_interval
        )
        
        self.pipeline = EventPipeline(num_consumers=num_consumers)
        
        self.running = False
        self.start_time = None
        self.cycle_count = 0
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        log_message("RuntimeSystem initialized", "INFO")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        log_message(f"Received signal {signum}, shutting down gracefully...", "INFO")
        self.stop()
        sys.exit(0)
    
    def add_data_source(self, source: DataSource):
        """Add a data source to the system."""
        self.source_manager.add_source(source)
    
    def start(self, continuous: bool = True):
        """Start the runtime system."""
        if self.running:
            log_message("Runtime system already running", "WARNING")
            return
        
        self.running = True
        self.start_time = time.time()
        
        log_message("=" * 60, "INFO")
        log_message("SDEWS Runtime System Starting", "INFO")
        log_message("=" * 60, "INFO")
        
        self.pipeline.start_consumers()
        
        if continuous:
            self._run_continuous()
        else:
            self._run_once()
    
    def _run_once(self):
        """Run a single fetch-process cycle."""
        log_message("Running single fetch-process cycle", "INFO")
        
        try:
            self.source_manager.fetch_all_sources()
            events = self.source_manager.get_events()
            
            if events:
                for event in events:
                    self.pipeline.add_events(event)
                
                log_message(f"Added {len(events)} event batches to pipeline", "INFO")
                # Timeout ile bekle (maksimum 60 saniye)
                self.pipeline.wait_for_completion(timeout=60.0)
                
                results = self.pipeline.get_results()
                self._display_results(results)
            else:
                log_message("No events fetched this cycle", "INFO")
            
            self.cycle_count += 1
            
        except Exception as e:
            log_message(f"Error in fetch-process cycle: {str(e)}", "ERROR")
        
        finally:
            # --once modunda consumer thread'leri hemen durdur
            # Böylece sürekli log mesajları üretilmez
            self.running = False
            self.pipeline.stop_consumers()
            self.stop()
    
    def _run_continuous(self):
        """Run continuous fetch-process cycles."""
        log_message("Starting continuous operation mode", "INFO")
        log_message("Press Ctrl+C to stop", "INFO")
        
        try:
            while self.running:
                try:
                    self.source_manager.fetch_all_sources()
                    events = self.source_manager.get_events()
                    
                    if events:
                        for event in events:
                            self.pipeline.add_events(event, block=False)
                        
                        log_message(f"Cycle {self.cycle_count}: Added {len(events)} event batches", "INFO")
                    
                    results = self.pipeline.get_results()
                    if results:
                        self._display_results(results)
                    
                    if self.cycle_count % 5 == 0:
                        self._display_status()
                    
                    self.cycle_count += 1
                    
                    time.sleep(self.source_manager.fetch_interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    log_message(f"Error in main loop: {str(e)}", "ERROR")
                    time.sleep(5)
                    
        finally:
            self.stop()
    
    def _display_results(self, results: List[dict]):
        """Display processing results."""
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
    
    def _display_status(self):
        """Display current system status."""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        source_status = self.source_manager.get_status()
        pipeline_stats = self.pipeline.get_statistics()
        
        log_message("=" * 60, "INFO")
        log_message("SYSTEM STATUS", "INFO")
        log_message("=" * 60, "INFO")
        log_message(f"Uptime: {uptime:.0f} seconds", "INFO")
        log_message(f"Cycles completed: {self.cycle_count}", "INFO")
        log_message(f"Data Sources: {source_status['source_count']}", "INFO")
        log_message(f"Processed events: {pipeline_stats['processed_count']}", "INFO")
        log_message(f"Errors: {pipeline_stats['error_count']}", "INFO")
        log_message("=" * 60, "INFO")
    
    def stop(self):
        """Stop the runtime system gracefully."""
        if not self.running:
            return
        
        log_message("Stopping RuntimeSystem...", "INFO")
        self.running = False
        
        self.pipeline.stop_consumers()
        
        self._display_status()
        
        log_message("=" * 60, "INFO")
        log_message("SDEWS Runtime System Stopped", "INFO")
        log_message("=" * 60, "INFO")
    
    def get_status(self) -> dict:
        """Get comprehensive system status."""
        return {
            'running': self.running,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'cycle_count': self.cycle_count,
            'source_manager': self.source_manager.get_status(),
            'pipeline': self.pipeline.get_statistics()
        }
