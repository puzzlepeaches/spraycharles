"""
Global configuration management for Spraycharles
Handles ~/.config/spraycharles/config.yaml
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from spraycharles.lib.logger import logger


class GlobalConfig:
    """Manages global configuration for Spraycharles"""
    
    DEFAULT_CONFIG = {
        'notifications': {
            'enabled': False,
            'provider': None,  # 'slack', 'teams', 'discord'
            'webhook': None,
            'notify_on_success': True,
            'notify_on_completion': True,
            'notify_on_pause': True
        },
        'output': {
            'default_dir': '~/.spraycharles',
            'save_last_config': True,
            'last_config_location': 'current'  # 'current' or 'global'
        },
        'spray': {
            'default_timeout': 5,
            'default_jitter': None,
            'default_jitter_min': None
        }
    }
    
    def __init__(self, auto_load=True):
        """Initialize global config"""
        self.config_dir = Path.home() / '.config' / 'spraycharles'
        self.config_file = self.config_dir / 'config.yaml'
        self.config = self.DEFAULT_CONFIG.copy()
        if auto_load:
            self._ensure_config_dir()
            self.load()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """Load config from file, create with defaults if doesn't exist"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f) or {}
                    # Deep merge with defaults
                    self.config = self._deep_merge(self.DEFAULT_CONFIG, loaded_config)
                    logger.debug(f"Loaded global config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Error loading global config: {e}, using defaults")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save()
            logger.debug(f"Created default global config at {self.config_file}")
        
        return self.config
    
    def save(self):
        """Save current config to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                f.write("\n# Spraycharles Global Configuration\n")
                f.write("# This file is automatically created and can be edited manually\n")
                f.write("# Location: ~/.config/spraycharles/config.yaml\n")
                f.write("#\n")
                f.write("# notifications:\n")
                f.write("#   enabled: Enable notification system\n")
                f.write("#   provider: Choose from 'slack', 'teams', or 'discord'\n")
                f.write("#   webhook: Your webhook URL\n")
                f.write("#   notify_on_success: Send notification on successful login\n")
                f.write("#   notify_on_completion: Send notification when spray completes\n")
                f.write("#   notify_on_pause: Send notification when spray is paused\n")
                f.write("#\n")
                f.write("# output:\n")
                f.write("#   default_dir: Default output directory for logs and results\n")
                f.write("#   save_last_config: Whether to save last-config.yaml after each run\n")
                f.write("#   last_config_location: Where to save last-config ('current' or 'global')\n")
                f.write("#\n")
                f.write("# spray:\n")
                f.write("#   default_timeout: Default timeout for web requests\n")
                f.write("#   default_jitter: Default jitter between requests\n")
                f.write("#   default_jitter_min: Default minimum jitter time\n")
            logger.debug(f"Saved global config to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving global config: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation
        Example: config.get('notifications.webhook')
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set config value using dot notation
        Example: config.set('notifications.webhook', 'https://...')
        """
        keys = key_path.split('.')
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        self.save()
    
    def update_from_cli(self, **kwargs):
        """
        Update config from CLI arguments
        Only updates non-None values
        """
        if kwargs.get('notify') and kwargs.get('webhook'):
            self.config['notifications']['enabled'] = True
            self.config['notifications']['provider'] = str(kwargs['notify']).lower()
            self.config['notifications']['webhook'] = kwargs['webhook']
            self.save()
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return self.config.get('notifications', {})
    
    def _deep_merge(self, default: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = default.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def show(self):
        """Display current configuration"""
        return yaml.dump(self.config, default_flow_style=False, sort_keys=False)


# Global instance
global_config = GlobalConfig()