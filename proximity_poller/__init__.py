"""Proximity sensor polling module for Inverse Theremin."""

from .sensor_manager import SensorManager, SensorSource
from .home_assistant_client import HomeAssistantClient
from .google_home_api import GoogleHomeAPI
from .device_registry import DeviceRegistry, get_attic_speaker, get_all_devices

__all__ = [
    "SensorManager",
    "SensorSource",
    "HomeAssistantClient",
    "GoogleHomeAPI",
    "DeviceRegistry",
    "get_attic_speaker",
    "get_all_devices",
]
