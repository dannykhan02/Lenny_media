"""
Development configuration - Uses Local SQLite
"""
import os
from .base import Config

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log all SQL queries
    
    # ============================================
    # LOCAL SQLITE DATABASE FOR DEVELOPMENT
    # ============================================
    # Use SQLite for local development (easy setup, no PostgreSQL needed)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///lenny_media.db"  # Creates lenny_media.db in instance/ folder
    )
    
    # Note: If you want to test with PostgreSQL locally, set DATABASE_URL in .env:
    # DATABASE_URL=postgresql://user:pass@localhost/lenny_media_dev
    
    # ============================================
    # DEVELOPMENT SECURITY SETTINGS (Relaxed)
    # ============================================
    # Development-specific JWT settings
    JWT_COOKIE_SECURE = False           # HTTP is fine for localhost
    JWT_COOKIE_CSRF_PROTECT = False     # Disable CSRF for easier testing
    JWT_COOKIE_SAMESITE = 'Lax'         # Lax for local same-site development
    
    # ============================================
    # DEVELOPMENT CLOUDINARY SETTINGS
    # ============================================
    CLOUDINARY_UPLOAD_FOLDER = "lenny_media_dev"  # Separate folder for dev uploads
    TEST_CLOUDINARY_ON_STARTUP = os.getenv('TEST_CLOUDINARY_ON_STARTUP', 'False').lower() in ('true', '1', 'yes')
    
    # ============================================
    # DEVELOPMENT EMAIL SETTINGS
    # ============================================
    MAIL_DEBUG = 1  # Show some email debug info in development
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() in ('true', '1', 'yes')
    
    # Test email on startup (optional)
    TEST_EMAIL_ON_STARTUP = os.getenv('TEST_EMAIL_ON_STARTUP', 'False').lower() in ('true', '1', 'yes')
    
    # ============================================
    # DEVELOPMENT CORS - Allow All Local Origins
    # ============================================
    CORS_ORIGINS = [
        "https://lennymedia.netlify.app",  # Allow production frontend for testing
        "http://localhost:3000",            # React default
        "http://localhost:5173",            # Vite default
        "http://localhost:8080",            # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080"
    ]
    
    # ============================================
    # DEVELOPMENT OPTIMIZATIONS
    # ============================================
    # Pretty print JSON in development for easier debugging
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True