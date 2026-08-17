"""Filtering and smoothing for proximity values."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SmoothingFilter:
    """Exponential smoothing filter for proximity values."""
    
    def __init__(self, factor: float = 0.7):
        """
        Initialize smoothing filter.
        
        Args:
            factor: Smoothing factor (0-1). Lower = more smoothing, higher = more responsive
        """
        self.factor = max(0.0, min(1.0, factor))
        self._last_value: Optional[float] = None
    
    def apply(self, value: float) -> float:
        """
        Apply smoothing filter.
        
        Args:
            value: Input value
            
        Returns:
            Smoothed value
        """
        if self._last_value is None:
            self._last_value = value
            return value
        
        # Exponential smoothing: output = alpha * input + (1 - alpha) * last_output
        smoothed = (self.factor * value) + ((1.0 - self.factor) * self._last_value)
        self._last_value = smoothed
        
        return smoothed
    
    def set_factor(self, factor: float):
        """Set new smoothing factor."""
        self.factor = max(0.0, min(1.0, factor))
        logger.debug(f"Smoothing factor set to: {self.factor}")
    
    def reset(self):
        """Reset the filter state."""
        self._last_value = None


class DeadzoneFilter:
    """Deadzone filter to ignore values outside a range."""
    
    def __init__(self, min_threshold: float = 5, max_threshold: float = 250):
        """
        Initialize deadzone filter.
        
        Args:
            min_threshold: Minimum valid value
            max_threshold: Maximum valid value
        """
        self.min_threshold = float(min_threshold)
        self.max_threshold = float(max_threshold)
    
    def is_valid(self, value: float) -> bool:
        """Check if value is within valid range."""
        return self.min_threshold <= value <= self.max_threshold
    
    def apply(self, value: float, default: Optional[float] = None) -> Optional[float]:
        """
        Apply deadzone filter.
        
        Args:
            value: Input value
            default: Value to return if outside deadzone
            
        Returns:
            Original value if valid, default otherwise
        """
        if self.is_valid(value):
            return value
        return default
    
    def set_thresholds(self, min_threshold: float, max_threshold: float):
        """Update deadzone thresholds."""
        self.min_threshold = float(min_threshold)
        self.max_threshold = float(max_threshold)
        logger.debug(f"Deadzone set to: {min_threshold}-{max_threshold}")


class DebounceFilter:
    """Debounce filter to ignore rapid changes."""
    
    def __init__(self, threshold: int = 10):
        """
        Initialize debounce filter.
        
        Args:
            threshold: Minimum difference to register as new value
        """
        self.threshold = int(threshold)
        self._last_value: Optional[float] = None
    
    def should_update(self, value: float) -> bool:
        """Check if value difference exceeds threshold."""
        if self._last_value is None:
            self._last_value = value
            return True
        
        if abs(value - self._last_value) >= self.threshold:
            self._last_value = value
            return True
        
        return False
    
    def set_threshold(self, threshold: int):
        """Update debounce threshold."""
        self.threshold = int(threshold)
        logger.debug(f"Debounce threshold set to: {threshold}")


class FilterChain:
    """Chain multiple filters together."""
    
    def __init__(self):
        """Initialize filter chain."""
        self.filters: list = []
    
    def add_filter(self, filter_obj) -> 'FilterChain':
        """Add a filter to the chain."""
        self.filters.append(filter_obj)
        return self
    
    def apply(self, value: float) -> Optional[float]:
        """
        Apply all filters in sequence.
        
        Args:
            value: Input value
            
        Returns:
            Filtered value or None if filtered out
        """
        current = value
        
        for filter_obj in self.filters:
            if isinstance(filter_obj, DeadzoneFilter):
                current = filter_obj.apply(current, default=None)
                if current is None:
                    return None
            elif isinstance(filter_obj, SmoothingFilter):
                current = filter_obj.apply(current)
            elif isinstance(filter_obj, DebounceFilter):
                if not filter_obj.should_update(current):
                    return None
        
        return current
    
    def clear(self):
        """Clear all filters."""
        self.filters.clear()
