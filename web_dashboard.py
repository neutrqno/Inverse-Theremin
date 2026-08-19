"""
Web Dashboard for Inverse Theremin
Real-time monitoring and control via web interface.
"""

from flask import Flask, render_template_string, jsonify, request
from threading import Thread
import json
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class WebDashboard:
    """Web-based dashboard for monitoring and controlling Inverse Theremin."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, 
                 performance_monitor=None, preset_manager=None):
        """
        Initialize web dashboard.
        
        Args:
            host: Server host
            port: Server port
            performance_monitor: PerformanceMonitor instance
            preset_manager: PresetManager instance
        """
        self.host = host
        self.port = port
        self.performance_monitor = performance_monitor
        self.preset_manager = preset_manager
        
        # State
        self.current_status = {
            "mode": "hand_tracking",
            "is_running": False,
            "hand_count": 0,
            "fps": 0.0,
            "latency_ms": 0.0
        }
        
        # Callbacks
        self.on_preset_change: Optional[Callable] = None
        self.on_gesture_trigger: Optional[Callable] = None
        self.on_mode_change: Optional[Callable] = None
        self.on_calibrate: Optional[Callable] = None
        
        # Create Flask app
        self.app = Flask(__name__)
        self._setup_routes()
        
        # Server thread
        self.server_thread = None
        self.is_running = False
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template_string(self.get_html_template())
        
        @self.app.route('/api/status')
        def api_status():
            """Get current system status."""
            return jsonify(self._get_status())
        
        @self.app.route('/api/presets')
        def api_presets():
            """Get list of presets."""
            if self.preset_manager is None:
                return jsonify([])
            
            presets = self.preset_manager.list_presets()
            return jsonify(presets)
        
        @self.app.route('/api/presets/<name>', methods=['GET'])
        def api_get_preset(name):
            """Get preset details."""
            if self.preset_manager is None:
                return jsonify({"error": "Preset manager not available"}), 400
            
            preset = self.preset_manager.get_preset(name)
            if preset is None:
                return jsonify({"error": "Preset not found"}), 404
            
            return jsonify(preset)
        
        @self.app.route('/api/presets/<name>/load', methods=['POST'])
        def api_load_preset(name):
            """Load a preset."""
            if self.preset_manager is None:
                return jsonify({"error": "Preset manager not available"}), 400
            
            config = self.preset_manager.load_preset(name)
            
            if self.on_preset_change:
                try:
                    self.on_preset_change(name, config)
                except Exception as e:
                    logger.error(f"Error in preset change callback: {e}")
                    return jsonify({"error": str(e)}), 500
            
            return jsonify({
                "success": True,
                "preset": name,
                "config": config
            })
        
        @self.app.route('/api/presets', methods=['POST'])
        def api_create_preset():
            """Create new preset."""
            if self.preset_manager is None:
                return jsonify({"error": "Preset manager not available"}), 400
            
            data = request.json
            name = data.get('name')
            config = data.get('config', {})
            description = data.get('description', '')
            
            if not name:
                return jsonify({"error": "Preset name required"}), 400
            
            success = self.preset_manager.create_preset(name, config, description)
            
            if success:
                return jsonify({"success": True, "preset": name})
            else:
                return jsonify({"error": "Failed to create preset"}), 500
        
        @self.app.route('/api/presets/<name>', methods=['DELETE'])
        def api_delete_preset(name):
            """Delete a preset."""
            if self.preset_manager is None:
                return jsonify({"error": "Preset manager not available"}), 400
            
            success = self.preset_manager.delete_preset(name)
            
            if success:
                return jsonify({"success": True})
            else:
                return jsonify({"error": "Failed to delete preset"}), 500
        
        @self.app.route('/api/calibrate', methods=['POST'])
        def api_calibrate():
            """Trigger calibration wizard."""
            if self.on_calibrate:
                try:
                    self.on_calibrate()
                    return jsonify({"success": True})
                except Exception as e:
                    logger.error(f"Calibration error: {e}")
                    return jsonify({"error": str(e)}), 500
            
            return jsonify({"error": "Calibration not available"}), 400
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Get performance metrics."""
            if self.performance_monitor is None:
                return jsonify({})
            
            summary = self.performance_monitor.get_performance_summary()
            return jsonify(summary)
        
        @self.app.route('/api/mode', methods=['POST'])
        def api_change_mode():
            """Change operating mode."""
            data = request.json
            mode = data.get('mode')
            
            if mode not in ['hand_tracking', 'sensor']:
                return jsonify({"error": "Invalid mode"}), 400
            
            if self.on_mode_change:
                try:
                    self.on_mode_change(mode)
                except Exception as e:
                    logger.error(f"Mode change error: {e}")
                    return jsonify({"error": str(e)}), 500
            
            self.current_status['mode'] = mode
            return jsonify({"success": True, "mode": mode})
        
        @self.app.route('/api/gesture', methods=['POST'])
        def api_trigger_gesture():
            """Trigger a gesture action."""
            data = request.json
            gesture = data.get('gesture')
            
            if self.on_gesture_trigger:
                try:
                    self.on_gesture_trigger(gesture)
                except Exception as e:
                    logger.error(f"Gesture error: {e}")
                    return jsonify({"error": str(e)}), 500
            
            return jsonify({"success": True})
    
    def _get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        status = self.current_status.copy()
        
        if self.performance_monitor:
            status['fps'] = self.performance_monitor.get_fps()
            status['latency_ms'] = self.performance_monitor.get_latency()
            status['health'] = self.performance_monitor.get_health_status()
        
        return status
    
    def update_status(self, **kwargs) -> None:
        """Update dashboard status."""
        self.current_status.update(kwargs)
    
    def start(self, debug: bool = False) -> None:
        """Start web server."""
        if self.is_running:
            logger.warning("Dashboard already running")
            return
        
        self.is_running = True
        self.server_thread = Thread(
            target=lambda: self.app.run(
                host=self.host, 
                port=self.port, 
                debug=debug, 
                use_reloader=False,
                threaded=True
            ),
            daemon=True
        )
        self.server_thread.start()
        logger.info(f"Web dashboard started at http://{self.host}:{self.port}")
    
    def stop(self) -> None:
        """Stop web server."""
        self.is_running = False
        logger.info("Web dashboard stopped")
    
    def get_html_template(self) -> str:
        """Get HTML template for dashboard."""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Inverse Theremin Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #00d4ff, #0099ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #aaa;
            font-size: 1.1em;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: #0f3460;
            border: 1px solid #16213e;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: #00d4ff;
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
        }
        
        .card-title {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #00d4ff;
            font-weight: 600;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: rgba(0, 212, 255, 0.05);
            border-radius: 5px;
        }
        
        .metric-label {
            color: #aaa;
        }
        
        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .status-healthy {
            background: rgba(0, 255, 0, 0.2);
            color: #00ff00;
            border: 1px solid #00ff00;
        }
        
        .status-degraded {
            background: rgba(255, 165, 0, 0.2);
            color: #ffa500;
            border: 1px solid #ffa500;
        }
        
        .status-error {
            background: rgba(255, 0, 0, 0.2);
            color: #ff0000;
            border: 1px solid #ff0000;
        }
        
        .button-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }
        
        button {
            padding: 12px 20px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #00d4ff, #0099ff);
            color: #fff;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 212, 255, 0.4);
        }
        
        .btn-secondary {
            background: #16213e;
            color: #00d4ff;
            border: 2px solid #00d4ff;
        }
        
        .btn-secondary:hover {
            background: #00d4ff;
            color: #0f3460;
        }
        
        .btn-danger {
            background: #ff4444;
            color: #fff;
        }
        
        .btn-danger:hover {
            background: #ff2222;
        }
        
        .presets-list {
            margin-top: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .preset-item {
            padding: 10px;
            margin: 5px 0;
            background: rgba(0, 212, 255, 0.1);
            border-left: 3px solid #00d4ff;
            border-radius: 3px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .preset-item:hover {
            background: rgba(0, 212, 255, 0.2);
        }
        
        .preset-item.active {
            background: rgba(0, 212, 255, 0.3);
            border-left-color: #00ff00;
        }
        
        .preset-name {
            flex: 1;
        }
        
        .preset-desc {
            font-size: 0.9em;
            color: #888;
            margin-top: 3px;
        }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #0099ff);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .warning {
            color: #ffa500;
            font-size: 0.9em;
            margin-top: 5px;
            padding: 5px;
            background: rgba(255, 165, 0, 0.1);
            border-left: 3px solid #ffa500;
            border-radius: 3px;
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 1.8em;
            }
            
            .dashboard {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎵 INVERSE THEREMIN</h1>
            <p class="subtitle">Webcam-Based MIDI Controller Dashboard</p>
        </header>
        
        <div class="dashboard">
            <!-- Status Card -->
            <div class="card">
                <div class="card-title">🔌 System Status</div>
                <div id="status-content">
                    <div class="metric">
                        <span class="metric-label">Mode:</span>
                        <span class="metric-value" id="mode">Loading...</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Status:</span>
                        <span id="health-badge" class="status-badge status-healthy">Healthy</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Uptime:</span>
                        <span class="metric-value" id="uptime">0s</span>
                    </div>
                </div>
            </div>
            
            <!-- Performance Card -->
            <div class="card">
                <div class="card-title">⚡ Performance</div>
                <div class="metric">
                    <span class="metric-label">FPS:</span>
                    <span class="metric-value" id="fps">0.0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Latency:</span>
                    <span class="metric-value" id="latency">0 ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Frame Time:</span>
                    <span class="metric-value" id="frame-time">0 ms</span>
                </div>
                <div id="warnings-container"></div>
            </div>
            
            <!-- Hand Tracking Card -->
            <div class="card">
                <div class="card-title">✋ Hand Tracking</div>
                <div class="metric">
                    <span class="metric-label">Hands Detected:</span>
                    <span class="metric-value" id="hand-count">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Detection Success:</span>
                    <span class="metric-value" id="detection-rate">0%</span>
                </div>
                <button class="btn-primary" onclick="startCalibration()">
                    🎯 Run Calibration
                </button>
            </div>
            
            <!-- MIDI Card -->
            <div class="card">
                <div class="card-title">🎹 MIDI</div>
                <div class="metric">
                    <span class="metric-label">Messages/sec:</span>
                    <span class="metric-value" id="midi-rate">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Sent:</span>
                    <span class="metric-value" id="midi-total">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Errors:</span>
                    <span class="metric-value" id="midi-errors">0</span>
                </div>
            </div>
            
            <!-- Presets Card -->
            <div class="card">
                <div class="card-title">💾 Presets</div>
                <div class="presets-list" id="presets-list">
                    Loading presets...
                </div>
                <button class="btn-secondary" onclick="showNewPresetForm()" style="margin-top: 10px;">
                    ➕ New Preset
                </button>
            </div>
            
            <!-- Controls Card -->
            <div class="card">
                <div class="card-title">🎮 Controls</div>
                <div class="button-group">
                    <button class="btn-primary" onclick="changeMode('hand_tracking')">
                        📷 Hand Mode
                    </button>
                    <button class="btn-primary" onclick="changeMode('sensor')">
                        📡 Sensor Mode
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh status every 500ms
        setInterval(updateDashboard, 500);
        
        // Load presets on startup
        loadPresets();
        
        async function updateDashboard() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                document.getElementById('mode').textContent = status.mode.toUpperCase();
                document.getElementById('hand-count').textContent = status.hand_count;
                
                if (status.health) {
                    const badge = document.getElementById('health-badge');
                    badge.textContent = status.health.status.toUpperCase();
                    badge.className = 'status-badge status-' + status.health.status;
                    
                    const warningsContainer = document.getElementById('warnings-container');
                    warningsContainer.innerHTML = '';
                    if (status.health.warnings) {
                        status.health.warnings.forEach(warning => {
                            const div = document.createElement('div');
                            div.className = 'warning';
                            div.textContent = '⚠ ' + warning;
                            warningsContainer.appendChild(div);
                        });
                    }
                }
            } catch (error) {
                console.error('Error updating status:', error);
            }
            
            try {
                const response = await fetch('/api/metrics');
                const metrics = await response.json();
                
                if (metrics.fps) document.getElementById('fps').textContent = metrics.fps.toFixed(1);
                if (metrics.latency_ms) document.getElementById('latency').textContent = metrics.latency_ms.toFixed(1) + ' ms';
                if (metrics.average_frame_time_ms) document.getElementById('frame-time').textContent = metrics.average_frame_time_ms.toFixed(1) + ' ms';
                if (metrics.uptime_seconds) document.getElementById('uptime').textContent = Math.floor(metrics.uptime_seconds) + 's';
                
                if (metrics.detection) {
                    document.getElementById('detection-rate').textContent = metrics.detection.success_rate.toFixed(1) + '%';
                }
                
                if (metrics.midi) {
                    document.getElementById('midi-rate').textContent = metrics.midi.messages_per_second.toFixed(1);
                    document.getElementById('midi-total').textContent = metrics.midi.messages_sent;
                    document.getElementById('midi-errors').textContent = metrics.midi.errors;
                }
            } catch (error) {
                console.error('Error updating metrics:', error);
            }
        }
        
        async function loadPresets() {
            try {
                const response = await fetch('/api/presets');
                const presets = await response.json();
                
                const list = document.getElementById('presets-list');
                list.innerHTML = '';
                
                presets.forEach(preset => {
                    const div = document.createElement('div');
                    div.className = 'preset-item' + (preset.is_current ? ' active' : '');
                    div.innerHTML = `
                        <div>
                            <div class="preset-name">${preset.name}</div>
                            <div class="preset-desc">${preset.description || 'No description'}</div>
                        </div>
                        <button class="btn-secondary" onclick="loadPreset('${preset.name}')" style="margin-left: 10px;">
                            Load
                        </button>
                    `;
                    list.appendChild(div);
                });
            } catch (error) {
                console.error('Error loading presets:', error);
            }
        }
        
        async function loadPreset(name) {
            try {
                const response = await fetch(`/api/presets/${name}/load`, {method: 'POST'});
                const result = await response.json();
                
                if (result.success) {
                    loadPresets();
                    alert('Preset loaded: ' + name);
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error loading preset: ' + error);
            }
        }
        
        async function changeMode(mode) {
            try {
                const response = await fetch('/api/mode', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({mode: mode})
                });
                const result = await response.json();
                
                if (result.success) {
                    alert('Mode changed to: ' + mode);
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error changing mode: ' + error);
            }
        }
        
        async function startCalibration() {
            try {
                const response = await fetch('/api/calibrate', {method: 'POST'});
                const result = await response.json();
                
                if (result.success) {
                    alert('Calibration started. Check your main window.');
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error starting calibration: ' + error);
            }
        }
        
        function showNewPresetForm() {
            const name = prompt('Enter preset name:');
            if (name) {
                alert('Create preset feature coming soon!');
            }
        }
    </script>
</body>
</html>
        '''


# Example usage in main.py integration
def create_web_dashboard(performance_monitor, preset_manager, 
                         host: str = "127.0.0.1", port: int = 5000) -> WebDashboard:
    """Create and configure web dashboard."""
    dashboard = WebDashboard(
        host=host,
        port=port,
        performance_monitor=performance_monitor,
        preset_manager=preset_manager
    )
    return dashboard
