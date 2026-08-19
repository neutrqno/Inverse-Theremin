"""
Gesture Recording and Playback System
Record hand motions and play them back in MIDI.
"""

import json
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Frame:
    """A single recorded frame."""
    timestamp: float  # Relative time from start
    hand_x: float
    hand_y: float
    hand_distance: float
    confidence: float
    hand_count: int


class GestureRecorder:
    """Record and playback hand gestures."""
    
    def __init__(self, recordings_dir: str = "recordings"):
        """
        Initialize gesture recorder.
        
        Args:
            recordings_dir: Directory to store recording files
        """
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_recording = False
        self.frames: List[Frame] = []
        self.start_time = None
        self.current_recording = None
    
    def start_recording(self, name: str = None) -> bool:
        """
        Start recording a gesture.
        
        Args:
            name: Optional recording name
            
        Returns:
            bool: Success status
        """
        if self.is_recording:
            logger.warning("Already recording. Stop current recording first.")
            return False
        
        self.is_recording = True
        self.frames = []
        self.start_time = time.time()
        self.current_recording = name or f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Started recording gesture: {self.current_recording}")
        return True
    
    def record_frame(self, hand_x: float, hand_y: float, hand_distance: float,
                    confidence: float = 1.0, hand_count: int = 1) -> bool:
        """
        Record a single frame during active recording.
        
        Args:
            hand_x: Normalized X position (0-1)
            hand_y: Normalized Y position (0-1)
            hand_distance: Distance value
            confidence: Detection confidence (0-1)
            hand_count: Number of hands detected
            
        Returns:
            bool: Success status
        """
        if not self.is_recording or self.start_time is None:
            return False
        
        try:
            relative_time = time.time() - self.start_time
            frame = Frame(
                timestamp=relative_time,
                hand_x=hand_x,
                hand_y=hand_y,
                hand_distance=hand_distance,
                confidence=confidence,
                hand_count=hand_count
            )
            self.frames.append(frame)
            return True
        except Exception as e:
            logger.error(f"Failed to record frame: {e}")
            return False
    
    def stop_recording(self, save: bool = True) -> Optional[str]:
        """
        Stop recording.
        
        Args:
            save: Save recording to file
            
        Returns:
            Recording name or None if failed
        """
        if not self.is_recording:
            logger.warning("Not currently recording")
            return None
        
        self.is_recording = False
        duration = time.time() - self.start_time if self.start_time else 0
        
        logger.info(f"Stopped recording: {self.current_recording} ({duration:.2f}s, {len(self.frames)} frames)")
        
        if save and self.frames:
            if self._save_recording(self.current_recording):
                return self.current_recording
        
        return None
    
    def _save_recording(self, name: str) -> bool:
        """Save recording to file."""
        try:
            recording_file = self.recordings_dir / f"{name}.json"
            
            recording_data = {
                "name": name,
                "created": datetime.now().isoformat(),
                "duration": self.frames[-1].timestamp if self.frames else 0,
                "frame_count": len(self.frames),
                "frames": [asdict(f) for f in self.frames]
            }
            
            with open(recording_file, 'w') as f:
                json.dump(recording_data, f, indent=2)
            
            logger.info(f"Saved recording: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")
            return False
    
    def load_recording(self, name: str) -> Optional[List[Frame]]:
        """
        Load a recording.
        
        Args:
            name: Recording name
            
        Returns:
            List of frames or None if not found
        """
        try:
            recording_file = self.recordings_dir / f"{name}.json"
            
            if not recording_file.exists():
                logger.error(f"Recording '{name}' not found")
                return None
            
            with open(recording_file, 'r') as f:
                data = json.load(f)
            
            frames = [
                Frame(
                    timestamp=f["timestamp"],
                    hand_x=f["hand_x"],
                    hand_y=f["hand_y"],
                    hand_distance=f["hand_distance"],
                    confidence=f["confidence"],
                    hand_count=f["hand_count"]
                )
                for f in data["frames"]
            ]
            
            logger.info(f"Loaded recording: {name} ({len(frames)} frames)")
            return frames
            
        except Exception as e:
            logger.error(f"Failed to load recording: {e}")
            return None
    
    def list_recordings(self) -> List[Dict]:
        """List all available recordings."""
        recordings = []
        
        for recording_file in self.recordings_dir.glob("*.json"):
            try:
                with open(recording_file, 'r') as f:
                    data = json.load(f)
                
                recordings.append({
                    "name": data["name"],
                    "created": data["created"],
                    "duration": data["duration"],
                    "frame_count": data["frame_count"]
                })
            except Exception as e:
                logger.warning(f"Failed to read recording {recording_file}: {e}")
        
        return sorted(recordings, key=lambda x: x["created"], reverse=True)
    
    def delete_recording(self, name: str) -> bool:
        """Delete a recording."""
        try:
            recording_file = self.recordings_dir / f"{name}.json"
            recording_file.unlink()
            logger.info(f"Deleted recording: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete recording: {e}")
            return False
    
    def get_recording_duration(self, name: str) -> Optional[float]:
        """Get duration of a recording."""
        try:
            recording_file = self.recordings_dir / f"{name}.json"
            with open(recording_file, 'r') as f:
                data = json.load(f)
            return data["duration"]
        except Exception as e:
            logger.error(f"Failed to get recording duration: {e}")
            return None


class GesturePlayer:
    """Playback recorded gestures with MIDI output."""
    
    def __init__(self, gesture_recorder: GestureRecorder):
        """
        Initialize gesture player.
        
        Args:
            gesture_recorder: GestureRecorder instance for loading recordings
        """
        self.recorder = gesture_recorder
        self.is_playing = False
        self.current_frames: List[Frame] = []
        self.current_frame_index = 0
        self.playback_start_time = None
        self.playback_speed = 1.0  # 1.0 = normal speed, 2.0 = 2x speed
        self.loop = False
    
    def load_recording(self, name: str) -> bool:
        """Load a recording for playback."""
        frames = self.recorder.load_recording(name)
        if frames is None:
            return False
        
        self.current_frames = frames
        self.current_frame_index = 0
        logger.info(f"Loaded recording for playback: {name}")
        return True
    
    def start_playback(self, loop: bool = False, speed: float = 1.0) -> bool:
        """
        Start playback.
        
        Args:
            loop: Loop playback
            speed: Playback speed (1.0 = normal)
            
        Returns:
            bool: Success status
        """
        if not self.current_frames:
            logger.error("No recording loaded")
            return False
        
        self.is_playing = True
        self.current_frame_index = 0
        self.playback_start_time = time.time()
        self.loop = loop
        self.playback_speed = speed
        
        logger.info(f"Started playback (loop={loop}, speed={speed}x)")
        return True
    
    def stop_playback(self) -> None:
        """Stop playback."""
        self.is_playing = False
        logger.info("Stopped playback")
    
    def get_current_frame(self) -> Optional[Frame]:
        """Get the current frame during playback."""
        if not self.is_playing or not self.current_frames:
            return None
        
        elapsed_time = (time.time() - self.playback_start_time) * self.playback_speed
        
        # Find frame that matches current elapsed time
        frame = None
        for f in self.current_frames:
            if f.timestamp <= elapsed_time:
                frame = f
            else:
                break
        
        # Check if playback is finished
        if elapsed_time > self.current_frames[-1].timestamp:
            if self.loop:
                self.playback_start_time = time.time()
            else:
                self.is_playing = False
        
        return frame
    
    def is_playing_status(self) -> bool:
        """Check if playback is active."""
        return self.is_playing
    
    def get_playback_progress(self) -> float:
        """Get playback progress (0-1)."""
        if not self.current_frames or not self.is_playing:
            return 0.0
        
        elapsed_time = (time.time() - self.playback_start_time) * self.playback_speed
        total_time = self.current_frames[-1].timestamp
        
        if total_time == 0:
            return 0.0
        
        return min(1.0, elapsed_time / total_time)


class GestureAnalyzer:
    """Analyze recorded gestures for statistics and patterns."""
    
    @staticmethod
    def get_statistics(frames: List[Frame]) -> Dict:
        """Get statistics about a recording."""
        if not frames:
            return {}
        
        distances = [f.hand_distance for f in frames]
        x_positions = [f.hand_x for f in frames]
        y_positions = [f.hand_y for f in frames]
        confidences = [f.confidence for f in frames]
        
        return {
            "frame_count": len(frames),
            "duration": frames[-1].timestamp,
            "avg_fps": len(frames) / frames[-1].timestamp if frames[-1].timestamp > 0 else 0,
            "distance": {
                "min": min(distances),
                "max": max(distances),
                "avg": sum(distances) / len(distances),
                "range": max(distances) - min(distances)
            },
            "x_position": {
                "min": min(x_positions),
                "max": max(x_positions),
                "avg": sum(x_positions) / len(x_positions)
            },
            "y_position": {
                "min": min(y_positions),
                "max": max(y_positions),
                "avg": sum(y_positions) / len(y_positions)
            },
            "avg_confidence": sum(confidences) / len(confidences)
        }
    
    @staticmethod
    def detect_gesture_type(frames: List[Frame]) -> str:
        """
        Detect type of gesture (swipe, circle, etc).
        
        Returns:
            Gesture type string
        """
        if len(frames) < 5:
            return "unknown"
        
        x_positions = [f.hand_x for f in frames]
        y_positions = [f.hand_y for f in frames]
        
        x_change = abs(x_positions[-1] - x_positions[0])
        y_change = abs(y_positions[-1] - y_positions[0])
        
        # Swipe detection
        if x_change > 0.5 and y_change < 0.2:
            return "horizontal_swipe"
        elif y_change > 0.5 and x_change < 0.2:
            return "vertical_swipe"
        
        # Distance motion (move closer/farther)
        distances = [f.hand_distance for f in frames]
        if abs(distances[-1] - distances[0]) > 0.3:
            if distances[-1] > distances[0]:
                return "move_away"
            else:
                return "move_closer"
        
        return "stationary"
