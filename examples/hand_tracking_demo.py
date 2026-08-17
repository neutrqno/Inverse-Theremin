#!/usr/bin/env python3
"""
Hand Tracking Demo
Demonstrates webcam-based hand detection and MIDI mapping.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hand_tracker import WebcamHandler, HandPositionMapper
from midi_mapper import MIDIController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic():
    """Basic hand detection demo - shows live video with hand tracking."""
    print("\n" + "="*60)
    print("DEMO: Basic Hand Detection")
    print("="*60)
    print("Press ESC to exit\n")
    
    # Initialize webcam
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    # Start capture
    webcam.start_capture()
    
    try:
        import time
        frame_count = 0
        
        while True:
            # Display frame with hand annotations
            if webcam.display_frame("Hand Detection - Press ESC to exit"):
                break  # ESC pressed
            
            # Print statistics
            frame_count += 1
            if frame_count % 30 == 0:
                hands = webcam.get_latest_hands()
                print(f"FPS: {webcam.fps:.1f} | Hands detected: {len(hands)}")
                
                for i, hand in enumerate(hands):
                    print(f"  Hand {i+1} ({hand.side.value}): "
                          f"distance={hand.distance:.2f}, "
                          f"confidence={hand.confidence:.2f}")
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()


def demo_midi_output():
    """Demo mapping hand distance to MIDI CC."""
    print("\n" + "="*60)
    print("DEMO: Hand Distance → MIDI CC Output")
    print("="*60)
    print("Press ESC to exit\n")
    
    # Initialize components
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    midi = MIDIController(output_device=0)
    if not midi.initialize():
        print("Failed to initialize MIDI")
        webcam.close()
        return
    
    mapper = HandPositionMapper(control_mode="distance", smoothing_factor=0.7)
    
    print(f"MIDI device: {midi.device_name}")
    print("Sending CC 74 (Filter Cutoff)")
    print("Move your hand closer/farther to control value\n")
    
    # Start capture
    webcam.start_capture()
    
    try:
        import time
        frame_count = 0
        last_midi_value = 0
        
        while True:
            # Get hand data
            hands = webcam.get_latest_hands()
            
            if hands:
                # Use primary hand
                hand = max(hands, key=lambda h: h.distance)
                
                # Map to MIDI
                midi_value = mapper.map_hand_to_midi(
                    hand.center[0],
                    hand.center[1],
                    hand.distance
                )
                
                # Send MIDI if changed
                if midi_value != last_midi_value:
                    midi.send_cc(cc_number=74, value=midi_value, channel=0)
                    last_midi_value = midi_value
            
            # Display frame
            if webcam.display_frame("Hand Tracking MIDI - Press ESC to exit"):
                break
            
            # Print statistics
            frame_count += 1
            if frame_count % 30 == 0:
                hands = webcam.get_latest_hands()
                print(f"FPS: {webcam.fps:.1f} | Hands: {len(hands)} | "
                      f"Last MIDI CC 74: {last_midi_value}")
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()
        midi.close()


def demo_control_modes():
    """Demo different control modes."""
    print("\n" + "="*60)
    print("DEMO: Control Modes")
    print("="*60)
    print("Press ESC to exit")
    print("Use these modes in config: distance, vertical, horizontal, depth, mixed\n")
    
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    # Create mappers for each control mode
    modes = ["distance", "vertical", "horizontal", "depth", "mixed"]
    mappers = {mode: HandPositionMapper(control_mode=mode, smoothing_factor=0.7) 
               for mode in modes}
    
    webcam.start_capture()
    
    try:
        import time
        frame_count = 0
        
        while True:
            hands = webcam.get_latest_hands()
            
            if hands:
                hand = max(hands, key=lambda h: h.distance)
                
                # Show MIDI values for each mode
                print(f"\rHand position: X={hand.center[0]:.2f}, Y={hand.center[1]:.2f}, "
                      f"Distance={hand.distance:.2f} | ", end="")
                
                for mode, mapper in mappers.items():
                    midi_value = mapper.map_hand_to_midi(
                        hand.center[0],
                        hand.center[1],
                        hand.distance
                    )
                    print(f"{mode}={midi_value:3d} ", end="")
            
            # Display frame
            if webcam.display_frame("Control Modes - Press ESC to exit"):
                break
            
            frame_count += 1
            time.sleep(0.01)
        
        print()  # Newline after loop
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()


def demo_gesture_detection():
    """Demo hand gesture direction detection."""
    print("\n" + "="*60)
    print("DEMO: Gesture Direction Detection")
    print("="*60)
    print("Press ESC to exit")
    print("Move your hand: up, down, left, right\n")
    
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    mapper = HandPositionMapper()
    
    webcam.start_capture()
    
    try:
        import time
        prev_pos = None
        
        while True:
            hands = webcam.get_latest_hands()
            
            if hands:
                hand = max(hands, key=lambda h: h.distance)
                curr_pos = hand.center
                
                if prev_pos:
                    direction = mapper.get_gesture_direction(
                        prev_pos[0], prev_pos[1],
                        curr_pos[0], curr_pos[1]
                    )
                    if direction != "none":
                        print(f"\rGesture: {direction:6s} | Position: ({curr_pos[0]:.2f}, {curr_pos[1]:.2f})", 
                              end="")
                
                prev_pos = curr_pos
            
            # Display frame
            if webcam.display_frame("Gesture Detection - Press ESC to exit"):
                break
            
            time.sleep(0.01)
        
        print()  # Newline
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()


def list_cameras():
    """List available cameras."""
    print("\nAvailable cameras:")
    webcam = WebcamHandler()
    cameras = webcam.list_cameras()
    
    if cameras:
        for camera_id in cameras:
            print(f"  Camera {camera_id}: Available")
    else:
        print("  No cameras found!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Hand tracking demonstration examples"
    )
    parser.add_argument(
        'demo',
        nargs='?',
        choices=['basic', 'midi', 'modes', 'gestures', 'all'],
        default='basic',
        help='Demo to run (default: basic)'
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Webcam device ID (default: 0)'
    )
    parser.add_argument(
        '--list-cameras',
        action='store_true',
        help='List available cameras and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_cameras:
        list_cameras()
        return
    
    demos = {
        'basic': demo_basic,
        'midi': demo_midi_output,
        'modes': demo_control_modes,
        'gestures': demo_gesture_detection,
    }
    
    if args.demo == 'all':
        for demo_name, demo_func in demos.items():
            try:
                demo_func()
                print("\nPress Enter to continue to next demo...")
                input()
            except Exception as e:
                print(f"Error in {demo_name}: {e}")
    else:
        demo_func = demos.get(args.demo)
        if demo_func:
            try:
                demo_func()
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)
        else:
            print(f"Unknown demo: {args.demo}")
            sys.exit(1)


if __name__ == '__main__':
    main()
