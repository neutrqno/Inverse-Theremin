"""
Performance Metrics Tracking
Monitor FPS, latency, MIDI messages, and system health.
"""

import time
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrameMetrics:
    """Metrics for a single frame."""
    timestamp: float
    capture_time: float  # ms
    detection_time: float  # ms
    mapping_time: float  # ms
    midi_time: float  # ms
    total_time: float  # ms
    fps: float
    hand_count: int = 0
    confidence: float = 0.0


class PerformanceMonitor:
    """Monitor system performance metrics."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Number of frames to keep in rolling window
        """
        self.window_size = window_size
        self.frame_metrics: deque = deque(maxlen=window_size)
        
        # MIDI tracking
        self.midi_messages_sent = 0
        self.midi_errors = 0
        
        # Hand detection tracking
        self.detections_total = 0
        self.detections_failed = 0
        
        # Timing
        self.start_time = time.time()
        self.uptime = 0.0
        
        # Performance thresholds (in ms)
        self.threshold_capture = 50  # Should capture in <50ms
        self.threshold_detection = 100  # Should detect in <100ms
        self.threshold_total = 200  # Should process in <200ms
    
    def record_frame(self, metrics: FrameMetrics) -> None:
        """Record metrics for a frame."""
        self.frame_metrics.append(metrics)
        self.uptime = time.time() - self.start_time
    
    def record_midi_sent(self, count: int = 1) -> None:
        """Record MIDI messages sent."""
        self.midi_messages_sent += count
    
    def record_midi_error(self) -> None:
        """Record MIDI error."""
        self.midi_errors += 1
    
    def record_detection(self, success: bool) -> None:
        """Record hand detection attempt."""
        self.detections_total += 1
        if not success:
            self.detections_failed += 1
    
    def get_fps(self) -> float:
        """Get current average FPS."""
        if len(self.frame_metrics) < 2:
            return 0.0
        
        oldest = self.frame_metrics[0]
        newest = self.frame_metrics[-1]
        time_span = newest.timestamp - oldest.timestamp
        
        if time_span == 0:
            return 0.0
        
        return len(self.frame_metrics) / time_span
    
    def get_average_frame_time(self) -> float:
        """Get average frame processing time in ms."""
        if not self.frame_metrics:
            return 0.0
        
        total_time = sum(f.total_time for f in self.frame_metrics)
        return total_time / len(self.frame_metrics)
    
    def get_latency(self) -> float:
        """Get average latency (hand detection to MIDI output) in ms."""
        if not self.frame_metrics:
            return 0.0
        
        latencies = []
        for f in self.frame_metrics:
            latency = f.detection_time + f.mapping_time + f.midi_time
            latencies.append(latency)
        
        return sum(latencies) / len(latencies)
    
    def get_average_times(self) -> Dict[str, float]:
        """Get average times for each processing stage."""
        if not self.frame_metrics:
            return {}
        
        return {
            "capture": sum(f.capture_time for f in self.frame_metrics) / len(self.frame_metrics),
            "detection": sum(f.detection_time for f in self.frame_metrics) / len(self.frame_metrics),
            "mapping": sum(f.mapping_time for f in self.frame_metrics) / len(self.frame_metrics),
            "midi": sum(f.midi_time for f in self.frame_metrics) / len(self.frame_metrics),
            "total": sum(f.total_time for f in self.frame_metrics) / len(self.frame_metrics)
        }
    
    def get_detection_stats(self) -> Dict:
        """Get hand detection statistics."""
        if self.detections_total == 0:
            return {}
        
        success_rate = (self.detections_total - self.detections_failed) / self.detections_total * 100
        
        return {
            "total_attempts": self.detections_total,
            "successful": self.detections_total - self.detections_failed,
            "failed": self.detections_failed,
            "success_rate": success_rate
        }
    
    def get_midi_stats(self) -> Dict:
        """Get MIDI statistics."""
        return {
            "messages_sent": self.midi_messages_sent,
            "errors": self.midi_errors,
            "messages_per_second": self.midi_messages_sent / self.uptime if self.uptime > 0 else 0,
            "error_rate": self.midi_errors / self.midi_messages_sent * 100 if self.midi_messages_sent > 0 else 0
        }
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        avg_times = self.get_average_times()
        
        return {
            "uptime_seconds": self.uptime,
            "fps": self.get_fps(),
            "average_frame_time_ms": self.get_average_frame_time(),
            "latency_ms": self.get_latency(),
            "timing": avg_times,
            "detection": self.get_detection_stats(),
            "midi": self.get_midi_stats(),
            "health": self.get_health_status()
        }
    
    def get_health_status(self) -> Dict:
        """Get system health status with warnings."""
        health = {
            "status": "healthy",
            "warnings": []
        }
        
        if self.get_fps() < 20:
            health["warnings"].append("Low FPS (< 20)")
            health["status"] = "degraded"
        
        avg_frame_time = self.get_average_frame_time()
        if avg_frame_time > self.threshold_total:
            health["warnings"].append(f"Slow frame processing ({avg_frame_time:.1f}ms > {self.threshold_total}ms)")
            health["status"] = "degraded"
        
        detection_stats = self.get_detection_stats()
        if detection_stats.get("success_rate", 100) < 70:
            health["warnings"].append(f"Low detection success ({detection_stats['success_rate']:.1f}%)")
            health["status"] = "degraded"
        
        midi_stats = self.get_midi_stats()
        if midi_stats.get("error_rate", 0) > 5:
            health["warnings"].append(f"High MIDI error rate ({midi_stats['error_rate']:.1f}%)")
            health["status"] = "degraded"
        
        return health
    
    def get_bottleneck(self) -> str:
        """Identify the main performance bottleneck."""
        avg_times = self.get_average_times()
        
        if not avg_times:
            return "unknown"
        
        bottleneck = max(avg_times, key=avg_times.get)
        return f"{bottleneck} ({avg_times[bottleneck]:.1f}ms)"
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.frame_metrics.clear()
        self.midi_messages_sent = 0
        self.midi_errors = 0
        self.detections_total = 0
        self.detections_failed = 0
        self.start_time = time.time()
        self.uptime = 0.0
        logger.info("Metrics reset")


class PerformanceProfiler:
    """Context manager for profiling code blocks."""
    
    def __init__(self, name: str):
        """
        Initialize profiler.
        
        Args:
            name: Name of the code block being profiled
        """
        self.name = name
        self.start_time = None
        self.elapsed_ms = None
    
    def __enter__(self):
        """Start profiling."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End profiling."""
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        logger.debug(f"{self.name}: {self.elapsed_ms:.2f}ms")
    
    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed_ms or 0.0


class MetricsLogger:
    """Log metrics to file and console."""
    
    def __init__(self, monitor: PerformanceMonitor, log_interval: int = 100):
        """
        Initialize metrics logger.
        
        Args:
            monitor: PerformanceMonitor instance
            log_interval: Log summary every N frames
        """
        self.monitor = monitor
        self.log_interval = log_interval
        self.frame_count = 0
    
    def on_frame(self) -> None:
        """Call after each frame processed."""
        self.frame_count += 1
        
        if self.frame_count % self.log_interval == 0:
            self.log_summary()
    
    def log_summary(self) -> None:
        """Log performance summary."""
        summary = self.monitor.get_performance_summary()
        
        logger.info(
            f"Performance: FPS={summary['fps']:.1f} | "
            f"Frame={summary['average_frame_time_ms']:.1f}ms | "
            f"Latency={summary['latency_ms']:.1f}ms | "
            f"Health={summary['health']['status']}"
        )
        
        if summary['health']['warnings']:
            for warning in summary['health']['warnings']:
                logger.warning(f"  ⚠ {warning}")
        
        bottleneck = self.monitor.get_bottleneck()
        logger.debug(f"  Bottleneck: {bottleneck}")
