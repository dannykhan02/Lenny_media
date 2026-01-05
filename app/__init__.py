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

    # ============================================
    # LOAD CONFIGURATION
    # ============================================
    from config import get_config
    config_name = os.getenv('FLASK_ENV', 'development')
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # ============================================
    # LOG CONFIGURATION (Enhanced for Debugging)
    # ============================================
    print("=" * 80)
    print(f"🚀 Starting Lenny Media API")
    print(f"   Environment: {config_name.upper()}")
    print(f"   Debug Mode: {app.config.get('DEBUG')}")
    print(f"   Version: {app.config.get('VERSION', '1.0.0')}")
    print("=" * 80)
    
    # Database configuration
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
    if 'postgresql://' in db_uri:
        # Mask password in production logs
        db_display = db_uri.split('@')[-1] if '@' in db_uri else 'PostgreSQL'
        print(f"🗄️  Database: PostgreSQL ({db_display})")
    elif 'sqlite:///' in db_uri:
        print(f"🗄️  Database: SQLite (Local)")
    else:
        print(f"🗄️  Database: {db_uri[:30]}...")
    
    print(f"🌍 Frontend: {app.config.get('FRONTEND_URL')}")
    print(f"🌐 CORS Origins: {len(app.config.get('CORS_ORIGINS', []))} configured")
    print(f"🔐 JWT Cookie Secure: {app.config.get('JWT_COOKIE_SECURE')}")
    print(f"🍪 JWT Cookie SameSite: {app.config.get('JWT_COOKIE_SAMESITE')}")
    print("=" * 80)

    # ============================================
    # INITIALIZE DATABASE
    # ============================================
    try:
        db.init_app(app)
        
        # Test database connection
        with app.app_context():
            try:
                db.session.execute(db.text('SELECT 1'))
                print("✅ Database connection verified")
            except Exception as e:
                print(f"⚠️  Database connection failed: {str(e)}")
                print(f"   This is normal if database doesn't exist yet.")
                print(f"   Run 'flask db upgrade' to create tables.")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        raise

    # ============================================
    # INITIALIZE EXTENSIONS
    # ============================================
    api = Api(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    print("✅ Flask extensions initialized")

    # ============================================
    # CLOUDINARY INITIALIZATION
    # ============================================
    try:
        cloudinary_cloud = app.config.get('CLOUDINARY_CLOUD_NAME')
        cloudinary_key = app.config.get('CLOUDINARY_API_KEY')
        cloudinary_secret = app.config.get('CLOUDINARY_API_SECRET')
        
        if not all([cloudinary_cloud, cloudinary_key, cloudinary_secret]):
            print("⚠️  Cloudinary credentials missing")
            print("   Image/video uploads will not work")
            print("   Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")
        else:
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=cloudinary_cloud,
                api_key=cloudinary_key,
                api_secret=cloudinary_secret,
                secure=app.config.get('CLOUDINARY_SECURE', True)
            )
            
            # Test connection if enabled
            if app.config.get('TEST_CLOUDINARY_ON_STARTUP', False):
                try:
                    from cloudinary.api import ping
                    response = ping()
                    if response.get('status') == 'ok':
                        print(f"✅ Cloudinary connected: {cloudinary_cloud}")
                    else:
                        print(f"⚠️  Cloudinary connection test failed: {response}")
                except Exception as e:
                    print(f"⚠️  Could not test Cloudinary: {str(e)}")
            else:
                print(f"✅ Cloudinary configured: {cloudinary_cloud}")
        
    except Exception as e:
        print(f"⚠️  Cloudinary initialization error: {str(e)}")

    # ============================================
    # CORS CONFIGURATION - WITH PREFLIGHT SUPPORT
    # ============================================
    cors_origins = app.config.get('CORS_ORIGINS', ["https://lennymedia.netlify.app"])
    
    CORS(
        app,
        origins=cors_origins,
        supports_credentials=app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
        expose_headers=app.config.get('CORS_EXPOSE_HEADERS', [
            "Set-Cookie", "Content-Type", "Authorization"
        ]),
        allow_headers=app.config.get('CORS_ALLOW_HEADERS', [
            "Content-Type", "Authorization", "X-Requested-With", "Accept"
        ]),
        methods=app.config.get('CORS_METHODS', [
            "GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"
        ])
    )
    print(f"✅ CORS configured for {len(cors_origins)} origins")

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
        mail_user = app.config.get('MAIL_USERNAME')
        mail_pass = app.config.get('MAIL_PASSWORD')
        
        if not all([mail_user, mail_pass]):
            print("⚠️  Email credentials missing")
            print("   Email functionality will not work")
            print("   Set MAIL_USERNAME and MAIL_PASSWORD")
            app.email_utils = None
            app.email_templates = None
        else:
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
            
            print(f"✅ Email service initialized: {mail_user}")
                
    except ImportError as e:
        print(f"⚠️  Could not import email services: {e}")
        app.email_utils = None
        app.email_templates = None
    except Exception as e:
        print(f"⚠️  Email initialization error: {str(e)}")
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
        
        print("✅ Cloudinary service initialized")
                
    except ImportError as e:
        print(f"⚠️  Could not import Cloudinary services: {e}")
        app.cloudinary_service = None

    # ============================================
    # REGISTER ALL ROUTES
    # ============================================
    routes_registered = []
    routes_failed = []
    
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
        routes_registered.append('auth')
        
        # Register RESTful API resources
        register_service_resources(api)
        routes_registered.append('services')
        
        register_booking_resources(api)
        routes_registered.append('bookings')
        
        register_quote_resources(api)
        routes_registered.append('quotes')
        
        register_dashboard_resources(api)
        routes_registered.append('dashboard')
        
        print(f"✅ Routes registered: {', '.join(routes_registered)}")
        
    except ImportError as e:
        print(f"⚠️  Warning: Could not import some routes: {e}")
        
        # Try to import and register individually
        try:
            from .routes.auth import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            routes_registered.append('auth')
        except ImportError:
            routes_failed.append('auth')
        
        try:
            from .routes.service import register_service_resources
            register_service_resources(api)
            routes_registered.append('services')
        except ImportError:
            routes_failed.append('services')
        
        try:
            from .routes.booking import register_booking_resources
            register_booking_resources(api)
            routes_registered.append('bookings')
        except ImportError:
            routes_failed.append('bookings')
        
        try:
            from .routes.quote import register_quote_resources
            register_quote_resources(api)
            routes_registered.append('quotes')
        except ImportError:
            routes_failed.append('quotes')
        
        try:
            from .routes.dashboard import register_dashboard_resources
            register_dashboard_resources(api)
            routes_registered.append('dashboard')
        except ImportError:
            routes_failed.append('dashboard')
        
        if routes_registered:
            print(f"✅ Partial routes registered: {', '.join(routes_registered)}")
        if routes_failed:
            print(f"❌ Failed routes: {', '.join(routes_failed)}")
    
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
        """Main API endpoint - shows configuration info"""
        return {
            "message": "Lenny Media Photography API",
            "version": app.config.get('VERSION', '1.0.0'),
            "status": "running",
            "environment": config_name,
            "frontend": app.config.get('FRONTEND_URL'),
            "cors": {
                "enabled": True,
                "origins_count": len(app.config.get('CORS_ORIGINS', [])),
                "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS')
            },
            "services": {
                "database": "configured",
                "cloudinary": "configured" if app.config.get('CLOUDINARY_CLOUD_NAME') else "not_configured",
                "email": "configured" if app.email_utils else "not_configured"
            },
            "routes": {
                "auth": "/api/auth",
                "services": "/services",
                "bookings": "/bookings",
                "quotes": "/quotes",
                "dashboard": "/dashboard",
                "health": "/health"
            }
        }

    @app.route('/health')
    def health():
        """Health check endpoint for Koyeb and monitoring"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "environment": config_name,
            "services": {}
        }
        
        # Check database connection
        try:
            db.session.execute(db.text('SELECT 1'))
            health_status["services"]["database"] = "connected"
        except Exception as e:
            health_status["services"]["database"] = "disconnected"
            health_status["status"] = "unhealthy"
            health_status["database_error"] = str(e)
        
        # Check Cloudinary connection
        if app.config.get('CLOUDINARY_CLOUD_NAME'):
            try:
                from cloudinary.api import ping
                response = ping()
                cloudinary_status = "connected" if response.get('status') == 'ok' else "error"
                health_status["services"]["cloudinary"] = cloudinary_status
            except Exception as e:
                health_status["services"]["cloudinary"] = "error"
                health_status["cloudinary_error"] = str(e)
        else:
            health_status["services"]["cloudinary"] = "not_configured"
        
        # Check email service
        if app.email_utils:
            health_status["services"]["email"] = "configured"
        else:
            health_status["services"]["email"] = "not_configured"
        
        # Add configuration info
        health_status["config"] = {
            "frontend": app.config.get('FRONTEND_URL'),
            "cors_origins": len(app.config.get('CORS_ORIGINS', [])),
            "jwt_cookie_secure": app.config.get('JWT_COOKIE_SECURE'),
            "jwt_cookie_samesite": app.config.get('JWT_COOKIE_SAMESITE')
        }
        
        # Return appropriate status code
        status_code = 200 if health_status["status"] == "healthy" else 503
        return health_status, status_code

    # ============================================
    # CORS HEADER FIX - CRITICAL FOR NETLIFY
    # ============================================
    @app.after_request
    def after_request(response):
        """Set CORS headers for all responses"""
        origin = request.headers.get('Origin')
        allowed_origins = app.config.get('CORS_ORIGINS', [])
        
        # For OPTIONS requests (preflight), already handled in before_request
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

    # ============================================
    # STARTUP SUMMARY
    # ============================================
    print("=" * 80)
    print("✅ Lenny Media API initialization complete")
    if routes_registered:
        print(f"   Routes: {', '.join(routes_registered)}")
    if routes_failed:
        print(f"   Failed: {', '.join(routes_failed)}")
    print("=" * 80)

    return app