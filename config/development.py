"""
Development configuration
"""
import os
from .base import Config

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log all SQL queries
    
    # Development-specific JWT settings
    JWT_COOKIE_SECURE = False  # HTTP is fine for development
    JWT_COOKIE_CSRF_PROTECT = False  # Disable CSRF in development
    JWT_COOKIE_SAMESITE = 'Lax'  # Lax for local development
    
    # Development-specific Cloudinary settings
    CLOUDINARY_UPLOAD_FOLDER = "lenny_media_dev"  # Separate folder for development
    
    # Development-specific email settings
    MAIL_DEBUG = 1  # Show some email debug info in development
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() in ('true', '1', 'yes')
    
    # Development CORS - prioritize Netlify but allow localhost
    CORS_ORIGINS = [
        "https://lennymedia.netlify.app",  # Primary frontend (Netlify)
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080"
    ]
    
    # Test email on startup (development only)
    TEST_EMAIL_ON_STARTUP = os.getenv('TEST_EMAIL_ON_STARTUP', 'False').lower() in ('true', '1', 'yes')
    
    # Test Cloudinary on startup
    TEST_CLOUDINARY_ON_STARTUP = os.getenv('TEST_CLOUDINARY_ON_STARTUP', 'False').lower() in ('true', '1', 'yes')