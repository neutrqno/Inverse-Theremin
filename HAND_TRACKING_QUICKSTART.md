# Hand Tracking Quick Start ⭐

Use your laptop's webcam to control MIDI with hand gestures. No additional hardware needed!

## 30-Second Setup

```bash
# 1. Install dependencies (includes OpenCV + MediaPipe)
pip install -r requirements.txt

# 2. Run hand tracking mode
python main.py --mode hand

# 3. Move your hand in front of the webcam
# Press ESC to exit
```

That's it! Your hand distance now controls MIDI CC 74 (Filter Cutoff).

## What's Happening

```
Your Hand
    ↓ (webcam sees it)
MediaPipe detects hand position + distance
    ↓
Maps hand distance to MIDI CC value (0-127)
    ↓
Sends to DAW
    ↓
Your synth responds! 🎵
```

## Common Commands

```bash
# Run with hand tracking (displays webcam)
python main.py --mode hand

# Run headless (no video window)
python main.py --mode hand --no-display

# Use specific camera (if you have multiple)
python main.py --mode hand --camera 1

# Try auto (sensor first, falls back to hand)
python main.py --mode auto

# Run examples
python examples/hand_tracking_demo.py basic      # Simple demo
python examples/hand_tracking_demo.py midi       # MIDI output
python examples/hand_tracking_demo.py modes      # Control modes
python examples/hand_tracking_demo.py gestures   # Gesture detection

# Advanced examples
python examples/advanced_hand_tracking.py multi      # Two hands, two CC
python examples/advanced_hand_tracking.py zones      # Zone triggering
python examples/advanced_hand_tracking.py xy        # XY mapping
python examples/advanced_hand_tracking.py velocity  # Distance → velocity
```

## Control Modes

Edit `config/default_config.json`:

```json
{
  "hand_tracking": {
    "control_mode": "distance"  // or: vertical, horizontal, depth, mixed
  }
}
```

| Mode | Effect | Best For |
|------|--------|----------|
| **distance** | Close→loud, Far→quiet | Filter, reverb, volume |
| **vertical** | Top→up, Bottom→down | Resonance, LFO depth |
| **horizontal** | Left→left, Right→right | Pan, width |
| **depth** | Center→quiet, Corners→loud | Trigger zones |
| **mixed** | Distance + vertical | Complex modulation |

## Quick Examples

### Example 1: Filter Sweep (Default)
```bash
python main.py --mode hand
# Move hand closer = filter opens
# Move hand farther = filter closes
```

### Example 2: Two-Hand Control
```bash
# Run advanced example
python examples/advanced_hand_tracking.py multi
# Left hand → CC 74 (Filter)
# Right hand → CC 91 (Reverb)
```

### Example 3: Zone-Based Triggering
```bash
# Run advanced example
python examples/advanced_hand_tracking.py zones
# Divide screen into 4 zones, trigger different notes
```

### Example 4: XY Control
```bash
# Run advanced example
python examples/advanced_hand_tracking.py xy
# X position → CC 10 (Pan)
# Y position → CC 74 (Filter)
```

## Performance Tips

| Problem | Solution |
|---------|----------|
| **Hand not detected** | Improve lighting, increase hand size (move closer) |
| **Shaky/jittery** | Increase smoothing: `smoothing_factor: 0.8-0.9` |
| **Slow/laggy** | Close other apps, reduce video resolution |
| **Noisy MIDI** | Reduce smoothing factor (default 0.7 is good) |

## DAW Integration

### Ableton Live
1. Preferences → Link/MIDI → Enable input
2. Cmd+M to enable MIDI mapping
3. Click parameter
4. Move your hand to map

### FL Studio
1. Options → MIDI Settings → Enable device
2. Hold Shift + click parameter
3. Move your hand to train mapping

### Reaper
1. Options → Enable MIDI input
2. Ctrl + click parameter
3. Select "MIDI Learn"

### Logic Pro
1. Smart Controls → Click parameter
2. MIDI Learn each parameter

## What Works Well

✅ **Hand-to-synth control** - Direct mapping of hand position to synth parameters
✅ **Real-time feedback** - See your hand in the video window
✅ **Gesture control** - Swipe gestures can trigger events
✅ **Multi-hand** - Use both hands for complex control
✅ **Low latency** - 100-150ms typical latency

## Limitations

⚠️ **Lighting dependent** - Needs decent lighting for reliable detection
⚠️ **Hand visibility** - Hand must be fully visible and unobstructed
⚠️ **Distance limited** - Works best 30-150 cm from camera
⚠️ **Precision** - Not as precise as faders, but good for expression
⚠️ **CPU usage** - ~8-10% CPU on typical laptop

## Configuration

### Basic Configuration
```json
{
  "hand_tracking": {
    "control_mode": "distance",
    "smoothing_factor": 0.7
  },
  "midi": {
    "cc_number": 74,           // Filter Cutoff
    "channel": 1
  }
}
```

### For Smoother Feel
```json
{
  "hand_tracking": {
    "smoothing_factor": 0.8    // More smoothing (0.8-0.9)
  }
}
```

### For More Responsive Feel
```json
{
  "hand_tracking": {
    "smoothing_factor": 0.5    // Less smoothing (0.3-0.5)
  }
}
```

## Troubleshooting

**Q: Webcam not found**
```bash
# List cameras
python -c "import cv2; [cv2.VideoCapture(i).isOpened() for i in range(5)]"

# Use specific camera
python main.py --mode hand --camera 1
```

**Q: Hand not detected**
- Improve lighting (put light in front of you)
- Move hand into frame fully
- Increase hand size (move closer to camera)
- Try different background (reduce clutter)

**Q: MIDI not working**
```bash
# Check MIDI device
python -c "import mido; print(list(enumerate(mido.get_output_names())))"

# Update output_device in config if needed
```

**Q: High CPU usage**
- Close background apps
- Reduce webcam resolution in code (currently 640x480)
- Lower FPS setting

## Next Steps

1. ✅ Run: `python main.py --mode hand`
2. ✅ Move your hand, watch MIDI values in your DAW
3. ✅ Configure your DAW to map CC to synth parameters
4. ✅ Adjust `smoothing_factor` in config for your feel
5. ✅ Explore different control modes
6. ✅ Create music!

## Advanced Usage

**Multiple CC channels:** See `advanced_hand_tracking.py multi`
**Zone triggering:** See `advanced_hand_tracking.py zones`
**XY mapping:** See `advanced_hand_tracking.py xy`
**Gesture recognition:** See `advanced_hand_tracking.py`

## More Information

- **Full guide:** See `docs/HAND_TRACKING.md`
- **Examples:** See `examples/hand_tracking_demo.py` and `examples/advanced_hand_tracking.py`
- **Troubleshooting:** See `docs/TROUBLESHOOTING.md`
- **Configuration:** See `config/default_config.json`

## Cool Ideas

- 🎹 Use left hand for bass, right hand for lead
- 🎚️ Map hand height to filter cutoff, hand distance to reverb
- 🎯 Create trigger zones on screen to play different notes
- 👐 Use gesture swipes to switch presets
- 🎵 Record hand movements for live playback

---

**Now go create some music with your hands!** 🎵🙌

For full documentation, see `docs/HAND_TRACKING.md`
