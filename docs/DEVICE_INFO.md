# Google Home Mini Device Information

This document contains the detailed specifications and configuration for your Google Home Mini.

## Device Details

### Basic Information
- **Name:** Attic speaker
- **Device ID:** aaasa
- **Location:** Attic
- **Model:** Google Home Mini Gen 2

### Network Information
- **IP Address:** 192.168.29.156
- **MAC Address:** 48:D6:D5:DA:AC:39
- **Wi-Fi Network:** jio_ub12
- **Port (mDNS):** 8008
- **Port (API):** 8008

### System Information
- **System Firmware Version:** 540761
- **Cast Firmware Version:** 578.540761
- **Language:** en-US

## Hardware Specifications

### Audio
- **Speaker Type:** Attic speaker
- **Audio Output:** Mono speaker
- **Proximity Sensor:** Ultrasonic (40 kHz frequency typical)

### Power and Connectivity
- **Power Input:** 15W USB-C adapter
- **Connectivity:** Wi-Fi 802.11 b/g/n
- **Bluetooth:** Yes (for casting/setup)

## Proximity Sensor Characteristics

The Google Home Mini Gen 2 uses an ultrasonic proximity sensor for:
- LED brightness control (responds to hand proximity)
- Touch detection accuracy
- Wake-word confirmation (visual feedback)

### Typical Proximity Sensor Range
- **Minimum Distance:** 5-10 cm (sensor sensitivity threshold)
- **Maximum Distance:** 150-200 cm (reliable detection range)
- **Raw Value Range:** 0-255 (proximity units)
- **Sensor Frequency:** ~40 kHz ultrasonic
- **Response Time:** 50-100 ms

### Proximity Sensor Mapping

| Proximity Value | Distance | Typical State |
|-----------------|----------|---------------|
| 0-50            | >100 cm  | LEDs off, far away |
| 51-150          | 50-100 cm| Approaching, faint LEDs |
| 151-255         | <50 cm   | Close, bright LEDs |

## Integration Points

### Home Assistant
To access the proximity sensor via Home Assistant:

1. **Entity ID:** `sensor.google_home_mini_proximity`
2. **Entity Type:** Sensor
3. **Data Type:** Numeric (float)
4. **Unit of Measurement:** Proximity units
5. **Update Frequency:** Every 100-500 ms
6. **Availability:** Device must be connected to Wi-Fi

### Direct API Access (Experimental)
Raw HTTP/REST access to internal APIs:

```
Protocol: HTTP/mDNS
Host: 192.168.29.156
Port: 8008
Path: /api/chromecasts
```

**Note:** Direct API is not officially documented and may change with firmware updates.

## Configuration Usage

### In .env File
```env
GOOGLE_HOME_IP=192.168.29.156
GOOGLE_HOME_NAME=Attic speaker
GOOGLE_HOME_MAC=48:D6:D5:DA:AC:39
GOOGLE_HOME_DEVICE_ID=aaasa
```

### In default_config.json
```json
{
  "sensor": {
    "google_home_direct": {
      "ip": "192.168.29.156",
      "port": 8008,
      "device_name": "Attic speaker",
      "device_id": "aaasa",
      "mac_address": "48:D6:D5:DA:AC:39"
    }
  }
}
```

## Testing Connectivity

### Test Wi-Fi Reachability
```bash
ping 192.168.29.156
```

### Test mDNS/HTTP Access
```bash
# Windows
Test-NetConnection -ComputerName 192.168.29.156 -Port 8008

# macOS/Linux
nc -zv 192.168.29.156 8008
```

### Test Home Assistant Integration
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://192.168.29.156:8123/api/states/sensor.google_home_mini_proximity
```

## Proximity Sensor Troubleshooting

### Sensor Not Responding
1. **Restart Device:** Unplug for 30 seconds, plug back in
2. **Check Network:** Ensure connected to jio_ub12 Wi-Fi
3. **Check Home Assistant:** Verify entity exists in Home Assistant
4. **Update Firmware:** Check Google Home app for available updates

### Noisy/Unstable Proximity Values
1. **Environmental Interference:** Move device away from:
   - Other ultrasonic devices
   - Microwave ovens
   - High-frequency electronics
2. **Reflective Surfaces:** Proximity can bounce off walls
   - Try repositioning the device
   - Add soft materials nearby to dampen echoes

### Values Stuck at 0 or 255
1. **Sensor Calibration:** Restart device
2. **Firmware Issue:** Check firmware version and update if available
3. **Hardware Failure:** If persists, sensor may be defective

## Performance Notes

### Optimal Placement
- Keep at least 1 meter from walls (reduces reflections)
- Place on a stable surface
- Avoid enclosed spaces (better in open areas)
- Keep away from other wireless devices for best Wi-Fi signal

### Latency Considerations
- **Network Latency:** ~10-50 ms typical over Wi-Fi
- **Sensor Polling:** 50-100 ms intervals recommended
- **Total Latency:** ~100-200 ms from hand movement to MIDI output

## Device Firmware

### Current Firmware
- **Version:** 540761
- **Language:** en-US
- **Last Updated:** Check Google Home app

### Update Procedure
1. Open Google Home app
2. Select device settings
3. Check for updates
4. Apply if available

**Note:** Firmware updates can change proximity sensor behavior. Test after updates.

## Related Links

- Google Home Mini Support: https://support.google.com/googlenest/answer/7029379
- Home Assistant Cast Integration: https://www.home-assistant.io/integrations/cast/
- Google Cast Protocol Documentation: https://developers.google.com/cast

## Notes

- This device was configured for use as an Inverse Theremin MIDI controller
- The proximity sensor is not officially documented by Google
- Behavior may vary with firmware updates
- Direct API access is experimental and unsupported by Google
- Home Assistant integration is the recommended method for production use

---

**Last Updated:** 2026-08-17
**Device Status:** Active and configured
