# Project Structure

## Overview

Inverse Theremin is a modular Python application that transforms a Google Home Mini's ultrasonic proximity sensor into a MIDI controller for music production.

```
inverse-theremin/
├── README.md                    # Main documentation
├── PROJECT_STRUCTURE.md         # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
│
├── main.py                      # Entry point - main application
├── run.sh                       # Linux/macOS quick start
├── run.ps1                      # Windows quick start
│
├── proximity_poller/            # Sensor data acquisition
│   ├── __init__.py
│   ├── sensor_manager.py        # Unified sensor interface
│   ├── home_assistant_client.py # Home Assistant integration
│   └── google_home_api.py       # Direct Google Home API (experimental)
│
├── midi_mapper/                 # MIDI output and mapping
│   ├── __init__.py
│   ├── midi_controller.py       # MIDI CC sending
│   ├── value_processor.py       # Proximity→MIDI conversion with curves
│   └── filters.py               # Smoothing, deadzone, debounce filters
│
├── config/                      # Configuration files
│   ├── default_config.json      # Main configuration
│   └── device_profiles.json     # Device-specific profiles
│
├── docs/                        # Documentation
│   ├── SETUP.md                 # Installation and setup guide
│   └── TROUBLESHOOTING.md       # Common issues and solutions
│
└── examples/                    # Usage examples
    └── basic_usage.py           # Example scripts
```

## Key Components

### Proximity Poller (`proximity_poller/`)

Handles real-time sensor data acquisition from the Google Home Mini.

**Main Classes:**
- `SensorManager` - Unified interface for sensor polling
- `HomeAssistantClient` - Home Assistant API integration
- `GoogleHomeAPI` - Direct API access (experimental)
- `ProximitySensorProtocol` - Protocol utilities

**Features:**
- Background thread polling
- Multiple sensor sources
- Event callbacks on new data
- Error handling and reconnection logic

### MIDI Mapper (`midi_mapper/`)

Converts proximity values to MIDI CC messages and sends them to your DAW.

**Main Classes:**
- `MIDIController` - MIDI message output
- `ValueProcessor` - Proximity-to-MIDI mapping with curves
- `SmoothingFilter` - Exponential smoothing
- `DeadzoneFilter` - Range-based filtering
- `DebounceFilter` - Jitter reduction
- `FilterChain` - Chain multiple filters

**Features:**
- Multiple mapping curves (linear, exponential, logarithmic, etc.)
- Real-time filtering
- MIDI device enumeration
- Support for various MIDI messages (CC, Note On/Off, Pitch Bend)

### Configuration (`config/`)

**default_config.json:**
- Sensor source selection
- Polling intervals
- MIDI device and CC mapping
- Curve selection
- Smoothing parameters
- Device-specific profiles

### Main Application (`main.py`)

`InverseThereminController` orchestrates the entire system:
1. Loads configuration
2. Initializes sensor and MIDI
3. Sets up filtering pipeline
4. Runs event loop processing proximity data

## Data Flow

```
Google Home Mini Sensor
        ↓
Home Assistant / Direct API
        ↓
SensorManager (poll loop)
        ↓
FilterChain (smoothing, deadzone, debounce)
        ↓
ValueProcessor (proximity → MIDI value)
        ↓
MIDIController (send CC message)
        ↓
DAW (Ableton, FL Studio, etc.)
```

## Usage Patterns

### Basic Usage

```python
from proximity_poller import SensorManager, SensorSource
from midi_mapper import MIDIController, ValueProcessor
import json

# Load config
with open('config/default_config.json') as f:
    config = json.load(f)

# Create sensor
sensor = SensorManager(source=SensorSource.HOME_ASSISTANT)
sensor.initialize(config['sensor'])
sensor.start_polling()

# Create MIDI
midi = MIDIController()
midi.initialize()

# Create processor
processor = ValueProcessor(**config['mapping'])

# Register callback
def on_proximity(value):
    midi_value = processor.process(value)
    midi.send_cc(74, midi_value)

sensor.register_callback(on_proximity)
```

### Advanced: Custom Curves

```python
from midi_mapper import ValueProcessor

# Exponential curve (favor far values)
processor = ValueProcessor(
    proximity_min=0,
    proximity_max=255,
    curve='exponential'
)

# Logarithmic curve (favor close values)
processor = ValueProcessor(
    proximity_min=0,
    proximity_max=255,
    curve='logarithmic'
)
```

### Advanced: Chained Filters

```python
from midi_mapper.filters import FilterChain, SmoothingFilter, DeadzoneFilter

chain = FilterChain()
chain.add_filter(DeadzoneFilter(min_threshold=20, max_threshold=240))
chain.add_filter(SmoothingFilter(factor=0.7))

# Apply all filters
filtered_value = chain.apply(raw_proximity)
```

## Configuration Examples

### Filter Cutoff (Common)

```json
{
  "midi": {"cc_number": 74},
  "mapping": {
    "proximity_min": 10,
    "proximity_max": 200,
    "curve": "exponential"
  }
}
```

### Reverb Wet/Dry

```json
{
  "midi": {"cc_number": 91},
  "mapping": {
    "proximity_min": 0,
    "proximity_max": 255,
    "curve": "linear"
  }
}
```

### Volume Control

```json
{
  "midi": {"cc_number": 7},
  "mapping": {
    "proximity_min": 50,
    "proximity_max": 255,
    "curve": "logarithmic"
  }
}
```

## Extension Points

### Add Custom Sensor Source

1. Create new class in `proximity_poller/`:
   ```python
   class CustomSensorClient:
       def get_proximity(self, timeout):
           # Implement sensor reading
           pass
   ```

2. Update `SensorManager.initialize()` to handle new source

### Add Custom Mapping Curve

1. Add to `MappingCurve` enum in `midi_mapper/value_processor.py`:
   ```python
   class MappingCurve(Enum):
       CUSTOM = "custom"
   ```

2. Add function to `_curve_functions()` map

### Add Custom Filter

1. Create new class inheriting from filter interface
2. Implement `apply()` or `should_update()` method
3. Add to `FilterChain` as needed

## Testing

Run examples:
```bash
python examples/basic_usage.py basic         # Full integration test
python examples/basic_usage.py smoothing     # Test smoothing filter
python examples/basic_usage.py curves        # View mapping curves
python examples/basic_usage.py cc            # Show MIDI CC reference
```

## Performance Considerations

- **Polling Rate**: Lower latency with `poll_interval_ms=25-50`
- **Smoothing**: Trade responsiveness for stability
- **Curves**: Exponential/logarithmic add minimal CPU
- **MIDI**: Only sends on value changes (smart update)

Typical CPU usage: <5% on modern systems

## Troubleshooting

See `docs/TROUBLESHOOTING.md` for:
- Connection issues
- Sensor not detecting
- MIDI not working
- Performance optimization

## Future Enhancements

- [ ] Web UI for live parameter adjustment
- [ ] Recording and playback of proximity gestures
- [ ] Multi-hand support
- [ ] Gesture recognition (swipe, tap, etc.)
- [ ] Support for other smart speakers (Google Home, Nest Hub)
- [ ] VST plugin wrapper
- [ ] Machine learning for gesture classification

## License

MIT License

## Support

1. Read README.md
2. Check docs/SETUP.md for setup
3. Check docs/TROUBLESHOOTING.md for issues
4. Enable DEBUG logging for detailed output
