"""
Interactive Calibration Wizard
Guide users through hand tracking setup and calibration.
"""

import cv2
import time
from typing import Optional, Tuple, Dict, Callable
import logging

logger = logging.getLogger(__name__)


class CalibrationWizard:
    """Interactive calibration for hand tracking."""
    
    def __init__(self, hand_detector, webcam_handler):
        """
        Initialize calibration wizard.
        
        Args:
            hand_detector: HandDetector instance
            webcam_handler: WebcamHandler instance
        """
        self.hand_detector = hand_detector
        self.webcam_handler = webcam_handler
        self.calibration_data = {
            "min_distance": float('inf'),
            "max_distance": float('-inf'),
            "hand_size_small": None,
            "hand_size_large": None,
            "confidence_threshold": 0.5
        }
    
    def run_full_calibration(self) -> Dict:
        """
        Run complete calibration sequence.
        
        Returns:
            Calibration data dictionary
        """
        logger.info("Starting full calibration wizard...")
        
        print("\n" + "="*60)
        print("INVERSE THEREMIN - HAND TRACKING CALIBRATION")
        print("="*60)
        
        # Step 1: Lighting check
        if not self._calibrate_lighting():
            logger.error("Calibration cancelled")
            return {}
        
        # Step 2: Hand position
        if not self._calibrate_hand_position():
            logger.error("Calibration cancelled")
            return {}
        
        # Step 3: Distance range
        if not self._calibrate_distance_range():
            logger.error("Calibration cancelled")
            return {}
        
        # Step 4: Hand size
        if not self._calibrate_hand_size():
            logger.error("Calibration cancelled")
            return {}
        
        # Step 5: Confidence threshold
        if not self._calibrate_confidence():
            logger.error("Calibration cancelled")
            return {}
        
        print("\n" + "="*60)
        print("CALIBRATION COMPLETE!")
        print("="*60)
        logger.info(f"Calibration data: {self.calibration_data}")
        
        return self.calibration_data
    
    def _calibrate_lighting(self) -> bool:
        """Calibrate lighting conditions."""
        print("\n[1/5] LIGHTING CALIBRATION")
        print("-" * 40)
        print("This checks if your webcam has adequate lighting.")
        print("Move around and show your hand from different angles.")
        print("\nPress SPACE to continue, ESC to skip...")
        
        start_time = time.time()
        duration = 5  # seconds
        brightness_values = []
        
        while time.time() - start_time < duration:
            ret, frame = self.webcam_handler.get_frame()
            if not ret or frame is None:
                logger.error("Failed to capture frame")
                return False
            
            # Calculate average brightness
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = gray.mean()
            brightness_values.append(brightness)
            
            # Draw instructions
            frame = self._draw_instruction(
                frame,
                f"Lighting: {brightness:.0f}/255",
                f"Time: {duration - int(time.time() - start_time)}s"
            )
            
            cv2.imshow("Calibration", frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("Skipped lighting calibration")
                return True
            elif key == 32:  # SPACE
                break
        
        avg_brightness = sum(brightness_values) / len(brightness_values) if brightness_values else 0
        
        if avg_brightness < 50:
            print("\n⚠ WARNING: Low lighting detected!")
            print("Consider improving lighting for better hand detection.")
            self.calibration_data["lighting"] = "low"
        elif avg_brightness > 200:
            print("\n⚠ WARNING: Very bright lighting detected!")
            print("This may cause glare. Adjust if possible.")
            self.calibration_data["lighting"] = "high"
        else:
            print(f"\n✓ Lighting looks good (brightness: {avg_brightness:.0f})")
            self.calibration_data["lighting"] = "good"
        
        return True
    
    def _calibrate_hand_position(self) -> bool:
        """Calibrate hand position detection."""
        print("\n[2/5] HAND POSITION CALIBRATION")
        print("-" * 40)
        print("Move your hand around the frame to calibrate position mapping.")
        print("Try to cover the full range of motion you'll use.")
        print("\nPress SPACE when ready, ESC to skip...")
        
        positions_x = []
        positions_y = []
        start_time = time.time()
        duration = 10  # seconds
        
        input("Press ENTER to start > ")
        
        while time.time() - start_time < duration:
            ret, frame = self.webcam_handler.get_frame()
            if not ret or frame is None:
                return False
            
            hands = self.hand_detector.detect(frame)
            
            if hands:
                for hand in hands:
                    if hand.position:
                        pos_x, pos_y = hand.position
                        positions_x.append(pos_x)
                        positions_y.append(pos_y)
            
            # Draw detected hands
            frame_with_hands = self.hand_detector.draw_hands(frame, hands)
            
            remaining = int(duration - (time.time() - start_time))
            frame_with_hands = self._draw_instruction(
                frame_with_hands,
                f"Move your hand",
                f"Time remaining: {remaining}s"
            )
            
            cv2.imshow("Calibration", frame_with_hands)
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("Skipped hand position calibration")
                return True
        
        if positions_x and positions_y:
            self.calibration_data["hand_position"] = {
                "x_range": (min(positions_x), max(positions_x)),
                "y_range": (min(positions_y), max(positions_y))
            }
            print(f"✓ Hand position calibrated")
            print(f"  X range: {min(positions_x):.2f} - {max(positions_x):.2f}")
            print(f"  Y range: {min(positions_y):.2f} - {max(positions_y):.2f}")
        
        return True
    
    def _calibrate_distance_range(self) -> bool:
        """Calibrate distance range."""
        print("\n[3/5] DISTANCE RANGE CALIBRATION")
        print("-" * 40)
        print("Move your hand CLOSE to the camera, then FAR away.")
        print("We'll measure the distance range for your setup.")
        print("\nPress ENTER to start > ")
        
        input()
        
        distances = []
        start_time = time.time()
        duration = 15  # seconds
        
        while time.time() - start_time < duration:
            ret, frame = self.webcam_handler.get_frame()
            if not ret or frame is None:
                return False
            
            hands = self.hand_detector.detect(frame)
            
            if hands:
                for hand in hands:
                    # Calculate hand size as distance proxy
                    if hand.landmarks:
                        distances.append(len(hand.landmarks))
            
            frame_with_hands = self.hand_detector.draw_hands(frame, hands)
            
            remaining = int(duration - (time.time() - start_time))
            frame_with_hands = self._draw_instruction(
                frame_with_hands,
                "Move hand CLOSE then FAR",
                f"Time: {remaining}s"
            )
            
            cv2.imshow("Calibration", frame_with_hands)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                return True
        
        if distances:
            self.calibration_data["min_distance"] = min(distances)
            self.calibration_data["max_distance"] = max(distances)
            
            print(f"✓ Distance range calibrated")
            print(f"  Min: {min(distances)}")
            print(f"  Max: {max(distances)}")
        
        return True
    
    def _calibrate_hand_size(self) -> bool:
        """Calibrate hand size detection."""
        print("\n[4/5] HAND SIZE CALIBRATION")
        print("-" * 40)
        print("Show a small hand gesture, then a large one.")
        print("\nPress ENTER to start > ")
        
        input()
        
        hand_sizes_small = []
        hand_sizes_large = []
        start_time = time.time()
        phase = 1  # 1 = small, 2 = large
        phase_duration = 5
        
        print("Show SMALL hand gesture (fist)...")
        
        while time.time() - start_time < phase_duration * 2:
            ret, frame = self.webcam_handler.get_frame()
            if not ret or frame is None:
                return False
            
            hands = self.hand_detector.detect(frame)
            
            elapsed_in_phase = (time.time() - start_time) % phase_duration
            
            if hands:
                for hand in hands:
                    size = len(hand.landmarks) if hand.landmarks else 0
                    
                    if time.time() - start_time < phase_duration:
                        hand_sizes_small.append(size)
                    else:
                        hand_sizes_large.append(size)
            
            frame_with_hands = self.hand_detector.draw_hands(frame, hands)
            
            if time.time() - start_time < phase_duration:
                phase_text = "SMALL gesture"
            else:
                phase_text = "LARGE gesture"
            
            remaining = int(phase_duration * 2 - (time.time() - start_time))
            frame_with_hands = self._draw_instruction(
                frame_with_hands,
                phase_text,
                f"Time: {remaining}s"
            )
            
            cv2.imshow("Calibration", frame_with_hands)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                return True
        
        if hand_sizes_small:
            self.calibration_data["hand_size_small"] = sum(hand_sizes_small) / len(hand_sizes_small)
        if hand_sizes_large:
            self.calibration_data["hand_size_large"] = sum(hand_sizes_large) / len(hand_sizes_large)
        
        print(f"✓ Hand size calibrated")
        
        return True
    
    def _calibrate_confidence(self) -> bool:
        """Calibrate confidence threshold."""
        print("\n[5/5] CONFIDENCE THRESHOLD CALIBRATION")
        print("-" * 40)
        print("Testing detection confidence levels...")
        print("We'll find the best confidence threshold.")
        print("\nPress ENTER to start > ")
        
        input()
        
        confidences = []
        start_time = time.time()
        duration = 5
        
        while time.time() - start_time < duration:
            ret, frame = self.webcam_handler.get_frame()
            if not ret or frame is None:
                return False
            
            hands = self.hand_detector.detect(frame)
            
            for hand in hands:
                confidences.append(hand.confidence)
            
            frame_with_hands = self.hand_detector.draw_hands(frame, hands)
            remaining = int(duration - (time.time() - start_time))
            frame_with_hands = self._draw_instruction(
                frame_with_hands,
                "Testing confidence...",
                f"Time: {remaining}s"
            )
            
            cv2.imshow("Calibration", frame_with_hands)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                return True
        
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            self.calibration_data["confidence_threshold"] = max(0.3, avg_confidence - 0.1)
            
            print(f"✓ Confidence calibrated")
            print(f"  Average: {avg_confidence:.2f}")
            print(f"  Threshold: {self.calibration_data['confidence_threshold']:.2f}")
        
        cv2.destroyAllWindows()
        return True
    
    @staticmethod
    def _draw_instruction(frame, instruction: str, status: str = "") -> any:
        """Draw calibration instructions on frame."""
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Text
        cv2.putText(frame, instruction, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        if status:
            cv2.putText(frame, status, (20, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1)
        
        # Instructions at bottom
        cv2.putText(frame, "ESC = Skip | SPACE/ENTER = Continue",
                   (20, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        return frame
    
    def save_calibration(self, filepath: str) -> bool:
        """Save calibration data to file."""
        import json
        try:
            with open(filepath, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            logger.info(f"Saved calibration to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return False
    
    def load_calibration(self, filepath: str) -> bool:
        """Load calibration data from file."""
        import json
        try:
            with open(filepath, 'r') as f:
                self.calibration_data = json.load(f)
            logger.info(f"Loaded calibration from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return False
