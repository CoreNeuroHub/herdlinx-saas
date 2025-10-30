import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MongoDB settings
    # In production (Vercel), MONGODB_URI must be set as environment variable
    _mongodb_uri = os.environ.get('MONGODB_URI')
    if not _mongodb_uri:
        # Check if we're in a production environment (Vercel sets VERCEL env var)
        if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
            raise ValueError(
                "MONGODB_URI environment variable is required but not set. "
                "Please set it in your Vercel project settings."
            )
        # Fallback for local development
        _mongodb_uri = 'mongodb://localhost:27017/'
    MONGODB_URI = _mongodb_uri
    
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'herdlinx_saas'
    
    # Session settings
    # Flask uses secure cookies by default, which work perfectly in serverless environments
    # SESSION_TYPE is only used if flask-session is explicitly configured
    SESSION_PERMANENT = False
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

