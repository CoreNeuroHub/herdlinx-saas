"""
Vercel serverless function entry point for Flask application.
This file is required for Vercel to properly deploy the Flask app as a serverless function.
"""

from app import create_app

# Create Flask app instance
app = create_app()

# Export the app for Vercel
# Vercel expects the handler to be available
handler = app

