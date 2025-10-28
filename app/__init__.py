from flask import Flask
from pymongo import MongoClient
from config import Config

# Initialize MongoDB connection
mongodb_client = MongoClient(Config.MONGODB_URI)
db = mongodb_client[Config.MONGODB_DB]

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
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

