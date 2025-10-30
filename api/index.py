"""
Vercel serverless function entry point for Flask application.
This file is required for Vercel to properly deploy the Flask app as a serverless function.
"""

import sys
import traceback

try:
    from app import create_app
    
    # Create Flask app instance
    app = create_app()
    
    # Export the app for Vercel
    # Vercel expects the handler to be available
    handler = app
    
except Exception as e:
    # If app creation fails, create a minimal error handler
    print(f"ERROR: Failed to create Flask app: {e}")
    traceback.print_exc()
    
    from flask import Flask, jsonify
    
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'type': type(e).__name__
        }), 500
    
    handler = error_app

