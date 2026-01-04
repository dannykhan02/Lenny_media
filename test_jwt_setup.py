#!/usr/bin/env python3
"""
Quick script to verify JWT and authentication setup
Run this before starting your Flask app
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_vars():
    """Check if required environment variables are set"""
    print("=" * 70)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("=" * 70)
    
    required_vars = {
        'SECRET_KEY': 'Flask secret key',
        'JWT_SECRET_KEY': 'JWT secret key',
        'DATABASE_URL': 'Database connection string',
        'FRONTEND_URL': 'Frontend URL for CORS'
    }
    
    optional_vars = {
        'FLASK_ENV': 'Flask environment (development/production)',
        'DEBUG': 'Debug mode',
        'JWT_COOKIE_SECURE': 'JWT cookie secure flag',
        'JWT_COOKIE_SAMESITE': 'JWT cookie SameSite policy'
    }
    
    missing = []
    
    # Check required variables
    print("\nRequired Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            display_value = value if var not in ['SECRET_KEY', 'JWT_SECRET_KEY'] else f"{value[:10]}..." if len(value) > 10 else "***"
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            missing.append(var)
    
    # Check optional variables
    print("\nOptional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var, 'Not set (using default)')
        print(f"  • {var}: {value}")
    
    if missing:
        print("\n❌ MISSING REQUIRED VARIABLES:")
        for var in missing:
            print(f"  - {var}")
        return False
    
    print("\n✅ All required environment variables are set!")
    return True


def check_config():
    """Check configuration settings"""
    print("\n" + "=" * 70)
    print("CHECKING CONFIGURATION")
    print("=" * 70)
    
    try:
        from config import get_config
        
        env = os.getenv('FLASK_ENV', 'development')
        config = get_config(env)
        
        print(f"\nEnvironment: {env}")
        print(f"Config Class: {config.__name__}")
        
        # Check JWT settings
        print("\nJWT Configuration:")
        jwt_settings = {
            'JWT_TOKEN_LOCATION': config.JWT_TOKEN_LOCATION,
            'JWT_COOKIE_SECURE': config.JWT_COOKIE_SECURE,
            'JWT_COOKIE_CSRF_PROTECT': config.JWT_COOKIE_CSRF_PROTECT,
            'JWT_COOKIE_SAMESITE': config.JWT_COOKIE_SAMESITE,
            'JWT_ACCESS_COOKIE_NAME': config.JWT_ACCESS_COOKIE_NAME,
        }
        
        for key, value in jwt_settings.items():
            status = "✓" if value else "✗"
            print(f"  {status} {key}: {value}")
        
        # Check CORS settings
        print("\nCORS Configuration:")
        print(f"  Supports Credentials: {config.CORS_SUPPORTS_CREDENTIALS}")
        print(f"  Allowed Origins: {len(config.CORS_ORIGINS)} origins")
        for origin in config.CORS_ORIGINS:
            print(f"    - {origin}")
        
        # Check critical settings
        print("\nCritical Checks:")
        checks = [
            ('cookies' in config.JWT_TOKEN_LOCATION, "JWT uses cookies"),
            (config.JWT_ACCESS_COOKIE_NAME == 'access_token_cookie', "Cookie name is correct"),
            (config.CORS_SUPPORTS_CREDENTIALS, "CORS supports credentials"),
            (not config.JWT_COOKIE_SECURE if env == 'development' else True, "Cookie security appropriate for env"),
        ]
        
        all_passed = True
        for passed, description in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {description}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n✅ Configuration looks good!")
        else:
            print("\n⚠️  Some configuration issues detected")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Error loading configuration: {e}")
        return False


def check_flask_imports():
    """Check if required Flask packages are installed"""
    print("\n" + "=" * 70)
    print("CHECKING FLASK PACKAGES")
    print("=" * 70)
    
    packages = {
        'flask': 'Flask',
        'flask_jwt_extended': 'Flask-JWT-Extended',
        'flask_cors': 'Flask-CORS',
        'flask_sqlalchemy': 'Flask-SQLAlchemy',
        'werkzeug': 'Werkzeug',
    }
    
    missing = []
    
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            missing.append(name)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join([p.lower().replace('-', '_') for p in missing]))
        return False
    
    print("\n✅ All required packages are installed!")
    return True


def main():
    """Run all checks"""
    print("\n" + "=" * 70)
    print("JWT AUTHENTICATION SETUP VERIFICATION")
    print("=" * 70)
    
    checks = [
        ("Environment Variables", check_env_vars),
        ("Flask Packages", check_flask_imports),
        ("Configuration", check_config),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All checks passed! Your JWT setup is ready.")
        print("\nNext steps:")
        print("1. Clear browser cookies")
        print("2. Restart Flask server: python run.py")
        print("3. Test login in your React app")
        sys.exit(0)
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()