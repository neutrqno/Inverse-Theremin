"""Device registry and information for known Google Home devices."""

from typing import Dict, Optional


class DeviceRegistry:
    """Registry of known Google Home devices."""
    
    DEVICES = {
        "aaasa": {
            "name": "Attic speaker",
            "ip": "192.168.29.156",
            "mac": "48:D6:D5:DA:AC:39",
            "location": "Attic",
            "model": "Google Home Mini Gen 2",
            "firmware": "540761",
            "language": "en-US",
            "notes": "Primary device for Inverse Theremin"
        }
    }
    
    @classmethod
    def get_device(cls, device_id: str) -> Optional[Dict]:
        """Get device information by ID."""
        return cls.DEVICES.get(device_id)
    
    @classmethod
    def get_device_by_ip(cls, ip: str) -> Optional[tuple]:
        """Get device ID and info by IP address."""
        for device_id, info in cls.DEVICES.items():
            if info.get("ip") == ip:
                return (device_id, info)
        return None
    
    @classmethod
    def get_device_by_mac(cls, mac: str) -> Optional[tuple]:
        """Get device ID and info by MAC address."""
        for device_id, info in cls.DEVICES.items():
            if info.get("mac") == mac:
                return (device_id, info)
        return None
    
    @classmethod
    def list_devices(cls) -> Dict:
        """List all known devices."""
        return cls.DEVICES.copy()
    
    @classmethod
    def add_device(cls, device_id: str, info: Dict):
        """Register a new device."""
        cls.DEVICES[device_id] = info
    
    @classmethod
    def get_default_device(cls) -> Optional[tuple]:
        """Get the first/default device."""
        if cls.DEVICES:
            device_id = next(iter(cls.DEVICES))
            return (device_id, cls.DEVICES[device_id])
        return None
    
    @classmethod
    def get_device_ip(cls, device_id: str) -> Optional[str]:
        """Get IP address for a device."""
        device = cls.get_device(device_id)
        return device.get("ip") if device else None
    
    @classmethod
    def get_device_name(cls, device_id: str) -> Optional[str]:
        """Get friendly name for a device."""
        device = cls.get_device(device_id)
        return device.get("name") if device else None


# Export convenience functions
def get_attic_speaker():
    """Get the Attic speaker configuration."""
    return DeviceRegistry.get_device("aaasa")


def get_all_devices():
    """Get all registered devices."""
    return DeviceRegistry.list_devices()


def get_device_by_ip(ip: str):
    """Find device by IP address."""
    return DeviceRegistry.get_device_by_ip(ip)


def get_device_by_mac(mac: str):
    """Find device by MAC address."""
    return DeviceRegistry.get_device_by_mac(mac)
