"""
Multi-Hand Advanced Control Modes
Support dual-hand XY mapping, independent CC control, and advanced gestures.
"""

from typing import List, Dict, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MultiHandMode(Enum):
    """Multi-hand control modes."""
    DUAL_HAND_XY = "dual_hand_xy"  # Left hand X, right hand Y
    INDEPENDENT_CC = "independent_cc"  # Each hand controls separate CC
    MULTI_INSTRUMENT = "multi_instrument"  # Different hands for different instruments
    HAND_GESTURES = "hand_gestures"  # Detect hand shapes/poses
    SYNCHRONIZED = "synchronized"  # Both hands in sync (same CC)


class MultiHandController:
    """Control multiple MIDI parameters from multiple hands."""
    
    def __init__(self, midi_controller=None):
        """
        Initialize multi-hand controller.
        
        Args:
            midi_controller: MIDIController instance
        """
        self.midi_controller = midi_controller
        self.mode = MultiHandMode.DUAL_HAND_XY
        
        # Hand tracking state
        self.hand_states: Dict[int, Dict] = {}  # hand_id -> hand data
        
        # Configuration
        self.config = {
            "hand1": {
                "id": 0,
                "cc_x": 1,  # Modulation
                "cc_y": 11,  # Expression
                "enabled": True
            },
            "hand2": {
                "id": 1,
                "cc_x": 74,  # Filter cutoff
                "cc_y": 91,  # Reverb mix
                "enabled": True
            }
        }
        
        # Calibration data
        self.calibration = {
            "hand1": {"min_x": 0.0, "max_x": 1.0, "min_y": 0.0, "max_y": 1.0},
            "hand2": {"min_x": 0.0, "max_x": 1.0, "min_y": 0.0, "max_y": 1.0}
        }
    
    def set_mode(self, mode: MultiHandMode) -> None:
        """Set multi-hand control mode."""
        self.mode = mode
        logger.info(f"Multi-hand mode changed to: {mode.value}")
    
    def update_hands(self, detected_hands: List) -> Dict[str, int]:
        """
        Update multi-hand state with detected hands.
        
        Args:
            detected_hands: List of DetectedHand objects
            
        Returns:
            Dictionary of MIDI messages sent {cc_number: value}
        """
        midi_messages = {}
        
        if self.mode == MultiHandMode.DUAL_HAND_XY:
            midi_messages = self._process_dual_hand_xy(detected_hands)
        
        elif self.mode == MultiHandMode.INDEPENDENT_CC:
            midi_messages = self._process_independent_cc(detected_hands)
        
        elif self.mode == MultiHandMode.MULTI_INSTRUMENT:
            midi_messages = self._process_multi_instrument(detected_hands)
        
        elif self.mode == MultiHandMode.SYNCHRONIZED:
            midi_messages = self._process_synchronized(detected_hands)
        
        return midi_messages
    
    def _process_dual_hand_xy(self, detected_hands: List) -> Dict[str, int]:
        """
        Dual hand XY mapping:
        - Left hand (hand 0) controls X axis (CC 1)
        - Right hand (hand 1) controls Y axis (CC 11)
        """
        midi_messages = {}
        
        if len(detected_hands) < 1:
            return midi_messages
        
        if len(detected_hands) >= 1:
            hand1 = detected_hands[0]
            if hand1.position and self.config["hand1"]["enabled"]:
                x, y = hand1.position
                
                # Map hand X to CC X
                x_normalized = self._normalize_position(
                    x,
                    self.calibration["hand1"]["min_x"],
                    self.calibration["hand1"]["max_x"]
                )
                cc_x = self.config["hand1"]["cc_x"]
                cc_value = self._position_to_cc(x_normalized)
                
                if self.midi_controller:
                    self.midi_controller.send_cc(cc_x, cc_value)
                midi_messages[cc_x] = cc_value
                
                logger.debug(f"Hand 1 X: CC{cc_x}={cc_value}")
        
        if len(detected_hands) >= 2:
            hand2 = detected_hands[1]
            if hand2.position and self.config["hand2"]["enabled"]:
                x, y = hand2.position
                
                # Map hand Y to CC Y
                y_normalized = self._normalize_position(
                    y,
                    self.calibration["hand2"]["min_y"],
                    self.calibration["hand2"]["max_y"]
                )
                cc_y = self.config["hand2"]["cc_y"]
                cc_value = self._position_to_cc(y_normalized)
                
                if self.midi_controller:
                    self.midi_controller.send_cc(cc_y, cc_value)
                midi_messages[cc_y] = cc_value
                
                logger.debug(f"Hand 2 Y: CC{cc_y}={cc_value}")
        
        return midi_messages
    
    def _process_independent_cc(self, detected_hands: List) -> Dict[str, int]:
        """
        Independent CC mode:
        - Hand 1 distance -> CC 74 (filter cutoff)
        - Hand 2 distance -> CC 91 (reverb mix)
        - Hand 3+ ignored
        """
        midi_messages = {}
        
        hand_assignments = [
            {"hand_idx": 0, "cc_distance": 74, "cc_xy": (1, 11)},
            {"hand_idx": 1, "cc_distance": 91, "cc_xy": (91, 93)},
            {"hand_idx": 2, "cc_distance": 76, "cc_xy": (76, 77)},
        ]
        
        for assignment in hand_assignments:
            hand_idx = assignment["hand_idx"]
            
            if hand_idx >= len(detected_hands):
                continue
            
            hand = detected_hands[hand_idx]
            if not hand.position:
                continue
            
            # Distance controls one CC
            cc_dist = assignment["cc_distance"]
            dist_value = self._distance_to_cc(hand)
            
            if self.midi_controller:
                self.midi_controller.send_cc(cc_dist, dist_value)
            midi_messages[cc_dist] = dist_value
            
            # Position controls X/Y on different CCs
            x, y = hand.position
            cc_x, cc_y = assignment["cc_xy"]
            
            x_value = self._position_to_cc(x)
            y_value = self._position_to_cc(y)
            
            if self.midi_controller:
                self.midi_controller.send_cc(cc_x, x_value)
                self.midi_controller.send_cc(cc_y, y_value)
            midi_messages[cc_x] = x_value
            midi_messages[cc_y] = y_value
            
            logger.debug(f"Hand {hand_idx}: CC{cc_dist}={dist_value}, "
                        f"CC{cc_x}={x_value}, CC{cc_y}={y_value}")
        
        return midi_messages
    
    def _process_multi_instrument(self, detected_hands: List) -> Dict[str, int]:
        """
        Multi-instrument mode:
        Route different hands to different MIDI channels for controlling
        multiple synths/drum machines simultaneously.
        """
        midi_messages = {}
        
        for hand_idx, hand in enumerate(detected_hands):
            if not hand.position or hand_idx > 3:
                continue
            
            # Route to different MIDI channels
            channel = hand_idx + 1
            x, y = hand.position
            
            x_cc = self._position_to_cc(x)
            y_cc = self._position_to_cc(y)
            
            # Send to different channels
            if self.midi_controller:
                self.midi_controller.send_cc(74, x_cc, channel=channel)
                self.midi_controller.send_cc(91, y_cc, channel=channel)
            
            midi_messages[f"ch{channel}_cc74"] = x_cc
            midi_messages[f"ch{channel}_cc91"] = y_cc
            
            logger.debug(f"Hand {hand_idx} -> Channel {channel}: "
                        f"CC74={x_cc}, CC91={y_cc}")
        
        return midi_messages
    
    def _process_synchronized(self, detected_hands: List) -> Dict[str, int]:
        """
        Synchronized mode:
        All hands control the same CC (average distance).
        """
        midi_messages = {}
        
        if not detected_hands:
            return midi_messages
        
        # Calculate average distance
        distances = []
        for hand in detected_hands:
            if hand.position:
                x, y = hand.position
                dist = (x + y) / 2  # Simple average
                distances.append(dist)
        
        if not distances:
            return midi_messages
        
        avg_distance = sum(distances) / len(distances)
        cc_value = self._position_to_cc(avg_distance)
        
        cc_number = 74
        if self.midi_controller:
            self.midi_controller.send_cc(cc_number, cc_value)
        midi_messages[cc_number] = cc_value
        
        logger.debug(f"Synchronized: {len(detected_hands)} hands -> CC{cc_number}={cc_value}")
        
        return midi_messages
    
    def _normalize_position(self, position: float, min_val: float, 
                           max_val: float) -> float:
        """Normalize position to 0-1 range."""
        if max_val == min_val:
            return 0.5
        
        normalized = (position - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))  # Clamp to 0-1
    
    def _position_to_cc(self, position: float) -> int:
        """Convert normalized position (0-1) to MIDI CC value (0-127)."""
        cc_value = int(position * 127)
        return max(0, min(127, cc_value))
    
    def _distance_to_cc(self, hand) -> int:
        """Convert hand distance to MIDI CC value."""
        # Use hand size or Z coordinate as distance proxy
        if hasattr(hand, 'distance') and hand.distance is not None:
            distance = hand.distance
        elif hand.landmarks:
            distance = len(hand.landmarks) / 21.0  # Normalize by max landmarks
        else:
            distance = 0.5
        
        return self._position_to_cc(distance)
    
    def calibrate_hand(self, hand_id: str, min_x: float, max_x: float,
                       min_y: float, max_y: float) -> None:
        """Calibrate position range for a hand."""
        if hand_id in self.calibration:
            self.calibration[hand_id] = {
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y
            }
            logger.info(f"Calibrated {hand_id}: X[{min_x:.2f}-{max_x:.2f}], "
                       f"Y[{min_y:.2f}-{max_y:.2f}]")
    
    def set_hand_config(self, hand_id: str, config: Dict) -> None:
        """Update configuration for a hand."""
        if hand_id in self.config:
            self.config[hand_id].update(config)
            logger.info(f"Updated config for {hand_id}: {config}")
    
    def get_hand_config(self, hand_id: str) -> Dict:
        """Get configuration for a hand."""
        return self.config.get(hand_id, {})
    
    def enable_hand(self, hand_id: str, enabled: bool = True) -> None:
        """Enable/disable a hand."""
        if hand_id in self.config:
            self.config[hand_id]["enabled"] = enabled
            logger.info(f"Hand {hand_id}: {'enabled' if enabled else 'disabled'}")
    
    def get_status(self) -> Dict:
        """Get multi-hand controller status."""
        return {
            "mode": self.mode.value,
            "hands_enabled": sum(
                1 for c in self.config.values() if c.get("enabled", False)
            ),
            "config": self.config,
            "calibration": self.calibration
        }


class HandDetectionTracker:
    """Track hand detection across frames."""
    
    def __init__(self, max_tracking_distance: float = 0.2):
        """
        Initialize hand tracker.
        
        Args:
            max_tracking_distance: Max distance to match hands between frames (0-1)
        """
        self.max_tracking_distance = max_tracking_distance
        self.tracked_hands: Dict[int, Dict] = {}
        self.next_hand_id = 0
    
    def update_detections(self, detected_hands: List) -> Dict[int, any]:
        """
        Update tracked hands with new detections.
        
        Args:
            detected_hands: List of newly detected hands
            
        Returns:
            Dictionary mapping hand ID to hand data
        """
        if not detected_hands:
            self.tracked_hands.clear()
            return {}
        
        # Match detections to tracked hands
        matched_hands = self._match_hands(detected_hands)
        
        return matched_hands
    
    def _match_hands(self, detected_hands: List) -> Dict[int, any]:
        """Match detected hands to tracked hands."""
        # Simple matching: find closest previously tracked hand
        matched = {}
        used_tracked = set()
        used_detected = set()
        
        # Try to match existing tracked hands
        for hand_id, tracked_data in list(self.tracked_hands.items()):
            best_dist = float('inf')
            best_detected_idx = -1
            
            for detected_idx, detected_hand in enumerate(detected_hands):
                if detected_idx in used_detected or not detected_hand.position:
                    continue
                
                dist = self._distance_between_hands(
                    tracked_data["position"],
                    detected_hand.position
                )
                
                if dist < best_dist:
                    best_dist = dist
                    best_detected_idx = detected_idx
            
            if best_dist < self.max_tracking_distance and best_detected_idx >= 0:
                matched[hand_id] = detected_hands[best_detected_idx]
                used_detected.add(best_detected_idx)
                used_tracked.add(hand_id)
            else:
                # Hand lost, remove from tracking
                del self.tracked_hands[hand_id]
        
        # Add new hands for unmatched detections
        for detected_idx, detected_hand in enumerate(detected_hands):
            if detected_idx not in used_detected:
                hand_id = self.next_hand_id
                self.next_hand_id += 1
                matched[hand_id] = detected_hand
                self.tracked_hands[hand_id] = {
                    "position": detected_hand.position,
                    "confidence": detected_hand.confidence
                }
        
        return matched
    
    @staticmethod
    def _distance_between_hands(pos1: Tuple, pos2: Tuple) -> float:
        """Calculate distance between two hand positions."""
        if not pos1 or not pos2:
            return float('inf')
        
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return (dx*dx + dy*dy) ** 0.5
