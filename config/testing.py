"""
Testing configuration
"""
import os
from .base import Config

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = False
    
    # Testing email settings - suppress actual sending
    MAIL_SUPPRESS_SEND = True
    MAIL_DEBUG = 2  # Full debug output for tests
    
    # Use a test email configuration
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025  # Common port for mail testing servers
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None