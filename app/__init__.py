import os
from dotenv import load_dotenv
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime
from app.db import db  # Import db from app.db, NOT from .models

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

    # Override database URL from .env
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///lenny_media.db")

    # Initialize extensions
    db.init_app(app)
    api = Api(app)  # Flask-RESTful API instance
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # Configure CORS
    CORS(app,
         origins=app.config.get('CORS_ORIGINS', ["http://localhost:3000"]),
         supports_credentials=True,
         expose_headers=["Set-Cookie"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

    # Register blueprints (for routes using Flask Blueprints)
    from .routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Register Flask-RESTful resources (for routes using Flask-RESTful)
    from .routes import register_service_resources
    register_service_resources(api)
    
    # JWT configuration
    @jwt.expired_token_loader
    def expired_token_loader(jwt_header, jwt_payload):
        return {"error": "token_expired", "message": "The token has expired. Please log in again."}, 401

    @jwt.invalid_token_loader
    def invalid_token_loader(error):
        return {"error": "invalid_token", "message": "Signature verification failed."}, 401

    @jwt.unauthorized_loader
    def missing_token_loader(error):
        return {"error": "authorization_required", "message": "Request does not contain a valid token."}, 401

    # Health check endpoints
    @app.route('/')
    def index():
        return {
            "message": "Lenny Media Photography API",
            "version": "1.0.0",
            "status": "running"
        }

    @app.route('/health')
    def health():
        try:
            db.session.execute('SELECT 1')
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, 503

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "not_found", "message": "The requested resource was not found."}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "internal_server_error", "message": "An internal server error occurred."}, 500

    return app