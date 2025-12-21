from config.development import DevelopmentConfig
from config.production import ProductionConfig

def get_config(env_name):
    config = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'default': DevelopmentConfig
    }
    return config.get(env_name, config['default'])