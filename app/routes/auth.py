# app/routes/auth.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity, 
    get_jwt,
    unset_jwt_cookies,
    set_access_cookies,
    verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
from functools import wraps
import logging
import re
import traceback
import os
import time
from sqlalchemy.exc import OperationalError, DisconnectionError
from werkzeug.utils import secure_filename

# Local imports
from ..models import User, UserRole
from .. import db
from ..services.cloudinary_service import (
    upload_image,
    upload_file,
    delete_image,
    get_cloudinary_config,
    upload_profile_picture,
    cleanup_old_profile_picture,
    generate_cloudinary_url,
    validate_file,
    upload_portfolio_image,
    upload_service_image,
    extract_public_id_from_url,
    test_cloudinary_connection
)

# Initialize blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Database retry function
def db_query_with_retry(query_func, max_retries=3, retry_delay=1):
    """
    Execute a database query with retry logic for connection issues
    """
    for attempt in range(max_retries):
        try:
            return query_func()
        except (OperationalError, DisconnectionError) as e:
            if "SSL SYSCALL error" in str(e) or "connection" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
            raise
    return None

# Helper functions
def role_required(required_role):
    """Decorator to check if user has the required role"""
    def decorator(fn):
        @jwt_required()
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role", "").upper()
            required_role_upper = required_role.upper()
            
            if user_role != required_role_upper:
                logger.warning(f"Access denied - User role '{user_role}' != required '{required_role_upper}'")
                return jsonify({"msg": "Forbidden: Access Denied"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    """Decorator to require admin role"""
    @jwt_required()
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        user_role = claims.get("role", "").upper()
        
        # Log for debugging
        logger.info(f"Admin check - Role from JWT: {user_role}")
        
        if user_role != "ADMIN":
            logger.warning(f"Access denied - User role '{user_role}' is not ADMIN")
            return jsonify({"msg": "Forbidden: Admin access required"}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def is_valid_email(email: str) -> bool:
    """
    Validates email format using RFC 5322 compliant regex pattern.
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    
    if len(email) > 254 or len(email) < 6:
        return False
    
    email_pattern = re.compile(
        r'^(?:[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*'
        r'|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")'
        r'@'
        r'(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?'
        r'|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\])$'
    )
    
    if not email_pattern.match(email):
        return False
    
    local_part, domain_part = email.rsplit('@', 1)
    
    if len(local_part) > 64:
        return False
    
    if len(domain_part) > 253:
        return False
    
    if '.' not in domain_part:
        return False
    
    if '..' in email:
        return False
    
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    if domain_part.startswith('-') or domain_part.endswith('-'):
        return False
    
    tld = domain_part.split('.')[-1]
    if len(tld) < 2:
        return False
    
    return True

def validate_admin_password(password):
    """Validate admin password requirements"""
    if not password:
        return False, "Password is required for admin users"
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, None

# ============================================
# CLOUDINARY UTILITY FUNCTIONS
# ============================================

def validate_upload_file(file, allowed_types=['image']):
    """
    Validate file for upload using Cloudinary service
    """
    # Determine file type based on extension
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    # Map extensions to file types
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'svg'}
    video_extensions = {'mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'webm', 'm4v'}
    document_extensions = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'xls', 'xlsx', 'ppt', 'pptx'}
    
    file_type = 'image'  # default
    if file_ext in video_extensions:
        file_type = 'video'
    elif file_ext in document_extensions:
        file_type = 'document'
    
    # Check if file type is allowed
    if file_type not in allowed_types:
        return False, f"File type '{file_type}' not allowed. Allowed types: {', '.join(allowed_types)}", None
    
    # Use Cloudinary service to validate
    is_valid, error_msg, file_size, file_ext = validate_file(file, file_type)
    
    if not is_valid:
        return False, error_msg, None
    
    return True, None, file_type

def handle_cloudinary_upload(file, upload_type='profile', **kwargs):
    """
    Handle different types of Cloudinary uploads
    """
    try:
        if upload_type == 'profile':
            user_id = kwargs.get('user_id')
            user_name = kwargs.get('user_name')
            if not user_id or not user_name:
                return {"success": False, "error": "User ID and name required for profile upload"}
            
            return upload_profile_picture(file, user_id, user_name)
        
        elif upload_type == 'portfolio':
            portfolio_id = kwargs.get('portfolio_id')
            title = kwargs.get('title')
            category = kwargs.get('category')
            
            if not portfolio_id or not title:
                return {"success": False, "error": "Portfolio ID and title required"}
            
            return upload_portfolio_image(file, portfolio_id, title, category)
        
        elif upload_type == 'service':
            service_id = kwargs.get('service_id')
            service_name = kwargs.get('service_name')
            
            if not service_id or not service_name:
                return {"success": False, "error": "Service ID and name required"}
            
            return upload_service_image(file, service_id, service_name)
        
        elif upload_type == 'general':
            folder = kwargs.get('folder')
            public_id = kwargs.get('public_id')
            file_type = kwargs.get('file_type', 'image')
            transformations = kwargs.get('transformations')
            
            return upload_file(file, file_type, folder, public_id, transformations)
        
        else:
            return {"success": False, "error": f"Unknown upload type: {upload_type}"}
    
    except Exception as e:
        logger.error(f"Cloudinary upload error: {str(e)}")
        return {"success": False, "error": str(e), "message": "Upload failed"}

# ============================================
# CLOUDINARY HEALTH CHECK ENDPOINTS
# ============================================

@auth_bp.route('/cloudinary/health', methods=['GET'])
@admin_required
def check_cloudinary_health():
    """Check Cloudinary connection and configuration (admin only)"""
    try:
        config = get_cloudinary_config()
        
        # Test connection
        connection_test = test_cloudinary_connection()
        
        return jsonify({
            "success": True,
            "cloudinary": {
                "configured": bool(config['cloud_name'] and config['api_key']),
                "cloud_name": config['cloud_name'],
                "api_key_truncated": f"{config['api_key'][:8]}...{config['api_key'][-4:]}" if config['api_key'] else None,
                "upload_folder": config['upload_folder'],
                "max_file_size_mb": config['max_file_size'] // (1024 * 1024),
                "secure": config['secure'],
                "connection_test": connection_test
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Cloudinary health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Cloudinary health check failed"
        }), 500

@auth_bp.route('/cloudinary/config', methods=['GET'])
@admin_required
def get_cloudinary_config_endpoint():
    """Get Cloudinary configuration (admin only)"""
    try:
        config = get_cloudinary_config()
        
        # Convert set to list for JSON serialization
        safe_config = {
            "cloud_name": config['cloud_name'],
            "upload_folder": config['upload_folder'],
            "allowed_formats": list(config['allowed_formats']),  # Convert set to list
            "max_file_size_mb": config['max_file_size'] // (1024 * 1024),
            "secure": config['secure'],
            "configured": bool(config['cloud_name'] and config['api_key'])
        }
        
        return jsonify({
            "success": True,
            "config": safe_config
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get Cloudinary config: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to get Cloudinary configuration"
        }), 500

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle admin login with JWT token generation (ONLY for ADMIN users with passwords)"""
    logger.info("=" * 60)
    logger.info("MEDIA LOGIN REQUEST RECEIVED - ADMIN ONLY")
    logger.info(f"Content-Type: {request.content_type}")
    
    try:
        data = request.get_json()
        logger.info(f"Parsed JSON: {data}")
    except Exception as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return jsonify({"error": "Invalid JSON format"}), 400
    
    if not data:
        logger.error("No data received")
        return jsonify({"error": "No data provided"}), 400
    
    email = data.get("email")
    password = data.get("password")
    
    logger.info(f"Email: {email}")
    logger.info(f"Password provided: {bool(password)}")

    if not email or not password:
        logger.error("Missing email or password")
        return jsonify({"error": "Email and password are required"}), 400

    def get_user():
        return User.query.filter_by(email=email).first()
    
    user = db_query_with_retry(get_user)
    
    # Check if user exists
    if not user:
        logger.error("User not found")
        return jsonify({"error": "Invalid email or password"}), 401
    
    # STRICT CHECK: Only ADMIN users can login
    if user.role != UserRole.ADMIN:
        logger.error(f"Non-admin user attempted login: {user.email} (Role: {user.role.value})")
        return jsonify({"error": "Access denied. Only administrators can log in."}), 403
    
    # Check if admin user has a password
    if not user.password:
        logger.error(f"Admin user {user.email} has no password set")
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Verify password
    if not check_password_hash(user.password, password):
        logger.error("Invalid password")
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        logger.error("Account deactivated")
        return jsonify({"error": "Account is deactivated"}), 403

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "role": str(user.role.value)
        },
        expires_delta=timedelta(days=1)
    )

    # Generate optimized avatar URL with cache busting
    avatar_url = user.avatar_url
    if not avatar_url and user.avatar_public_id:
        avatar_url = generate_cloudinary_url(
            user.avatar_public_id,
            width=200,
            height=200,
            crop='thumb',
            gravity='face'
        )

    response = jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": str(user.role.value),
            "full_name": user.full_name,
            "phone": user.phone,
            "avatar_url": avatar_url,
            "avatar_public_id": user.avatar_public_id,
            "is_active": user.is_active
        }
    })

    # Use Flask-JWT-Extended's built-in function to set cookies
    set_access_cookies(response, access_token)

    logger.info("ADMIN LOGIN SUCCESS")
    logger.info(f"Admin: {user.email}")
    logger.info(f"Admin ID: {user.id}")
    logger.info("=" * 60)
    
    return response, 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Clear authentication cookie - only admins can logout (since only they can login)"""
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    logger.info("Admin logged out - cookies cleared")
    return response, 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new admin user - DISABLED. Use /register-first-admin instead."""
    return jsonify({
        "msg": "Direct registration is disabled. Admins must use /register-first-admin, other users are created by admins."
    }), 403

@auth_bp.route('/check-admin', methods=['GET'])
def check_admin():
    """Check if admin user exists"""
    def get_admin():
        return User.query.filter_by(role=UserRole.ADMIN).first()
    
    admin_exists = db_query_with_retry(get_admin) is not None
    return jsonify({"admin_exists": admin_exists}), 200

@auth_bp.route('/register-first-admin', methods=['POST'])
def register_first_admin():
    """Register the first admin user (only if no admin exists) and auto-login"""
    def get_admin():
        return User.query.filter_by(role=UserRole.ADMIN).first()
    
    if db_query_with_retry(get_admin):
        return jsonify({"msg": "Admin already exists"}), 403

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not all([email, password, full_name]):
        return jsonify({"msg": "All fields are required"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400
    
    # Validate admin password
    is_valid, error_msg = validate_admin_password(password)
    if not is_valid:
        return jsonify({"msg": error_msg}), 400

    def check_email():
        return User.query.filter_by(email=email).first()
    
    if db_query_with_retry(check_email):
        return jsonify({"msg": "Email already registered"}), 400

    hashed_password = generate_password_hash(password)
    new_admin = User(
        email=email,
        password=hashed_password,
        full_name=full_name,
        role=UserRole.ADMIN
    )
    db.session.add(new_admin)
    db.session.commit()

    # Auto-login the admin
    access_token = create_access_token(
        identity=str(new_admin.id),
        additional_claims={
            "email": new_admin.email,
            "role": str(new_admin.role.value)
        },
        expires_delta=timedelta(days=1)
    )

    response = jsonify({
        "msg": "First admin registered successfully",
        "admin_id": new_admin.id,
        "email": new_admin.email,
        "user": {
            "id": new_admin.id,
            "email": new_admin.email,
            "role": str(new_admin.role.value),
            "full_name": new_admin.full_name,
            "phone": new_admin.phone,
            "is_active": new_admin.is_active
        }
    })

    set_access_cookies(response, access_token)

    logger.info("=" * 60)
    logger.info("FIRST ADMIN REGISTRATION SUCCESS")
    logger.info(f"Admin: {new_admin.email}")
    logger.info(f"Admin ID: {new_admin.id}")
    logger.info("=" * 60)
    
    return response, 201

# ============================================
# USER MANAGEMENT ROUTES WITH CLOUDINARY
# ============================================

@auth_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get list of all users (admin only)"""
    def get_all_users():
        return User.query.order_by(User.created_at.desc()).all()
    
    users = db_query_with_retry(get_all_users)
    
    # Enhance user data with optimized avatar URLs
    enhanced_users = []
    for user in users:
        user_dict = user.as_dict()
        
        # Generate optimized avatar URL if we have public_id
        if user.avatar_public_id and (not user.avatar_url or 'cloudinary' not in user.avatar_url):
            user_dict['avatar_url'] = generate_cloudinary_url(
                user.avatar_public_id,
                width=200,
                height=200,
                crop='thumb',
                gravity='face'
            )
        
        enhanced_users.append(user_dict)
    
    return jsonify(enhanced_users), 200

@auth_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Create a new user (admin only) - Non-admin users don't get passwords"""
    data = request.get_json()
    
    # Validate required fields
    email = data.get("email")
    full_name = data.get("full_name")
    role = data.get("role", "PHOTOGRAPHER")  # Default to PHOTOGRAPHER for media system
    
    if not all([email, full_name]):
        return jsonify({"msg": "Email and full name are required"}), 400
    
    # Validate email format
    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400
    
    # Check if email already exists
    def check_email_exists():
        return User.query.filter_by(email=email).first()
    
    if db_query_with_retry(check_email_exists):
        return jsonify({"msg": "Email already registered"}), 409
    
    # Validate role
    try:
        user_role = UserRole[role.upper()]
    except KeyError:
        valid_roles = [r.name for r in UserRole]
        return jsonify({
            "msg": f"Invalid role specified. Must be one of: {', '.join(valid_roles)}"
        }), 400
    
    # Handle password based on role
    hashed_password = None
    
    if user_role == UserRole.ADMIN:
        # Admin users MUST have a password
        password = data.get("password")
        
        # Validate admin password
        is_valid, error_msg = validate_admin_password(password)
        if not is_valid:
            return jsonify({"msg": error_msg}), 400
        
        hashed_password = generate_password_hash(password)
    else:
        # Non-admin users: No password (will be NULL in database)
        hashed_password = None
        
        logger.info(f"Creating non-admin user {email} - NO LOGIN ACCESS (Role: {user_role.value})")
    
    try:
        # Create new user
        new_user = User(
            email=email,
            password=hashed_password,  # NULL for non-admin users
            full_name=full_name,
            role=user_role,
            phone=data.get("phone"),
            is_active=data.get("is_active", True),
            avatar_url=data.get("avatar_url"),  # Allow setting avatar URL from external source
            avatar_public_id=data.get("avatar_public_id")  # Allow setting public ID
        )
        
        # Extract public_id from URL if provided
        if new_user.avatar_url and not new_user.avatar_public_id:
            new_user.avatar_public_id = extract_public_id_from_url(new_user.avatar_url)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"Admin created new user: {new_user.email} (ID: {new_user.id}, Role: {user_role.value})")
        
        response_msg = "User created successfully"
        if user_role != UserRole.ADMIN:
            response_msg += " (Note: Non-admin users cannot log in - they are for tracking purposes only)"
        
        return jsonify({
            "msg": response_msg,
            "user": new_user.as_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": f"Failed to create user: {str(e)}"}), 500

@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get a specific user by ID (admin only)"""
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    user_dict = user.as_dict()
    
    # Generate optimized avatar URL if needed
    if user.avatar_public_id and (not user.avatar_url or 'cloudinary' not in user.avatar_url):
        user_dict['avatar_url'] = generate_cloudinary_url(
            user.avatar_public_id,
            width=300,
            height=300,
            crop='thumb',
            gravity='face'
        )
    
    return jsonify(user_dict), 200

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update a user (admin only)"""
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    data = request.get_json()
    
    # Update email if provided and valid
    if 'email' in data:
        new_email = data['email']
        if not is_valid_email(new_email):
            return jsonify({"msg": "Invalid email address"}), 400
        
        # Check if email is already taken by another user
        def check_email_duplicate():
            return User.query.filter_by(email=new_email).first()
        
        existing_user = db_query_with_retry(check_email_duplicate)
        if existing_user and existing_user.id != user_id:
            return jsonify({"msg": "Email already in use"}), 409
        
        user.email = new_email
    
    # Update other fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'phone' in data:
        user.phone = data['phone']
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    # Handle avatar updates
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
        # Extract public_id from URL if provided
        if data['avatar_url']:
            user.avatar_public_id = extract_public_id_from_url(data['avatar_url'])
        else:
            user.avatar_public_id = None
    
    if 'avatar_public_id' in data:
        user.avatar_public_id = data['avatar_public_id']
    
    # Handle role update
    if 'role' in data:
        try:
            new_role = UserRole[data['role'].upper()]
            old_role = user.role
            
            # If changing TO admin role, require password
            if new_role == UserRole.ADMIN and old_role != UserRole.ADMIN:
                password = data.get("password")
                
                # Validate admin password
                is_valid, error_msg = validate_admin_password(password)
                if not is_valid:
                    return jsonify({"msg": error_msg}), 400
                
                user.password = generate_password_hash(password)
                logger.info(f"User {user.email} promoted to admin - password set")
            
            # If changing FROM admin to non-admin, remove password
            if old_role == UserRole.ADMIN and new_role != UserRole.ADMIN:
                user.password = None
                logger.info(f"User {user.email} demoted from admin - password removed")
            
            user.role = new_role
            
        except KeyError:
            valid_roles = [r.name for r in UserRole]
            return jsonify({
                "msg": f"Invalid role specified. Must be one of: {', '.join(valid_roles)}"
            }), 400
    
    # Update password if provided (only for admin users)
    if 'password' in data and data['password']:
        if user.role == UserRole.ADMIN:
            # Validate admin password
            is_valid, error_msg = validate_admin_password(data['password'])
            if not is_valid:
                return jsonify({"msg": error_msg}), 400
            
            user.password = generate_password_hash(data['password'])
            logger.info(f"Admin password updated for user: {user.email}")
        else:
            return jsonify({"msg": "Cannot set password for non-admin users"}), 400
    
    try:
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin updated user: {user.email} (ID: {user_id})")
        
        return jsonify({
            "msg": "User updated successfully",
            "user": user.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": f"Failed to update user: {str(e)}"}), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only) - soft delete by deactivating"""
    # Get current admin user
    admin_id = get_jwt_identity()
    
    # Prevent admin from deleting themselves
    if str(user_id) == str(admin_id):
        return jsonify({"msg": "Cannot delete your own account"}), 400
    
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    try:
        # Clean up profile picture from Cloudinary if exists
        if user.avatar_public_id:
            delete_result = delete_image(user.avatar_public_id)
            if delete_result.get('success'):
                logger.info(f"Cleaned up Cloudinary avatar for user {user.email}: {user.avatar_public_id}")
            else:
                logger.warning(f"Failed to delete Cloudinary avatar for user {user.email}: {delete_result.get('error')}")
        
        # Soft delete - deactivate instead of actual deletion
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin deactivated user: {user.email} (ID: {user_id})")
        
        return jsonify({
            "msg": "User deactivated successfully",
            "user_id": user_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deactivating user: {str(e)}")
        return jsonify({"msg": "Failed to deactivate user"}), 500

@auth_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """Activate a deactivated user (admin only)"""
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    try:
        user.is_active = True
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin activated user: {user.email} (ID: {user_id})")
        
        return jsonify({
            "msg": "User activated successfully",
            "user": user.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error activating user: {str(e)}")
        return jsonify({"msg": "Failed to activate user"}), 500

# ============================================
# CLOUDINARY FILE UPLOAD ROUTES
# ============================================

@auth_bp.route('/profile/avatar', methods=['POST'])
@jwt_required()
def upload_profile_avatar():
    """Upload profile picture for current user (admin only)"""
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get("role", "").upper()
    
    # Only admins can upload their own profile pictures
    if user_role != "ADMIN":
        return jsonify({"msg": "Only administrators can upload profile pictures"}), 403
    
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Check if file was uploaded
    if 'avatar' not in request.files:
        return jsonify({"msg": "No file uploaded. Please select a file."}), 400
    
    file = request.files['avatar']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({"msg": "No file selected"}), 400
    
    # Validate file using Cloudinary service
    is_valid, error_msg, file_type = validate_upload_file(file, allowed_types=['image'])
    if not is_valid:
        return jsonify({"msg": error_msg}), 400
    
    try:
        # Clean up old profile picture if exists
        if user.avatar_public_id:
            cleanup_result = cleanup_old_profile_picture(user.avatar_public_id)
            if cleanup_result:
                logger.info(f"Cleaned up old avatar for user {user.email}")
        
        # Upload to Cloudinary using enhanced service
        upload_result = handle_cloudinary_upload(
            file=file,
            upload_type='profile',
            user_id=user_id,
            user_name=user.full_name
        )
        
        if not upload_result.get('success'):
            return jsonify({
                "msg": "Failed to upload profile picture",
                "error": upload_result.get('error', 'Unknown error')
            }), 500
        
        # Update user with new avatar information
        user.avatar_url = upload_result.get('avatar_url')
        user.avatar_public_id = upload_result.get('public_id')
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Admin {user.email} uploaded new profile picture: {upload_result.get('public_id')}")
        
        # Generate URLs with cache busting
        avatar_url_cache_bust = generate_cloudinary_url(
            user.avatar_public_id,
            width=200,
            height=200,
            crop='thumb',
            gravity='face'
        )
        
        thumbnail_url_cache_bust = generate_cloudinary_url(
            user.avatar_public_id,
            width=100,
            height=100,
            crop='thumb'
        )
        
        # Update user dict with cache-busted URL
        user_dict = user.as_dict()
        user_dict['avatar_url'] = avatar_url_cache_bust
        
        return jsonify({
            "msg": "Profile picture uploaded successfully",
            "avatar_url": avatar_url_cache_bust,
            "stored_avatar_url": user.avatar_url,
            "avatar_public_id": user.avatar_public_id,
            "original_url": upload_result.get('original_url'),
            "thumbnail_url": thumbnail_url_cache_bust,
            "user": user_dict,
            "cache_bust": True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading profile picture for user {user_id}: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({
            "msg": "Failed to upload profile picture",
            "error": str(e)
        }), 500

@auth_bp.route('/users/<int:user_id>/avatar', methods=['POST'])
@admin_required
def upload_user_avatar(user_id):
    """Upload profile picture for any user (admin only)"""
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Check if file was uploaded
    if 'avatar' not in request.files:
        return jsonify({"msg": "No file uploaded. Please select a file."}), 400
    
    file = request.files['avatar']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({"msg": "No file selected"}), 400
    
    # Validate file using Cloudinary service
    is_valid, error_msg, file_type = validate_upload_file(file, allowed_types=['image'])
    if not is_valid:
        return jsonify({"msg": error_msg}), 400
    
    try:
        # Clean up old profile picture if exists
        if user.avatar_public_id:
            cleanup_result = cleanup_old_profile_picture(user.avatar_public_id)
            if cleanup_result:
                logger.info(f"Cleaned up old avatar for user {user.email}")
        
        # Upload to Cloudinary using enhanced service
        upload_result = handle_cloudinary_upload(
            file=file,
            upload_type='profile',
            user_id=user_id,
            user_name=user.full_name
        )
        
        if not upload_result.get('success'):
            return jsonify({
                "msg": "Failed to upload profile picture",
                "error": upload_result.get('error', 'Unknown error')
            }), 500
        
        # Update user with new avatar information
        user.avatar_url = upload_result.get('avatar_url')
        user.avatar_public_id = upload_result.get('public_id')
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Admin uploaded profile picture for user {user.email}: {upload_result.get('public_id')}")
        
        # Generate cache-busted URL
        avatar_url_cache_bust = generate_cloudinary_url(
            user.avatar_public_id,
            width=200,
            height=200,
            crop='thumb',
            gravity='face'
        )
        
        # Update user dict with cache-busted URL
        user_dict = user.as_dict()
        user_dict['avatar_url'] = avatar_url_cache_bust
        
        return jsonify({
            "msg": "Profile picture uploaded successfully",
            "avatar_url": avatar_url_cache_bust,
            "stored_avatar_url": user.avatar_url,
            "avatar_public_id": user.avatar_public_id,
            "original_url": upload_result.get('original_url'),
            "user": user_dict,
            "cache_bust": True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading profile picture for user {user_id}: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({
            "msg": "Failed to upload profile picture",
            "error": str(e)
        }), 500

@auth_bp.route('/profile/avatar', methods=['DELETE'])
@jwt_required()
def delete_profile_avatar():
    """Delete current user's profile picture (admin only)"""
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get("role", "").upper()
    
    # Only admins can delete their profile pictures
    if user_role != "ADMIN":
        return jsonify({"msg": "Only administrators can delete profile pictures"}), 403
    
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    if not user.avatar_public_id:
        return jsonify({"msg": "No profile picture to delete"}), 400
    
    try:
        # Delete from Cloudinary using enhanced service
        delete_result = delete_image(user.avatar_public_id)
        
        if not delete_result.get('success'):
            logger.warning(f"Failed to delete Cloudinary image {user.avatar_public_id}: {delete_result.get('error')}")
            # Continue with database update even if Cloudinary deletion fails
        
        # Update user
        old_avatar_url = user.avatar_url
        old_public_id = user.avatar_public_id
        
        user.avatar_url = None
        user.avatar_public_id = None
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Admin {user.email} deleted profile picture: {old_public_id}")
        
        return jsonify({
            "msg": "Profile picture deleted successfully",
            "deleted_avatar_url": old_avatar_url,
            "deleted_public_id": old_public_id,
            "cloudinary_result": delete_result.get('result') if delete_result.get('success') else None,
            "user": user.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting profile picture for user {user_id}: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({
            "msg": "Failed to delete profile picture",
            "error": str(e)
        }), 500

@auth_bp.route('/users/<int:user_id>/avatar', methods=['DELETE'])
@admin_required
def delete_user_avatar(user_id):
    """Delete profile picture for any user (admin only)"""
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    if not user.avatar_public_id:
        return jsonify({"msg": "No profile picture to delete"}), 400
    
    try:
        # Delete from Cloudinary using enhanced service
        delete_result = delete_image(user.avatar_public_id)
        
        if not delete_result.get('success'):
            logger.warning(f"Failed to delete Cloudinary image {user.avatar_public_id}: {delete_result.get('error')}")
            # Continue with database update even if Cloudinary deletion fails
        
        # Update user
        old_avatar_url = user.avatar_url
        old_public_id = user.avatar_public_id
        
        user.avatar_url = None
        user.avatar_public_id = None
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Admin deleted profile picture for user {user.email}: {old_public_id}")
        
        return jsonify({
            "msg": "Profile picture deleted successfully",
            "deleted_avatar_url": old_avatar_url,
            "deleted_public_id": old_public_id,
            "cloudinary_result": delete_result.get('result') if delete_result.get('success') else None,
            "user": user.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting profile picture for user {user_id}: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({
            "msg": "Failed to delete profile picture",
            "error": str(e)
        }), 500

# ============================================
# GENERAL FILE UPLOAD ROUTES
# ============================================

@auth_bp.route('/upload', methods=['POST'])
@admin_required
def upload_file_endpoint():
    """Upload any file to Cloudinary (admin only)"""
    if 'file' not in request.files:
        return jsonify({"msg": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No file selected"}), 400
    
    # Get upload parameters
    upload_type = request.form.get('type', 'general')
    folder = request.form.get('folder')
    public_id = request.form.get('public_id')
    file_type = request.form.get('file_type', 'image')
    
    # Validate file
    is_valid, error_msg, detected_type = validate_upload_file(file, allowed_types=['image', 'video', 'document'])
    if not is_valid:
        return jsonify({"msg": error_msg}), 400
    
    try:
        # Handle different upload types
        if upload_type == 'portfolio':
            portfolio_id = request.form.get('portfolio_id')
            title = request.form.get('title')
            category = request.form.get('category')
            
            if not portfolio_id or not title:
                return jsonify({"msg": "Portfolio ID and title are required for portfolio upload"}), 400
            
            upload_result = handle_cloudinary_upload(
                file=file,
                upload_type='portfolio',
                portfolio_id=portfolio_id,
                title=title,
                category=category
            )
        
        elif upload_type == 'service':
            service_id = request.form.get('service_id')
            service_name = request.form.get('service_name')
            
            if not service_id or not service_name:
                return jsonify({"msg": "Service ID and name are required for service upload"}), 400
            
            upload_result = handle_cloudinary_upload(
                file=file,
                upload_type='service',
                service_id=service_id,
                service_name=service_name
            )
        
        else:
            # General upload
            upload_result = handle_cloudinary_upload(
                file=file,
                upload_type='general',
                folder=folder,
                public_id=public_id,
                file_type=file_type
            )
        
        if not upload_result.get('success'):
            return jsonify({
                "msg": "File upload failed",
                "error": upload_result.get('error', 'Unknown error')
            }), 500
        
        # Generate thumbnail for images
        if upload_result.get('resource_type') == 'image' and upload_result.get('public_id'):
            upload_result['thumbnail_url'] = generate_cloudinary_url(
                upload_result['public_id'],
                width=300,
                height=200,
                crop='fill'
            )
        
        logger.info(f"File uploaded successfully: {upload_result.get('public_id')}")
        
        return jsonify({
            "msg": "File uploaded successfully",
            "data": upload_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({
            "msg": "Failed to upload file",
            "error": str(e)
        }), 500

# ============================================
# USER FILTERING AND STATISTICS ROUTES
# ============================================

@auth_bp.route('/users/non-admins', methods=['GET'])
@admin_required
def get_non_admin_users():
    """Get list of all non-admin users (photographers, staff, etc.) - admin only"""
    try:
        def get_non_admins():
            return User.query.filter(
                User.role != UserRole.ADMIN
            ).order_by(User.created_at.desc()).all()
        
        users = db_query_with_retry(get_non_admins)
        
        if not users:
            return jsonify({
                "msg": "No non-admin users found",
                "users": []
            }), 200
        
        logger.info(f"Admin retrieved {len(users)} non-admin users")
        
        return jsonify({
            "count": len(users),
            "users": [user.as_dict() for user in users]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching non-admin users: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": "Failed to fetch non-admin users"}), 500

@auth_bp.route('/users/by-role/<role>', methods=['GET'])
@admin_required
def get_users_by_role(role):
    """Get list of users filtered by specific role - admin only"""
    try:
        # Validate role
        try:
            user_role = UserRole[role.upper()]
        except KeyError:
            valid_roles = [r.name for r in UserRole]
            return jsonify({
                "msg": f"Invalid role specified. Must be one of: {', '.join(valid_roles)}"
            }), 400
        
        def get_users_with_role():
            return User.query.filter_by(
                role=user_role
            ).order_by(User.created_at.desc()).all()
        
        users = db_query_with_retry(get_users_with_role)
        
        logger.info(f"Admin retrieved {len(users)} users with role {role.upper()}")
        
        return jsonify({
            "role": role.upper(),
            "count": len(users),
            "users": [user.as_dict() for user in users]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching users by role {role}: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": f"Failed to fetch users with role {role}"}), 500

@auth_bp.route('/users/photographers', methods=['GET'])
@admin_required
def get_photographers():
    """Get list of all photographers - admin only (convenience endpoint)"""
    try:
        def get_photographer_users():
            return User.query.filter_by(
                role=UserRole.PHOTOGRAPHER
            ).order_by(User.created_at.desc()).all()
        
        photographers = db_query_with_retry(get_photographer_users)
        
        logger.info(f"Admin retrieved {len(photographers)} photographers")
        
        return jsonify({
            "count": len(photographers),
            "photographers": [user.as_dict() for user in photographers]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching photographers: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": "Failed to fetch photographers"}), 500

@auth_bp.route('/users/videographers', methods=['GET'])
@admin_required
def get_videographers():
    """Get list of all videographers - admin only (NEW ENDPOINT)"""
    try:
        def get_videographer_users():
            return User.query.filter_by(
                role=UserRole.VIDEOGRAPHY
            ).order_by(User.created_at.desc()).all()
        
        videographers = db_query_with_retry(get_videographer_users)
        
        logger.info(f"Admin retrieved {len(videographers)} videographers")
        
        return jsonify({
            "count": len(videographers),
            "videographers": [user.as_dict() for user in videographers]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching videographers: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": "Failed to fetch videographers"}), 500

@auth_bp.route('/users/media-staff', methods=['GET'])
@admin_required
def get_media_staff():
    """Get list of all media staff (photographers and videographers) - admin only (NEW ENDPOINT)"""
    try:
        def get_media_staff_users():
            return User.query.filter(
                User.role.in_([UserRole.PHOTOGRAPHER, UserRole.VIDEOGRAPHY])
            ).order_by(User.created_at.desc()).all()
        
        media_staff = db_query_with_retry(get_media_staff_users)
        
        logger.info(f"Admin retrieved {len(media_staff)} media staff members")
        
        # Group by role for frontend convenience
        photographers = [user for user in media_staff if user.role == UserRole.PHOTOGRAPHER]
        videographers = [user for user in media_staff if user.role == UserRole.VIDEOGRAPHY]
        
        return jsonify({
            "count": len(media_staff),
            "photographers_count": len(photographers),
            "videographers_count": len(videographers),
            "media_staff": [user.as_dict() for user in media_staff],
            "photographers": [user.as_dict() for user in photographers],
            "videographers": [user.as_dict() for user in videographers]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching media staff: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": "Failed to fetch media staff"}), 500

@auth_bp.route('/users/stats', methods=['GET'])
@admin_required
def get_user_stats():
    """Get user statistics by role - admin only"""
    try:
        def get_all_users():
            return User.query.all()
        
        all_users = db_query_with_retry(get_all_users)
        
        # Count users by role
        role_counts = {}
        active_counts = {}
        inactive_counts = {}
        login_enabled_counts = {}  # Only admins with passwords
        with_avatar_counts = {}    # Users with Cloudinary avatars
        
        for role in UserRole:
            role_name = role.value
            role_users = [u for u in all_users if u.role == role]
            role_counts[role_name] = len(role_users)
            active_counts[role_name] = len([u for u in role_users if u.is_active])
            inactive_counts[role_name] = len([u for u in role_users if not u.is_active])
            with_avatar_counts[role_name] = len([u for u in role_users if u.avatar_public_id])
            
            # Count users who can login (only admins with passwords)
            if role == UserRole.ADMIN:
                login_enabled_counts[role_name] = len([u for u in role_users if u.password is not None])
            else:
                login_enabled_counts[role_name] = 0  # Non-admins can't login
        
        total_users = len(all_users)
        total_active = len([u for u in all_users if u.is_active])
        total_inactive = len([u for u in all_users if not u.is_active])
        total_can_login = len([u for u in all_users if u.role == UserRole.ADMIN and u.password is not None])
        total_with_avatar = len([u for u in all_users if u.avatar_public_id])
        
        logger.info(f"Admin retrieved user statistics")
        
        return jsonify({
            "total_users": total_users,
            "total_active": total_active,
            "total_inactive": total_inactive,
            "total_can_login": total_can_login,
            "total_with_avatar": total_with_avatar,
            "by_role": role_counts,
            "active_by_role": active_counts,
            "inactive_by_role": inactive_counts,
            "login_enabled_by_role": login_enabled_counts,
            "with_avatar_by_role": with_avatar_counts
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": "Failed to fetch user statistics"}), 500

# ============================================
# USER PROFILE ROUTES
# ============================================

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info from JWT - only admins will have valid tokens"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        def get_user_by_id():
            return User.query.get(user_id)
        
        user = db_query_with_retry(get_user_by_id)
        if not user:
            logger.error(f"User not found in database: {user_id}")
            return jsonify({"msg": "User not found"}), 404
        
        # Generate optimized avatar URL with cache busting
        avatar_url = user.avatar_url
        if not avatar_url and user.avatar_public_id:
            avatar_url = generate_cloudinary_url(
                user.avatar_public_id,
                width=200,
                height=200,
                crop='thumb',
                gravity='face'
            )
        elif user.avatar_public_id:
            # Generate cache-busted version even if we have a URL
            avatar_url = generate_cloudinary_url(
                user.avatar_public_id,
                width=200,
                height=200,
                crop='thumb',
                gravity='face'
            )
        
        return jsonify({
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name,
            "phone": user.phone,
            "avatar_url": avatar_url,
            "avatar_public_id": user.avatar_public_id,
            "is_active": user.is_active,
            "can_login": user.role == UserRole.ADMIN and user.password is not None
        }), 200
        
    except Exception as e:
        logger.error(f"ERROR in get_current_user: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"msg": "Invalid or missing token"}), 401

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile - only admins can access this"""
    user_id = get_jwt_identity()
    
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user_dict = user.as_dict()
    
    # Generate optimized avatar URL if needed
    if user.avatar_public_id and (not user.avatar_url or 'cloudinary' not in user.avatar_url):
        user_dict['avatar_url'] = generate_cloudinary_url(
            user.avatar_public_id,
            width=300,
            height=300,
            crop='thumb',
            gravity='face'
        )
    elif user.avatar_public_id:
        # Generate cache-busted version
        user_dict['avatar_url'] = generate_cloudinary_url(
            user.avatar_public_id,
            width=300,
            height=300,
            crop='thumb',
            gravity='face'
        )
    
    return jsonify(user_dict), 200

# ============================================
# CREATE USER WITH AVATAR UPLOAD (NEW ENDPOINT)
# ============================================

@auth_bp.route('/users/upload-avatar', methods=['POST'])
@admin_required
def create_user_with_avatar():
    """Create a new user with avatar upload (admin only)"""
    # Check if file was uploaded
    if 'avatar' not in request.files:
        return jsonify({"msg": "No file uploaded. Please select a file."}), 400
    
    file = request.files['avatar']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({"msg": "No file selected"}), 400
    
    # Get form data for user creation
    email = request.form.get('email')
    full_name = request.form.get('full_name')
    role = request.form.get('role', 'PHOTOGRAPHER')
    phone = request.form.get('phone')
    is_active = request.form.get('is_active', 'true').lower() == 'true'
    password = request.form.get('password')
    confirm_password = request.form.get('confirmPassword')
    
    # Validate required fields
    if not all([email, full_name]):
        return jsonify({"msg": "Email and full name are required"}), 400
    
    # Validate email format
    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400
    
    # Check if email already exists
    def check_email_exists():
        return User.query.filter_by(email=email).first()
    
    if db_query_with_retry(check_email_exists):
        return jsonify({"msg": "Email already registered"}), 409
    
    # Validate role
    try:
        user_role = UserRole[role.upper()]
    except KeyError:
        valid_roles = [r.name for r in UserRole]
        return jsonify({
            "msg": f"Invalid role specified. Must be one of: {', '.join(valid_roles)}"
        }), 400
    
    # Handle password based on role
    hashed_password = None
    if user_role == UserRole.ADMIN:
        # Admin users MUST have a password
        if not password:
            return jsonify({"msg": "Password is required for admin users"}), 400
        
        # Validate admin password
        is_valid_pw, error_msg = validate_admin_password(password)
        if not is_valid_pw:
            return jsonify({"msg": error_msg}), 400
        
        # Check password confirmation
        if password != confirm_password:
            return jsonify({"msg": "Passwords do not match"}), 400
        
        hashed_password = generate_password_hash(password)
    else:
        # Non-admin users: No password
        hashed_password = None
        
        logger.info(f"Creating non-admin user {email} - NO LOGIN ACCESS (Role: {user_role.value})")
    
    # Validate file using Cloudinary service
    is_valid_file, error_msg, file_type = validate_upload_file(file, allowed_types=['image'])
    if not is_valid_file:
        return jsonify({"msg": error_msg}), 400
    
    try:
        # Create the user without avatar first
        new_user = User(
            email=email,
            password=hashed_password,
            full_name=full_name,
            role=user_role,
            phone=phone,
            is_active=is_active,
            avatar_url=None,
            avatar_public_id=None
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Now upload the avatar
        upload_result = handle_cloudinary_upload(
            file=file,
            upload_type='profile',
            user_id=new_user.id,
            user_name=new_user.full_name
        )
        
        if not upload_result.get('success'):
            # If upload fails, delete the user and return error
            db.session.delete(new_user)
            db.session.commit()
            return jsonify({
                "msg": "Failed to upload profile picture",
                "error": upload_result.get('error', 'Unknown error')
            }), 500
        
        # Update user with avatar information
        new_user.avatar_url = upload_result.get('avatar_url')
        new_user.avatar_public_id = upload_result.get('public_id')
        new_user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Admin created new user with avatar: {new_user.email} (ID: {new_user.id}, Role: {user_role.value})")
        
        # Generate cache-busted URL
        avatar_url_cache_bust = generate_cloudinary_url(
            new_user.avatar_public_id,
            width=200,
            height=200,
            crop='thumb',
            gravity='face'
        )
        
        # Update user dict with cache-busted URL
        user_dict = new_user.as_dict()
        user_dict['avatar_url'] = avatar_url_cache_bust
        
        response_msg = "User created successfully with profile picture"
        if user_role != UserRole.ADMIN:
            response_msg += " (Note: Non-admin users cannot log in - they are for tracking purposes only)"
        
        return jsonify({
            "msg": response_msg,
            "avatar_url": avatar_url_cache_bust,
            "stored_avatar_url": new_user.avatar_url,
            "avatar_public_id": new_user.avatar_public_id,
            "original_url": upload_result.get('original_url'),
            "user": user_dict,
            "cache_bust": True
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user with avatar: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({
            "msg": "Failed to create user with profile picture",
            "error": str(e)
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile information - only admins can update their profile"""
    user_id = get_jwt_identity()
    
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Only admins can update profiles (only they have JWT tokens)
    if user.role != UserRole.ADMIN:
        return jsonify({"msg": "Only administrators can update profiles"}), 403

    data = request.get_json()
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
        # Extract public_id from URL if provided
        if data['avatar_url']:
            user.avatar_public_id = extract_public_id_from_url(data['avatar_url'])

    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "msg": "Profile updated successfully",
        "user": user.as_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change current user's password (admin only - only admins have passwords)"""
    user_id = get_jwt_identity()
    
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Only admins can change passwords (they're the only ones with passwords)
    if user.role != UserRole.ADMIN:
        return jsonify({"msg": "Only administrators can change passwords"}), 403

    data = request.get_json()
    
    # Validate required fields
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return jsonify({"msg": "All password fields are required"}), 400
    
    # Verify current password
    if not check_password_hash(user.password, current_password):
        return jsonify({"msg": "Current password is incorrect"}), 400
    
    # Check if new password matches confirmation
    if new_password != confirm_password:
        return jsonify({"msg": "New passwords do not match"}), 400
    
    # Validate admin password requirements
    is_valid, error_msg = validate_admin_password(new_password)
    if not is_valid:
        return jsonify({"msg": error_msg}), 400
    
    # Check if new password is same as current password
    if check_password_hash(user.password, new_password):
        return jsonify({"msg": "New password cannot be the same as current password"}), 400
    
    try:
        # Update password
        user.password = generate_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin {user.email} changed their password")
        
        return jsonify({
            "msg": "Password changed successfully",
            "user": user.as_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password for admin {user.email}: {str(e)}")
        return jsonify({"msg": "Failed to change password"}), 500

# ============================================
# DEBUG AND ADMIN UTILITY ROUTES
# ============================================

@auth_bp.route('/debug-token', methods=['GET'])
@jwt_required()
def debug_token():
    """Temporary debug endpoint to see JWT contents - admin only"""
    claims = get_jwt()
    identity = get_jwt_identity()
    return jsonify({
        "identity": identity,
        "claims": claims
    }), 200

@auth_bp.route('/users/admins', methods=['GET'])
@admin_required
def get_admin_users():
    """Get list of all admin users - admin only"""
    try:
        def get_admin_users():
            return User.query.filter_by(
                role=UserRole.ADMIN
            ).order_by(User.created_at.desc()).all()
        
        admins = db_query_with_retry(get_admin_users)
        
        logger.info(f"Admin retrieved {len(admins)} admin users")
        
        # Filter to show only admins who can login (have passwords)
        admins_with_login = [admin for admin in admins if admin.password is not None]
        
        return jsonify({
            "count": len(admins),
            "count_with_login": len(admins_with_login),
            "admins": [admin.as_dict() for admin in admins]
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching admin users: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return jsonify({"msg": "Failed to fetch admin users"}), 500

@auth_bp.route('/users/<int:user_id>/set-password', methods=['POST'])
@admin_required
def set_user_password(user_id):
    """Set or reset password for a user (admin only) - Only for admin users"""
    data = request.get_json()
    password = data.get("password")
    
    if not password:
        return jsonify({"msg": "Password is required"}), 400
    
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Only admin users can have passwords
    if user.role != UserRole.ADMIN:
        return jsonify({"msg": "Cannot set password for non-admin users"}), 400
    
    # Validate admin password
    is_valid, error_msg = validate_admin_password(password)
    if not is_valid:
        return jsonify({"msg": error_msg}), 400
    
    try:
        user.password = generate_password_hash(password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin set password for user: {user.email}")
        
        return jsonify({
            "msg": "Password set successfully",
            "user_id": user_id,
            "can_login": True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting password: {str(e)}")
        return jsonify({"msg": "Failed to set password"}), 500

@auth_bp.route('/users/<int:user_id>/remove-password', methods=['POST'])
@admin_required
def remove_user_password(user_id):
    """Remove password from a user (admin only) - For demoting admin to non-admin"""
    def get_user_by_id():
        return User.query.get(user_id)
    
    user = db_query_with_retry(get_user_by_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Only remove password if changing role from admin
    if user.role == UserRole.ADMIN:
        return jsonify({"msg": "Cannot remove password from admin user without changing role"}), 400
    
    try:
        user.password = None
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin removed password from user: {user.email}")
        
        return jsonify({
            "msg": "Password removed successfully (user cannot login)",
            "user_id": user_id,
            "can_login": False
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing password: {str(e)}")
        return jsonify({"msg": "Failed to remove password"}), 500