"""
Production configuration - Optimized for Koyeb deployment
"""
import os
from .base import Config

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # ============================================
    # KOYEB POSTGRESQL DATABASE
    # ============================================
    # Get DATABASE_URL from environment (Koyeb provides this)
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError(
            "❌ DATABASE_URL environment variable is required for production!\n"
            "   Please add it in your Koyeb service environment variables."
        )
    
    # Fix Koyeb's postgres:// to postgresql:// (required by SQLAlchemy)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        print("✅ Converted DATABASE_URL: postgres:// → postgresql://")
    
    SQLALCHEMY_DATABASE_URI = database_url
    
    # Production database pool settings (optimized for Koyeb)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,              # Maintain 5 connections
        'max_overflow': 10,          # Allow 10 extra connections if needed
        'pool_timeout': 30,          # Wait 30s for available connection
        'pool_recycle': 1800,        # Recycle connections every 30 min
        'pool_pre_ping': True,       # Test connection before using
    }
    
    # ============================================
    # PRODUCTION JWT SETTINGS - SECURE FOR NETLIFY
    # ============================================
    JWT_COOKIE_SECURE = True              # HTTPS only (CRITICAL for production)
    JWT_COOKIE_CSRF_PROTECT = False       # Disabled for cookie-based auth with CORS
    JWT_COOKIE_SAMESITE = 'None'          # Required for cross-origin (Netlify → Koyeb)
    
    # ============================================
    # PRODUCTION SESSION SETTINGS
    # ============================================
    SESSION_COOKIE_SECURE = True          # HTTPS only
    SESSION_COOKIE_HTTPONLY = True        # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'None'      # Cross-origin from Netlify
    
    # ============================================
    # PRODUCTION CLOUDINARY SETTINGS
    # ============================================
    CLOUDINARY_UPLOAD_FOLDER = "lenny_media_prod"
    CLOUDINARY_SECURE = True              # Always use HTTPS URLs
    TEST_CLOUDINARY_ON_STARTUP = False    # Skip startup test (faster deployment)
    
    # Cloudinary production optimizations
    CLOUDINARY_QUALITY = "auto:good"      # Auto optimize image quality
    CLOUDINARY_FETCH_FORMAT = "auto"      # Auto convert to webp when supported
    
    # ============================================
    # PRODUCTION EMAIL SETTINGS
    # ============================================
    MAIL_DEBUG = 0                        # No debug output in production
    MAIL_SUPPRESS_SEND = False            # Always send emails in production
    
    # ============================================
    # PRODUCTION CORS - STRICT ORIGINS ONLY
    # ============================================
    # Only allow production frontend origins
    CORS_ORIGINS = [
        "https://lennymedia.netlify.app",  # PRIMARY: Netlify frontend
        "https://lennymedia.co.ke",        # Your custom domain (if you have one)
    ]
    
    # Optionally add backend URL for webhooks/callbacks
    BACKEND_URL = os.getenv('BACKEND_URL')
    if BACKEND_URL and BACKEND_URL not in CORS_ORIGINS:
        CORS_ORIGINS.append(BACKEND_URL)
        print(f"✅ Added backend URL to CORS origins: {BACKEND_URL}")
    
    # ============================================
    # PRODUCTION RATE LIMITING
    # ============================================
    RATELIMIT_DEFAULT_LIMIT = "60 per hour"  # Stricter than development
    
    # ============================================
    # PRODUCTION OPTIMIZATIONS
    # ============================================
    # JSON settings for better performance
    JSON_SORT_KEYS = False                # Don't sort keys (faster)
    JSONIFY_PRETTYPRINT_REGULAR = False   # Compact JSON (smaller response size)