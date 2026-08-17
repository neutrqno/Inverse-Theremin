#!/usr/bin/env python3
"""Utility to display device information and test connectivity."""

import sys
import json
import socket
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from proximity_poller import DeviceRegistry, get_attic_speaker


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def show_device_info():
    """Display complete device information."""
    print_section("DEVICE INFORMATION")
    
    device = get_attic_speaker()
    if not device:
        print("No device information found!")
        return
    
    print(f"\nBasic Information:")
    print(f"  Name:           {device['name']}")
    print(f"  Location:       {device['location']}")
    print(f"  Model:          {device['model']}")
    print(f"  Device ID:      aaasa")
    
    print(f"\nNetwork Information:")
    print(f"  IP Address:     {device['ip']}")
    print(f"  MAC Address:    {device['mac']}")
    print(f"  Port (mDNS):    8008")
    
    print(f"\nSystem Information:")
    print(f"  Firmware:       {device['firmware']}")
    print(f"  Language:       {device['language']}")
    
    print(f"\nNotes:")
    print(f"  {device.get('notes', 'N/A')}")


def test_connectivity():
    """Test network connectivity to device."""
    print_section("CONNECTIVITY TEST")
    
    device = get_attic_speaker()
    if not device:
        print("No device information found!")
        return
    
    ip = device['ip']
    port = 8008
    
    print(f"\nTesting connection to {ip}:{port}...\n")
    
    # Test ping (ICMP)
    print(f"1. Testing ICMP (ping)...")
    result = socket.call(['ping', '-c', '1', ip] if sys.platform != 'win32' 
                        else ['ping', '-n', '1', ip])
    if result == 0:
        print("   ✓ Device is reachable")
    else:
        print("   ✗ Device is not reachable")
    
    # Test HTTP port
    print(f"\n2. Testing HTTP port (8008)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"   ✓ Port 8008 is open")
        else:
            print(f"   ✗ Port 8008 is closed")
    except Exception as e:
        print(f"   ✗ Error testing port: {e}")


def show_environment_vars():
    """Show environment variable configuration."""
    print_section("ENVIRONMENT VARIABLES")
    
    device = get_attic_speaker()
    if not device:
        print("No device information found!")
        return
    
    print(f"\nFor .env file:\n")
    print(f"GOOGLE_HOME_IP={device['ip']}")
    print(f"GOOGLE_HOME_NAME={device['name']}")
    print(f"GOOGLE_HOME_MAC={device['mac']}")
    print(f"GOOGLE_HOME_DEVICE_ID=aaasa")


def show_config_json():
    """Show configuration.json format."""
    print_section("CONFIG FILE FORMAT")
    
    device = get_attic_speaker()
    if not device:
        print("No device information found!")
        return
    
    config = {
        "sensor": {
            "source": "home_assistant",
            "home_assistant": {
                "url": f"http://{device['ip']}:8123",
                "token": "YOUR_TOKEN_HERE",
                "entity_id": "sensor.google_home_mini_proximity"
            },
            "google_home_direct": {
                "ip": device['ip'],
                "port": 8008,
                "device_name": device['name'],
                "device_id": "aaasa",
                "mac_address": device['mac']
            }
        }
    }
    
    print(f"\nFor config/default_config.json:\n")
    print(json.dumps(config, indent=2))


def show_registry():
    """Show complete device registry."""
    print_section("DEVICE REGISTRY")
    
    devices = DeviceRegistry.list_devices()
    
    if not devices:
        print("\nNo devices registered!")
        return
    
    print(f"\nRegistered Devices: {len(devices)}\n")
    
    for device_id, info in devices.items():
        print(f"Device ID: {device_id}")
        print(f"  Name:     {info['name']}")
        print(f"  IP:       {info['ip']}")
        print(f"  MAC:      {info['mac']}")
        print(f"  Location: {info['location']}")
        print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Google Home Mini device information and testing utility"
    )
    parser.add_argument(
        'command',
        nargs='?',
        default='info',
        choices=['info', 'test', 'env', 'config', 'registry', 'all'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    if args.command == 'info' or args.command == 'all':
        show_device_info()
    
    if args.command == 'test' or args.command == 'all':
        test_connectivity()
    
    if args.command == 'env' or args.command == 'all':
        show_environment_vars()
    
    if args.command == 'config' or args.command == 'all':
        show_config_json()
    
    if args.command == 'registry' or args.command == 'all':
        show_registry()
    
    print("\n")


if __name__ == '__main__':
    main()
