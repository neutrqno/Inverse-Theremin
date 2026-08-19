"""
Gesture Recognition System
Detect hand gestures (swipes, circles, pinch, etc) and trigger actions.
"""

from typing import List, Tuple, Optional, Callable, Dict
from dataclasses import dataclass
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class GestureType(Enum):
    """Recognized gesture types."""
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    CIRCLE_CLOCKWISE = "circle_cw"
    CIRCLE_COUNTER_CLOCKWISE = "circle_ccw"
    PINCH = "pinch"
    OPEN_HAND = "open_hand"
    PEACE_SIGN = "peace"
    THUMBS_UP = "thumbs_up"
    SHAKE = "shake"
    NONE = "none"


@dataclass
class GesturePoint:
    """A point in a gesture."""
    x: float
    y: float
    time: float


class GestureRecognizer:
    """Recognize hand gestures from position history."""
    
    def __init__(self, history_size: int = 30, min_gesture_duration: float = 0.3):
        """
        Initialize gesture recognizer.
        
        Args:
            history_size: Number of points to track
            min_gesture_duration: Minimum duration for gesture in seconds
        """
        self.history_size = history_size
        self.min_gesture_duration = min_gesture_duration
        self.position_history: List[GesturePoint] = []
        
        # Thresholds
        self.swipe_min_distance = 0.15  # Min distance for swipe (0-1)
        self.swipe_max_duration = 0.5  # Max time for swipe (seconds)
        self.circle_min_radius = 0.05
        self.shake_threshold = 0.1
        
        # Callbacks
        self.gesture_callbacks: Dict[GestureType, List[Callable]] = {
            gesture_type: [] for gesture_type in GestureType
        }
        
        # Last recognized gesture
        self.last_gesture = GestureType.NONE
        self.last_gesture_time = None
    
    def add_point(self, x: float, y: float, time: float) -> None:
        """
        Add a point to position history.
        
        Args:
            x: X position (0-1)
            y: Y position (0-1)
            time: Timestamp in seconds
        """
        point = GesturePoint(x=x, y=y, time=time)
        self.position_history.append(point)
        
        # Keep history size limited
        if len(self.position_history) > self.history_size:
            self.position_history.pop(0)
        
        # Try to recognize gestures
        self._recognize_gestures(time)
    
    def _recognize_gestures(self, current_time: float) -> None:
        """Recognize gestures from history."""
        if len(self.position_history) < 5:
            return
        
        # Try different gesture recognitions
        gesture = self._detect_swipe(current_time)
        if gesture != GestureType.NONE:
            self._trigger_gesture(gesture, current_time)
            return
        
        gesture = self._detect_circle(current_time)
        if gesture != GestureType.NONE:
            self._trigger_gesture(gesture, current_time)
            return
        
        gesture = self._detect_shake(current_time)
        if gesture != GestureType.NONE:
            self._trigger_gesture(gesture, current_time)
            return
    
    def _detect_swipe(self, current_time: float) -> GestureType:
        """Detect swipe gestures."""
        if len(self.position_history) < 3:
            return GestureType.NONE
        
        # Get recent points within time window
        recent_points = [
            p for p in self.position_history
            if current_time - p.time <= self.swipe_max_duration
        ]
        
        if len(recent_points) < 3:
            return GestureType.NONE
        
        start = recent_points[0]
        end = recent_points[-1]
        
        dx = end.x - start.x
        dy = end.y - start.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < self.swipe_min_distance:
            return GestureType.NONE
        
        # Determine swipe direction
        if abs(dx) > abs(dy):  # Horizontal swipe
            if dx > 0:
                return GestureType.SWIPE_RIGHT
            else:
                return GestureType.SWIPE_LEFT
        else:  # Vertical swipe
            if dy > 0:
                return GestureType.SWIPE_DOWN
            else:
                return GestureType.SWIPE_UP
    
    def _detect_circle(self, current_time: float) -> GestureType:
        """Detect circular gestures."""
        if len(self.position_history) < 10:
            return GestureType.NONE
        
        # Get all points
        points = self.position_history
        
        # Calculate center
        center_x = sum(p.x for p in points) / len(points)
        center_y = sum(p.y for p in points) / len(points)
        
        # Calculate distances from center
        distances = [
            math.sqrt((p.x - center_x)**2 + (p.y - center_y)**2)
            for p in points
        ]
        
        avg_distance = sum(distances) / len(distances)
        
        if avg_distance < self.circle_min_radius:
            return GestureType.NONE
        
        # Check if points form a circle (consistent radius)
        variance = sum((d - avg_distance)**2 for d in distances) / len(distances)
        
        if variance > avg_distance:  # Too much variance
            return GestureType.NONE
        
        # Detect direction (clockwise vs counter-clockwise)
        direction = self._detect_circle_direction(points, center_x, center_y)
        
        if direction > 0:
            return GestureType.CIRCLE_CLOCKWISE
        elif direction < 0:
            return GestureType.CIRCLE_COUNTER_CLOCKWISE
        
        return GestureType.NONE
    
    def _detect_circle_direction(self, points: List[GesturePoint], 
                                center_x: float, center_y: float) -> float:
        """
        Detect circle direction.
        
        Returns:
            Positive for clockwise, negative for counter-clockwise
        """
        if len(points) < 3:
            return 0
        
        cross_products = []
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            
            # Vectors from center
            v1 = (p1.x - center_x, p1.y - center_y)
            v2 = (p2.x - center_x, p2.y - center_y)
            
            # Cross product
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            cross_products.append(cross)
        
        avg_cross = sum(cross_products) / len(cross_products)
        return avg_cross
    
    def _detect_shake(self, current_time: float) -> GestureType:
        """Detect shaking motion."""
        if len(self.position_history) < 5:
            return GestureType.NONE
        
        # Look for rapid back-and-forth motion
        recent_points = self.position_history[-10:]
        
        direction_changes = 0
        prev_dx = 0
        
        for i in range(1, len(recent_points)):
            p1 = recent_points[i - 1]
            p2 = recent_points[i]
            
            dx = p2.x - p1.x
            
            if i > 1 and dx * prev_dx < 0:  # Direction changed
                direction_changes += 1
            
            prev_dx = dx
        
        # Shake requires at least 2 direction changes with high motion
        if direction_changes >= 2:
            motion_amount = max(
                abs(recent_points[-1].x - recent_points[0].x),
                abs(recent_points[-1].y - recent_points[0].y)
            )
            
            if motion_amount > self.shake_threshold:
                return GestureType.SHAKE
        
        return GestureType.NONE
    
    def _trigger_gesture(self, gesture: GestureType, current_time: float) -> None:
        """Trigger callbacks for recognized gesture."""
        if gesture == self.last_gesture:
            return  # Avoid duplicate triggers
        
        logger.info(f"Gesture recognized: {gesture.value}")
        self.last_gesture = gesture
        self.last_gesture_time = current_time
        
        # Call registered callbacks
        if gesture in self.gesture_callbacks:
            for callback in self.gesture_callbacks[gesture]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in gesture callback: {e}")
        
        # Clear history after recognizing gesture
        self.position_history.clear()
    
    def register_callback(self, gesture: GestureType, 
                         callback: Callable) -> None:
        """
        Register callback for gesture.
        
        Args:
            gesture: Gesture type
            callback: Function to call when gesture is recognized
        """
        if gesture not in self.gesture_callbacks:
            self.gesture_callbacks[gesture] = []
        
        self.gesture_callbacks[gesture].append(callback)
        logger.info(f"Registered callback for gesture: {gesture.value}")
    
    def unregister_callback(self, gesture: GestureType, 
                           callback: Callable) -> None:
        """Unregister callback for gesture."""
        if gesture in self.gesture_callbacks:
            try:
                self.gesture_callbacks[gesture].remove(callback)
            except ValueError:
                logger.warning(f"Callback not found for gesture: {gesture.value}")
    
    def clear_callbacks(self, gesture: GestureType = None) -> None:
        """Clear all callbacks for a gesture (or all gestures if None)."""
        if gesture is None:
            for g in self.gesture_callbacks:
                self.gesture_callbacks[g] = []
        else:
            self.gesture_callbacks[gesture] = []
    
    def get_last_gesture(self) -> Tuple[GestureType, Optional[float]]:
        """Get last recognized gesture and timestamp."""
        return self.last_gesture, self.last_gesture_time
    
    def reset(self) -> None:
        """Reset gesture state."""
        self.position_history.clear()
        self.last_gesture = GestureType.NONE
        self.last_gesture_time = None


class GestureActions:
    """Pre-built gesture action handlers."""
    
    def __init__(self, on_action: Callable[[str], None]):
        """
        Initialize gesture actions.
        
        Args:
            on_action: Callback for actions (name, *args, **kwargs)
        """
        self.on_action = on_action
    
    def create_preset_selector(self, presets: List[str]) -> Dict[GestureType, Callable]:
        """
        Create gesture handlers to cycle through presets.
        
        Args:
            presets: List of preset names
            
        Returns:
            Dictionary of gesture -> action mapping
        """
        self.preset_index = 0
        self.presets = presets
        
        def next_preset():
            self.preset_index = (self.preset_index + 1) % len(self.presets)
            self.on_action(f"select_preset:{self.presets[self.preset_index]}")
        
        def prev_preset():
            self.preset_index = (self.preset_index - 1) % len(self.presets)
            self.on_action(f"select_preset:{self.presets[self.preset_index]}")
        
        return {
            GestureType.SWIPE_RIGHT: next_preset,
            GestureType.SWIPE_LEFT: prev_preset,
        }
    
    def create_parameter_control(self, param_name: str, 
                                step: float = 0.1) -> Dict[GestureType, Callable]:
        """
        Create gesture handlers to control a parameter.
        
        Args:
            param_name: Parameter to control
            step: Step size for adjustment
            
        Returns:
            Dictionary of gesture -> action mapping
        """
        def increase():
            self.on_action(f"param_adjust:{param_name}:+{step}")
        
        def decrease():
            self.on_action(f"param_adjust:{param_name}:-{step}")
        
        def reset_param():
            self.on_action(f"param_reset:{param_name}")
        
        return {
            GestureType.SWIPE_UP: increase,
            GestureType.SWIPE_DOWN: decrease,
            GestureType.SHAKE: reset_param,
        }
