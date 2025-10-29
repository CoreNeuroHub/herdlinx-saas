from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from config import Config

# Initialize MongoDB connection
mongodb_client = MongoClient(Config.MONGODB_URI)
db = mongodb_client[Config.MONGODB_DB]

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
    
    # Initialize database
    from .models import init_db, create_default_admin
    init_db()
    create_default_admin()
    
    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.top_level_routes import top_level_bp
    from .routes.feedlot_routes import feedlot_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(top_level_bp)
    app.register_blueprint(feedlot_bp)
    
    return app

