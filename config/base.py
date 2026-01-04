"""
Base configuration class with common settings
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    # Application Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    APP_NAME = "Lenny Media Kenya"
    VERSION = "1.0.0"
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///lenny_media.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
    
    # ============================================
    # CLOUDINARY CONFIGURATION
    # ============================================
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")
    
    # Cloudinary upload settings
    CLOUDINARY_UPLOAD_FOLDER = "lenny_media"
    CLOUDINARY_ALLOWED_FORMATS = ["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "avi", "mkv"]
    CLOUDINARY_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # ============================================
    # JWT CONFIGURATION - OPTIMIZED FOR COOKIES
    # ============================================
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    
    # CRITICAL: Token location - cookies AND headers for flexibility
    JWT_TOKEN_LOCATION = ['cookies', 'headers']  # Support both for compatibility
    
    # Cookie settings - READ FROM .ENV
    JWT_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
    JWT_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', 'Lax')  # Lax for localhost, None for cross-domain
    JWT_COOKIE_CSRF_PROTECT = os.getenv('JWT_COOKIE_CSRF_PROTECT', 'False').lower() in ('true', '1', 'yes')
    JWT_SESSION_COOKIE = False  # Not a session cookie
    
    # Cookie names
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token_cookie'
    
    # Cookie path and domain - CRITICAL
    JWT_COOKIE_DOMAIN = None  # None = let browser handle it (CRITICAL for localhost)
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_REFRESH_COOKIE_PATH = '/'
    
    # Token expiration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Session Configuration
    SESSION_TYPE = "sqlalchemy"
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "session:"
    SESSION_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = 86400
    
    # ============================================
    # CORS CONFIGURATION - FIXED HEADERS
    # ============================================
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://lennymedia.netlify.app')
    
    # Default CORS origins - PRIMARY: lennymedia.netlify.app
    CORS_ORIGINS = [
        "https://lennymedia.netlify.app",  # PRIMARY FRONTEND
        "http://localhost:3000",           # Development
        "http://localhost:5173",           # Development (Vite)
        "http://localhost:8080",           # Development
        "http://127.0.0.1:3000",           # Localhost
        "http://127.0.0.1:5173",           # Localhost (Vite)
        "http://127.0.0.1:8080"            # Localhost
    ]
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_EXPOSE_HEADERS = ["Set-Cookie", "Content-Type", "Authorization"]
    
    # FIX: Allow all common headers including Content-Type
    CORS_ALLOW_HEADERS = [
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "X-CSRF-Token",
        "Cache-Control"
    ]
    
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    
    # Security Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Rate Limiting (optional)
    RATELIMIT_DEFAULT_LIMIT = "100 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # ============================================
    # EMAIL CONFIGURATION (Flask-Mail with Gmail)
    # ============================================
    
    # SMTP Server Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
    
    # Email Account Credentials (from .env)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Admin Notification Email (where booking alerts go)
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', MAIL_USERNAME)
    
    # Business Information (Used in Email Templates)
    BUSINESS_NAME = os.getenv('BUSINESS_NAME', 'Lenny Media Photography Studio')
    BUSINESS_PHONE = os.getenv('BUSINESS_PHONE', '+254 705 459768')
    BUSINESS_EMAIL = os.getenv('BUSINESS_EMAIL', MAIL_USERNAME)
    BUSINESS_ADDRESS = os.getenv('BUSINESS_ADDRESS', 'Juja Square, 1st Floor, Next to the Highway, Juja, Kenya')
    BUSINESS_WEBSITE = os.getenv('BUSINESS_WEBSITE', 'https://lennymedia.co.ke')
    
    # Social Media Links (For Email Footer)
    SOCIAL_FACEBOOK = os.getenv('SOCIAL_FACEBOOK', 'https://facebook.com/lennymedia')
    SOCIAL_INSTAGRAM = os.getenv('SOCIAL_INSTAGRAM', 'https://instagram.com/lennymedia')
    SOCIAL_TWITTER = os.getenv('SOCIAL_TWITTER', 'https://twitter.com/lennymedia')
    SOCIAL_TIKTOK = os.getenv('SOCIAL_TIKTOK', 'https://tiktok.com/@lennymedia')
    SOCIAL_YOUTUBE = os.getenv('SOCIAL_YOUTUBE', 'https://youtube.com/@lennymedia')
    SOCIAL_LINKEDIN = os.getenv('SOCIAL_LINKEDIN', 'https://linkedin.com/company/lennymedia')
    
    # Optional Email Settings
    MAIL_MAX_EMAILS = int(os.getenv('MAIL_MAX_EMAILS', 100)) if os.getenv('MAIL_MAX_EMAILS') else None
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() in ('true', '1', 'yes')
    MAIL_ASCII_ATTACHMENTS = os.getenv('MAIL_ASCII_ATTACHMENTS', 'False').lower() in ('true', '1', 'yes')
    
    # Email connection timeout settings
    MAIL_TIMEOUT = 30  # seconds
    MAIL_DEBUG = 0  # 0 = no debug output, 1 = some, 2 = full
    
    def __init__(self):
        """Initialize configuration and validate required settings"""
        self.validate_email_config()
        self.validate_cloudinary_config()
    
    def validate_email_config(self):
        """Validate that email configuration is properly set"""
        required_email_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD']
        missing_vars = [var for var in required_email_vars if not getattr(self, var)]
        
        if missing_vars:
            print(f"WARNING: Missing email configuration: {missing_vars}")
            print("Email functionality may not work properly.")
    
    def validate_cloudinary_config(self):
        """Validate that Cloudinary configuration is properly set"""
        required_cloudinary_vars = ['CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET']
        missing_vars = [var for var in required_cloudinary_vars if not getattr(self, var)]
        
        if missing_vars:
            print(f"WARNING: Missing Cloudinary configuration: {missing_vars}")
            print("Image/Video upload functionality may not work properly.")
        else:
            print("Cloudinary configuration loaded successfully.")