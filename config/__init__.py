"""
Configuration selector for the Flask application
"""
import os

def get_config(config_name):
    """Return the appropriate configuration class based on environment"""
    from .base import Config
    from .development import DevelopmentConfig
    from .production import ProductionConfig
    from .testing import TestingConfig
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'default': DevelopmentConfig
    }
    
    return config_map.get(config_name, config_map['default'])