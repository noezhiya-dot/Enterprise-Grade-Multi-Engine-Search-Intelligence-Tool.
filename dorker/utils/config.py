"""Configuration file loading utilities."""

import os
import logging
from typing import Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Configuration dictionary
    """
    config = {}
    
    default_paths = ["config.yaml", "config.yml", ".dorker.yaml"]
    if config_path:
        default_paths.insert(0, config_path)
    
    for path in default_paths:
        if os.path.exists(path):
            try:
                if yaml is None:
                    logger.warning("PyYAML not installed, skipping config file")
                    break
                with open(path, "r") as f:
                    config = yaml.safe_load(f) or {}
                break
            except Exception as e:
                logger.warning(f"Error loading config from {path}: {e}")
    
    # Load from environment variables
    env_mappings = {
        "SERPAPI_KEY": "serpapi_key",
        "GOOGLE_API_KEY": "google_api_key",
        "GOOGLE_CX": "google_cx",
        "BING_API_KEY": "bing_api_key",
        "BRAVE_API_KEY": "brave_api_key",
    }
    
    for env_var, config_key in env_mappings.items():
        if env_var in os.environ and config_key not in config:
            config[config_key] = os.environ[env_var]
    
    return config
