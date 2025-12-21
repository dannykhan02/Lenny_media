from .base import Config

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True