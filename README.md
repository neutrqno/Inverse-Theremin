# Inverse Theremin: Ultrasonic Proximity Mapping

Turn your Google Home Mini into a MIDI controller by hacking its proximity sensor.

## Overview

The Google Home Mini (especially Gen 2) uses ultrasound to detect proximity for LED control. This project intercepts that proximity data and maps it to MIDI Control Change (CC) messages, allowing you to modulate synthesizers in real-time using hand gestures.

## How It Works

1. **Proximity Detection**: Poll the Google Home Mini's internal proximity sensor via Home Assistant or direct API
2. **Distance Mapping**: Convert proximity values (0-255) to MIDI CC values
3. **MIDI Output**: Send CC messages over USB/network to your DAW (Ableton, FL Studio, etc.)
4. **Real-time Control**: Move your hand to modulate effects like filter cutoff, reverb, etc.

## Project Structure

```
inverse-theremin/
├── docs/                          # Documentation
│   ├── SETUP.md                  # Detailed setup instructions
│   └── TROUBLESHOOTING.md        # Common issues and solutions
├── proximity_poller/              # Core proximity sensing
│   ├── __init__.py
│   ├── home_assistant_client.py  # Home Assistant API integration
│   ├── google_home_api.py        # Direct Google Home API access
│   └── sensor_manager.py         # Unified sensor interface
├── midi_mapper/                   # MIDI mapping and output
│   ├── __init__.py
│   ├── midi_controller.py        # MIDI CC output logic
│   ├── value_processor.py        # Distance-to-MIDI conversion
│   └── filters.py                # Smoothing and filtering
├── config/                        # Configuration files
│   ├── default_config.json       # Default settings
│   └── device_profiles.json      # Device-specific profiles
├── main.py                        # Entry point
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variables template
```

## Quick Start

### Prerequisites
- Python 3.8+
- Google Home Mini (Gen 2 recommended)
- DAW with MIDI input support (Ableton, FL Studio, etc.)
- USB MIDI interface or network MIDI routing

### Installation

1. Clone/download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your setup (see `docs/SETUP.md`)
4. Run the main script:
   ```bash
   python main.py
   ```

## Configuration

Edit `config/default_config.json` to customize:
- Proximity sensor source (Home Assistant or direct API)
- MIDI output device/port
- Mapping curves (linear, exponential, logarithmic)
- Smoothing/filtering parameters



## API Documentation

See `docs/` for detailed API docs on:
- `ProximityPoller` - Interface for sensor data
- `MIDIController` - MIDI output handling
- `ValueProcessor` - Distance-to-MIDI conversion

## Troubleshooting

See `docs/TROUBLESHOOTING.md` for common issues:
- Proximity sensor not detected
- MIDI messages not reaching DAW
- Noisy/unstable values
- Home Assistant connection issues

## Contributing

Contributions welcome! Areas for enhancement:
- Support for additional Google Home devices
- Web UI for configuration
- Recording and playback of proximity gestures
- Machine learning for gesture recognition

## License

MIT License

## Disclaimer

This project involves accessing internal APIs and sensors. Use at your own risk and ensure compliance with your device's terms of service.
