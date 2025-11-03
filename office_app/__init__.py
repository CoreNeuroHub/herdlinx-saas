from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    # Import config using relative import
    from .config import Config

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Initialize SQLAlchemy with app
    db.init_app(app)

    # Register blueprints
    from .remote_api import remote_api_bp, init_socketio, register_socketio_handlers
    from .sync_api import sync_api_bp

    app.register_blueprint(remote_api_bp)
    app.register_blueprint(sync_api_bp)

    # Initialize WebSocket for real-time updates
    socketio = init_socketio(app)
    register_socketio_handlers(socketio)

    # Initialize database tables
    with app.app_context():
        db.create_all()
        # Create default admin user if it doesn't exist
        from .models.user import User
        if not User.query.filter_by(username='admin').first():
            User.create_admin('admin', 'admin@office.local', 'admin')

    # Initialize background payload processing worker
    from .utils.background_worker import init_background_worker
    init_background_worker(app, interval=5)  # Process payloads every 5 seconds

    return app
