"""
Configuration selector for the Flask application
Automatically selects the right config based on FLASK_ENV environment variable
"""
import os

def get_config(config_name=None):
    """
    Return the appropriate configuration class based on environment
    
    Args:
        config_name: 'development', 'production', 'testing', or None (auto-detect)
    
    Returns:
        Configuration class (DevelopmentConfig, ProductionConfig, or TestingConfig)
    
    Example:
        # In your app/__init__.py:
        from config import get_config
        config = get_config()
        app.config.from_object(config)
    """
    from .base import Config
    from .development import DevelopmentConfig
    from .production import ProductionConfig
    from .testing import TestingConfig
    
    # Auto-detect environment if not specified
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Map config names to classes
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'default': DevelopmentConfig
    }
    
    # Get the config class
    selected_config = config_map.get(config_name.lower(), config_map['default'])
    
    # Log which config is being used
    print("=" * 80)
    print(f"🔧 Loading configuration: {selected_config.__name__}")
    print(f"   Environment: {config_name.upper()}")
    print("=" * 80)
    
    return selected_config


# Export all config classes for direct import
from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

__all__ = [
    'get_config',
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestingConfig'
]