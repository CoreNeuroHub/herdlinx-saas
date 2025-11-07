import os
from dotenv import load_dotenv

load_dotenv()

# Get MongoDB URI at module level to avoid issues during class definition
def _get_mongodb_uri():
    """Get MongoDB URI with proper error handling"""
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
    return _mongodb_uri

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MongoDB settings
    # In production (Vercel), MONGODB_URI must be set as environment variable
    # Get URI at class definition time, but handle errors gracefully
    try:
        MONGODB_URI = _get_mongodb_uri()
    except ValueError:
        # If MONGODB_URI is missing in production, we'll raise later when actually needed
        # For now, set to None to allow class definition to complete
        # This prevents import errors that could confuse Vercel's handler detection
        MONGODB_URI = None
    
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'herdlinx_saas'
    
    # Session settings
    # Flask uses secure cookies by default, which work perfectly in serverless environments
    # SESSION_TYPE is only used if flask-session is explicitly configured
    SESSION_PERMANENT = False
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

