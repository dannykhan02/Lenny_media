"""
Testing configuration - Uses in-memory SQLite database
"""
import os
from .base import Config

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # ============================================
    # TESTING DATABASE - IN-MEMORY SQLITE
    # ============================================
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Fast in-memory database
    SQLALCHEMY_ECHO = False  # Don't log SQL queries during tests (cleaner output)
    
    # ============================================
    # TESTING JWT SETTINGS - RELAXED
    # ============================================
    JWT_COOKIE_CSRF_PROTECT = False  # Disabled for testing
    JWT_COOKIE_SECURE = False        # Allow HTTP for tests
    JWT_COOKIE_SAMESITE = 'Lax'
    
    # ============================================
    # TESTING EMAIL SETTINGS - SUPPRESS SENDING
    # ============================================
    MAIL_SUPPRESS_SEND = True        # Never actually send emails during tests
    MAIL_DEBUG = 2                   # Full debug output for test debugging
    
    # Use a test email configuration
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025                 # Common port for mail testing servers (MailHog, etc.)
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    
    # ============================================
    # TESTING CLOUDINARY SETTINGS
    # ============================================
    TEST_CLOUDINARY_ON_STARTUP = False  # Skip Cloudinary tests
    
    # ============================================
    # TESTING CSRF SETTINGS
    # ============================================
    WTF_CSRF_ENABLED = False         # Disable CSRF for form testing
    
    # ============================================
    # TESTING CORS - ALLOW ALL
    # ============================================
    CORS_ORIGINS = ["*"]             # Allow all origins in testing