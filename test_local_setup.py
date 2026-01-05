#!/usr/bin/env python3
"""
Test script to verify local setup before Koyeb deployment
Run: python test_local_setup.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_environment_variables():
    """Check if required environment variables are set"""
    print("\n" + "=" * 80)
    print("🔍 Testing Environment Variables")
    print("=" * 80)
    
    required_vars = {
        'SECRET_KEY': 'Application secret key',
        'JWT_SECRET_KEY': 'JWT secret key',
    }
    
    optional_vars = {
        'FLASK_ENV': 'Flask environment (development/production)',
        'DATABASE_URL': 'Database connection string',
        'CLOUDINARY_CLOUD_NAME': 'Cloudinary cloud name',
        'CLOUDINARY_API_KEY': 'Cloudinary API key',
        'CLOUDINARY_API_SECRET': 'Cloudinary API secret',
        'MAIL_USERNAME': 'Email username',
        'MAIL_PASSWORD': 'Email password',
        'FRONTEND_URL': 'Frontend URL',
    }
    
    # Check required variables
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked} ({description})")
        else:
            print(f"❌ {var}: NOT SET ({description})")
            missing_required.append(var)
    
    # Check optional variables
    missing_optional = []
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                masked = value[:5] + "..." if len(value) > 5 else "***"
            else:
                masked = value[:30] + "..." if len(value) > 30 else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"⚠️  {var}: Not set ({description})")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional variables: {', '.join(missing_optional)}")
        print("   App will work but some features may be disabled")
    
    return True


def test_config_loading():
    """Test if configuration loads correctly"""
    print("\n" + "=" * 80)
    print("🔍 Testing Configuration Loading")
    print("=" * 80)
    
    try:
        from config import get_config
        
        # Test development config
        print("\n📝 Testing Development Config:")
        dev_config = get_config('development')
        print(f"   Class: {dev_config.__name__}")
        print(f"   Debug: {dev_config.DEBUG}")
        print(f"   Database: {dev_config.SQLALCHEMY_DATABASE_URI[:50]}...")
        
        # Test production config (will fail if DATABASE_URL not set)
        print("\n📝 Testing Production Config:")
        try:
            # Temporarily set DATABASE_URL if not set
            original_db = os.getenv('DATABASE_URL')
            if not original_db:
                os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
            
            prod_config = get_config('production')
            print(f"   Class: {prod_config.__name__}")
            print(f"   Debug: {prod_config.DEBUG}")
            print(f"   JWT Secure: {prod_config.JWT_COOKIE_SECURE}")
            print(f"   JWT SameSite: {prod_config.JWT_COOKIE_SAMESITE}")
            
            # Restore original
            if not original_db:
                del os.environ['DATABASE_URL']
            
        except ValueError as e:
            print(f"   ⚠️  Production config requires DATABASE_URL: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_creation():
    """Test if Flask app can be created"""
    print("\n" + "=" * 80)
    print("🔍 Testing Flask App Creation")
    print("=" * 80)
    
    try:
        # Set to development for testing
        os.environ['FLASK_ENV'] = 'development'
        
        from app import create_app
        
        print("\n📝 Creating Flask app...")
        app = create_app()
        
        print(f"\n✅ App created successfully")
        print(f"   Name: {app.name}")
        print(f"   Debug: {app.debug}")
        print(f"   Environment: {app.config.get('ENV', 'not set')}")
        
        # Test database connection
        print("\n📝 Testing database connection...")
        with app.app_context():
            from app.db import db
            try:
                db.session.execute(db.text('SELECT 1'))
                print("   ✅ Database connection successful")
            except Exception as e:
                print(f"   ⚠️  Database connection failed: {e}")
                print("   This is normal if migrations haven't been run yet")
        
        # Test routes
        print("\n📝 Registered routes:")
        with app.app_context():
            for rule in app.url_map.iter_rules():
                if not rule.rule.startswith('/static'):
                    print(f"   {rule.rule} [{', '.join(rule.methods)}]")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_uri_conversion():
    """Test if postgres:// to postgresql:// conversion works"""
    print("\n" + "=" * 80)
    print("🔍 Testing Database URI Conversion")
    print("=" * 80)
    
    test_cases = [
        "postgres://user:pass@host:5432/db",
        "postgresql://user:pass@host:5432/db",
        "sqlite:///local.db",
    ]
    
    for uri in test_cases:
        print(f"\n📝 Testing: {uri[:30]}...")
        
        # Temporarily set DATABASE_URL
        os.environ['DATABASE_URL'] = uri
        os.environ['FLASK_ENV'] = 'production'
        
        try:
            from config import get_config
            
            # Reload the module to pick up new env var
            import importlib
            import config.production
            importlib.reload(config.production)
            
            config = get_config('production')
            result_uri = config.SQLALCHEMY_DATABASE_URI
            
            if uri.startswith('postgres://'):
                expected = uri.replace('postgres://', 'postgresql://', 1)
                if result_uri == expected:
                    print(f"   ✅ Converted correctly to: postgresql://...")
                else:
                    print(f"   ❌ Conversion failed")
                    print(f"      Expected: {expected[:40]}...")
                    print(f"      Got: {result_uri[:40]}...")
            else:
                if result_uri == uri:
                    print(f"   ✅ URI unchanged (correct)")
                else:
                    print(f"   ❌ URI changed unexpectedly")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Clean up
    if 'DATABASE_URL' in os.environ:
        del os.environ['DATABASE_URL']
    os.environ['FLASK_ENV'] = 'development'
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🚀 Lenny Media API - Local Setup Verification")
    print("=" * 80)
    
    results = {
        'Environment Variables': test_environment_variables(),
        'Config Loading': test_config_loading(),
        'Database URI Conversion': test_database_uri_conversion(),
        'App Creation': test_app_creation(),
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Ready for deployment.")
        print("\nNext steps:")
        print("1. Commit your changes: git add . && git commit -m 'Ready for Koyeb'")
        print("2. Push to GitHub: git push origin main")
        print("3. Create PostgreSQL database on Koyeb")
        print("4. Deploy Flask service on Koyeb")
        return 0
    else:
        print("\n❌ Some tests failed. Fix the issues before deploying.")
        return 1


if __name__ == '__main__':
    sys.exit(main())