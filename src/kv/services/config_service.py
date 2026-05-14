"""Configuration file service with YAML support"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigService:
    """Configuration file management service"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration service

        Args:
            config_dir: Configuration directory path (defaults to KNOWIT_HOME/config)
        """
        from kv.core.config import config

        self.config_dir = config_dir or config.config_dir
        self.config_file = self.config_dir / "config.yaml"

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Returns:
            Configuration dictionary
        """
        if not YAML_AVAILABLE:
            return {}

        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
            return {}

    def save_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        Save configuration to YAML file

        Args:
            config_dict: Configuration dictionary

        Returns:
            True if successful
        """
        if not YAML_AVAILABLE:
            print("Warning: PyYAML not installed, cannot save config file")
            print("Install with: pip install pyyaml")
            return False

        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)

            return True
        except Exception as e:
            print(f"Error: Failed to save config file: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation)

        Args:
            key: Configuration key (e.g., "dedup.threshold")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config_dict = self.load_config()

        # Support nested keys with dot notation
        keys = key.split('.')
        value = config_dict

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value by key (supports nested keys with dot notation)

        Args:
            key: Configuration key (e.g., "dedup.threshold")
            value: Value to set

        Returns:
            True if successful
        """
        config_dict = self.load_config()

        # Support nested keys with dot notation
        keys = key.split('.')
        current = config_dict

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

        return self.save_config(config_dict)

    def init_default_config(self) -> bool:
        """
        Initialize default configuration file

        Returns:
            True if successful
        """
        default_config = {
            'dedup': {
                'threshold': 0.75,
                'enabled': True,
            },
            'scraper': {
                'timeout': 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'export': {
                'default_format': 'html',
                'open_in_browser': False,
                'organize_by': 'date',  # 'date' or 'collection'
                'directory': None,  # None = default (KNOWIT_HOME/exports)
            },
            'auto_export': {
                'enabled': True,  # Auto-export enabled by default
                'directory': None,  # None = default (KNOWIT_HOME/exports)
                'formats': ['html', 'pdf'],  # Export formats
                'clean_html': True,  # Clean HTML content
                'use_kami': True,  # Use Kami full format with cover page
                'organize_by': 'collection',  # Organize by: 'date', 'collection', or 'none'
                'on_error': 'warn',  # Error handling: 'warn' or 'ignore'
            },
            'search': {
                'limit': 20,
                'preview_length': 200,
            },
            'display': {
                'date_format': '%Y-%m-%d %H:%M',
                'max_preview_length': 500,
            },
        }

        return self.save_config(default_config)

    def get_config_file_path(self) -> str:
        """Get the configuration file path"""
        return str(self.config_file)


# Global config service instance
config_service = ConfigService()
