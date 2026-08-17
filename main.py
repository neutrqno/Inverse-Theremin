#!/usr/bin/env python3
"""
Inverse Theremin: Proximity Mapping & Hand Tracking
Transform your Google Home Mini or Webcam into a MIDI controller.
"""

import logging
import sys
import json
import os
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from proximity_poller import SensorManager, SensorSource, DeviceRegistry, get_attic_speaker
from midi_mapper import MIDIController, ValueProcessor, SmoothingFilter, FilterChain
from hand_tracker import WebcamHandler, HandPositionMapper

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InverseThereminController:
    """Main controller for the Inverse Theremin system (Sensor Mode)."""
    
    def __init__(self, config_path: str = "config/default_config.json"):
        """
        Initialize the controller.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.sensor_manager: Optional[SensorManager] = None
        self.midi_controller: Optional[MIDIController] = None
        self.value_processor: Optional[ValueProcessor] = None
        self.filter_chain = FilterChain()
        self._running = False
        self.mode = "sensor"
        
        # Device information is loaded from config
        logger.info("Sensor mode: Configure device details in config/default_config.json")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config: {e}")
            sys.exit(1)
    
    def initialize(self) -> bool:
        """Initialize all components."""
        logger.info("Initializing Inverse Theremin...")
        
        try:
            # Initialize sensor
            sensor_config = self.config.get('sensor', {})
            source = SensorSource(sensor_config.get('source', 'home_assistant'))
            
            self.sensor_manager = SensorManager(
                source=source,
                poll_interval_ms=sensor_config.get('poll_interval_ms', 50),
                timeout_ms=sensor_config.get('timeout_ms', 5000)
            )
            
            if not self.sensor_manager.initialize(sensor_config):
                logger.error("Failed to initialize sensor")
                return False
            
            # Initialize MIDI
            midi_config = self.config.get('midi', {})
            self.midi_controller = MIDIController(
                output_device=midi_config.get('output_device', 0)
            )
            
            if not self.midi_controller.initialize():
                logger.error("Failed to initialize MIDI")
                return False
            
            # Initialize value processor
            mapping_config = self.config.get('mapping', {})
            self.value_processor = ValueProcessor(
                proximity_min=mapping_config.get('proximity_min', 0),
                proximity_max=mapping_config.get('proximity_max', 255),
                midi_min=self.config.get('midi', {}).get('min_value', 0),
                midi_max=self.config.get('midi', {}).get('max_value', 127),
                curve=mapping_config.get('curve', 'linear'),
                invert=mapping_config.get('invert', False)
            )
            
            # Setup filters
            processing_config = self.config.get('processing', {})
            
            if processing_config.get('smoothing', {}).get('enabled', True):
                smoothing_factor = processing_config['smoothing'].get('factor', 0.7)
                self.filter_chain.add_filter(SmoothingFilter(factor=smoothing_factor))
            
            logger.info("Initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def run(self):
        """Run the main loop."""
        if not self.sensor_manager or not self.midi_controller or not self.value_processor:
            logger.error("Components not initialized")
            return
        
        logger.info("Starting Inverse Theremin...")
        self._running = True
        
        # Register callback
        self.sensor_manager.register_callback(self._on_proximity_data)
        
        # Start polling
        self.sensor_manager.start_polling()
        
        try:
            # Keep the program running
            import time
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.shutdown()
    
    def _on_proximity_data(self, proximity: float):
        """Handle incoming proximity data."""
        try:
            # Apply filters
            filtered = self.filter_chain.apply(proximity)
            if filtered is None:
                return
            
            # Process to MIDI value
            midi_config = self.config.get('midi', {})
            midi_value = self.value_processor.process(filtered)
            
            # Send MIDI
            cc_number = midi_config.get('cc_number', 74)
            channel = midi_config.get('channel', 1) - 1  # Convert to 0-based
            
            self.midi_controller.send_cc(cc_number, midi_value, channel)
            
        except Exception as e:
            logger.error(f"Error processing proximity data: {e}")
    
    def shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down...")
        self._running = False
        
        if self.sensor_manager and self.sensor_manager.is_polling:
            self.sensor_manager.stop_polling()
        
        if self.midi_controller:
            self.midi_controller.close()
        
        logger.info("Shutdown complete")
    
    def get_status(self) -> dict:
        """Get current system status."""
        return {
            'running': self._running,
            'mode': self.mode,
            'sensor': {
                'polling': self.sensor_manager.is_polling if self.sensor_manager else False,
                'current_value': self.sensor_manager.get_current_value() if self.sensor_manager else None
            },
            'midi': {
                'connected': self.midi_controller.is_connected if self.midi_controller else False,
                'device': self.midi_controller.device_name if self.midi_controller else None
            }
        }


class HandTrackingController:
    """Main controller for the Inverse Theremin system (Hand Tracking Mode)."""
    
    def __init__(self, 
                 config_path: str = "config/default_config.json",
                 camera_id: int = 0,
                 display: bool = True):
        """
        Initialize hand tracking controller.
        
        Args:
            config_path: Path to configuration file
            camera_id: Webcam device ID
            display: Whether to display video window
        """
        self.config = self._load_config(config_path)
        self.camera_id = camera_id
        self.display = display
        self._running = False
        self.mode = "hand_tracking"
        
        # Components
        self.webcam: Optional[WebcamHandler] = None
        self.midi_controller: Optional[MIDIController] = None
        self.hand_mapper: Optional[HandPositionMapper] = None
        self.filter_chain = FilterChain()
        
        logger.info("Hand Tracking Mode initialized")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config: {e}")
            sys.exit(1)
    
    def initialize(self) -> bool:
        """Initialize all components."""
        logger.info("Initializing Hand Tracking...")
        
        try:
            # Initialize webcam
            self.webcam = WebcamHandler(
                camera_id=self.camera_id,
                width=640,
                height=480,
                fps=30
            )
            
            if not self.webcam.initialize():
                logger.error("Failed to initialize webcam")
                return False
            
            # Initialize MIDI
            midi_config = self.config.get('midi', {})
            self.midi_controller = MIDIController(
                output_device=midi_config.get('output_device', 0)
            )
            
            if not self.midi_controller.initialize():
                logger.error("Failed to initialize MIDI")
                return False
            
            # Initialize hand mapper
            hand_config = self.config.get('hand_tracking', {})
            self.hand_mapper = HandPositionMapper(
                control_mode=hand_config.get('control_mode', 'distance'),
                invert_distance=hand_config.get('invert_distance', False),
                invert_vertical=hand_config.get('invert_vertical', False),
                invert_horizontal=hand_config.get('invert_horizontal', False),
                smoothing_factor=hand_config.get('smoothing_factor', 0.7)
            )
            
            # Setup filters
            processing_config = self.config.get('processing', {})
            if processing_config.get('smoothing', {}).get('enabled', True):
                smoothing_factor = processing_config['smoothing'].get('factor', 0.7)
                self.filter_chain.add_filter(SmoothingFilter(factor=smoothing_factor))
            
            logger.info("Hand Tracking initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def run(self):
        """Run the main loop."""
        if not self.webcam or not self.midi_controller or not self.hand_mapper:
            logger.error("Components not initialized")
            return
        
        logger.info("Starting Hand Tracking...")
        self._running = True
        
        # Start webcam capture
        self.webcam.start_capture()
        
        try:
            import time
            
            while self._running:
                # Get hand data
                hands = self.webcam.get_latest_hands()
                
                if hands:
                    # Process primary hand
                    primary_hand = max(hands, key=lambda h: h.distance)
                    
                    # Map to MIDI
                    midi_value = self.hand_mapper.map_hand_to_midi(
                        primary_hand.center[0],
                        primary_hand.center[1],
                        primary_hand.distance
                    )
                    
                    # Apply filters
                    filtered = self.filter_chain.apply(float(midi_value))
                    if filtered is not None:
                        midi_value = int(filtered)
                    
                    # Send MIDI
                    midi_config = self.config.get('midi', {})
                    cc_number = midi_config.get('cc_number', 74)
                    channel = midi_config.get('channel', 1) - 1
                    
                    self.midi_controller.send_cc(cc_number, midi_value, channel)
                
                # Display if enabled
                if self.display:
                    if self.webcam.display_frame():
                        self._running = False
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down...")
        self._running = False
        
        if self.webcam:
            self.webcam.close()
        
        if self.midi_controller:
            self.midi_controller.close()
        
        logger.info("Shutdown complete")
    
    def get_status(self) -> dict:
        """Get current system status."""
        return {
            'running': self._running,
            'mode': self.mode,
            'webcam': {
                'running': self.webcam.is_running if self.webcam else False,
                'fps': self.webcam.fps if self.webcam else 0,
                'hands': len(self.webcam.get_latest_hands()) if self.webcam else 0
            },
            'midi': {
                'connected': self.midi_controller.is_connected if self.midi_controller else False,
                'device': self.midi_controller.device_name if self.midi_controller else None
            }
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inverse Theremin - MIDI controller via proximity or hand tracking"
    )
    parser.add_argument(
        '--mode',
        choices=['sensor', 'hand', 'auto'],
        default='auto',
        help='Control mode: sensor (Google Home), hand (webcam), auto (try sensor first)'
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Webcam device ID (default: 0)'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Disable video display window (hand tracking mode)'
    )
    parser.add_argument(
        '--config',
        default='config/default_config.json',
        help='Configuration file path'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Inverse Theremin - MIDI Controller")
    logger.info("=" * 60)
    
    # Determine mode
    mode = args.mode
    
    if mode == 'auto':
        # Try sensor first, fall back to hand tracking
        logger.info("Auto mode: Attempting to connect to proximity sensor...")
        sensor_controller = InverseThereminController(args.config)
        
        if sensor_controller.initialize():
            logger.info("Proximity sensor initialized successfully")
            controller = sensor_controller
            mode = 'sensor'
        else:
            logger.info("Proximity sensor failed, falling back to hand tracking...")
            hand_controller = HandTrackingController(
                args.config,
                camera_id=args.camera,
                display=not args.no_display
            )
            
            if hand_controller.initialize():
                logger.info("Hand tracking initialized successfully")
                controller = hand_controller
                mode = 'hand'
            else:
                logger.error("Both modes failed!")
                sys.exit(1)
    
    elif mode == 'sensor':
        controller = InverseThereminController(args.config)
        if not controller.initialize():
            logger.error("Failed to initialize proximity sensor")
            sys.exit(1)
    
    else:  # hand
        controller = HandTrackingController(
            args.config,
            camera_id=args.camera,
            display=not args.no_display
        )
        if not controller.initialize():
            logger.error("Failed to initialize hand tracking")
            sys.exit(1)
    
    # Show status
    status = controller.get_status()
    logger.info(f"Status: {json.dumps(status, indent=2)}")
    
    # Run
    controller.run()


if __name__ == '__main__':
    main()
