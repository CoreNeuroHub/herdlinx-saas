from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from config import Config
import certifi

# Initialize MongoDB connection
# PyMongo connects lazily, so this won't fail even if MongoDB is temporarily unavailable
try:
    # Configure MongoDB client with appropriate settings
    # For mongodb+srv:// connections, TLS is automatically enabled
    # Ensure connection string includes proper query parameters (tls=true, retryWrites=true, etc.)
    client_options = {
        'serverSelectionTimeoutMS': 30000,  # Increased timeout for serverless
        'connectTimeoutMS': 30000,  # Increased timeout for serverless
        'socketTimeoutMS': 30000,  # Increased timeout for serverless
        'retryWrites': True,
        'retryReads': True,
    }
    
    # For serverless environments (like Vercel), explicitly use certifi's CA bundle
    # This ensures SSL certificates are properly validated
    if Config.MONGODB_URI.startswith('mongodb+srv://'):
        # For mongodb+srv:// connections, use certifi's CA bundle for SSL
        # This is critical for serverless environments that may not have system certificates
        client_options['tlsCAFile'] = certifi.where()
    else:
        # For regular mongodb:// connections, check if TLS is needed
        # (This is typically for local connections without TLS)
        pass
    
    mongodb_client = MongoClient(Config.MONGODB_URI, **client_options)
    db = mongodb_client[Config.MONGODB_DB]
except Exception as e:
    # If connection string is invalid, this will fail
    # Log error but allow app to initialize (will fail on first DB operation)
    print(f"Warning: MongoDB client creation error: {e}")
    import sys
    import traceback
    traceback.print_exc()
    # Re-raise to fail fast during deployment
    raise

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Add custom Jinja filters
    @app.template_filter('strftime')
    def strftime_filter(value, fmt='%Y-%m-%d'):
        """Convert datetime or date string to formatted string"""
        if value is None:
            return ''
        # If it's already a string, try to parse and format it
        if isinstance(value, str):
            try:
                # Try parsing as datetime
                if 'T' in value or ' ' in value:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    value = datetime.strptime(value, '%Y-%m-%d')
                return value.strftime(fmt)
            except (ValueError, AttributeError):
                return value  # Return original if parsing fails
        # If it's a datetime object, format it
        elif hasattr(value, 'strftime'):
            return value.strftime(fmt)
        return value
    
    # Initialize database with error handling
    try:
        from .models import init_db, create_default_admin
        init_db()
        create_default_admin()
    except Exception as e:
        print(f"Warning: Database initialization error: {e}")
        # App will still work, but database operations may fail
    
    # Register blueprints
    try:
        from .routes.auth_routes import auth_bp
        from .routes.top_level_routes import top_level_bp
        from .routes.feedlot_routes import feedlot_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(top_level_bp)
        app.register_blueprint(feedlot_bp)
    except Exception as e:
        print(f"Error registering blueprints: {e}")
        raise
    
    return app

