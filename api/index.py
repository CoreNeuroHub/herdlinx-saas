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
    
except Exception as e:
    # If app creation fails, create a minimal error handler
    print(f"ERROR: Failed to create Flask app: {e}")
    traceback.print_exc()
    
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_handler(path):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'type': type(e).__name__
        }), 500

# Export the app for Vercel
# Vercel expects the Flask app instance directly
handler = app

