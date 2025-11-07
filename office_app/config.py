import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('OFFICE_SECRET_KEY') or 'office-dev-secret-key-change-in-production'
    
    # SQLite database settings
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('OFFICE_DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "office_app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

