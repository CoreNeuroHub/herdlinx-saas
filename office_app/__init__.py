from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    # Import config using relative import
    from .config import Config
    
    app = Flask(__name__, 
                template_folder='templates', 
                static_folder='static',
                instance_relative_config=True)
    app.config.from_object(Config)
    
    # Initialize SQLAlchemy with app
    db.init_app(app)
    
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
    
    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.office_routes import office_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(office_bp)
    
    # Initialize database tables
    with app.app_context():
        db.create_all()
        # Create default admin user if it doesn't exist
        from .models.user import User
        if not User.query.filter_by(username='admin').first():
            User.create_admin('admin', 'admin@office.local', 'admin')

    # Initialize background payload processing worker (only on Pi backend)
    if app.config.get('IS_PI_BACKEND', False):
        from .utils.background_worker import init_background_worker
        init_background_worker(app, interval=5)  # Process payloads every 5 seconds

    # Initialize database sync service and WebSocket (only on server UI)
    if app.config.get('IS_SERVER_UI', False):
        from .sync_service import create_sync_service_from_config
        from .websocket_client import create_websocket_client_from_config

        try:
            # Start database sync service (syncs from Pi every 10 seconds)
            create_sync_service_from_config(app)
            app.logger.info("Database sync service initialized")

            # Keep WebSocket for real-time updates
            create_websocket_client_from_config(app)
            app.logger.info("WebSocket client initialized successfully")
        except Exception as e:
            app.logger.warning(f"Failed to initialize remote services: {str(e)}")

    return app
