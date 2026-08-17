"""Home Assistant API client for proximity sensor data."""

import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """Client for fetching proximity data from Home Assistant."""
    
    # Known Google Home Mini device information
    KNOWN_DEVICES = {
        "aaasa": {
            "name": "Attic speaker",
            "ip": "192.168.29.156",
            "mac": "48:D6:D5:DA:AC:39",
            "location": "Attic",
            "model": "Google Home Mini Gen 2"
        }
    }
    
    def __init__(self, url: str, token: str, entity_id: str):
        """
        Initialize Home Assistant client.
        
        Args:
            url: Home Assistant URL (e.g., http://localhost:8123)
            token: Long-lived access token
            entity_id: Entity ID of the proximity sensor (e.g., sensor.google_home_mini_proximity)
        """
        self.url = url.rstrip('/')
        self.token = token
        self.entity_id = entity_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        self._last_value: Optional[float] = None
        self._last_update: Optional[datetime] = None
        
    def get_proximity(self, timeout: float = 5.0) -> Optional[float]:
        """
        Fetch current proximity value from Home Assistant.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            Proximity value (typically 0-255) or None if error
        """
        try:
            url = f"{self.url}/api/states/{self.entity_id}"
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            state_str = data.get('state')
            
            if state_str is None:
                logger.warning(f"No state value for {self.entity_id}")
                return None
            
            # Try to convert to float
            proximity = float(state_str)
            self._last_value = proximity
            self._last_update = datetime.now()
            
            logger.debug(f"Proximity: {proximity}")
            return proximity
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Home Assistant request failed: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse proximity value: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if Home Assistant is accessible."""
        try:
            response = self.session.get(
                f"{self.url}/api/config",
                timeout=2.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    def get_sensor_state(self) -> Optional[Dict[str, Any]]:
        """Get full sensor state including attributes."""
        try:
            url = f"{self.url}/api/states/{self.entity_id}"
            response = self.session.get(url, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get sensor state: {e}")
            return None
    
    @property
    def last_value(self) -> Optional[float]:
        """Get the last proximity value read."""
        return self._last_value
    
    @property
    def last_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the last update."""
        return self._last_update
