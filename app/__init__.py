from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from config import Config
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Initialize MongoDB connection lazily
# Don't create connection at module level for serverless - defer to first use
_mongodb_client = None
_db_instance = None
_feedlot_db_cache = {}  # Cache for feedlot-specific databases

def _clean_mongodb_uri(uri):
    """Clean MongoDB URI by removing SSL/TLS parameters for mongodb+srv:// connections
    
    For mongodb+srv://, PyMongo automatically handles TLS, so any ssl= or tls= 
    parameters in the URI can cause warnings. This function removes them.
    """
    if not uri.startswith('mongodb+srv://'):
        return uri
    
    # Parse the URI
    parsed = urlparse(uri)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    
    # Remove SSL/TLS related parameters that can cause warnings
    params_to_remove = ['ssl', 'tls', 'ssl=true', 'ssl=false', 'tls=true', 'tls=false']
    cleaned_params = {}
    for key, value_list in query_params.items():
        key_lower = key.lower()
        # Skip SSL/TLS parameters
        if key_lower not in ['ssl', 'tls']:
            cleaned_params[key] = value_list
    
    # Reconstruct the URI
    cleaned_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
    cleaned_uri = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        cleaned_query,
        parsed.fragment
    ))
    
    return cleaned_uri

def _get_mongodb_client():
    """Get or create MongoDB client"""
    global _mongodb_client
    
    if _mongodb_client is not None:
        return _mongodb_client
    
    # Validate MONGODB_URI is set (may be None if Config failed to load it during import)
    if Config.MONGODB_URI is None:
        raise ValueError(
            "MONGODB_URI environment variable is required but not set. "
            "Please set it in your Vercel project settings."
        )
    
    try:
        # Clean the URI to remove problematic SSL/TLS parameters
        cleaned_uri = _clean_mongodb_uri(Config.MONGODB_URI)
        
        # Configure MongoDB client with appropriate settings for serverless environments
        client_options = {
            'serverSelectionTimeoutMS': 30000,  # Increased timeout for serverless
            'connectTimeoutMS': 30000,  # Increased timeout for serverless
            'socketTimeoutMS': 30000,  # Increased timeout for serverless
            'retryWrites': True,
            'retryReads': True,
        }
        
        # For serverless environments (like Vercel), configure TLS/SSL properly
        if cleaned_uri.startswith('mongodb+srv://'):
            # For mongodb+srv://, TLS is automatically enabled by PyMongo
            # Don't set tls options explicitly - let PyMongo handle it automatically
            # This prevents SSL parameter warnings and works better in serverless environments
            print("Using automatic TLS for mongodb+srv:// connection")
        else:
            # For non-SRV connections, configure TLS explicitly if needed
            # Only set TLS options if the URI doesn't already specify them
            # Don't enable TLS for localhost connections (local MongoDB typically doesn't use SSL)
            is_localhost = 'localhost' in cleaned_uri.lower() or '127.0.0.1' in cleaned_uri.lower()
            if not is_localhost and 'ssl=' not in cleaned_uri.lower() and 'tls=' not in cleaned_uri.lower():
                client_options['tls'] = True
                client_options['tlsAllowInvalidCertificates'] = False
                client_options['tlsAllowInvalidHostnames'] = False
                print("TLS enabled for remote MongoDB connection")
            elif is_localhost:
                print("TLS disabled for localhost MongoDB connection")
        
        # Create client - connection is lazy, won't connect until first use
        print(f"Creating MongoDB client with URI: {cleaned_uri[:20]}...")  # Debug
        _mongodb_client = MongoClient(cleaned_uri, **client_options)
        print("MongoDB client created successfully")
        return _mongodb_client
    except Exception as e:
        print(f"Error creating MongoDB client: {e}")
        import traceback
        traceback.print_exc()
        raise

def get_db():
    """Get master MongoDB database connection (for feedlots and users collections)"""
    global _db_instance
    
    # Return cached connection if available
    if _db_instance is not None:
        return _db_instance
    
    client = _get_mongodb_client()
    _db_instance = client[Config.MONGODB_DB]
    return _db_instance

def get_feedlot_db(feedlot_code):
    """Get feedlot-specific MongoDB database connection
    
    Args:
        feedlot_code: The feedlot code (will be normalized to lowercase)
    
    Returns:
        Database instance for the feedlot
    """
    global _feedlot_db_cache
    
    if not feedlot_code:
        raise ValueError("feedlot_code is required")
    
    # Normalize feedlot_code to lowercase for consistency
    normalized_code = feedlot_code.lower().strip()
    db_name = f"feedlot_{normalized_code}"
    
    # Return cached connection if available
    if db_name in _feedlot_db_cache:
        return _feedlot_db_cache[db_name]
    
    # Create new database connection
    client = _get_mongodb_client()
    feedlot_db = client[db_name]
    _feedlot_db_cache[db_name] = feedlot_db
    
    return feedlot_db

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
    
    # Initialize database on first request (Flask 3.0+ compatible)
    def initialize_database_once():
        if not hasattr(app, '_db_initialized'):
            # Set flag immediately to prevent retry attempts on subsequent requests
            # This ensures we fail fast if initialization fails
            app._db_initialized = False
            try:
                from .models import init_db, create_default_admin
                # Ensure DB connection is established
                get_db()
                init_db()
                create_default_admin()
                app._db_initialized = True
            except Exception as e:
                import traceback
                print(f"Error: Database initialization failed: {e}")
                traceback.print_exc()
                # Re-raise the exception to fail fast and prevent silent failures
                # This ensures the application doesn't continue with an uninitialized database
                raise
    
    # Register the before_request handler
    app.before_request(initialize_database_once)
    
    # Register blueprints
    try:
        from .routes.auth_routes import auth_bp
        from .routes.top_level_routes import top_level_bp
        from .routes.feedlot_routes import feedlot_bp
        # API routes are only served by scripts/run_api.py (port 5021)
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(top_level_bp)
        app.register_blueprint(feedlot_bp)
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
            'current_feedlot_code': None,
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
                    nav_context['current_feedlot_code'] = feedlot.get('feedlot_code')
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

