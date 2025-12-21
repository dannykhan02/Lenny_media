from .base import Config

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False