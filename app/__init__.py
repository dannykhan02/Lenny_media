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

# Load environment variables
load_dotenv()

def create_app():
    """Application factory function - OPTIMIZED"""
    app = Flask(__name__)

    # ============================================
    # LOAD CONFIGURATION
    # ============================================
    from config import get_config
    config_name = os.getenv('FLASK_ENV', 'development')
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Minimal startup logging
    if app.config.get('DEBUG'):
        print(f"🚀 Lenny Media API - {config_name.upper()}")

    # ============================================
    # INITIALIZE DATABASE
    # ============================================
    db.init_app(app)

    # ============================================
    # INITIALIZE EXTENSIONS
    # ============================================
    api = Api(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # ============================================
    # CLOUDINARY
    # ============================================
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET'),
        secure=app.config.get('CLOUDINARY_SECURE', True)
    )

    # ============================================
    # CORS - FIXED FOR PREFLIGHT
    # ============================================
    CORS(
        app,
        origins=app.config.get('CORS_ORIGINS', ["https://lennymedia.netlify.app"]),
        supports_credentials=True,
        expose_headers=["Set-Cookie", "Content-Type", "Authorization"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        max_age=3600
    )

    # Handle preflight manually
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_response("")
            origin = request.headers.get('Origin')
            if origin in app.config.get('CORS_ORIGINS', []):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Max-Age'] = '3600'
            return response

    # ============================================
    # EMAIL SERVICE
    # ============================================
    try:
        from .services.email_utils import mail as email_mail
        email_mail.init_app(app)
        
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
    except Exception:
        app.email_templates = None

    # ============================================
    # CLOUDINARY SERVICE
    # ============================================
    try:
        from .services.cloudinary_service import (
            upload_image, upload_file, delete_image, get_cloudinary_config
        )
        app.cloudinary_service = {
            'upload_image': upload_image,
            'upload_file': upload_file,
            'delete_image': delete_image,
            'get_config': get_cloudinary_config
        }
    except Exception:
        app.cloudinary_service = None

    # ============================================
    # REGISTER ROUTES
    # ============================================
    from .routes import (
        auth_bp, 
        register_service_resources, 
        register_booking_resources,
        register_quote_resources,
        register_dashboard_resources
    )
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    register_service_resources(api)
    register_booking_resources(api)
    register_quote_resources(api)
    register_dashboard_resources(api)
    
    # ============================================
    # JWT ERROR HANDLERS
    # ============================================
    @jwt.expired_token_loader
    def expired_token_loader(jwt_header, jwt_payload):
        return jsonify({"msg": "Token has expired", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_loader(error):
        return jsonify({"msg": "Invalid token", "error": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_loader(error):
        return jsonify({"msg": "Authorization required", "error": "authorization_required"}), 401
    
    # ============================================
    # ROOT ENDPOINT
    # ============================================
    @app.route('/')
    def index():
        return {
            "message": "Lenny Media Photography API",
            "version": "1.0.0",
            "status": "running"
        }

    # ============================================
    # CORS HEADERS ON RESPONSES
    # ============================================
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        allowed_origins = app.config.get('CORS_ORIGINS', [])
        
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response

    return app