from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
import logging
import re
from ..models import User, UserRole
from .. import db


# Initialize blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Helper functions
def role_required(required_role):
    """Decorator to check if user has the required role"""
    def decorator(fn):
        @jwt_required()
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if "role" not in claims or claims["role"].upper() != required_role.upper():
                return jsonify({"msg": "Forbidden: Access Denied"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def is_valid_email(email: str) -> bool:
    """
    Validates email format using RFC 5322 compliant regex pattern.
    
    Checks for:
    - Valid local part (before @)
    - Valid domain part (after @)
    - Proper domain structure with TLD
    - No invalid characters
    - Reasonable length constraints
    
    Args:
        email: Email address string to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Trim whitespace
    email = email.strip()
    
    # Check length constraints (RFC 5321)
    if len(email) > 254 or len(email) < 6:  # min: a@b.co
        return False
    
    # RFC 5322 compliant email regex pattern
    # This pattern checks for valid email structure
    email_pattern = re.compile(
        r'^(?:[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*'  # Local part
        r'|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")'  # Quoted local part
        r'@'  # @ symbol
        r'(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?'  # Domain
        r'|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\])$'  # IP address
    )
    
    if not email_pattern.match(email):
        return False
    
    # Additional validation checks
    local_part, domain_part = email.rsplit('@', 1)
    
    # Check local part length (RFC 5321)
    if len(local_part) > 64:
        return False
    
    # Check domain part length and structure
    if len(domain_part) > 253:
        return False
    
    # Ensure domain has at least one dot (TLD requirement)
    if '.' not in domain_part:
        return False
    
    # Check for consecutive dots
    if '..' in email:
        return False
    
    # Check that domain doesn't start or end with a dot or hyphen
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    if domain_part.startswith('-') or domain_part.endswith('-'):
        return False
    
    # Validate TLD (top-level domain) - at least 2 characters
    tld = domain_part.split('.')[-1]
    if len(tld) < 2:
        return False
    
    return True

# Authentication routes
@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login with JWT token generation"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "role": str(user.role.value)
        },
        expires_delta=timedelta(days=1)
    )

    response = jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": str(user.role.value),
            "full_name": user.full_name,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active
        }
    })

    # Set HTTP-only cookie with the access token
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite='Lax',
        path='/',
        max_age=24*60*60  # 24 hours
    )

    logger.info(f"User logged in: {user.email}")
    return response, 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear authentication cookie"""
    response = jsonify({"message": "Logout successful"})
    response.delete_cookie('access_token')
    return response, 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user (default: STAFF role)"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    role = data.get("role", "STAFF")  # Default to staff

    if not all([email, password, full_name]):
        return jsonify({"msg": "Email, password, and full name are required"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 400

    # Validate role
    try:
        user_role = UserRole[role.upper()]
    except KeyError:
        return jsonify({"msg": f"Invalid role specified. Must be one of: {', '.join([r.name for r in UserRole])}"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(
        email=email,
        password=hashed_password,
        full_name=full_name,
        role=user_role,
        phone=data.get("phone"),
        avatar_url=data.get("avatar_url")
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "msg": "User registered successfully",
        "user_id": new_user.id,
        "email": new_user.email
    }), 201

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify(user.as_dict()), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile information"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']

    db.session.commit()
    return jsonify({
        "msg": "Profile updated successfully",
        "user": user.as_dict()
    }), 200

@auth_bp.route('/check-admin', methods=['GET'])
def check_admin():
    """Check if admin user exists"""
    admin_exists = User.query.filter_by(role=UserRole.ADMIN).first() is not None
    return jsonify({"admin_exists": admin_exists}), 200

@auth_bp.route('/register-first-admin', methods=['POST'])
def register_first_admin():
    """Register the first admin user (only if no admin exists) and auto-login"""
    if User.query.filter_by(role=UserRole.ADMIN).first():
        return jsonify({"msg": "Admin already exists"}), 403

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not all([email, password, full_name]):
        return jsonify({"msg": "All fields are required"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400

    if User.query.filter_by(email=email).first():
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
            "avatar_url": new_admin.avatar_url,
            "is_active": new_admin.is_active
        }
    })

    # Set HTTP-only cookie with the access token
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite='Lax',
        path='/',
        max_age=24*60*60  # 24 hours
    )

    logger.info(f"Admin registered and auto-logged in: {new_admin.email}")
    return response, 201

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get list of all users (admin only)"""
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Forbidden: Access Denied"}), 403
    
    users = User.query.all()
    return jsonify([user.as_dict() for user in users]), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info from JWT"""
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "email": user.email,
        "role": user.role.value,
        "full_name": user.full_name,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "claims": claims
    }), 200