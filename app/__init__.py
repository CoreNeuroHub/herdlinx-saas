from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from config import Config

# Initialize MongoDB connection lazily
# Don't create connection at module level for serverless - defer to first use
_mongodb_client = None
_db_instance = None

def get_db():
    """Get MongoDB database connection, creating it if necessary"""
    global _mongodb_client, _db_instance
    
    # Return cached connection if available
    if _db_instance is not None:
        return _db_instance
    
    try:
        # Configure MongoDB client with appropriate settings for serverless environments
        client_options = {
            'serverSelectionTimeoutMS': 30000,  # Increased timeout for serverless
            'connectTimeoutMS': 30000,  # Increased timeout for serverless
            'socketTimeoutMS': 30000,  # Increased timeout for serverless
            'retryWrites': True,
            'retryReads': True,
        }
        
        # For serverless environments (like Vercel), configure TLS/SSL properly
        if Config.MONGODB_URI.startswith('mongodb+srv://'):
            # For mongodb+srv://, TLS is automatically enabled by PyMongo
            # In Vercel's serverless environment, we should use system certificates
            # Don't set tlsCAFile explicitly - let PyMongo use system defaults
            # This works better in serverless environments where certifi paths may not be accessible
            client_options['tls'] = True
            client_options['tlsAllowInvalidCertificates'] = False
            client_options['tlsAllowInvalidHostnames'] = False
            # Don't set tlsCAFile - let Python's ssl module use system default CA bundle
            print("Using system default CA certificates for TLS")
        
        # Create client - connection is lazy, won't connect until first use
        print(f"Creating MongoDB client with URI: {Config.MONGODB_URI[:20]}...")  # Debug
        _mongodb_client = MongoClient(Config.MONGODB_URI, **client_options)
        _db_instance = _mongodb_client[Config.MONGODB_DB]
        print("MongoDB client created successfully")
        return _db_instance
    except Exception as e:
        print(f"Error creating MongoDB client: {e}")
        import traceback
        traceback.print_exc()
        raise

# Initialize db variable to be a lazy proxy
class LazyDB:
    """Lazy proxy for database that connects on first access"""
    def __getattr__(self, name):
        # Get the actual database connection
        actual_db = get_db()
        return getattr(actual_db, name)
    
    def __getitem__(self, key):
        """Support dictionary-style access like db['users']"""
        actual_db = get_db()
        return actual_db[key]

db = LazyDB()

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
    
    # Database initialization is deferred until first use
    # This prevents connection failures during cold starts in serverless environments
    # The init_db() and create_default_admin() will be called on first database access
    
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

