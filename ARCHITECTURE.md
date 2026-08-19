# Inverse Theremin - Enhanced Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INVERSE THEREMIN CONTROLLER                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      INPUT LAYER                                  │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │  📷 Webcam Handler          📡 Sensor Manager (Sensor Mode)     │  │
│  │  ├─ Frame Capture           ├─ Home Assistant API               │  │
│  │  ├─ FPS Control             ├─ Google Home Direct API           │  │
│  │  └─ Camera Settings         └─ Proximity Polling                │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                   PROCESSING LAYER                                │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │  🎯 Hand Detector              ⏱️  Performance Monitor           │  │
│  │  ├─ MediaPipe Detection        ├─ FPS Tracking                  │  │
│  │  ├─ HSV Fallback               ├─ Latency Measurement           │  │
│  │  ├─ Landmark Tracking          ├─ Frame Time Analysis           │  │
│  │  └─ Confidence Filtering       └─ Health Monitoring             │  │
│  │                                                                   │  │
│  │  ✋ Gesture Recognizer          📊 Calibration Wizard            │  │
│  │  ├─ Swipe Detection            ├─ Lighting Analysis             │  │
│  │  ├─ Circle Detection           ├─ Position Calibration          │  │
│  │  ├─ Shake Detection            ├─ Distance Range Setup          │  │
│  │  └─ Custom Callbacks           ├─ Hand Size Detection           │  │
│  │                                 └─ Confidence Optimization       │  │
│  │                                                                   │  │
│  │  🎮 Multi-Hand Controller      📹 Gesture Recorder              │  │
│  │  ├─ Dual Hand XY               ├─ Frame Recording               │  │
│  │  ├─ Independent CC             ├─ Playback System               │  │
│  │  ├─ Multi-Instrument           ├─ Gesture Analysis              │  │
│  │  └─ Synchronized Mode          └─ Statistics                    │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    MAPPING LAYER                                  │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │  Hand Position Mapper          Preset Manager                    │  │
│  │  ├─ Position → Value           ├─ Save Presets                  │  │
│  │  ├─ Distance → Value           ├─ Load Presets                  │  │
│  │  ├─ Curve Selection            ├─ Default Templates             │  │
│  │  └─ Smoothing Filter           └─ Import/Export                 │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    OUTPUT LAYER                                   │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │  🎹 MIDI Controller            🌐 Web Dashboard                 │  │
│  │  ├─ CC Output                  ├─ Status Display                │  │
│  │  ├─ Channel Routing            ├─ Metrics Dashboard             │  │
│  │  ├─ Velocity Control           ├─ Preset Manager UI             │  │
│  │  └─ Error Handling             ├─ Calibration Trigger           │  │
│  │                                 ├─ Mode Switching               │  │
│  │                                 └─ Real-time Updates            │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                 EXTERNAL OUTPUTS                                  │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │  🎵 DAW / Synthesizer          💾 File Storage                   │  │
│  │  (Ableton, FL Studio, etc.)    (Presets, Recordings)            │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────┐
│   Webcam    │
└──────┬──────┘
       │ Raw Frames
       ▼
┌─────────────────────┐
│ Hand Detector       │
│ (MediaPipe/HSV)     │
└──────┬──────────────┘
       │ Detected Hands
       ├─────────────────────┬─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Gesture      │  │ Performance     │  │ Multi-Hand       │
│ Recognizer   │  │ Monitor         │  │ Controller       │
└──────┬───────┘  └────────┬────────┘  └────────┬─────────┘
       │                   │                    │
       │ Gestures          │ Metrics            │ Hand Data
       │                   │                    │
       └─────────┬─────────┴─────────┬──────────┘
                 │                   │
                 ▼                   ▼
         ┌──────────────────┐  ┌──────────────┐
         │ Preset Manager   │  │ Gesture      │
         │                  │  │ Recorder     │
         └────────┬─────────┘  └──────┬───────┘
                  │                   │
                  └────────┬──────────┘
                           │ Configuration
                           ▼
                  ┌────────────────────┐
                  │ Hand Position      │
                  │ Mapper             │
                  └────────┬───────────┘
                           │ CC Values
                           ▼
                  ┌────────────────────┐
                  │ MIDI Controller    │
                  └────────┬───────────┘
                           │ MIDI CC Messages
                           ▼
                  ┌────────────────────┐
                  │ DAW / Synth        │
                  └────────────────────┘
                  
                  └──────┬──────────┘
                         │ Status Updates
                         ▼
                  ┌────────────────────┐
                  │ Web Dashboard      │
                  └────────────────────┘
```

---

## Feature Interaction Matrix

```
┌─────────────────────────────────────────────────────────────────────┐
│                 FEATURE INTERACTIONS                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Preset Manager ←→ Hand Position Mapper                             │
│  │ Stores/loads mapping configurations                             │
│  └─ Enables quick switching between control setups                 │
│                                                                       │
│  Gesture Recorder ←→ Gesture Recognizer ←→ Gesture Player          │
│  │ Detects gestures → Records them → Plays back                   │
│  └─ Creates MIDI sequences from hand motions                       │
│                                                                       │
│  Calibration Wizard ←→ Hand Detector                               │
│  │ Optimizes detection parameters                                 │
│  └─ Improves hand tracking accuracy                               │
│                                                                       │
│  Performance Monitor ←→ Web Dashboard                              │
│  │ Collects metrics → Displays in UI                              │
│  └─ Real-time system monitoring                                   │
│                                                                       │
│  Multi-Hand Controller ←→ Hand Detector                            │
│  │ Processes multiple hands separately                            │
│  └─ Enables dual-hand and multi-instrument control                │
│                                                                       │
│  All Features ←→ Preset Manager                                    │
│  │ Each feature's config can be saved                             │
│  └─ Create complete performance presets                           │
│                                                                       │
│  All Features ←→ Performance Monitor                               │
│  │ Each component logs its metrics                                │
│  └─ Comprehensive system monitoring                               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Processing Pipeline

```
FRAME CAPTURE (10-15ms)
    │
    ├─ Read from webcam
    ├─ Apply any preprocessing
    └─ Update FPS counter
         │
         ▼
HAND DETECTION (15-30ms)
    │
    ├─ MediaPipe detection
    ├─ HSV fallback if needed
    ├─ Filter by confidence
    └─ Extract landmarks
         │
         ▼
GESTURE TRACKING (5-10ms)
    │
    ├─ Add points to history
    ├─ Recognize gestures
    ├─ Trigger callbacks
    └─ Record if active
         │
         ▼
MULTI-HAND PROCESSING (5-10ms)
    │
    ├─ Sort hands by position
    ├─ Track hand IDs
    ├─ Route to controllers
    └─ Generate MIDI
         │
         ▼
MIDI OUTPUT (2-5ms)
    │
    ├─ Send CC messages
    ├─ Handle errors
    └─ Log transactions
         │
         ▼
METRICS COLLECTION (1-2ms)
    │
    ├─ Record timing data
    ├─ Update health status
    ├─ Log to dashboard
    └─ Check thresholds
         │
         ▼
VISUALIZATION (5-10ms)
    │
    ├─ Draw detections
    ├─ Show metrics
    ├─ Render UI
    └─ Display to screen
         │
         ▼
FRAME COMPLETE
    │
    └─ Total: 45-80ms (12-22 FPS guaranteed)
```

---

## Module Dependencies

```
main.py
│
├─ hand_tracker/
│  ├─ hand_detector.py          (CV detection)
│  ├─ webcam_handler.py         (Video input)
│  ├─ hand_position_mapper.py   (MIDI mapping)
│  └─ multi_hand_controller.py  (Multi-hand modes)
│
├─ utils/
│  ├─ preset_manager.py         (Config storage)
│  ├─ gesture_recorder.py       (Recording/playback)
│  ├─ performance_metrics.py    (Monitoring)
│  ├─ calibration_wizard.py     (Setup)
│  └─ gesture_recognition.py    (Gesture detection)
│
├─ midi_mapper/
│  ├─ midi_controller.py        (MIDI output)
│  ├─ value_processor.py        (Value conversion)
│  └─ filters.py                (Signal processing)
│
├─ web_dashboard.py             (Web interface)
│
└─ config/
   └─ default_config.json       (Configuration)
```

---

## Class Hierarchy

```
HandTrackingController (from main.py)
    │
    ├─ Contains: HandDetector
    │            WebcamHandler
    │            MIDIController
    │            HandPositionMapper
    │
    ├─ Uses: PresetManager
    │        GestureRecorder
    │        GesturePlayer
    │        PerformanceMonitor
    │        MetricsLogger
    │        CalibrationWizard
    │        GestureRecognizer
    │        WebDashboard
    │        MultiHandController
    │        HandDetectionTracker
    │
    └─ Methods:
       ├─ initialize()
       ├─ run()
       ├─ load_preset()
       ├─ record_gesture()
       ├─ playback_gesture()
       ├─ run_calibration()
       ├─ change_hand_mode()
       └─ shutdown()
```

---

## Data Structures

```
Frame (from capture)
    ├─ timestamp: float
    ├─ image: numpy array (H×W×3)
    ├─ fps: float
    └─ camera_id: int

DetectedHand
    ├─ id: Optional[int]
    ├─ position: Tuple[float, float]  (x, y)
    ├─ distance: float
    ├─ landmarks: List[Tuple[float, float, float]]
    ├─ confidence: float
    ├─ side: HandSide (LEFT/RIGHT)
    └─ area: float

FrameMetrics (performance data)
    ├─ timestamp: float
    ├─ capture_time: float
    ├─ detection_time: float
    ├─ mapping_time: float
    ├─ midi_time: float
    ├─ total_time: float
    ├─ fps: float
    ├─ hand_count: int
    └─ confidence: float

MIDIMessage
    ├─ type: str ("cc", "note", etc)
    ├─ channel: int
    ├─ number: int
    ├─ value: int (0-127)
    └─ timestamp: float

Gesture Frame (from recorder)
    ├─ timestamp: float
    ├─ hand_x: float
    ├─ hand_y: float
    ├─ hand_distance: float
    ├─ confidence: float
    └─ hand_count: int
```

---

## State Transitions

```
IDLE
├─ On "run": → RUNNING
├─ On "calibrate": → CALIBRATING
└─ On "record": → RECORDING

RUNNING
├─ Detecting hands
├─ Processing MIDI
├─ Recording (if active)
├─ On "calibrate": → CALIBRATING
├─ On "record": → RECORDING
└─ On "stop": → IDLE

CALIBRATING
├─ Lighting check
├─ Position mapping
├─ Distance range
├─ Hand size
├─ Confidence threshold
└─ On complete: → RUNNING

RECORDING
├─ Capturing frames
├─ Storing gesture data
├─ On stop: → SAVING
└─ On error: → IDLE

SAVING
├─ Writing to file
└─ On complete: → RUNNING

ERROR
└─ On recovery attempt: → IDLE
```

---

## Performance Characteristics

```
Component Performance (per frame):

Hand Detection
├─ MediaPipe: 15-30ms
├─ HSV Fallback: 10-20ms
└─ Total: ~25ms (40 FPS capability)

Gesture Recognition
├─ History management: 1ms
├─ Detection: 2-5ms
└─ Total: ~3ms

Multi-Hand Processing
├─ Sorting: 1ms
├─ Routing: 2-3ms
└─ Total: ~3ms

MIDI Output
├─ Serialization: 1ms
├─ Transmission: 1-2ms
└─ Total: ~2ms

Metrics Collection
├─ Recording: 0.5ms
├─ Analysis: 1ms
└─ Total: ~1.5ms

Frame Visualization
├─ Drawing: 3-5ms
├─ Display: 2-3ms
└─ Total: ~5ms

TOTAL: 45-80ms per frame
≈ 12-22 FPS (guaranteed)
```

---

## Configuration Hierarchy

```
default_config.json (base)
    │
    ├─ .env overrides
    │
    ├─ calibrations/*.json (device-specific)
    │
    ├─ presets/*.json (user presets)
    │
    └─ Runtime modifications
       (via web dashboard or API)
```

---

This architecture supports:
- ✅ Real-time hand tracking & MIDI control
- ✅ Multi-hand simultaneous processing
- ✅ Gesture recording & playback
- ✅ Performance monitoring
- ✅ Web-based remote control
- ✅ Extensible plugin system
- ✅ Preset management
- ✅ Interactive calibration

