# Google Home Mini Setup for Inverse Theremin

## Your Device

**Name:** Attic speaker  
**Location:** Attic  
**Model:** Google Home Mini Gen 2  
**Device ID:** aaasa

## Network Details

| Property | Value |
|----------|-------|
| IP Address | 192.168.29.156 |
| MAC Address | 48:D6:D5:DA:AC:39 |
| Wi-Fi Network | jio_ub12 |
| Firmware Version | 540761 |
| Language | en-US |

## Configuration Files

All configuration files have been pre-filled with your device details. You only need to add your Home Assistant token.

### Step 1: Create .env File

The `.env` file has already been created with your device information:

```env
# Home Assistant Configuration
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_token_here    # ← FILL THIS IN

# Google Home Mini Details (Pre-configured)
GOOGLE_HOME_IP=192.168.29.156
GOOGLE_HOME_NAME=Attic speaker
GOOGLE_HOME_MAC=48:D6:D5:DA:AC:39
GOOGLE_HOME_DEVICE_ID=aaasa
```

### Step 2: Add Home Assistant Token

1. Open Home Assistant UI at your HA IP address
2. Click your profile icon (bottom left)
3. Scroll down to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Name it "Inverse Theremin"
6. Copy the token
7. Paste it in `.env` file as `HOME_ASSISTANT_TOKEN`

### Step 3: Verify Configuration

Check that `config/default_config.json` has your device IP:

```json
{
  "sensor": {
    "google_home_direct": {
      "ip": "192.168.29.156",
      "device_name": "Attic speaker",
      "device_id": "aaasa",
      "mac_address": "48:D6:D5:DA:AC:39"
    }
  }
}
```

✓ Already configured!

## Quick Tests

### Test 1: Device Reachability

```bash
ping 192.168.29.156
```

Should respond with ping times (device is online).

### Test 2: Check Device Info

```bash
python utils/device_info.py info
```

Should display your device details.

### Test 3: Test Connectivity

```bash
python utils/device_info.py test
```

Should show connection status to the device.

### Test 4: View All Configuration

```bash
python utils/device_info.py all
```

Shows device info, connectivity test, environment variables, and config format.

## Home Assistant Setup

### Enable Google Cast Integration

1. Open Home Assistant UI
2. Go to **Settings → Devices & Services**
3. Click **Create Automation** (or search for Google Cast)
4. Select **Google Cast**
5. Choose your "Attic speaker" device
6. Confirm the integration

### Find Proximity Sensor Entity

1. Go to **Developer Tools → States** in Home Assistant
2. Search for "proximity" or "Attic"
3. You should see something like:
   - `sensor.attic_speaker_proximity`
   - `sensor.google_home_mini_proximity`
   - or similar

4. Update the entity_id in `.env` if different:
   ```env
   GOOGLE_HOME_ENTITY_ID=sensor.your_entity_id_here
   ```

## Testing Proximity Sensor

### Method 1: Home Assistant UI

1. In Home Assistant, go to Developer Tools → States
2. Find the proximity entity
3. Move your hand near the device
4. Watch the value change in real-time

### Method 2: Using Python

```python
from proximity_poller import SensorManager, SensorSource
import json

with open('config/default_config.json') as f:
    config = json.load(f)

manager = SensorManager(SensorSource.HOME_ASSISTANT)
manager.initialize(config['sensor'])
manager.start_polling()

import time
for i in range(10):
    value = manager.get_current_value()
    print(f"Proximity: {value}")
    time.sleep(0.5)
```

## MIDI Setup

Your MIDI configuration can stay default (CC 74 = Filter Cutoff):

```json
{
  "midi": {
    "output_device": 0,
    "channel": 1,
    "cc_number": 74,
    "max_value": 127
  }
}
```

To change which MIDI device is used:

1. List available MIDI devices:
   ```bash
   python -c "import mido; print(list(enumerate(mido.get_output_names())))"
   ```

2. Update `output_device` in `config/default_config.json` with the index

## Ready to Run!

Once you have:
1. ✓ Created `.env` with Home Assistant token
2. ✓ Verified device connectivity (ping works)
3. ✓ Set up Home Assistant Google Cast integration
4. ✓ Configured MIDI output device

You can start:

```bash
python main.py
```

Move your hand near the "Attic speaker" and watch the MIDI values update in your DAW!

## Troubleshooting

### Device not reachable

```bash
# Windows
Test-NetConnection -ComputerName 192.168.29.156 -Port 8008

# macOS/Linux
nc -zv 192.168.29.156 8008
```

### Proximity sensor not updating

1. Check Home Assistant entity exists
2. Restart the Google Home Mini (unplug 30 seconds)
3. Verify Wi-Fi connection (jio_ub12)
4. Check Home Assistant logs for errors

### MIDI not working

1. Verify MIDI device is enabled in DAW
2. Test MIDI with: `python examples/basic_usage.py basic`
3. Check CC number is supported by synth

## Device Specifications

- **Proximity Sensor Range:** 5-200 cm (reliable)
- **Sensor Frequency:** ~40 kHz (ultrasonic)
- **Update Rate:** 50-100 ms typical
- **Proximity Values:** 0-255 range
- **Latency:** ~100-200 ms (network + polling)

## Next Steps

1. Read `QUICKSTART.md` for full setup
2. Check `docs/SETUP.md` for detailed configuration
3. See `docs/TROUBLESHOOTING.md` for issues
4. Review `docs/DEVICE_INFO.md` for technical specs

---

**Status:** Device configuration complete! 🎵
