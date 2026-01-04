# app/__init__.py
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime
from app.db import db
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load environment variables
load_dotenv()

def create_app():
    """Application factory function"""
    app = Flask(__name__)

    # Load configuration
    from config import get_config
    config_name = os.getenv('FLASK_ENV', 'development')
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Log configuration
    print("=" * 80)
    print(f"🚀 Starting Lenny Media API in {config_name.upper()} mode")
    print(f"🌍 Frontend URL: {app.config.get('FRONTEND_URL')}")
    print(f"🌐 CORS Origins: {app.config.get('CORS_ORIGINS')}")
    print(f"🔐 Cookie Secure: {app.config.get('JWT_COOKIE_SECURE')}")
    print(f"🍪 Cookie SameSite: {app.config.get('JWT_COOKIE_SAMESITE')}")
    print("=" * 80)

    # Initialize extensions
    db.init_app(app)
    api = Api(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # ============================================
    # CLOUDINARY INITIALIZATION
    # ============================================
    try:
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
            api_key=app.config.get('CLOUDINARY_API_KEY'),
            api_secret=app.config.get('CLOUDINARY_API_SECRET'),
            secure=app.config.get('CLOUDINARY_SECURE', True)
        )
        
        # Test Cloudinary connection
        if app.config.get('TEST_CLOUDINARY_ON_STARTUP', False):
            try:
                from cloudinary.api import ping
                response = ping()
                if response.get('status') == 'ok':
                    print("✅ Cloudinary connected successfully")
                else:
                    print(f"⚠️ Cloudinary connection test failed: {response}")
            except Exception as e:
                print(f"⚠️ Could not test Cloudinary connection: {str(e)}")
        
        print(f"✅ Cloudinary configured for cloud: {app.config.get('CLOUDINARY_CLOUD_NAME')}")
        
    except Exception as e:
        print(f"⚠️ Failed to initialize Cloudinary: {str(e)}")
        print("⚠️ Image upload functionality will not work without Cloudinary configuration")

    # ============================================
    # CORS CONFIGURATION - WITH PREFLIGHT SUPPORT
    # ============================================
    CORS(
        app,
        origins=app.config.get('CORS_ORIGINS', ["https://lennymedia.netlify.app"]),
        supports_credentials=app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
        expose_headers=app.config.get('CORS_EXPOSE_HEADERS', ["Set-Cookie", "Content-Type", "Authorization"]),
        allow_headers=app.config.get('CORS_ALLOW_HEADERS', ["Content-Type", "Authorization", "X-Requested-With", "Accept"]),
        methods=app.config.get('CORS_METHODS', ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    )

    # ============================================
    # MANUAL CORS FOR PREFLIGHT REQUESTS
    # ============================================
    @app.before_request
    def handle_preflight():
        """Handle CORS preflight requests"""
        if request.method == "OPTIONS":
            response = jsonify({"status": "preflight"})
            origin = request.headers.get('Origin')
            allowed_origins = app.config.get('CORS_ORIGINS', [])
            
            if origin and origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
                response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
            return response, 200

    # ============================================
    # EMAIL SERVICE INITIALIZATION
    # ============================================
    try:
        from .services.email_utils import mail as email_mail, send_email, test_email_configuration
        
        email_mail.init_app(app)
        
        app.email_utils = {
            'mail': email_mail,
            'send_email': send_email,
            'test_email_configuration': test_email_configuration
        }
        
        from .services.email_templates import (
            booking_confirmation_template,
            admin_booking_alert_template,
            booking_status_update_template
        )
        
        app.email_templates = {
            'booking_confirmation': booking_confirmation_template,
            'admin_booking_alert': admin_booking_alert_template,
            'booking_status_update': booking_status_update_template
        }
        
        print("✅ Email service initialized successfully")
                
    except ImportError as e:
        print(f"⚠️ Warning: Could not import email services: {e}")
        app.email_utils = None
        app.email_templates = None

    # ============================================
    # CLOUDINARY SERVICE INITIALIZATION
    # ============================================
    try:
        from .services.cloudinary_service import (
            upload_image,
            upload_file,
            delete_image,
            get_cloudinary_config
        )
        
        app.cloudinary_service = {
            'upload_image': upload_image,
            'upload_file': upload_file,
            'delete_image': delete_image,
            'get_config': get_cloudinary_config
        }
        
        print("✅ Cloudinary service initialized successfully")
                
    except ImportError as e:
        print(f"⚠️ Warning: Could not import Cloudinary services: {e}")
        app.cloudinary_service = None

    # ============================================
    # REGISTER ALL ROUTES
    # ============================================
    try:
        # Import all route registration functions
        from .routes import (
            auth_bp, 
            register_service_resources, 
            register_booking_resources,
            register_quote_resources,
            register_dashboard_resources
        )
        
        # Register authentication blueprint
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        
        # Register RESTful API resources
        register_service_resources(api)
        register_booking_resources(api)
        register_quote_resources(api)
        register_dashboard_resources(api)
        
        print("✅ All routes registered successfully")
        
    except ImportError as e:
        print(f"⚠️ Warning: Could not import some routes: {e}")
        # Try to import and register individually
        try:
            from .routes.auth import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            print("✅ Auth routes registered")
        except ImportError:
            print("❌ Auth routes could not be imported")
        
        try:
            from .routes.service import register_service_resources
            register_service_resources(api)
            print("✅ Service routes registered")
        except ImportError:
            print("❌ Service routes could not be imported")
        
        try:
            from .routes.booking import register_booking_resources
            register_booking_resources(api)
            print("✅ Booking routes registered")
        except ImportError:
            print("❌ Booking routes could not be imported")
        
        try:
            from .routes.quote import register_quote_resources
            register_quote_resources(api)
            print("✅ Quote routes registered")
        except ImportError as quote_error:
            print(f"❌ Quote routes could not be imported: {quote_error}")
            # Try to diagnose the quote import error
            import traceback
            traceback.print_exc()
    
    # ============================================
    # JWT ERROR HANDLERS
    # ============================================
    @jwt.expired_token_loader
    def expired_token_loader(jwt_header, jwt_payload):
        return jsonify({
            "msg": "Token has expired",
            "error": "token_expired"
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_loader(error):
        return jsonify({
            "msg": "Invalid token",
            "error": "invalid_token"
        }), 401

    @jwt.unauthorized_loader
    def missing_token_loader(error):
        return jsonify({
            "msg": "Authorization required",
            "error": "authorization_required"
        }), 401
    
    # ============================================
    # HEALTH CHECK ENDPOINTS
    # ============================================
    @app.route('/')
    def index():
        return {
            "message": "Lenny Media Photography API",
            "version": app.config.get('VERSION', '1.0.0'),
            "status": "running",
            "mode": config_name,
            "frontend": app.config.get('FRONTEND_URL'),
            "cors_origins": app.config.get('CORS_ORIGINS'),
            "cors_enabled": True,
            "cors_supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS'),
            "cloudinary": {
                "configured": app.config.get('CLOUDINARY_CLOUD_NAME') is not None,
                "cloud_name": app.config.get('CLOUDINARY_CLOUD_NAME'),
                "upload_folder": app.config.get('CLOUDINARY_UPLOAD_FOLDER')
            },
            "routes": {
                "auth": "/api/auth",
                "services": "/services",
                "bookings": "/bookings",
                "quotes": "/quotes"
            }
        }

    @app.route('/health')
    def health():
        try:
            db.session.execute(db.text('SELECT 1'))
            
            # Check Cloudinary connection
            cloudinary_status = "not_configured"
            if app.config.get('CLOUDINARY_CLOUD_NAME'):
                try:
                    from cloudinary.api import ping
                    response = ping()
                    cloudinary_status = "connected" if response.get('status') == 'ok' else "disconnected"
                except:
                    cloudinary_status = "error"
            
            return {
                "status": "healthy",
                "database": "connected",
                "cloudinary": cloudinary_status,
                "timestamp": datetime.now().isoformat(),
                "frontend": app.config.get('FRONTEND_URL'),
                "cors_configuration": {
                    "origins": app.config.get('CORS_ORIGINS'),
                    "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS'),
                    "allow_headers": app.config.get('CORS_ALLOW_HEADERS')[:3]
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, 503

    # ============================================
    # CORS HEADER FIX - CRITICAL FOR NETLIFY
    # ============================================
    @app.after_request
    def after_request(response):
        """Set CORS headers for all responses"""
        origin = request.headers.get('Origin')
        allowed_origins = app.config.get('CORS_ORIGINS', [])
        
        # For OPTIONS requests (preflight), handle in before_request
        if request.method == 'OPTIONS':
            return response
        
        # Allow the origin if it's in our allowed list
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Expose-Headers'] = 'Set-Cookie, Content-Type, Authorization'
        
        # Security headers for production
        if not app.config.get('DEBUG'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

    return app