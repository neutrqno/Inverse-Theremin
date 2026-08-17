#!/usr/bin/env python3
"""
Advanced Hand Tracking Examples
Demonstrates advanced features like multi-hand control, zone detection, etc.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hand_tracker import WebcamHandler, HandPositionMapper, MultiHandMapper
from midi_mapper import MIDIController
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_multi_hand_dual_cc():
    """
    Advanced: Use left and right hands to control different CC numbers.
    Left hand → CC 74 (Filter Cutoff)
    Right hand → CC 91 (Reverb)
    """
    print("\n" + "="*60)
    print("EXAMPLE: Multi-Hand Dual CC Control")
    print("="*60)
    print("Left hand controls CC 74 (Filter Cutoff)")
    print("Right hand controls CC 91 (Reverb)")
    print("Press ESC to exit\n")
    
    # Initialize
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    midi = MIDIController(output_device=0)
    if not midi.initialize():
        print("Failed to initialize MIDI")
        webcam.close()
        return
    
    # Create mappers for each hand
    left_mapper = HandPositionMapper(control_mode="distance", smoothing_factor=0.7)
    right_mapper = HandPositionMapper(control_mode="distance", smoothing_factor=0.7)
    
    # Multi-hand mapper
    multi_mapper = MultiHandMapper()
    multi_mapper.add_hand_mapper("left", left_mapper)
    multi_mapper.add_hand_mapper("right", right_mapper)
    
    webcam.start_capture()
    
    try:
        import time
        
        while True:
            hands = webcam.get_latest_hands()
            
            if hands:
                # Build hands data dict
                hands_data = {}
                for hand in hands:
                    hand_id = hand.side.value  # "left" or "right"
                    hands_data[hand_id] = (hand.center[0], hand.center[1], hand.distance)
                
                # Map all hands
                midi_values = multi_mapper.map_hands(hands_data)
                
                # Send MIDI for each hand
                if "left" in midi_values:
                    midi.send_cc(cc_number=74, value=midi_values["left"], channel=0)
                    print(f"Left hand (CC 74): {midi_values['left']:3d}", end="  ")
                
                if "right" in midi_values:
                    midi.send_cc(cc_number=91, value=midi_values["right"], channel=0)
                    print(f"Right hand (CC 91): {midi_values['right']:3d}", end="")
                
                print()
            
            if webcam.display_frame("Multi-Hand Control - Press ESC to exit"):
                break
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()
        midi.close()


def example_zone_triggering():
    """
    Advanced: Define zones on screen, trigger different actions when hand enters zones.
    Useful for triggering notes or switching parameters.
    """
    print("\n" + "="*60)
    print("EXAMPLE: Zone-Based Triggering")
    print("="*60)
    print("Screen divided into 4 zones")
    print("Hand position determines active zone")
    print("Press ESC to exit\n")
    
    # Define zones
    zones = {
        "top_left": (0.0, 0.5, 0.0, 0.5, 60),      # x_min, x_max, y_min, y_max, midi_note
        "top_right": (0.5, 1.0, 0.0, 0.5, 62),
        "bottom_left": (0.0, 0.5, 0.5, 1.0, 64),
        "bottom_right": (0.5, 1.0, 0.5, 1.0, 67),
    }
    
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    midi = MIDIController(output_device=0)
    if not midi.initialize():
        print("Failed to initialize MIDI")
        webcam.close()
        return
    
    mapper = HandPositionMapper()
    
    webcam.start_capture()
    
    try:
        import time
        last_zone = None
        
        while True:
            hands = webcam.get_latest_hands()
            
            if hands:
                hand = max(hands, key=lambda h: h.distance)
                x, y = hand.center
                
                # Check which zone hand is in
                for zone_name, (x_min, x_max, y_min, y_max, note) in zones.items():
                    if mapper.is_hand_in_zone(x, y, x_min, x_max, y_min, y_max):
                        if zone_name != last_zone:
                            print(f"Zone: {zone_name} → Sending Note {note}")
                            midi.send_note_on(note=note, velocity=100)
                            last_zone = zone_name
                        break
            
            if webcam.display_frame("Zone Triggering - Press ESC to exit"):
                break
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()
        midi.close()


def example_xy_mapping():
    """
    Advanced: Map X and Y position to two different CC numbers.
    X (horizontal) → CC 10 (Pan)
    Y (vertical) → CC 74 (Filter Cutoff)
    """
    print("\n" + "="*60)
    print("EXAMPLE: XY Position Mapping")
    print("="*60)
    print("X position (left-right) → CC 10 (Pan)")
    print("Y position (up-down) → CC 74 (Filter Cutoff)")
    print("Press ESC to exit\n")
    
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    midi = MIDIController(output_device=0)
    if not midi.initialize():
        print("Failed to initialize MIDI")
        webcam.close()
        return
    
    mapper = HandPositionMapper(smoothing_factor=0.7)
    
    webcam.start_capture()
    
    try:
        import time
        last_x = None
        last_y = None
        
        while True:
            hands = webcam.get_latest_hands()
            
            if hands:
                hand = max(hands, key=lambda h: h.distance)
                x, y = hand.center
                
                # Map X and Y to MIDI
                midi_x, midi_y = mapper.map_hand_xy_to_midi(x, y)
                
                # Send only if changed
                if midi_x != last_x:
                    midi.send_cc(cc_number=10, value=midi_x, channel=0)
                    last_x = midi_x
                
                if midi_y != last_y:
                    midi.send_cc(cc_number=74, value=midi_y, channel=0)
                    last_y = midi_y
                
                print(f"Position: ({x:.2f}, {y:.2f}) → CC 10={midi_x:3d}, CC 74={midi_y:3d}", 
                      end="\r")
            
            if webcam.display_frame("XY Mapping - Press ESC to exit"):
                break
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()
        midi.close()


def example_distance_velocity():
    """
    Advanced: Map hand distance to MIDI note velocity for dynamics.
    Closer hand = higher velocity (louder)
    """
    print("\n" + "="*60)
    print("EXAMPLE: Distance → Velocity Mapping")
    print("="*60)
    print("Hand distance determines note velocity")
    print("Close hand = loud note, Far hand = soft note")
    print("Press ESC to exit\n")
    
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    midi = MIDIController(output_device=0)
    if not midi.initialize():
        print("Failed to initialize MIDI")
        webcam.close()
        return
    
    mapper = HandPositionMapper(control_mode="distance")
    
    webcam.start_capture()
    
    try:
        import time
        
        while True:
            hands = webcam.get_latest_hands()
            
            if hands:
                hand = max(hands, key=lambda h: h.distance)
                
                # Map distance to velocity
                velocity = mapper.map_hand_distance_velocity(
                    hand.distance,
                    velocity_min=30,
                    velocity_max=120
                )
                
                print(f"Distance: {hand.distance:.2f} → Velocity: {velocity:3d}", end="\r")
            
            if webcam.display_frame("Distance → Velocity - Press ESC to exit"):
                break
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()
        midi.close()


def example_real_time_config():
    """
    Advanced: Demonstrate real-time configuration changes.
    Shows how to modify mapping behavior on the fly.
    """
    print("\n" + "="*60)
    print("EXAMPLE: Real-Time Configuration")
    print("="*60)
    print("Control modes will cycle every 5 seconds")
    print("Press ESC to exit\n")
    
    webcam = WebcamHandler(camera_id=0, width=640, height=480, fps=30)
    if not webcam.initialize():
        print("Failed to initialize webcam")
        return
    
    midi = MIDIController(output_device=0)
    if not midi.initialize():
        print("Failed to initialize MIDI")
        webcam.close()
        return
    
    mapper = HandPositionMapper(control_mode="distance")
    
    modes = ["distance", "vertical", "horizontal", "depth", "mixed"]
    current_mode_idx = 0
    last_mode_change = 0
    
    webcam.start_capture()
    
    try:
        import time
        
        while True:
            # Change mode every 5 seconds
            current_time = time.time()
            if current_time - last_mode_change > 5:
                current_mode_idx = (current_mode_idx + 1) % len(modes)
                new_mode = modes[current_mode_idx]
                mapper.set_control_mode(new_mode)
                print(f"\nMode changed to: {new_mode}")
                last_mode_change = current_time
            
            hands = webcam.get_latest_hands()
            
            if hands:
                hand = max(hands, key=lambda h: h.distance)
                midi_value = mapper.map_hand_to_midi(
                    hand.center[0],
                    hand.center[1],
                    hand.distance
                )
                
                midi.send_cc(cc_number=74, value=midi_value, channel=0)
                
                mode = modes[current_mode_idx]
                print(f"Mode: {mode:12s} | MIDI: {midi_value:3d}", end="\r")
            
            if webcam.display_frame("Real-Time Config - Press ESC to exit"):
                break
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        webcam.close()
        midi.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced hand tracking examples"
    )
    parser.add_argument(
        'example',
        nargs='?',
        choices=['multi', 'zones', 'xy', 'velocity', 'config', 'all'],
        default='multi',
        help='Example to run (default: multi)'
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Webcam device ID (default: 0)'
    )
    
    args = parser.parse_args()
    
    examples = {
        'multi': example_multi_hand_dual_cc,
        'zones': example_zone_triggering,
        'xy': example_xy_mapping,
        'velocity': example_distance_velocity,
        'config': example_real_time_config,
    }
    
    if args.example == 'all':
        for example_name, example_func in examples.items():
            try:
                example_func()
                print("\nPress Enter to continue to next example...")
                input()
            except Exception as e:
                print(f"Error in {example_name}: {e}")
    else:
        example_func = examples.get(args.example)
        if example_func:
            try:
                example_func()
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)


if __name__ == '__main__':
    main()
