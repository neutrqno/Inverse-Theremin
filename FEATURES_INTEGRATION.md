# Integration Guide: Using New Features in main.py

This guide shows how to integrate all new features into your existing Inverse Theremin setup.

---

## 1. Update main.py Imports

Add these imports to your `main.py`:

```python
from utils.preset_manager import PresetManager
from utils.gesture_recorder import GestureRecorder, GesturePlayer
from utils.performance_metrics import PerformanceMonitor, FrameMetrics, MetricsLogger
from utils.calibration_wizard import CalibrationWizard
from utils.gesture_recognition import GestureRecognizer, GestureType
from web_dashboard import WebDashboard
from hand_tracker.multi_hand_controller import MultiHandController, MultiHandMode
```

---

## 2. Enhanced HandTrackingController

Here's how to extend the existing `HandTrackingController` class:

```python
class EnhancedHandTrackingController:
    """Hand tracking with all new features enabled."""
    
    def __init__(self, config_path: str = "config/default_config.json"):
        """Initialize with all features."""
        self._load_config(config_path)
        
        # Initialize components
        self.hand_detector = HandDetector()
        self.webcam_handler = WebcamHandler(camera_id=0)
        self.midi_controller = MIDIController()
        self.hand_position_mapper = HandPositionMapper(self.config)
        
        # NEW: Initialize new features
        self.preset_manager = PresetManager("presets")
        self.gesture_recorder = GestureRecorder("recordings")
        self.gesture_player = GesturePlayer(self.gesture_recorder)
        self.performance_monitor = PerformanceMonitor()
        self.metrics_logger = MetricsLogger(self.performance_monitor)
        self.gesture_recognizer = GestureRecognizer()
        self.calibration_wizard = CalibrationWizard(self.hand_detector, self.webcam_handler)
        self.web_dashboard = WebDashboard(
            port=5000,
            performance_monitor=self.performance_monitor,
            preset_manager=self.preset_manager
        )
        self.multi_hand_controller = MultiHandController(self.midi_controller)
        
        # Counters
        self.frame_count = 0
        self.is_recording = False
        self.is_calibrating = False
    
    def initialize(self) -> bool:
        """Initialize all systems."""
        logger.info("Initializing Enhanced Hand Tracking Controller...")
        
        if not self.hand_detector.initialize():
            logger.error("Failed to initialize hand detector")
            return False
        
        if not self.webcam_handler.initialize():
            logger.error("Failed to initialize webcam")
            return False
        
        if not self.midi_controller.initialize():
            logger.error("Failed to initialize MIDI")
            return False
        
        # Create default presets
        self.preset_manager.create_default_presets()
        
        # Setup gesture callbacks
        self._setup_gesture_callbacks()
        
        # Setup web dashboard callbacks
        self._setup_dashboard_callbacks()
        
        # Start web dashboard if enabled
        if self.config.get("web_dashboard", {}).get("enabled", False):
            self.web_dashboard.start(debug=False)
        
        logger.info("Enhanced controller initialization complete")
        return True
    
    def _setup_gesture_callbacks(self) -> None:
        """Setup gesture recognition callbacks."""
        def on_swipe_left():
            logger.info("Gesture: Swipe Left - Previous Preset")
            # Cycle to previous preset
            current = self.preset_manager.get_current_preset()
            presets = self.preset_manager.list_presets()
            if presets and current:
                names = [p["name"] for p in presets]
                idx = names.index(current) - 1
                prev_preset = names[idx % len(names)]
                self.load_preset(prev_preset)
        
        def on_swipe_right():
            logger.info("Gesture: Swipe Right - Next Preset")
            # Cycle to next preset
            current = self.preset_manager.get_current_preset()
            presets = self.preset_manager.list_presets()
            if presets and current:
                names = [p["name"] for p in presets]
                idx = names.index(current) + 1
                next_preset = names[idx % len(names)]
                self.load_preset(next_preset)
        
        def on_swipe_up():
            logger.info("Gesture: Swipe Up - Start Recording")
            if not self.is_recording:
                self.start_gesture_recording()
        
        def on_swipe_down():
            logger.info("Gesture: Swipe Down - Stop Recording")
            if self.is_recording:
                self.stop_gesture_recording()
        
        def on_circle():
            logger.info("Gesture: Circle - Toggle Playback")
            if self.gesture_player.is_playing_status():
                self.gesture_player.stop_playback()
            else:
                # Playback last recorded
                recordings = self.gesture_recorder.list_recordings()
                if recordings:
                    self.gesture_player.load_recording(recordings[0]["name"])
                    self.gesture_player.start_playback(loop=True)
        
        self.gesture_recognizer.register_callback(GestureType.SWIPE_LEFT, on_swipe_left)
        self.gesture_recognizer.register_callback(GestureType.SWIPE_RIGHT, on_swipe_right)
        self.gesture_recognizer.register_callback(GestureType.SWIPE_UP, on_swipe_up)
        self.gesture_recognizer.register_callback(GestureType.SWIPE_DOWN, on_swipe_down)
        self.gesture_recognizer.register_callback(GestureType.CIRCLE_CLOCKWISE, on_circle)
    
    def _setup_dashboard_callbacks(self) -> None:
        """Setup web dashboard callbacks."""
        self.web_dashboard.on_preset_change = self.load_preset
        self.web_dashboard.on_mode_change = self.change_mode
        self.web_dashboard.on_calibrate = self.run_calibration
    
    def run(self) -> None:
        """Main control loop."""
        logger.info("Starting enhanced hand tracking controller...")
        
        try:
            while True:
                # Capture frame
                frame_start = time.time()
                ret, frame = self.webcam_handler.get_frame()
                
                if not ret or frame is None:
                    logger.warning("Failed to capture frame")
                    continue
                
                capture_time = (time.time() - frame_start) * 1000
                
                # Detect hands
                detection_start = time.time()
                hands = self.hand_detector.detect(frame)
                detection_time = (time.time() - detection_start) * 1000
                
                # Track hand detection
                if hands:
                    self.performance_monitor.record_detection(True)
                else:
                    self.performance_monitor.record_detection(False)
                
                # Update gesture recognizer
                if hands and len(hands) > 0:
                    hand = hands[0]
                    if hand.position:
                        x, y = hand.position
                        self.gesture_recognizer.add_point(x, y, time.time())
                
                # Record gesture if recording
                if self.is_recording and hands:
                    for hand in hands:
                        if hand.position:
                            x, y = hand.position
                            self.gesture_recorder.record_frame(
                                x, y,
                                getattr(hand, 'distance', 0.5),
                                hand.confidence
                            )
                
                # Process hands to MIDI
                mapping_start = time.time()
                
                if self.multi_hand_controller.mode == MultiHandMode.INDEPENDENT_CC:
                    # Use multi-hand controller
                    self.multi_hand_controller.update_hands(hands)
                else:
                    # Use standard mapping
                    for hand in hands:
                        if hand.position:
                            cc_value = self.hand_position_mapper.map_hand_to_midi(hand)
                            
                            midi_cc = self.config["hand_tracking"].get("midi_cc", 74)
                            midi_start = time.time()
                            self.midi_controller.send_cc(midi_cc, cc_value)
                            midi_time = (time.time() - midi_start) * 1000
                            
                            self.performance_monitor.record_midi_sent()
                
                mapping_time = (time.time() - mapping_start) * 1000
                
                # Record metrics
                total_time = (time.time() - frame_start) * 1000
                metrics = FrameMetrics(
                    timestamp=time.time(),
                    capture_time=capture_time,
                    detection_time=detection_time,
                    mapping_time=mapping_time,
                    midi_time=0,  # Already included above
                    total_time=total_time,
                    fps=self.webcam_handler.fps,
                    hand_count=len(hands),
                    confidence=hands[0].confidence if hands else 0.0
                )
                self.performance_monitor.record_frame(metrics)
                self.metrics_logger.on_frame()
                
                # Update dashboard
                self.web_dashboard.update_status(
                    hand_count=len(hands),
                    is_running=True,
                    fps=self.performance_monitor.get_fps()
                )
                
                # Draw visualization
                frame_with_hands = self.hand_detector.draw_hands(frame, hands)
                
                # Draw gesture recording indicator
                if self.is_recording:
                    cv2.putText(frame_with_hands, "REC", (20, 40),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Draw FPS
                fps = self.performance_monitor.get_fps()
                cv2.putText(frame_with_hands, f"FPS: {fps:.1f}", (20, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow("Hand Tracking", frame_with_hands)
                
                # Handle input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("Quit requested")
                    break
                elif key == ord('c'):
                    logger.info("Calibration requested")
                    self.run_calibration()
                elif key == ord('r'):
                    if self.is_recording:
                        self.stop_gesture_recording()
                    else:
                        self.start_gesture_recording()
                elif key == ord('p'):
                    if self.gesture_player.is_playing_status():
                        self.gesture_player.stop_playback()
                    else:
                        self.start_gesture_playback()
                
                self.frame_count += 1
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def load_preset(self, preset_name: str, config: Dict = None) -> bool:
        """Load a preset."""
        config = self.preset_manager.load_preset(preset_name)
        if not config:
            logger.error(f"Failed to load preset: {preset_name}")
            return False
        
        # Apply config
        self.config.update(config)
        logger.info(f"Loaded preset: {preset_name}")
        return True
    
    def start_gesture_recording(self) -> None:
        """Start recording a gesture."""
        self.is_recording = True
        recording_name = f"gesture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.gesture_recorder.start_recording(recording_name)
        logger.info(f"Started recording gesture: {recording_name}")
    
    def stop_gesture_recording(self) -> None:
        """Stop recording and save gesture."""
        name = self.gesture_recorder.stop_recording(save=True)
        self.is_recording = False
        logger.info(f"Stopped recording: {name}")
    
    def start_gesture_playback(self) -> None:
        """Start playing back a recorded gesture."""
        recordings = self.gesture_recorder.list_recordings()
        if not recordings:
            logger.warning("No recordings available")
            return
        
        latest = recordings[0]
        if self.gesture_player.load_recording(latest["name"]):
            self.gesture_player.start_playback(loop=True, speed=1.0)
            logger.info(f"Playing back: {latest['name']}")
    
    def run_calibration(self) -> None:
        """Run calibration wizard."""
        logger.info("Starting calibration wizard...")
        self.is_calibrating = True
        
        try:
            calibration_data = self.calibration_wizard.run_full_calibration()
            
            if calibration_data:
                self.calibration_wizard.save_calibration("calibrations/last_calibration.json")
                logger.info("Calibration completed successfully")
            else:
                logger.warning("Calibration cancelled")
        
        except Exception as e:
            logger.error(f"Calibration failed: {e}", exc_info=True)
        
        finally:
            self.is_calibrating = False
            cv2.destroyAllWindows()
    
    def change_mode(self, mode: str) -> None:
        """Change multi-hand control mode."""
        try:
            if mode == "dual_hand_xy":
                self.multi_hand_controller.set_mode(MultiHandMode.DUAL_HAND_XY)
            elif mode == "independent_cc":
                self.multi_hand_controller.set_mode(MultiHandMode.INDEPENDENT_CC)
            elif mode == "multi_instrument":
                self.multi_hand_controller.set_mode(MultiHandMode.MULTI_INSTRUMENT)
            elif mode == "synchronized":
                self.multi_hand_controller.set_mode(MultiHandMode.SYNCHRONIZED)
            
            logger.info(f"Changed to mode: {mode}")
        except Exception as e:
            logger.error(f"Failed to change mode: {e}")
    
    def shutdown(self) -> None:
        """Shutdown all systems."""
        logger.info("Shutting down enhanced controller...")
        
        if self.is_recording:
            self.stop_gesture_recording()
        
        self.gesture_player.stop_playback()
        self.web_dashboard.stop()
        self.webcam_handler.close()
        
        cv2.destroyAllWindows()
        logger.info("Controller shutdown complete")
```

---

## 3. Command-Line Arguments

Update your argument parser to include new features:

```python
def main():
    parser = argparse.ArgumentParser(description="Inverse Theremin Controller")
    
    # Existing arguments
    parser.add_argument('--mode', choices=['hand', 'sensor'], default='hand')
    parser.add_argument('--config', default='config/default_config.json')
    parser.add_argument('--camera', type=int, default=0)
    
    # NEW: Feature flags
    parser.add_argument('--web-dashboard', action='store_true', 
                       help='Enable web dashboard')
    parser.add_argument('--web-port', type=int, default=5000,
                       help='Web dashboard port')
    parser.add_argument('--calibrate', action='store_true',
                       help='Run calibration wizard on startup')
    parser.add_argument('--multi-hand', action='store_true',
                       help='Enable multi-hand control')
    parser.add_argument('--hand-mode', choices=['dual_xy', 'independent_cc', 'multi_instrument'],
                       default='dual_xy', help='Multi-hand mode')
    parser.add_argument('--performance-monitoring', action='store_true',
                       help='Enable performance monitoring')
    
    args = parser.parse_args()
    
    # Create controller
    controller = EnhancedHandTrackingController(args.config)
    
    # Apply settings from arguments
    if args.web_dashboard:
        controller.config["web_dashboard"]["enabled"] = True
        controller.config["web_dashboard"]["port"] = args.web_port
    
    if args.multi_hand:
        controller.multi_hand_controller.set_mode(
            MultiHandMode.DUAL_HAND_XY if args.hand_mode == 'dual_xy'
            else MultiHandMode.INDEPENDENT_CC
        )
    
    # Initialize
    if not controller.initialize():
        logger.error("Failed to initialize controller")
        return
    
    # Run calibration if requested
    if args.calibrate:
        controller.run_calibration()
    
    # Start main loop
    controller.run()


if __name__ == "__main__":
    main()
```

---

## 4. Keyboard Controls in Real-Time

While running, press:

| Key | Action |
|-----|--------|
| `Q` | Quit application |
| `C` | Run calibration wizard |
| `R` | Toggle gesture recording |
| `P` | Play recorded gesture |
| `Left Arrow` | Previous preset (if gesture recognition) |
| `Right Arrow` | Next preset (if gesture recognition) |

---

## 5. Configuration File Updates

Add these to your `config/default_config.json`:

```json
{
  "web_dashboard": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 5000,
    "debug": false
  },
  "presets": {
    "directory": "presets",
    "auto_load_on_startup": null
  },
  "gesture_recording": {
    "directory": "recordings",
    "auto_replay": false
  },
  "performance_monitoring": {
    "enabled": true,
    "log_interval": 100
  },
  "calibration": {
    "auto_run_on_startup": false
  },
  "multi_hand": {
    "enabled": true,
    "mode": "dual_hand_xy",
    "max_hands": 4,
    "calibration_file": "calibrations/default.json"
  },
  "gesture_recognition": {
    "enabled": true,
    "history_size": 30
  }
}
```

---

## 6. Example: Minimal Enhanced Setup

```python
from main import EnhancedHandTrackingController

# Create controller with all features
controller = EnhancedHandTrackingController()

# Enable features you want
controller.config["web_dashboard"]["enabled"] = True
controller.config["multi_hand"]["enabled"] = True

# Initialize
controller.initialize()

# Run
controller.run()
# Now open: http://localhost:5000 in your browser
```

---

## 7. Docker Integration (Optional)

If you're using Docker, add to your `Dockerfile`:

```dockerfile
# Install additional dependencies for web dashboard
RUN pip install flask==3.0.0

# Create directories
RUN mkdir -p /app/presets /app/recordings /app/calibrations

# Volume mounts for persistence
VOLUME ["/app/presets", "/app/recordings", "/app/calibrations"]

# Expose web dashboard port
EXPOSE 5000
```

---

## 🔧 Troubleshooting Integration

**Issue**: Web dashboard not accessible
```bash
# Check if port 5000 is available
netstat -an | grep 5000
# Try different port: python main.py --web-port 8000
```

**Issue**: Gesture recognition not working
```python
# Check gesture history size
recognizer = GestureRecognizer(history_size=50)  # Increase if needed
```

**Issue**: Performance degradation with all features
```python
# Disable features you don't need
controller.config["web_dashboard"]["enabled"] = False
controller.config["gesture_recording"]["enabled"] = False
```

---

All new features are now integrated and ready to use! 🚀
