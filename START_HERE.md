# 🎵 Inverse Theremin - START HERE

Welcome! Your Google Home Mini has been configured as a MIDI controller. This guide will get you started in 5 minutes.

## What You Have

- **Device:** Attic speaker (Google Home Mini Gen 2)
- **IP Address:** 192.168.29.156
- **Purpose:** Control synth parameters via hand proximity

## Files You Need to Know About

### 📋 Documentation (Read in This Order)

1. **QUICK_REFERENCE.txt** ← Read this first! (ASCII reference guide)
2. **QUICKSTART.md** ← 5-minute setup guide
3. **DEVICE_SETUP.md** ← Your device configuration details
4. **docs/SETUP.md** ← Detailed installation instructions
5. **docs/DEVICE_INFO.md** ← Technical specifications

### ⚙️ Configuration Files (Pre-configured)

- `.env` ← Edit this with your Home Assistant token
- `config/default_config.json` ← Main configuration (already set)

### 🚀 How to Run

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
pip install -r requirements.txt
python main.py
```

## ⚡ Quick Setup (3 Steps)

### Step 1: Install Dependencies
Choose your OS:
- **Windows:** Run `.\run.ps1`
- **macOS/Linux:** Run `bash run.sh`

### Step 2: Add Home Assistant Token
Edit the `.env` file and fill in:
```env
HOME_ASSISTANT_TOKEN=your_token_here
```

Get your token from Home Assistant:
1. Open Home Assistant UI
2. Click profile icon (bottom left)
3. Scroll to "Long-Lived Access Tokens"
4. Click "Create Token", name it "Inverse Theremin"
5. Copy and paste into `.env`

### Step 3: Run It!
```bash
python main.py
```

Move your hand near the device. Watch the MIDI values update in your DAW!

## ✅ Verification

### Test Device Connectivity
```bash
ping 192.168.29.156
```
Should respond successfully.

### View Device Details
```bash
python utils/device_info.py info
```

### Test Full System
```bash
python utils/device_info.py test
```

## 🎛️ Configure Your DAW

### Ableton Live
1. Preferences → Link/MIDI → Enable your MIDI device
2. Cmd+M (or Ctrl+M) to enable MIDI mapping
3. Click the parameter you want to control
4. Move your hand near the device to map

### FL Studio
1. Options → MIDI Settings → Enable your device
2. Hold Shift and click a synth parameter
3. Move your hand to map

### Other DAWs
Look for MIDI Learn or MIDI mapping mode, then:
1. Enable the mode
2. Click the parameter you want to control
3. Move your hand to create the mapping

## 📊 What's Happening Behind the Scenes

```
Google Home Mini
    ↓
Home Assistant (reads proximity)
    ↓
Inverse Theremin (polls proximity)
    ↓
Maps proximity to MIDI CC values
    ↓
Sends to DAW
    ↓
Your synth parameter updates
```

## 🎚️ Common MIDI CC Numbers

| CC # | Parameter | Typical Use |
|------|-----------|-------------|
| 74 | Filter Cutoff | Brightness (default) |
| 91 | Reverb | Reverb amount |
| 7 | Volume | Level control |
| 71 | Filter Q | Resonance |
| 10 | Pan | Stereo position |

To change, edit `config/default_config.json` → `midi.cc_number`

## 🎛️ Mapping Curves

How proximity maps to MIDI values:
- **linear** - Direct mapping (default)
- **exponential** - More control when hand is far
- **logarithmic** - More control when hand is close
- **quadratic** - Smooth curve
- **sqrt** - Square root curve

Edit in `config/default_config.json` → `mapping.curve`

## 🔧 Your Device Specs

| Property | Value |
|----------|-------|
| Name | Attic speaker |
| IP | 192.168.29.156 |
| MAC | 48:D6:D5:DA:AC:39 |
| Model | Google Home Mini Gen 2 |
| Firmware | 540761 |

## 📚 Documentation Map

```
START_HERE.md (you are here)
├── QUICK_REFERENCE.txt          (Reference card)
├── QUICKSTART.md                (5-min guide)
├── DEVICE_SETUP.md              (Device config)
├── README.md                    (Full overview)
├── docs/
│   ├── SETUP.md                (Detailed setup)
│   ├── DEVICE_INFO.md          (Tech specs)
│   └── TROUBLESHOOTING.md       (Problem solving)
└── examples/
    └── basic_usage.py           (Code examples)
```

## 🐛 Quick Troubleshooting

**Device not reachable?**
- Verify IP: `ping 192.168.29.156`
- Check Wi-Fi: Connected to `jio_ub12`?
- Restart device: Unplug 30 seconds

**Proximity not updating?**
- Check Home Assistant can see the device
- Verify token is valid
- Check entity exists in HA UI

**MIDI not working?**
- Enable MIDI in DAW
- Verify CC number is supported
- Test with: `python examples/basic_usage.py basic`

**Values too noisy?**
- Increase smoothing in config
- Increase polling interval
- Move device away from obstacles

See `docs/TROUBLESHOOTING.md` for more solutions.

## 🎵 Next Steps

1. ✅ Complete the 3-step setup above
2. ✅ Test connectivity: `python utils/device_info.py test`
3. ✅ Set up your DAW (MIDI mapping)
4. ✅ Run: `python main.py`
5. ✅ Move your hand, enjoy the sound!

## 📞 Need Help?

1. Check `QUICK_REFERENCE.txt` for commands
2. Read `DEVICE_SETUP.md` for configuration
3. See `docs/TROUBLESHOOTING.md` for issues
4. Run `python utils/device_info.py all` for full diagnostics

## 🎯 Performance Tips

- **Lowest Latency:** Decrease `poll_interval_ms` (25-30ms)
- **Most Stable:** Increase smoothing factor (0.7-0.9)
- **Best Control:** Use exponential curve for fine adjustments
- **Smooth Feel:** Increase polling interval (50-100ms)

## 🎉 You're Ready!

Everything is pre-configured with your device details. You just need:
1. Your Home Assistant token (in `.env`)
2. Your DAW MIDI mapping set up

Then run `python main.py` and start creating! 🎵

---

**Quick Links:**
- Read: `QUICK_REFERENCE.txt`
- Setup: `QUICKSTART.md`
- Troubleshoot: `docs/TROUBLESHOOTING.md`
- Reference: `docs/DEVICE_INFO.md`
