"""Unified sensor manager for proximity polling."""

import logging
import threading
import time
from typing import Optional, Callable, List
from enum import Enum

from .home_assistant_client import HomeAssistantClient
from .google_home_api import GoogleHomeAPI

logger = logging.getLogger(__name__)


class SensorSource(Enum):
    """Available proximity sensor sources."""
    HOME_ASSISTANT = "home_assistant"
    GOOGLE_HOME_DIRECT = "google_home_direct"


class SensorManager:
    """
    Unified manager for proximity sensor polling.
    
    Supports multiple sensor sources and handles polling in a background thread.
    """
    
    def __init__(self, 
                 source: SensorSource = SensorSource.HOME_ASSISTANT,
                 poll_interval_ms: int = 50,
                 timeout_ms: int = 5000):
        """
        Initialize sensor manager.
        
        Args:
            source: Which sensor source to use
            poll_interval_ms: Polling interval in milliseconds
            timeout_ms: Request timeout in milliseconds
        """
        self.source = source
        self.poll_interval = poll_interval_ms / 1000.0  # Convert to seconds
        self.timeout = timeout_ms / 1000.0
        
        self.client: Optional[object] = None
        self._current_value: Optional[float] = None
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[float], None]] = []
        self._lock = threading.Lock()
    
    def initialize(self, config: dict) -> bool:
        """
        Initialize the sensor client based on configuration.
        
        Args:
            config: Configuration dict with sensor settings
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.source == SensorSource.HOME_ASSISTANT:
                ha_config = config.get('home_assistant', {})
                self.client = HomeAssistantClient(
                    url=ha_config.get('url', 'http://localhost:8123'),
                    token=ha_config.get('token', ''),
                    entity_id=ha_config.get('entity_id', 'sensor.google_home_mini_proximity')
                )
                
                if not self.client.is_connected():
                    logger.error("Cannot connect to Home Assistant")
                    return False
                    
            elif self.source == SensorSource.GOOGLE_HOME_DIRECT:
                gh_config = config.get('google_home_direct', {})
                self.client = GoogleHomeAPI(
                    ip=gh_config.get('ip', '192.168.1.100'),
                    port=gh_config.get('port', 8008)
                )
                
                if not self.client.is_reachable():
                    logger.error("Cannot reach Google Home device")
                    return False
            
            logger.info(f"Sensor manager initialized with source: {self.source.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize sensor: {e}")
            return False
    
    def start_polling(self):
        """Start the polling thread."""
        if self._polling:
            logger.warning("Polling already started")
            return
        
        if self.client is None:
            logger.error("Sensor not initialized")
            return
        
        self._polling = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        logger.info("Proximity polling started")
    
    def stop_polling(self):
        """Stop the polling thread."""
        self._polling = False
        if self._poll_thread:
            self._poll_thread.join(timeout=2.0)
        logger.info("Proximity polling stopped")
    
    def _poll_loop(self):
        """Main polling loop (runs in background thread)."""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self._polling:
            try:
                proximity = self.client.get_proximity(timeout=self.timeout)
                
                if proximity is not None:
                    with self._lock:
                        self._current_value = proximity
                    consecutive_errors = 0
                    
                    # Trigger callbacks
                    for callback in self._callbacks:
                        try:
                            callback(proximity)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(
                            f"Too many consecutive errors ({consecutive_errors}), stopping polling"
                        )
                        self._polling = False
                        break
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                consecutive_errors += 1
                time.sleep(self.poll_interval)
    
    def get_current_value(self) -> Optional[float]:
        """Get the current proximity value."""
        with self._lock:
            return self._current_value
    
    def register_callback(self, callback: Callable[[float], None]):
        """
        Register a callback to be called when new proximity data arrives.
        
        Args:
            callback: Function that takes proximity value as parameter
        """
        self._callbacks.append(callback)
        logger.debug(f"Registered callback, total: {len(self._callbacks)}")
    
    def unregister_callback(self, callback: Callable[[float], None]):
        """Unregister a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.debug(f"Unregistered callback, total: {len(self._callbacks)}")
    
    @property
    def is_polling(self) -> bool:
        """Check if polling is active."""
        return self._polling
