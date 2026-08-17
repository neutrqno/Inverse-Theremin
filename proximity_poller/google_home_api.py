"""Direct Google Home API client for proximity sensing (experimental)."""

import logging
import socket
import struct
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleHomeAPI:
    """
    Direct Google Home API client for proximity sensing.
    
    Note: This is experimental. Requires reverse-engineered knowledge of
    the internal proximity sensor protocol. The preferred method is using
    Home Assistant.
    """
    
    # Known Google Home Mini device information
    KNOWN_DEVICES = {
        "aaasa": {
            "name": "Attic speaker",
            "ip": "192.168.29.156",
            "mac": "48:D6:D5:DA:AC:39",
            "location": "Attic",
            "model": "Google Home Mini Gen 2",
            "firmware": "540761",
            "language": "en-US"
        }
    }
    
    def __init__(self, ip: str, port: int = 8008):
        """
        Initialize Google Home API client.
        
        Args:
            ip: IP address of the Google Home Mini
            port: MDNS port (default 8008)
        """
        self.ip = ip
        self.port = port
        self._last_value: Optional[float] = None
        self._last_update: Optional[datetime] = None
    
    def get_proximity(self, timeout: float = 5.0) -> Optional[float]:
        """
        Attempt to fetch proximity from device.
        
        Note: This method is experimental and may not work on all devices.
        Consider using Home Assistant instead.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Proximity value or None if unable to fetch
        """
        try:
            logger.warning(
                "Direct Google Home API is experimental. "
                "Consider using Home Assistant for more reliable access."
            )
            # Placeholder for actual implementation
            # Would require reverse-engineered protocol knowledge
            return None
        except Exception as e:
            logger.error(f"Failed to get proximity: {e}")
            return None
    
    def is_reachable(self, timeout: float = 2.0) -> bool:
        """Check if the Google Home device is reachable."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.ip, self.port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Reachability check failed: {e}")
            return False
    
    @property
    def last_value(self) -> Optional[float]:
        """Get the last proximity value read."""
        return self._last_value
    
    @property
    def last_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the last update."""
        return self._last_update


class ProximitySensorProtocol:
    """
    Helper class for proximity sensor protocol handling.
    
    This contains utilities for working with the ultrasonic proximity
    sensor data format.
    """
    
    # Common proximity sensor value ranges
    RANGE_MIN = 0
    RANGE_MAX = 255
    
    # Typical distance ranges (cm) - device specific
    DISTANCE_MIN_CM = 5
    DISTANCE_MAX_CM = 200
    
    @staticmethod
    def normalize_value(raw: float, min_val: float = RANGE_MIN, 
                       max_val: float = RANGE_MAX) -> float:
        """Normalize raw proximity value to 0-255 range."""
        if max_val <= min_val:
            return 0.0
        normalized = ((raw - min_val) / (max_val - min_val)) * 255
        return max(0, min(255, normalized))
    
    @staticmethod
    def parse_proximity_bytes(data: bytes) -> Optional[float]:
        """Parse proximity value from raw sensor bytes."""
        if len(data) < 2:
            return None
        try:
            # Common format: 2-byte little-endian value
            value = struct.unpack('<H', data[:2])[0]
            return float(value)
        except struct.error:
            return None
