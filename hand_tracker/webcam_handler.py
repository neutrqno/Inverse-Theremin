"""Webcam input handler for real-time video capture and processing."""

import logging
import cv2
import threading
import time
from typing import Optional, Callable, List
from queue import Queue, Empty

from .hand_detector import HandDetector, DetectedHand

logger = logging.getLogger(__name__)


class WebcamHandler:
    """Handles webcam video capture and hand detection in real-time."""
    
    def __init__(self, 
                 camera_id: int = 0,
                 width: int = 640,
                 height: int = 480,
                 fps: int = 30):
        """
        Initialize webcam handler.
        
        Args:
            camera_id: Webcam device ID (0 for default)
            width: Frame width
            height: Frame height
            fps: Target frames per second
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self._target_fps = fps
        self.frame_time = 1.0 / fps
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.hand_detector = HandDetector()
        
        self._running = False
        self._capture_thread: Optional[threading.Thread] = None
        self._frame_queue = Queue(maxsize=2)
        self._hand_queue = Queue(maxsize=2)
        
        self._callbacks: List[Callable] = []
        self._last_frame: Optional[cv2.Mat] = None
        self._last_hands: List[DetectedHand] = []
        
        self._fps_counter = 0
        self._last_fps_time = time.time()
        self._actual_fps = 0
    
    def initialize(self) -> bool:
        """
        Initialize webcam.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open webcam {self.camera_id}")
                return False
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self._target_fps)
            
            # Reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            logger.info(f"Webcam {self.camera_id} initialized: {self.width}x{self.height} @ {self._target_fps}fps")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize webcam: {e}")
            return False
    
    def start_capture(self):
        """Start background capture and processing thread."""
        if self._running:
            logger.warning("Capture already running")
            return
        
        if self.cap is None:
            logger.error("Webcam not initialized")
            return
        
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        logger.info("Webcam capture started")
    
    def stop_capture(self):
        """Stop capture thread."""
        self._running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        logger.info("Webcam capture stopped")
    
    def _capture_loop(self):
        """Main capture loop (runs in background thread)."""
        frame_count = 0
        
        while self._running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame")
                    continue
                
                # Resize frame
                frame = cv2.resize(frame, (self.width, self.height))
                
                # Detect hands
                hands = self.hand_detector.detect(frame)
                
                # Store latest
                self._last_frame = frame.copy()
                self._last_hands = hands
                
                # Update FPS counter
                frame_count += 1
                current_time = time.time()
                elapsed = current_time - self._last_fps_time
                
                if elapsed >= 1.0:
                    self._actual_fps = frame_count / elapsed
                    frame_count = 0
                    self._last_fps_time = current_time
                    logger.debug(f"FPS: {self._actual_fps:.1f}")
                
                # Try to queue (non-blocking)
                try:
                    self._frame_queue.put_nowait(frame)
                    self._hand_queue.put_nowait(hands)
                except:
                    pass  # Queue full, skip frame
                
                # Trigger callbacks
                for callback in self._callbacks:
                    try:
                        callback(frame, hands)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                # Frame rate limiting
                time.sleep(self.frame_time)
                
            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                continue
    
    def get_latest_frame(self) -> Optional[cv2.Mat]:
        """Get the latest captured frame."""
        return self._last_frame.copy() if self._last_frame is not None else None
    
    def get_latest_hands(self) -> List[DetectedHand]:
        """Get hands detected in the latest frame."""
        return self._last_hands.copy() if self._last_hands else []
    
    def get_frame_with_hands(self, draw: bool = True) -> Optional[cv2.Mat]:
        """
        Get latest frame with hand annotations.
        
        Args:
            draw: Whether to draw hand annotations
            
        Returns:
            Annotated frame
        """
        frame = self.get_latest_frame()
        hands = self.get_latest_hands()
        
        if frame is None:
            return None
        
        if draw:
            frame = self.hand_detector.draw_hands(frame, hands)
            
            # Draw FPS
            cv2.putText(frame,
                       f"FPS: {self._actual_fps:.1f}",
                       (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.7,
                       (0, 255, 0),
                       2)
            
            # Draw detection info
            cv2.putText(frame,
                       f"Hands: {len(hands)}",
                       (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.7,
                       (0, 255, 0),
                       2)
        
        return frame
    
    def register_callback(self, callback: Callable[[cv2.Mat, List[DetectedHand]], None]):
        """
        Register a callback for each frame.
        
        Args:
            callback: Function(frame, hands) called for each frame
        """
        self._callbacks.append(callback)
        logger.debug(f"Callback registered, total: {len(self._callbacks)}")
    
    def unregister_callback(self, callback: Callable):
        """Unregister a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_primary_hand(self) -> Optional[DetectedHand]:
        """
        Get the primary (largest/closest) hand.
        
        Returns:
            Primary hand or None if no hands detected
        """
        hands = self.get_latest_hands()
        if not hands:
            return None
        
        # Return hand with highest distance (closest to camera)
        return max(hands, key=lambda h: h.distance)
    
    def get_hand_position_normalized(self, hand: Optional[DetectedHand] = None) -> tuple:
        """
        Get normalized hand position (0-1 range).
        
        Args:
            hand: Hand to get position for (uses primary if None)
            
        Returns:
            (x, y) normalized position (0-1, 0-1)
        """
        if hand is None:
            hand = self.get_primary_hand()
        
        if hand is None:
            return (0.5, 0.5)  # Center if no hand
        
        return hand.center
    
    def get_hand_distance_normalized(self, hand: Optional[DetectedHand] = None) -> float:
        """
        Get normalized hand distance (0-1 range).
        
        Args:
            hand: Hand to get distance for (uses primary if None)
            
        Returns:
            Distance value 0-1 (0=far, 1=close)
        """
        if hand is None:
            hand = self.get_primary_hand()
        
        if hand is None:
            return 0.0
        
        return hand.distance
    
    def display_frame(self, window_name: str = "Inverse Theremin - Hand Tracking") -> bool:
        """
        Display current frame in a window.
        
        Args:
            window_name: Name of the window
            
        Returns:
            True if ESC was pressed (signal to quit)
        """
        frame = self.get_frame_with_hands(draw=True)
        
        if frame is None:
            return False
        
        cv2.imshow(window_name, frame)
        
        # Check for ESC key
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            cv2.destroyWindow(window_name)
            return True
        
        return False
    
    def close(self):
        """Clean up resources."""
        self.stop_capture()
        
        if self.cap is not None:
            self.cap.release()
            logger.info("Webcam released")
        
        self.hand_detector.close()
        cv2.destroyAllWindows()
    
    @property
    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._running
    
    @property
    def fps(self) -> float:
        """Get actual frames per second."""
        return self._actual_fps
    
    def list_cameras(self) -> list:
        """List available cameras."""
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
