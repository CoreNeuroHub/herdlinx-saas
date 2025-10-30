import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MongoDB settings
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'herdlinx_saas'
    
    # Session settings
    # Flask uses secure cookies by default, which work perfectly in serverless environments
    # SESSION_TYPE is only used if flask-session is explicitly configured
    SESSION_PERMANENT = False
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

