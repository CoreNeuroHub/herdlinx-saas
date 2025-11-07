"""
Vercel serverless function entry point for Flask application.
This file is required for Vercel to properly deploy the Flask app as a serverless function.
"""

# Import Flask first to ensure it's available
from flask import Flask, jsonify

# Create Flask app instance - Vercel expects 'app' to be a WSGI application
# Initialize as None first, then create
app = None

try:
    # Import create_app after Flask is imported
    from app import create_app
    
    # Create Flask app instance
    app = create_app()
    
    # Verify app is a Flask instance
    if not isinstance(app, Flask):
        raise TypeError(f"create_app() returned {type(app)}, expected Flask instance")
    
    # Initialize database on first request instead of at import time
    # This prevents connection failures during cold starts
    # Flask 3.0+ removed before_first_request, so we use before_request with a flag
    def initialize_database_once():
        if not hasattr(app, '_db_initialized'):
            try:
                from app.models import init_db, create_default_admin
                # Ensure DB connection is established
                from app import get_db
                get_db()
                init_db()
                create_default_admin()
                app._db_initialized = True
            except Exception as e:
                import traceback
                print(f"Warning: Database initialization error: {e}")
                traceback.print_exc()
    
    # Register the before_request handler
    app.before_request(initialize_database_once)
    
except Exception as e:
    # If app creation fails, create a minimal error handler
    import traceback
    print(f"ERROR: Failed to create Flask app: {e}")
    traceback.print_exc()
    
    # Create fallback Flask app - this must be a clean Flask instance
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'type': type(e).__name__
        }), 500

# Final verification - ensure app is a Flask instance
if app is None or not isinstance(app, Flask):
    raise RuntimeError(f"Failed to initialize Flask app. Got: {type(app)}")

# Explicitly define what should be exported from this module
# This ensures Vercel only sees the 'app' variable and doesn't get confused
# by other imports or module-level objects
__all__ = ['app']

