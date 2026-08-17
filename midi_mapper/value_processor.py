"""Value processing for mapping proximity to MIDI."""

import logging
import math
from typing import Callable
from enum import Enum

logger = logging.getLogger(__name__)


class MappingCurve(Enum):
    """Available mapping curves for proximity-to-MIDI conversion."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    QUADRATIC = "quadratic"
    CUBIC = "cubic"
    SQRT = "sqrt"


class ValueProcessor:
    """Processes proximity values and maps them to MIDI CC values."""
    
    def __init__(self, 
                 proximity_min: float = 0,
                 proximity_max: float = 255,
                 midi_min: int = 0,
                 midi_max: int = 127,
                 curve: str = "linear",
                 invert: bool = False):
        """
        Initialize value processor.
        
        Args:
            proximity_min: Minimum proximity input value
            proximity_max: Maximum proximity input value
            midi_min: Minimum MIDI output value (0-127)
            midi_max: Maximum MIDI output value (0-127)
            curve: Mapping curve type
            invert: Invert the mapping (far = min, close = max)
        """
        self.proximity_min = float(proximity_min)
        self.proximity_max = float(proximity_max)
        self.midi_min = max(0, min(127, int(midi_min)))
        self.midi_max = max(0, min(127, int(midi_max)))
        
        try:
            self.curve = MappingCurve(curve)
        except ValueError:
            logger.warning(f"Unknown curve '{curve}', using linear")
            self.curve = MappingCurve.LINEAR
        
        self.invert = invert
        self._curve_func: Callable[[float], float] = self._get_curve_function()
    
    def process(self, proximity_value: float) -> int:
        """
        Process a proximity value and return MIDI CC value.
        
        Args:
            proximity_value: Raw proximity input (0-255 typical)
            
        Returns:
            MIDI CC value (0-127)
        """
        # Normalize to 0-1 range
        proximity_range = self.proximity_max - self.proximity_min
        if proximity_range <= 0:
            normalized = 0.0
        else:
            normalized = (proximity_value - self.proximity_min) / proximity_range
        
        # Clamp to 0-1
        normalized = max(0.0, min(1.0, normalized))
        
        # Apply inversion if needed
        if self.invert:
            normalized = 1.0 - normalized
        
        # Apply curve function
        curved = self._curve_func(normalized)
        
        # Map to MIDI range
        midi_range = self.midi_max - self.midi_min
        midi_value = self.midi_min + (curved * midi_range)
        
        # Convert to integer and clamp
        midi_value = int(round(midi_value))
        midi_value = max(self.midi_min, min(self.midi_max, midi_value))
        
        return midi_value
    
    def _get_curve_function(self) -> Callable[[float], float]:
        """Get the curve mapping function."""
        curve_map = {
            MappingCurve.LINEAR: lambda x: x,
            MappingCurve.EXPONENTIAL: lambda x: x ** 2,
            MappingCurve.LOGARITHMIC: lambda x: math.sqrt(x),
            MappingCurve.QUADRATIC: lambda x: x ** 2,
            MappingCurve.CUBIC: lambda x: x ** 3,
            MappingCurve.SQRT: lambda x: math.sqrt(x),
        }
        return curve_map.get(self.curve, lambda x: x)
    
    def set_curve(self, curve: str):
        """Change the mapping curve."""
        try:
            self.curve = MappingCurve(curve)
            self._curve_func = self._get_curve_function()
            logger.info(f"Curve changed to: {curve}")
        except ValueError:
            logger.error(f"Invalid curve: {curve}")
    
    def set_range(self, proximity_min: float, proximity_max: float):
        """Update proximity input range."""
        self.proximity_min = float(proximity_min)
        self.proximity_max = float(proximity_max)
        logger.info(f"Proximity range: {proximity_min}-{proximity_max}")
    
    def set_midi_range(self, midi_min: int, midi_max: int):
        """Update MIDI output range."""
        self.midi_min = max(0, min(127, int(midi_min)))
        self.midi_max = max(0, min(127, int(midi_max)))
        logger.info(f"MIDI range: {self.midi_min}-{self.midi_max}")
    
    def get_curve_preview(self, steps: int = 11) -> list[int]:
        """
        Get a preview of the mapping curve.
        
        Args:
            steps: Number of points to sample
            
        Returns:
            List of MIDI values for evenly spaced proximity inputs
        """
        preview = []
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            proximity = self.proximity_min + t * (self.proximity_max - self.proximity_min)
            midi_value = self.process(proximity)
            preview.append(midi_value)
        return preview
