"""
Vercel serverless function entry point for Flask application.
This file is required for Vercel to properly deploy the Flask app as a serverless function.
"""

import sys
import traceback
from flask import Flask, jsonify

# Initialize app as None first to avoid reference errors
app = None
handler = None

try:
    from app import create_app
    
    # Create Flask app instance
    app = create_app()
    
    # Ensure app is a Flask instance for Vercel's handler detection
    if not isinstance(app, Flask):
        raise TypeError(f"Expected Flask instance, got {type(app)}")
    
    # Initialize database on first request instead of at import time
    # This prevents connection failures during cold starts
    # Flask 3.0+ removed before_first_request, so we use before_request with a flag
    @app.before_request
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
                print(f"Warning: Database initialization error: {e}")
                traceback.print_exc()
    
    # Set handler to app for Vercel
    handler = app
    
except Exception as e:
    # If app creation fails, create a minimal error handler
    print(f"ERROR: Failed to create Flask app: {e}")
    traceback.print_exc()
    
    # Create fallback Flask app
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'type': type(e).__name__
        }), 500
    
    handler = app

# Ensure handler is exported and is a Flask instance
# Vercel Python runtime expects either 'app' or 'handler' to be a WSGI application
if handler is None:
    raise RuntimeError("Handler was not initialized")

# Export both app and handler for maximum compatibility
# Some Vercel configurations look for 'app', others for 'handler'
__all__ = ['app', 'handler']

