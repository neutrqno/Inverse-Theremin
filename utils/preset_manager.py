"""
Preset Management System
Save, load, and switch between control profiles for hand tracking and sensor modes.
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PresetManager:
    """Manage control presets for different instruments/effects."""
    
    def __init__(self, presets_dir: str = "presets"):
        """
        Initialize preset manager.
        
        Args:
            presets_dir: Directory to store preset files
        """
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.current_preset = None
        self._load_presets_cache()
    
    def _load_presets_cache(self) -> None:
        """Load all available presets into cache."""
        self.presets = {}
        for preset_file in self.presets_dir.glob("*.json"):
            try:
                with open(preset_file, 'r') as f:
                    preset_data = json.load(f)
                    preset_name = preset_file.stem
                    self.presets[preset_name] = preset_data
                    logger.debug(f"Loaded preset: {preset_name}")
            except Exception as e:
                logger.error(f"Failed to load preset {preset_file}: {e}")
    
    def create_preset(self, name: str, config: Dict, 
                     description: str = "", overwrite: bool = False) -> bool:
        """
        Create a new preset.
        
        Args:
            name: Preset name (used as filename)
            config: Configuration dictionary
            description: Optional description
            overwrite: Allow overwriting existing preset
            
        Returns:
            bool: Success status
        """
        if not name or not config:
            logger.error("Preset name and config are required")
            return False
        
        preset_file = self.presets_dir / f"{name}.json"
        
        if preset_file.exists() and not overwrite:
            logger.error(f"Preset '{name}' already exists. Set overwrite=True to replace.")
            return False
        
        try:
            preset_data = {
                "name": name,
                "description": description,
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "config": config
            }
            
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            self.presets[name] = preset_data
            logger.info(f"Created preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create preset '{name}': {e}")
            return False
    
    def load_preset(self, name: str) -> Optional[Dict]:
        """
        Load a preset by name.
        
        Args:
            name: Preset name
            
        Returns:
            Configuration dictionary or None if not found
        """
        if name not in self.presets:
            logger.error(f"Preset '{name}' not found")
            return None
        
        self.current_preset = name
        logger.info(f"Loaded preset: {name}")
        return self.presets[name].get("config", {})
    
    def get_preset(self, name: str) -> Optional[Dict]:
        """Get preset data (including metadata)."""
        return self.presets.get(name)
    
    def update_preset(self, name: str, config: Dict, description: str = None) -> bool:
        """
        Update an existing preset.
        
        Args:
            name: Preset name
            config: New configuration
            description: Optional new description
            
        Returns:
            bool: Success status
        """
        if name not in self.presets:
            logger.error(f"Preset '{name}' not found")
            return False
        
        try:
            preset_data = self.presets[name]
            preset_data["config"] = config
            preset_data["modified"] = datetime.now().isoformat()
            
            if description is not None:
                preset_data["description"] = description
            
            preset_file = self.presets_dir / f"{name}.json"
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            logger.info(f"Updated preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update preset '{name}': {e}")
            return False
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset.
        
        Args:
            name: Preset name
            
        Returns:
            bool: Success status
        """
        if name not in self.presets:
            logger.error(f"Preset '{name}' not found")
            return False
        
        try:
            preset_file = self.presets_dir / f"{name}.json"
            preset_file.unlink()
            del self.presets[name]
            
            if self.current_preset == name:
                self.current_preset = None
            
            logger.info(f"Deleted preset: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete preset '{name}': {e}")
            return False
    
    def list_presets(self) -> List[Dict]:
        """
        Get list of all available presets with metadata.
        
        Returns:
            List of preset information dictionaries
        """
        presets_list = []
        for name, data in self.presets.items():
            presets_list.append({
                "name": name,
                "description": data.get("description", ""),
                "created": data.get("created", ""),
                "modified": data.get("modified", ""),
                "is_current": name == self.current_preset
            })
        
        return sorted(presets_list, key=lambda x: x["modified"], reverse=True)
    
    def duplicate_preset(self, source_name: str, new_name: str, 
                        description: str = None) -> bool:
        """
        Duplicate an existing preset.
        
        Args:
            source_name: Name of preset to duplicate
            new_name: Name for the new preset
            description: Optional description for new preset
            
        Returns:
            bool: Success status
        """
        if source_name not in self.presets:
            logger.error(f"Source preset '{source_name}' not found")
            return False
        
        if new_name in self.presets:
            logger.error(f"Preset '{new_name}' already exists")
            return False
        
        try:
            source_config = self.presets[source_name]["config"].copy()
            desc = description or f"Copy of {source_name}"
            
            return self.create_preset(new_name, source_config, desc)
            
        except Exception as e:
            logger.error(f"Failed to duplicate preset: {e}")
            return False
    
    def export_preset(self, name: str, export_path: str) -> bool:
        """Export preset to a custom location."""
        if name not in self.presets:
            logger.error(f"Preset '{name}' not found")
            return False
        
        try:
            with open(export_path, 'w') as f:
                json.dump(self.presets[name], f, indent=2)
            logger.info(f"Exported preset '{name}' to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export preset: {e}")
            return False
    
    def import_preset(self, import_path: str, new_name: str = None) -> bool:
        """Import preset from external file."""
        try:
            with open(import_path, 'r') as f:
                preset_data = json.load(f)
            
            name = new_name or preset_data.get("name", Path(import_path).stem)
            config = preset_data.get("config", preset_data)
            description = preset_data.get("description", "")
            
            return self.create_preset(name, config, description, overwrite=True)
            
        except Exception as e:
            logger.error(f"Failed to import preset: {e}")
            return False
    
    def get_current_preset(self) -> Optional[str]:
        """Get name of currently loaded preset."""
        return self.current_preset
    
    def create_default_presets(self) -> None:
        """Create a set of useful default presets."""
        defaults = {
            "filter_cutoff": {
                "description": "High-pass filter cutoff (responsive)",
                "config": {
                    "hand_tracking": {
                        "control_mode": "distance",
                        "midi_cc": 74,
                        "invert": False,
                        "smoothing_factor": 0.5
                    },
                    "mapping": {
                        "curve": "exponential",
                        "min_value": 0,
                        "max_value": 127
                    }
                }
            },
            "reverb_mix": {
                "description": "Reverb wet/dry mix (smooth)",
                "config": {
                    "hand_tracking": {
                        "control_mode": "distance",
                        "midi_cc": 91,
                        "invert": False,
                        "smoothing_factor": 0.8
                    },
                    "mapping": {
                        "curve": "linear",
                        "min_value": 0,
                        "max_value": 127
                    }
                }
            },
            "volume": {
                "description": "Master volume control",
                "config": {
                    "hand_tracking": {
                        "control_mode": "distance",
                        "midi_cc": 7,
                        "invert": False,
                        "smoothing_factor": 0.7
                    },
                    "mapping": {
                        "curve": "logarithmic",
                        "min_value": 0,
                        "max_value": 127
                    }
                }
            },
            "dual_hand_xy": {
                "description": "Dual hand: X→CC1, Y→CC11",
                "config": {
                    "hand_tracking": {
                        "control_mode": "mixed",
                        "multi_hand": True,
                        "hand1_cc_x": 1,
                        "hand1_cc_y": 11,
                        "smoothing_factor": 0.6
                    },
                    "mapping": {
                        "curve": "linear",
                        "min_value": 0,
                        "max_value": 127
                    }
                }
            },
            "pad_performance": {
                "description": "Optimized for pad/ambient sounds",
                "config": {
                    "hand_tracking": {
                        "control_mode": "distance",
                        "midi_cc": 91,
                        "invert": False,
                        "smoothing_factor": 0.9
                    },
                    "mapping": {
                        "curve": "logarithmic",
                        "min_value": 40,
                        "max_value": 127
                    },
                    "processing": {
                        "deadzone": {
                            "enabled": True,
                            "min_threshold": 10,
                            "max_threshold": 245
                        }
                    }
                }
            },
            "fast_synth": {
                "description": "Quick, responsive synth control",
                "config": {
                    "hand_tracking": {
                        "control_mode": "vertical",
                        "midi_cc": 74,
                        "invert": False,
                        "smoothing_factor": 0.3
                    },
                    "mapping": {
                        "curve": "exponential",
                        "min_value": 0,
                        "max_value": 127
                    }
                }
            }
        }
        
        for name, data in defaults.items():
            if name not in self.presets:
                self.create_preset(
                    name,
                    data["config"],
                    data["description"]
                )
                logger.info(f"Created default preset: {name}")
