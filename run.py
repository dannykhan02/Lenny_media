import os
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("📸 LENNY MEDIA PHOTOGRAPHY API")
    print("=" * 60)
    print(f"Environment: {app.config.get('FLASK_ENV', 'development')}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    
    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
    
    # Start the server
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Server starting on http://localhost:{port}")
    print("📡 Available endpoints:")
    print(f"   - Home: http://localhost:{port}/")
    print(f"   - Health: http://localhost:{port}/health")
    print(f"   - Auth: http://localhost:{port}/api/auth/*")
    print("=" * 60)
    
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=port)