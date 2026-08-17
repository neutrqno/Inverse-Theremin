# Setup Guide for Inverse Theremin

## Prerequisites

- Python 3.8 or higher
- Google Home Mini (Gen 2 recommended)
- DAW with MIDI input (Ableton Live, FL Studio, Logic Pro, Reaper, etc.)
- Network access to Google Home Mini
- (Optional) Home Assistant instance for sensor polling

## Installation

### 1. Clone the Repository

```bash
cd Inverse-theremin
```

### 2. Create Virtual Environment (Recommended)

```bash
# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Option A: Using Home Assistant (Recommended)

Home Assistant provides a stable, well-documented way to access the Google Home Mini's proximity sensor.

#### 1. Set up Home Assistant

If you don't have Home Assistant installed:

- Visit [Home Assistant Installation Guide](https://www.home-assistant.io/installation/)
- Choose your platform (Docker, Raspberry Pi OS, generic Linux, etc.)
- Follow the setup wizard

#### 2. Add Google Home Mini Integration

1. In Home Assistant UI, go to **Settings → Devices & Services → Create Automation**
2. Search for "Google Cast" and add the integration
3. Find your Google Home Mini and select it
4. It will create entities including proximity sensor (`sensor.google_home_mini_proximity` or similar)

#### 3. Generate Home Assistant Token

1. Go to Home Assistant UI
2. Click your profile icon (bottom left)
3. Scroll down to "Long-Lived Access Tokens"
4. Create a new token and copy it

#### 4. Configure Inverse Theremin

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env`:

```env
HOME_ASSISTANT_URL=http://192.168.29.156:8123
HOME_ASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GOOGLE_HOME_IP=192.168.29.156
GOOGLE_HOME_NAME=Attic speaker
GOOGLE_HOME_MAC=48:D6:D5:DA:AC:39
GOOGLE_HOME_DEVICE_ID=aaasa
```

Or edit `config/default_config.json`:

```json
{
  "sensor": {
    "source": "home_assistant",
    "home_assistant": {
      "url": "http://192.168.29.156:8123",
      "token": "YOUR_TOKEN_HERE",
      "entity_id": "sensor.google_home_mini_proximity"
    }
  }
}
```

**Your Google Home Mini:**
- **Name:** Attic speaker
- **IP Address:** 192.168.29.156
- **MAC Address:** 48:D6:D5:DA:AC:39
- **Device ID:** aaasa
- **Location:** Attic
- **Model:** Google Home Mini Gen 2
- **Firmware:** 540761

### Option B: Direct Google Home API (Experimental)

This method attempts direct communication with the Google Home Mini. Success varies by firmware version.

Edit `config/default_config.json`:

```json
{
  "sensor": {
    "source": "google_home_direct",
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

## MIDI Setup

### 1. Choose MIDI Output Device

List available MIDI outputs:

```bash
python -c "import mido; print(mido.get_output_names())"
```

Note the index or name of your target device (DAW, virtual port, MIDI interface, etc.).

### 2. Configure MIDI in default_config.json

```json
{
  "midi": {
    "output_device": 0,
    "channel": 1,
    "cc_number": 74,
    "min_value": 0,
    "max_value": 127
  }
}
```

**Common CC Numbers:**
- 74 - Filter Cutoff (Brightness)
- 91 - Reverb Wet/Dry
- 93 - Chorus Wet/Dry
- 71 - Resonance/Filter Q
- 7 - Volume
- 10 - Pan
- 1 - Modulation Wheel
- 64-69 - Sustain Pedal (0-63 = off, 64-127 = on)

### 3. Configure Mapping Curves

The `curve` parameter controls how proximity maps to MIDI values:

- **linear** - Direct 1:1 mapping (default)
- **exponential** - Favor far values (more control when hand is far)
- **logarithmic** - Favor close values (more control when hand is close)
- **quadratic** - Smooth acceleration
- **cubic** - Stronger acceleration
- **sqrt** - Square root mapping

Example - Using exponential curve for filter cutoff:

```json
{
  "mapping": {
    "proximity_min": 10,
    "proximity_max": 200,
    "curve": "exponential",
    "invert": false
  }
}
```

## DAW Setup

### Ableton Live

1. **Enable MIDI Input:**
   - Preferences → Link/MIDI → MIDI Ports
   - Set your MIDI device to "Track" and "Remote"

2. **Map the CC to a Control:**
   - Enable MIDI mapping (Cmd+M or Ctrl+M)
   - Click the parameter you want to control
   - Move your hand near the Google Home Mini

3. **Assign to Synth Parameter:**
   - Click the synth's filter cutoff, reverb wet, etc.
   - It will map to the CC value

### FL Studio

1. **Enable MIDI:**
   - Options → MIDI Settings
   - Select your MIDI device

2. **Enable Learning:**
   - Hold Shift and click a parameter
   - Move your hand to learn the mapping

### Other DAWs (Logic, Reaper, etc.)

- Look for MIDI Input settings
- Enable your MIDI device
- Enable MIDI learn mode on the parameter you want to control
- Move your hand to map

## Testing

### 1. Check Sensor Connection

```bash
python -c "
from proximity_poller import SensorManager, SensorSource
import json
with open('config/default_config.json') as f:
    config = json.load(f)
manager = SensorManager(SensorSource.HOME_ASSISTANT, poll_interval_ms=100)
manager.initialize(config.get('sensor', {}))
manager.start_polling()
import time
time.sleep(2)
print(f'Last value: {manager.get_current_value()}')
"
```

### 2. Check MIDI Output

```bash
python -c "
from midi_mapper import MIDIController
midi = MIDIController(0)
if midi.initialize():
    for i in range(128):
        midi.send_cc(74, i)
    print('MIDI test complete')
"
```

### 3. Run Full System

```bash
python main.py
```

Move your hand near the Google Home Mini and watch the MIDI values change in your DAW.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

## Advanced Configuration

### Smoothing

The `smoothing` filter reduces jitter:

```json
{
  "processing": {
    "smoothing": {
      "enabled": true,
      "factor": 0.7
    }
  }
}
```

Lower factor = more smoothing (less responsive)
Higher factor = more responsive (more jitter)

### Deadzone

Ignore values outside a certain range:

```json
{
  "processing": {
    "deadzone": {
      "enabled": true,
      "min_threshold": 20,
      "max_threshold": 240
    }
  }
}
```

## Performance Optimization

- Increase `poll_interval_ms` (default 50ms) to reduce CPU usage
- Decrease `poll_interval_ms` for lower latency (minimum 10ms recommended)
- Adjust `smoothing.factor` for your use case

## Next Steps

- Explore different MIDI profiles in `config/device_profiles.json`
- Create custom profiles for different synths
- Experiment with different proximity ranges for your space
- Consider creating presets for different use cases

## Support

For issues:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`
3. Check logs in `logs/inverse_theremin.log`
