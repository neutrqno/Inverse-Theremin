# Quick Start Guide

Get the Inverse Theremin up and running in 5 minutes.

## 1. Install Dependencies

**Windows:**
```powershell
.\run.ps1
```

**macOS/Linux:**
```bash
bash run.sh
```

Or manually:
```bash
python -m venv venv
source venv/bin/activate  # or: .\venv\Scripts\Activate.ps1 (Windows)
pip install -r requirements.txt
```

## 2. Configure Home Assistant

### a. Get your Home Assistant URL and Token

1. Open Home Assistant UI in browser
2. Click your profile icon (bottom left)
3. Scroll to "Long-Lived Access Tokens"
4. Click "Create Token", name it "Inverse Theremin"
5. Copy the token

### b. Update Configuration

Create `.env` file (or edit if it exists):

```env
HOME_ASSISTANT_URL=http://192.168.29.156:8123
HOME_ASSISTANT_TOKEN=paste_your_token_here
GOOGLE_HOME_IP=192.168.29.156
GOOGLE_HOME_NAME=Attic speaker
GOOGLE_HOME_MAC=48:D6:D5:DA:AC:39
GOOGLE_HOME_DEVICE_ID=aaasa
```

**Your Google Home Mini Details:**
- **Name:** Attic speaker
- **IP Address:** 192.168.29.156
- **MAC Address:** 48:D6:D5:DA:AC:39
- **Device ID:** aaasa
- **Location:** Attic
- **Model:** Google Home Mini Gen 2

## 3. Configure MIDI Output

Edit `config/default_config.json`:

Look for the `midi` section:
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

**Choose your device:**
- Option A: Use your DAW's MIDI input
- Option B: Use a virtual MIDI port (loopMIDI on Windows, IAC on Mac)

To list available MIDI devices:
```bash
python -c "import mido; print(list(enumerate(mido.get_output_names())))"
```

## 4. Set Up Your DAW

### Ableton Live

1. Preferences → Link/MIDI
2. Set your MIDI device to "Track" and "Remote"
3. Cmd+M (or Ctrl+M) to enable MIDI mapping
4. Click the parameter you want to control
5. Move your hand near the Google Home Mini to map

### FL Studio

1. Options → MIDI Settings
2. Enable your MIDI device
3. Hold Shift and click a synth parameter
4. Move your hand to map

### Other DAWs

1. Enable MIDI input for your device
2. Enable MIDI learn
3. Click parameter → move hand to map

## 5. Run It!

```bash
python main.py
```

Move your hand near the Google Home Mini. You should see:
- Proximity values in the terminal
- MIDI messages being sent
- Parameter changes in your DAW

## Common MIDI CC Numbers

```
74  - Filter Cutoff (brightness)
91  - Reverb Wet/Dry
7   - Volume
71  - Filter Resonance
10  - Pan
1   - Modulation
64  - Sustain Pedal
```

## Troubleshooting

### "Cannot connect to Home Assistant"
- Check your URL and token
- Make sure Home Assistant is running
- Verify network connection

### "No MIDI output devices"
- Install loopMIDI (Windows), IAC Driver (Mac), or ALSA (Linux)
- Or connect a MIDI device
- Check `output_device` index in config

### "Proximity values not updating"
- Verify entity_id in config matches Home Assistant
- Check sensors in Home Assistant: Developer Tools → States
- Restart Google Home Mini

### "MIDI not reaching DAW"
- Check MIDI device is enabled in DAW
- Verify CC number is supported by synth
- Enable MIDI mapping mode in DAW

## Next Steps

1. **Optimize for your space:** Adjust `proximity_min` and `proximity_max` in config
2. **Try different curves:** Change `curve` to `exponential` or `logarithmic`
3. **Reduce jitter:** Increase `smoothing.factor` (higher = less smoothing)
4. **Create profiles:** Use profiles in `config/device_profiles.json` for different synths

## Full Documentation

- Setup details: `docs/SETUP.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Project structure: `PROJECT_STRUCTURE.md`
- Examples: `examples/basic_usage.py`

## Tips

- **Latency:** Lower `poll_interval_ms` (20-30 for lowest latency)
- **Stability:** Increase `smoothing.factor` or `poll_interval_ms`
- **Control:** Use exponential curves for finer control when hand is far
- **Mapping:** Different curves work better for different parameters

---

