#!/usr/bin/env python3
"""
Basic usage example for Inverse Theremin.
Shows how to use the components programmatically.
"""

import json
import time
from proximity_poller import SensorManager, SensorSource
from midi_mapper import MIDIController, ValueProcessor, SmoothingFilter


def example_basic():
    """Basic example: proximity to MIDI mapping."""
    print("=== Basic Usage Example ===\n")
    
    # Load config
    with open('config/default_config.json') as f:
        config = json.load(f)
    
    # Create sensor manager
    sensor_config = config['sensor']
    source = SensorSource(sensor_config['source'])
    
    sensor = SensorManager(
        source=source,
        poll_interval_ms=50,
        timeout_ms=5000
    )
    
    if not sensor.initialize(sensor_config):
        print("Failed to initialize sensor")
        return
    
    # Create value processor
    mapping_config = config['mapping']
    processor = ValueProcessor(
        proximity_min=mapping_config['proximity_min'],
        proximity_max=mapping_config['proximity_max'],
        curve=mapping_config['curve'],
        invert=mapping_config.get('invert', False)
    )
    
    # Create MIDI controller
    midi_config = config['midi']
    midi = MIDIController(midi_config['output_device'])
    
    if not midi.initialize():
        print("Failed to initialize MIDI")
        return
    
    # Start polling
    sensor.start_polling()
    
    print("Polling for 10 seconds. Move your hand near the sensor.\n")
    
    try:
        for i in range(100):  # 10 seconds at 100ms intervals
            proximity = sensor.get_current_value()
            if proximity is not None:
                midi_value = processor.process(proximity)
                midi.send_cc(midi_config['cc_number'], midi_value)
                print(f"Proximity: {proximity:6.1f} → MIDI: {midi_value:3d}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        sensor.stop_polling()
        midi.close()


def example_smoothing():
    """Example with smoothing filter."""
    print("=== Smoothing Filter Example ===\n")
    
    # Create a smoothing filter
    smoother = SmoothingFilter(factor=0.7)
    
    # Simulate noisy sensor data
    noisy_data = [50, 48, 52, 49, 51, 50, 100, 102, 101, 99]
    
    print("Comparing raw vs smoothed values:\n")
    print("Raw     | Smoothed")
    print("--------|----------")
    
    for raw in noisy_data:
        smoothed = smoother.apply(raw)
        print(f"{raw:7.1f} | {smoothed:8.1f}")
    
    print("\nNotice how smoothed values are less jumpy")


def example_curves():
    """Example: different mapping curves."""
    print("=== Mapping Curves Example ===\n")
    
    curves = ['linear', 'exponential', 'logarithmic', 'quadratic', 'sqrt']
    
    for curve in curves:
        processor = ValueProcessor(
            proximity_min=0,
            proximity_max=255,
            midi_min=0,
            midi_max=127,
            curve=curve
        )
        
        preview = processor.get_curve_preview(steps=6)
        print(f"{curve:15s}: {preview}")


def example_midi_cc_numbers():
    """Show common MIDI CC numbers for different parameters."""
    print("=== Common MIDI CC Numbers ===\n")
    
    cc_numbers = {
        1: "Modulation Wheel",
        7: "Volume",
        10: "Pan",
        11: "Expression",
        64: "Sustain Pedal",
        71: "Filter Resonance (Q)",
        74: "Filter Cutoff (Brightness)",
        91: "Reverb Wet/Dry",
        93: "Chorus Wet/Dry",
        94: "Delay Wet/Dry",
    }
    
    print("CC# | Parameter")
    print("----|----------------------------")
    for cc, name in sorted(cc_numbers.items()):
        print(f"{cc:3d} | {name}")
    
    print("\nUse these CC numbers in your config to control different parameters.")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        if example == 'basic':
            example_basic()
        elif example == 'smoothing':
            example_smoothing()
        elif example == 'curves':
            example_curves()
        elif example == 'cc':
            example_midi_cc_numbers()
        else:
            print(f"Unknown example: {example}")
            print("Available: basic, smoothing, curves, cc")
    else:
        print("Inverse Theremin - Examples\n")
        print("Usage: python examples/basic_usage.py [example]\n")
        print("Available examples:")
        print("  basic      - Basic sensor to MIDI mapping")
        print("  smoothing  - Demonstrate smoothing filter")
        print("  curves     - Show different mapping curves")
        print("  cc         - List common MIDI CC numbers")
