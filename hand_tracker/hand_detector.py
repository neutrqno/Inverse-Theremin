"""Hand detection using MediaPipe."""

import logging
import cv2
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import MediaPipe
try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False
    logger.warning("MediaPipe not available, hand detection will be limited")


class HandSide(Enum):
    """Hand classification."""
    LEFT = "left"
    RIGHT = "right"


@dataclass
class HandLandmark:
    """Single hand landmark point."""
    x: float  # 0-1 normalized coordinate
    y: float  # 0-1 normalized coordinate
    z: float  # Depth coordinate (relative)
    confidence: float  # 0-1 confidence score


@dataclass
class DetectedHand:
    """Complete hand detection result."""
    side: HandSide
    landmarks: List[HandLandmark]  # 21 landmarks per hand
    handedness: float  # Confidence of hand classification (0-1)
    center: Tuple[float, float]  # (x, y) center point
    distance: float  # Estimated distance (0-1, where 0=far, 1=close)
    bounding_box: Tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max)
    
    @property
    def confidence(self) -> float:
        """Overall detection confidence."""
        return self.handedness


class HandDetector:
    """Hand detector using MediaPipe."""
    
    # Hand landmark indices (MediaPipe hand model)
    LANDMARK_WRIST = 0
    LANDMARK_THUMB_TIP = 4
    LANDMARK_INDEX_TIP = 8
    LANDMARK_MIDDLE_TIP = 12
    LANDMARK_RING_TIP = 16
    LANDMARK_PINKY_TIP = 20
    
    def __init__(self, 
                 model_complexity: int = 0,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        """
        Initialize hand detector.
        
        Args:
            model_complexity: 0 (lite) or 1 (full)
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
        """
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        if MP_AVAILABLE:
            try:
                # Try importing from correct namespace
                mp_hands = mp.solutions.hands
                
                self.hands = mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    model_complexity=model_complexity,
                    min_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence
                )
                self.use_mediapipe = True
                logger.info(f"Hand detector initialized with MediaPipe (complexity={model_complexity})")
            except Exception as e:
                logger.warning(f"MediaPipe initialization failed: {e}. Using fallback hand detection.")
                self.use_mediapipe = False
        else:
            self.use_mediapipe = False
            logger.warning("Using fallback hand detection (no MediaPipe). For best results, install MediaPipe.")
    
    def detect(self, frame: cv2.Mat) -> List[DetectedHand]:
        """
        Detect hands in a frame.
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            List of detected hands
        """
        try:
            if not self.use_mediapipe:
                # Fallback: simple color-based detection
                return self._detect_hands_fallback(frame)
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = frame.shape
            
            # Run detection
            results = self.hands.process(rgb_frame)
            
            detected_hands = []
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for landmarks, handedness_info in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness
                ):
                    hand = self._process_hand(landmarks, handedness_info, (w, h))
                    detected_hands.append(hand)
            
            return detected_hands
            
        except Exception as e:
            logger.error(f"Hand detection error: {e}")
            return []
    
    def _detect_hands_fallback(self, frame: cv2.Mat) -> List[DetectedHand]:
        """Fallback hand detection using color and contours."""
        h, w, _ = frame.shape
        detected_hands = []
        
        try:
            # Convert to HSV for skin detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Skin color range in HSV
            lower_skin = (0, 20, 70)
            upper_skin = (20, 255, 255)
            mask1 = cv2.inRange(hsv, lower_skin, upper_skin)
            
            lower_skin2 = (170, 20, 70)
            upper_skin2 = (180, 255, 255)
            mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
            
            mask = cv2.bitwise_or(mask1, mask2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum hand size
                    x, y, width, height = cv2.boundingRect(contour)
                    
                    # Calculate hand center and distance
                    center_x = (x + width / 2) / w
                    center_y = (y + height / 2) / h
                    hand_size = (width * height) / (w * h)
                    distance = min(1.0, hand_size * 5)  # Normalize
                    
                    # Create detected hand
                    hand = DetectedHand(
                        side=HandSide.RIGHT,  # Default to right
                        landmarks=[],  # Empty for fallback
                        handedness=0.8,  # Default confidence
                        center=(center_x, center_y),
                        distance=distance,
                        bounding_box=(x/w, y/h, (x+width)/w, (y+height)/h)
                    )
                    detected_hands.append(hand)
        
        except Exception as e:
            logger.debug(f"Fallback detection error: {e}")
        
        return detected_hands
    
    def _process_hand(self, 
                     landmarks, 
                     handedness_info,
                     frame_size: Tuple[int, int]) -> DetectedHand:
        """Process MediaPipe hand output."""
        w, h = frame_size
        
        # Extract hand side
        side = HandSide.LEFT if handedness_info.classification[0].label == 'Left' else HandSide.RIGHT
        handedness_confidence = handedness_info.classification[0].score
        
        # Convert landmarks
        hand_landmarks = []
        xs, ys, zs = [], [], []
        
        for landmark in landmarks.landmark:
            lm = HandLandmark(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                confidence=landmark.presence if hasattr(landmark, 'presence') else 1.0
            )
            hand_landmarks.append(lm)
            xs.append(landmark.x)
            ys.append(landmark.y)
            zs.append(landmark.z)
        
        # Calculate center
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)
        
        # Calculate bounding box
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        # Estimate distance from z-coordinate and hand size
        # Larger hand size = closer to camera
        hand_size = (x_max - x_min) * (y_max - y_min)
        avg_z = sum(zs) / len(zs)
        
        # Normalize: closer hand = higher distance value
        # hand_size: 0.001-0.5 → 0-1 scale
        # z: -0.5 to 0.5 → inverted to 0-1
        distance = max(0, min(1, hand_size * 2))  # Larger hand = closer = higher value
        
        return DetectedHand(
            side=side,
            landmarks=hand_landmarks,
            handedness=handedness_confidence,
            center=(center_x, center_y),
            distance=distance,
            bounding_box=(x_min, y_min, x_max, y_max)
        )
    
    def draw_hands(self, frame: cv2.Mat, hands: List[DetectedHand]) -> cv2.Mat:
        """
        Draw hand annotations on frame.
        
        Args:
            frame: OpenCV frame
            hands: List of detected hands
            
        Returns:
            Annotated frame
        """
        try:
            h, w, _ = frame.shape
            
            for hand in hands:
                # Draw bounding box
                x_min, y_min, x_max, y_max = hand.bounding_box
                x_min_px = int(x_min * w)
                y_min_px = int(y_min * h)
                x_max_px = int(x_max * w)
                y_max_px = int(y_max * h)
                
                # Green for right hand, blue for left hand
                color = (0, 255, 0) if hand.side == HandSide.RIGHT else (255, 0, 0)
                
                cv2.rectangle(frame, (x_min_px, y_min_px), (x_max_px, y_max_px), color, 2)
                
                # Draw center point
                center_x_px = int(hand.center[0] * w)
                center_y_px = int(hand.center[1] * h)
                cv2.circle(frame, (center_x_px, center_y_px), 5, color, -1)
                
                # Draw landmarks
                for landmark in hand.landmarks:
                    lm_x = int(landmark.x * w)
                    lm_y = int(landmark.y * h)
                    cv2.circle(frame, (lm_x, lm_y), 2, color, -1)
                
                # Draw distance indicator
                distance_px = int(hand.distance * 100)
                cv2.putText(frame, 
                           f"{hand.side.value}: {distance_px}%",
                           (x_min_px, y_min_px - 10),
                           cv2.FONT_HERSHEY_SIMPLEX,
                           0.5,
                           color,
                           2)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error drawing hands: {e}")
            return frame
    
    def get_hand_distance_mm(self, hand: DetectedHand, 
                            calibration_distance_mm: float = 150) -> float:
        """
        Estimate hand distance in millimeters using calibration.
        
        Args:
            hand: Detected hand
            calibration_distance_mm: Known distance for calibration (typical: 150mm for hand)
            
        Returns:
            Estimated distance in mm
        """
        # Hand width typically 80-100mm at 30cm distance
        bounding_box = hand.bounding_box
        hand_width = (bounding_box[2] - bounding_box[0])  # Normalized 0-1
        
        # Inverse relationship: wider hand = closer
        # At ~30cm (300mm), hand width ≈ 0.3 of frame width
        # Empirical calibration
        estimated_distance = 400 * (0.3 / max(hand_width, 0.05))
        
        return estimated_distance
    
    def close(self):
        """Clean up resources."""
        self.hands.close()
        logger.info("Hand detector closed")
