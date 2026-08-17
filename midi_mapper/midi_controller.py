"""MIDI controller for sending CC messages."""

import logging
from typing import Optional, Dict, Any
import mido
from mido import MidiFile, MidiTrack, Message

logger = logging.getLogger(__name__)


class MIDIController:
    """Controller for sending MIDI CC (Control Change) messages."""
    
    def __init__(self, output_device: int = 0):
        """
        Initialize MIDI controller.
        
        Args:
            output_device: Index of MIDI output device
        """
        self.output_device = output_device
        self.output: Optional[mido.ports.BaseOutput] = None
        self._connected = False
        self._last_sent_values: Dict[int, int] = {}
    
    def initialize(self) -> bool:
        """
        Initialize MIDI output device.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            outputs = mido.get_output_names()
            
            if not outputs:
                logger.warning("No MIDI output devices available")
                logger.info("Available outputs: %s", outputs)
                # Still initialize - might work with virtual ports
            
            self.output = mido.open_output(outputs[self.output_device])
            self._connected = True
            logger.info(f"MIDI output initialized: {self.output.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MIDI output: {e}")
            logger.info("Available MIDI outputs: %s", mido.get_output_names())
            return False
    
    def send_cc(self, cc_number: int, value: int, channel: int = 0) -> bool:
        """
        Send a MIDI Control Change message.
        
        Args:
            cc_number: CC number (0-127)
            value: CC value (0-127)
            channel: MIDI channel (0-15)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected or self.output is None:
            logger.warning("MIDI output not connected")
            return False
        
        try:
            # Clamp values
            cc_number = max(0, min(127, int(cc_number)))
            value = max(0, min(127, int(value)))
            
            # Only send if value changed (prevents flooding)
            key = (cc_number, channel)
            if key in self._last_sent_values and self._last_sent_values[key] == value:
                return True
            
            msg = Message('control_change', 
                         control=cc_number, 
                         value=value, 
                         channel=channel)
            self.output.send(msg)
            
            self._last_sent_values[key] = value
            logger.debug(f"Sent CC: {cc_number}={value} (ch{channel})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send MIDI CC: {e}")
            return False
    
    def send_note_on(self, note: int, velocity: int = 100, 
                     channel: int = 0) -> bool:
        """Send a Note On message."""
        if not self._connected or self.output is None:
            return False
        
        try:
            note = max(0, min(127, int(note)))
            velocity = max(0, min(127, int(velocity)))
            
            msg = Message('note_on', note=note, velocity=velocity, channel=channel)
            self.output.send(msg)
            logger.debug(f"Sent Note On: {note} vel={velocity}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Note On: {e}")
            return False
    
    def send_note_off(self, note: int, channel: int = 0) -> bool:
        """Send a Note Off message."""
        if not self._connected or self.output is None:
            return False
        
        try:
            note = max(0, min(127, int(note)))
            msg = Message('note_off', note=note, channel=channel)
            self.output.send(msg)
            logger.debug(f"Sent Note Off: {note}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Note Off: {e}")
            return False
    
    def send_pitch_bend(self, value: int, channel: int = 0) -> bool:
        """
        Send a Pitch Bend message.
        
        Args:
            value: Pitch bend value (-8192 to 8191, 0 = center)
            channel: MIDI channel
        """
        if not self._connected or self.output is None:
            return False
        
        try:
            value = max(-8192, min(8191, int(value)))
            msg = Message('pitchwheel', pitch=value, channel=channel)
            self.output.send(msg)
            logger.debug(f"Sent Pitch Bend: {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Pitch Bend: {e}")
            return False
    
    def send_aftertouch(self, value: int, channel: int = 0) -> bool:
        """
        Send channel aftertouch.
        
        Args:
            value: Aftertouch value (0-127)
            channel: MIDI channel
        """
        if not self._connected or self.output is None:
            return False
        
        try:
            value = max(0, min(127, int(value)))
            msg = Message('aftertouch', value=value, channel=channel)
            self.output.send(msg)
            logger.debug(f"Sent Aftertouch: {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Aftertouch: {e}")
            return False
    
    def list_outputs(self) -> list[str]:
        """List available MIDI output devices."""
        return mido.get_output_names()
    
    def close(self):
        """Close MIDI output."""
        if self.output:
            self.output.close()
            self._connected = False
            logger.info("MIDI output closed")
    
    @property
    def is_connected(self) -> bool:
        """Check if MIDI output is connected."""
        return self._connected
    
    @property
    def device_name(self) -> Optional[str]:
        """Get the name of the connected device."""
        if self.output:
            return self.output.name
        return None
