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
    
    # Validate MONGODB_URI is set (may be None if Config failed to load it during import)
    if Config.MONGODB_URI is None:
        raise ValueError(
            "MONGODB_URI environment variable is required but not set. "
            "Please set it in your Vercel project settings."
        )
    
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
    def strftime_filter(value, fmt='%B %d, %Y'):
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
        from .routes.api_routes import api_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(top_level_bp)
        app.register_blueprint(feedlot_bp)
        app.register_blueprint(api_bp, url_prefix='/api')
    except Exception as e:
        print(f"Error registering blueprints: {e}")
        raise
    
    # Add context processor for navigation
    @app.context_processor
    def inject_navigation_context():
        """Inject navigation context into all templates"""
        from flask import request, session, url_for
        from .models.feedlot import Feedlot
        from .utils.breadcrumbs import generate_breadcrumbs
        from bson import ObjectId
        import re
        
        nav_context = {
            'current_feedlot': None,
            'current_feedlot_id': None,
            'show_top_level_nav': False,
            'show_feedlot_nav': False,
            'user_type': session.get('user_type'),
            'breadcrumbs': [],
        }
        
        # Check if user is logged in
        if 'user_id' not in session:
            return nav_context
        
        user_type = session.get('user_type')
        
        # Determine if we're in a feedlot context by checking URL pattern
        path = request.path
        feedlot_pattern = r'/feedlot/([^/]+)'
        match = re.search(feedlot_pattern, path)
        
        current_feedlot = None
        if match:
            feedlot_id = match.group(1)
            nav_context['current_feedlot_id'] = feedlot_id
            
            # Fetch feedlot data
            try:
                feedlot = Feedlot.find_by_id(feedlot_id)
                if feedlot:
                    # Load branding data
                    branding = Feedlot.get_branding(feedlot_id)
                    if branding:
                        feedlot['branding'] = branding
                    nav_context['current_feedlot'] = feedlot
                    nav_context['show_feedlot_nav'] = True
                    current_feedlot = feedlot
            except Exception:
                # If feedlot not found or error, don't show feedlot nav
                pass
        
        # Determine which navigation sections to show
        # Top-level users (super_owner, super_admin) always see top-level nav
        if user_type in ['super_owner', 'super_admin']:
            nav_context['show_top_level_nav'] = True
        # Business owner/admin users also see top-level nav (dashboard, feedlot hub, settings)
        elif user_type in ['business_owner', 'business_admin']:
            nav_context['show_top_level_nav'] = True
        
        # Generate breadcrumbs
        try:
            nav_context['breadcrumbs'] = generate_breadcrumbs(current_feedlot=current_feedlot, request_obj=request)
        except Exception as e:
            # If breadcrumb generation fails, just use empty list
            nav_context['breadcrumbs'] = []
        
        return nav_context
    
    return app

