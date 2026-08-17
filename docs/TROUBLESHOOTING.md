# Troubleshooting Guide

## Common Issues and Solutions

### Sensor Issues

#### "Cannot connect to Home Assistant"

**Symptoms:**
- Error: `Cannot connect to Home Assistant`
- Sensor manager initialization fails

**Solutions:**
1. **Check Home Assistant URL:**
   ```bash
   curl http://192.168.1.x:8123
   ```
   Should return HTML content

2. **Verify token:**
   - Go to Home Assistant UI → Profile → Long-Lived Access Tokens
   - Regenerate if expired (tokens expire after 1 year)

3. **Check network:**
   ```bash
   ping 192.168.1.x
   ```

4. **Firewall:**
   - Home Assistant port (default 8123) must be accessible
   - Some routers block local services by default

#### Proximity values not updating

**Symptoms:**
- Values stay at 0 or don't change
- Logging shows successful connection but no data

**Solutions:**
1. **Verify entity ID:**
   - Check Home Assistant UI → Developer Tools → States
   - Find the correct sensor entity (usually `sensor.google_home_mini_proximity`)
   - Update `entity_id` in config if different

2. **Check sensor in Home Assistant:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://192.168.1.x:8123/api/states/sensor.google_home_mini_proximity
   ```
   Should show current proximity value

3. **Google Home Mini not reporting:**
   - Restart the Google Home Mini
   - Check if it's actually detecting proximity (LEDs should change with hand movement)

#### Proximity values are unstable/noisy

**Symptoms:**
- MIDI values jumping around rapidly
- Difficult to control smoothly

**Solutions:**
1. **Enable smoothing:**
   ```json
   {
     "processing": {
       "smoothing": {
         "enabled": true,
         "factor": 0.5
       }
     }
   }
   ```

2. **Increase polling interval:**
   ```json
   {
     "sensor": {
       "poll_interval_ms": 100
     }
   }
   ```

3. **Add deadzone:**
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

4. **Adjust mapping range:**
   - Your hand might not be moving through the full sensor range
   - Narrow the range in config to use only the stable part

---

### MIDI Issues

#### "No MIDI output devices available"

**Symptoms:**
- Error: `No MIDI output devices available`
- MIDI controller fails to initialize

**Solutions:**
1. **Install virtual MIDI ports:**
   - **Windows:** Use [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
     - Download and install
     - Create a virtual port
     - Point Inverse Theremin to it
   
   - **macOS:** Use [IAC Driver](https://help.apple.com/macos/monterey/#/mactip5472)
     - Audio MIDI Setup → Window → Show MIDI Studio
     - Add IAC Driver
   
   - **Linux:** ALSA provides virtual ports by default

2. **Connect physical MIDI device:**
   - USB MIDI interface
   - Keyboard with MIDI out

3. **Check device index:**
   ```bash
   python -c "import mido; print(list(enumerate(mido.get_output_names())))"
   ```
   Use the correct index in config

#### MIDI messages not reaching DAW

**Symptoms:**
- MIDI CC values not showing in DAW
- No effect on synth parameters

**Solutions:**
1. **Verify MIDI routing in DAW:**
   - Ableton: Check Preferences → Link/MIDI → MIDI Ports
   - FL Studio: Check Options → MIDI Settings
   - Other DAWs: Check MIDI input settings

2. **Test MIDI output:**
   ```bash
   python -c "
   from midi_mapper import MIDIController
   midi = MIDIController(0)
   midi.initialize()
   for i in range(0, 128, 10):
       midi.send_cc(74, i)
       print(f'Sent CC 74 = {i}')
   "
   ```

3. **Check CC number:**
   - Verify `cc_number` in config (typically 74 for filter cutoff)
   - Some parameters don't respond to all CC numbers
   - Check your synth's MIDI mapping

4. **Check MIDI channel:**
   - Ensure channel in config matches synth's input channel
   - Default is channel 1

---

### Configuration Issues

#### "Invalid curve type"

**Symptoms:**
- Error: `Unknown curve 'xyz'`
- Script fails to start

**Solutions:**
- Use valid curve: `linear`, `exponential`, `logarithmic`, `quadratic`, `cubic`, `sqrt`

#### Configuration file not found

**Symptoms:**
- Error: `Config file not found: config/default_config.json`

**Solutions:**
```bash
# Make sure you're in the project root directory
cd /path/to/Inverse-theremin

# Verify config exists
ls config/default_config.json
```

---

### Connection/Network Issues

#### Timeouts connecting to devices

**Symptoms:**
- Error: `Request timeout`
- Sensor connection fails after working

**Solutions:**
1. **Check network stability:**
   ```bash
   ping 192.168.1.x
   # Should show consistent latency, no packet loss
   ```

2. **Increase timeout:**
   ```json
   {
     "sensor": {
       "timeout_ms": 10000
     }
   }
   ```

3. **Check WiFi signal:**
   - Move Google Home Mini and computer closer
   - Check for interference on 2.4GHz channel

4. **Restart devices:**
   - Restart Google Home Mini
   - Restart Home Assistant
   - Restart computer

#### "Device not reachable" (direct API mode)

**Symptoms:**
- Error when using `google_home_direct` source

**Solutions:**
1. **Verify device IP:**
   ```bash
   # Find all devices on network
   nmap 192.168.1.0/24
   # Or use Google Home app to see device IP
   ```

2. **Check device port:**
   - Default is 8008
   - Some custom ROMs use different ports

3. **Switch to Home Assistant:**
   - Direct API is experimental
   - Home Assistant is more reliable
   - Update config to use `home_assistant` source

---

### Performance Issues

#### High CPU usage

**Symptoms:**
- Script using 20%+ CPU constantly
- Computer sluggish

**Solutions:**
1. **Increase polling interval:**
   ```json
   {
     "sensor": {
       "poll_interval_ms": 100
     }
   }
   ```

2. **Increase smoothing interval:**
   ```json
   {
     "processing": {
       "debounce_ms": 50
     }
   }
   ```

3. **Disable features you don't need:**
   - Disable smoothing if not needed
   - Disable deadzone if not needed

#### Latency issues

**Symptoms:**
- Hand movement doesn't affect DAW immediately
- Noticeable delay

**Solutions:**
1. **Decrease polling interval** (lower latency):
   ```json
   {
     "sensor": {
       "poll_interval_ms": 25
     }
   }
   ```

2. **Reduce smoothing factor** (more responsive):
   ```json
   {
     "processing": {
       "smoothing": {
         "factor": 0.9
       }
     }
   }
   ```

3. **Use direct connection:**
   - Wired Ethernet if possible
   - Reduce WiFi interference

---

### Advanced Debugging

#### Enable debug logging

Edit `.env`:
```env
LOG_LEVEL=DEBUG
```

Or run with debug:
```bash
python main.py 2>&1 | tee debug.log
```

#### Check sensor raw values

```bash
python -c "
import json
from proximity_poller import SensorManager, SensorSource

with open('config/default_config.json') as f:
    config = json.load(f)

manager = SensorManager(SensorSource.HOME_ASSISTANT)
manager.initialize(config['sensor'])
manager.start_polling()

import time
for _ in range(10):
    value = manager.get_current_value()
    print(f'Raw proximity: {value}')
    time.sleep(0.1)
"
```

#### Test value mapping

```bash
python -c "
import json
from midi_mapper import ValueProcessor

with open('config/default_config.json') as f:
    config = json.load(f)

proc = ValueProcessor(
    proximity_min=config['mapping']['proximity_min'],
    proximity_max=config['mapping']['proximity_max'],
    curve=config['mapping']['curve']
)

# Test a range of values
for proximity in [0, 50, 100, 150, 200, 255]:
    midi = proc.process(proximity)
    print(f'Proximity {proximity} → MIDI {midi}')
"
```

---

### Getting Help

If the issue persists:

1. **Check the logs:**
   ```bash
   tail -f logs/inverse_theremin.log
   ```

2. **Enable debug mode:**
   - Set `LOG_LEVEL=DEBUG` in `.env`
   - Run again and check detailed output

3. **Provide information:**
   - Your OS and Python version
   - Home Assistant version (if using)
   - DAW and MIDI device name
   - Complete error message
   - Relevant config section

4. **Try Home Assistant:**
   - If using direct API, switch to Home Assistant
   - More stable and better documented

5. **Check Internet:**
   - Latest issues and solutions might be in project documentation
   - Community forums may have similar issues
