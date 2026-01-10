"""Configuration loader for Ó bože."""
import logging
from pathlib import Path
import yaml

logger = logging.getLogger("oboze.config")

# Find config file relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# Global config instance
_config = None


def load_config() -> dict:
    """Load configuration from config.yaml."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Config file not found: {CONFIG_PATH}\n"
            "Please copy config.example.yaml to config.yaml and fill in your API key."
        )
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict) -> None:
    """Save configuration to config.yaml."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    logger.info(f"Configuration saved to {CONFIG_PATH}")
    # Clear cache
    global _config
    _config = None


def get_config() -> dict:
    """Get cached config."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> dict:
    """Force reload config from file."""
    global _config
    _config = load_config()
    return _config


def update_config(updates: dict) -> dict:
    """Update specific config values and save."""
    config = get_config().copy()
    
    # Deep merge updates
    for key, value in updates.items():
        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            config[key].update(value)
        else:
            config[key] = value
    
    save_config(config)
    return reload_config()
