"""
Production configuration
"""
import os
from .base import Config

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Production JWT settings - SECURE FOR NETLIFY
    JWT_COOKIE_SECURE = True  # MUST be True in production (requires HTTPS)
    JWT_COOKIE_CSRF_PROTECT = True  # Enable CSRF protection in production
    JWT_COOKIE_SAMESITE = 'None'  # None for cross-origin from Netlify (requires Secure=True)
    
    # Production Cloudinary settings
    CLOUDINARY_UPLOAD_FOLDER = "lenny_media_prod"
    CLOUDINARY_SECURE = True  # Use HTTPS for Cloudinary URLs
    
    # Production email settings
    MAIL_DEBUG = 0  # No debug output in production
    MAIL_SUPPRESS_SEND = False  # Always send in production
    
    # Production CORS - ONLY allow Netlify and your domain
    CORS_ORIGINS = [
        "https://lennymedia.netlify.app",  # Netlify frontend (PRIMARY)
        "https://lennymedia.co.ke",        # Your custom domain
    ]
    
    # Add backend URL as origin (if needed)
    BACKEND_URL = os.getenv('BACKEND_URL', 'https://your-backend-url.com')
    if BACKEND_URL not in CORS_ORIGINS:
        CORS_ORIGINS.append(BACKEND_URL)
    
    # Production database - prefer PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://username:password@localhost/lenny_media_prod"
    )
    
    # Additional production security settings
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'  # For cross-origin (Netlify)
    
    # Stronger rate limiting in production
    RATELIMIT_DEFAULT_LIMIT = "60 per hour"
    
    # Cloudinary production optimizations
    CLOUDINARY_QUALITY = "auto:good"  # Auto optimize image quality
    CLOUDINARY_FETCH_FORMAT = "auto"  # Auto convert to webp when possible