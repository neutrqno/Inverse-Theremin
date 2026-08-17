"""Map hand position and distance to MIDI CC values."""

import logging
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ControlMode(Enum):
    """Hand tracking control modes."""
    DISTANCE = "distance"  # Hand distance from camera
    VERTICAL = "vertical"  # Hand vertical position (Y)
    HORIZONTAL = "horizontal"  # Hand horizontal position (X)
    DEPTH = "depth"  # Hand depth (Z)
    MIXED = "mixed"  # Combination of parameters


class HandPositionMapper:
    """Map hand position/distance to MIDI CC values."""
    
    def __init__(self,
                 control_mode: str = "distance",
                 invert_distance: bool = False,
                 invert_vertical: bool = False,
                 invert_horizontal: bool = False,
                 smoothing_factor: float = 0.7):
        """
        Initialize hand position mapper.
        
        Args:
            control_mode: Which parameter to control (distance, vertical, horizontal, depth, mixed)
            invert_distance: Invert distance mapping
            invert_vertical: Invert vertical position mapping
            invert_horizontal: Invert horizontal position mapping
            smoothing_factor: Exponential smoothing factor (0-1)
        """
        try:
            self.control_mode = ControlMode(control_mode)
        except ValueError:
            logger.warning(f"Unknown control mode '{control_mode}', using distance")
            self.control_mode = ControlMode.DISTANCE
        
        self.invert_distance = invert_distance
        self.invert_vertical = invert_vertical
        self.invert_horizontal = invert_horizontal
        self.smoothing_factor = max(0.0, min(1.0, smoothing_factor))
        
        # Smoothing state
        self._last_value: Optional[int] = None
        
        logger.info(f"Hand mapper initialized: mode={self.control_mode.value}, smoothing={smoothing_factor}")
    
    def map_hand_to_midi(self,
                        hand_x: float,
                        hand_y: float,
                        hand_distance: float) -> int:
        """
        Map hand position to MIDI CC value.
        
        Args:
            hand_x: Normalized X position (0-1)
            hand_y: Normalized Y position (0-1)
            hand_distance: Normalized distance (0-1, 0=far, 1=close)
            
        Returns:
            MIDI CC value (0-127)
        """
        # Clamp inputs
        hand_x = max(0.0, min(1.0, hand_x))
        hand_y = max(0.0, min(1.0, hand_y))
        hand_distance = max(0.0, min(1.0, hand_distance))
        
        # Map based on control mode
        if self.control_mode == ControlMode.DISTANCE:
            normalized = hand_distance
            if self.invert_distance:
                normalized = 1.0 - normalized
        
        elif self.control_mode == ControlMode.VERTICAL:
            normalized = hand_y
            if self.invert_vertical:
                normalized = 1.0 - normalized
        
        elif self.control_mode == ControlMode.HORIZONTAL:
            normalized = hand_x
            if self.invert_horizontal:
                normalized = 1.0 - normalized
        
        elif self.control_mode == ControlMode.DEPTH:
            # Map 2D position to estimated depth
            # Corners are further, center is closer (approximate)
            dist_from_center_x = abs(hand_x - 0.5) * 2
            dist_from_center_y = abs(hand_y - 0.5) * 2
            normalized = max(dist_from_center_x, dist_from_center_y)
        
        elif self.control_mode == ControlMode.MIXED:
            # Combine distance and vertical position
            normalized = (hand_distance * 0.7) + (hand_y * 0.3)
        
        else:
            normalized = 0.0
        
        # Convert to MIDI range
        midi_value = int(normalized * 127)
        midi_value = max(0, min(127, midi_value))
        
        # Apply smoothing
        if self._last_value is not None:
            midi_value = int(
                (self.smoothing_factor * midi_value) + 
                ((1.0 - self.smoothing_factor) * self._last_value)
            )
        
        self._last_value = midi_value
        
        return midi_value
    
    def map_hand_xy_to_midi(self,
                           hand_x: float,
                           hand_y: float) -> Tuple[int, int]:
        """
        Map hand X and Y position to two separate MIDI CC values.
        
        Useful for mapping X to pan and Y to filter cutoff, etc.
        
        Args:
            hand_x: Normalized X position (0-1)
            hand_y: Normalized Y position (0-1)
            
        Returns:
            Tuple of (midi_x, midi_y) values
        """
        x = int(max(0.0, min(1.0, hand_x)) * 127)
        y = int(max(0.0, min(1.0, hand_y)) * 127)
        
        if self.invert_horizontal:
            x = 127 - x
        if self.invert_vertical:
            y = 127 - y
        
        return (x, y)
    
    def map_hand_distance_velocity(self,
                                  hand_distance: float,
                                  velocity_min: int = 40,
                                  velocity_max: int = 100) -> int:
        """
        Map hand distance to MIDI note velocity (for triggering notes).
        
        Args:
            hand_distance: Normalized distance (0-1)
            velocity_min: Minimum velocity
            velocity_max: Maximum velocity
            
        Returns:
            MIDI velocity (0-127)
        """
        hand_distance = max(0.0, min(1.0, hand_distance))
        
        if self.invert_distance:
            hand_distance = 1.0 - hand_distance
        
        velocity = velocity_min + (hand_distance * (velocity_max - velocity_min))
        velocity = int(max(0, min(127, velocity)))
        
        return velocity
    
    def is_hand_in_zone(self,
                       hand_x: float,
                       hand_y: float,
                       x_min: float = 0.2,
                       x_max: float = 0.8,
                       y_min: float = 0.2,
                       y_max: float = 0.8) -> bool:
        """
        Check if hand is within a rectangular zone.
        
        Useful for triggering events (e.g., hand enters zone = play note).
        
        Args:
            hand_x: Normalized X position
            hand_y: Normalized Y position
            x_min, x_max: X range
            y_min, y_max: Y range
            
        Returns:
            True if hand is in zone
        """
        return (x_min <= hand_x <= x_max) and (y_min <= hand_y <= y_max)
    
    def get_gesture_direction(self,
                            prev_x: float,
                            prev_y: float,
                            curr_x: float,
                            curr_y: float) -> str:
        """
        Detect hand gesture direction based on movement.
        
        Args:
            prev_x, prev_y: Previous position
            curr_x, curr_y: Current position
            
        Returns:
            Direction: "up", "down", "left", "right", "none"
        """
        dx = curr_x - prev_x
        dy = curr_y - prev_y
        
        threshold = 0.05
        
        if abs(dx) < threshold and abs(dy) < threshold:
            return "none"
        
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"
    
    def set_control_mode(self, mode: str):
        """Change control mode."""
        try:
            self.control_mode = ControlMode(mode)
            logger.info(f"Control mode changed to: {mode}")
        except ValueError:
            logger.error(f"Invalid control mode: {mode}")
    
    def reset_smoothing(self):
        """Reset smoothing state."""
        self._last_value = None
    
    def get_config(self) -> dict:
        """Get current configuration as dict."""
        return {
            "control_mode": self.control_mode.value,
            "invert_distance": self.invert_distance,
            "invert_vertical": self.invert_vertical,
            "invert_horizontal": self.invert_horizontal,
            "smoothing_factor": self.smoothing_factor,
        }


class MultiHandMapper:
    """Map multiple hands to different MIDI parameters."""
    
    def __init__(self):
        """Initialize multi-hand mapper."""
        self.mappers = {}
        logger.info("Multi-hand mapper initialized")
    
    def add_hand_mapper(self, hand_id: str, mapper: HandPositionMapper):
        """
        Add a mapper for a specific hand.
        
        Args:
            hand_id: Identifier for the hand (e.g., "left", "right")
            mapper: HandPositionMapper instance
        """
        self.mappers[hand_id] = mapper
        logger.info(f"Added mapper for hand: {hand_id}")
    
    def remove_hand_mapper(self, hand_id: str):
        """Remove mapper for a hand."""
        if hand_id in self.mappers:
            del self.mappers[hand_id]
            logger.info(f"Removed mapper for hand: {hand_id}")
    
    def map_hands(self, hands_data: dict) -> dict:
        """
        Map multiple hands to MIDI values.
        
        Args:
            hands_data: Dict of {hand_id: (x, y, distance)}
            
        Returns:
            Dict of {hand_id: midi_value}
        """
        results = {}
        
        for hand_id, (x, y, distance) in hands_data.items():
            if hand_id in self.mappers:
                midi_value = self.mappers[hand_id].map_hand_to_midi(x, y, distance)
                results[hand_id] = midi_value
        
        return results
    
    def get_primary_hand_value(self, hands_data: dict) -> Optional[int]:
        """
        Get MIDI value for primary hand (right hand if available, else left).
        
        Args:
            hands_data: Dict of hand positions
            
        Returns:
            MIDI value or None
        """
        # Prefer right hand
        if "right" in hands_data and "right" in self.mappers:
            x, y, distance = hands_data["right"]
            return self.mappers["right"].map_hand_to_midi(x, y, distance)
        
        # Fall back to left hand
        if "left" in hands_data and "left" in self.mappers:
            x, y, distance = hands_data["left"]
            return self.mappers["left"].map_hand_to_midi(x, y, distance)
        
        return None
