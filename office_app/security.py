"""Security utilities for remote API access

Handles API key validation, JWT token generation, and SSL/TLS configuration.
"""
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os

# API Configuration
API_KEY_HEADER = 'X-API-Key'
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

class APIKeyManager:
    """Manage API keys for secure remote access"""

    @staticmethod
    def generate_api_key(prefix='hxb'):
        """Generate a secure API key"""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{''.join([c for c in random_part if c.isalnum()])[:40]}"

    @staticmethod
    def hash_api_key(api_key):
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def validate_api_key(api_key, stored_hash):
        """Validate API key against stored hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == stored_hash


class TokenManager:
    """Manage JWT tokens for authenticated API access"""

    @staticmethod
    def generate_token(user_id, api_key_id=None, expires_in_hours=JWT_EXPIRATION_HOURS):
        """Generate a JWT token"""
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'api_key_id': api_key_id,
            'iat': now,
            'exp': now + timedelta(hours=expires_in_hours)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def is_token_expired(payload):
        """Check if token is expired"""
        if not payload:
            return True
        exp = payload.get('exp')
        if exp:
            return datetime.utcfromtimestamp(exp) < datetime.utcnow()
        return False


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get(API_KEY_HEADER)

        if not api_key:
            return jsonify({
                'success': False,
                'message': f'Missing API key. Use header: {API_KEY_HEADER}'
            }), 401

        # In production, validate against stored hash
        # For now, simple check (implement proper validation with database)
        if not _validate_api_key_from_env(api_key):
            return jsonify({
                'success': False,
                'message': 'Invalid API key'
            }), 401

        return f(*args, **kwargs)

    return decorated_function


def require_auth(f):
    """Decorator to require API key or valid JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key first
        api_key = request.headers.get(API_KEY_HEADER)
        if api_key and _validate_api_key_from_env(api_key):
            return f(*args, **kwargs)

        # Check for JWT token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = TokenManager.verify_token(token)

            if payload and not TokenManager.is_token_expired(payload):
                return f(*args, **kwargs)

        return jsonify({
            'success': False,
            'message': 'Unauthorized. Provide API key or valid JWT token'
        }), 401

    return decorated_function


def _validate_api_key_from_env(api_key):
    """Validate API key against environment variable"""
    valid_key = os.environ.get('PI_API_KEY')
    if not valid_key:
        # If no env key set, accept any key in development
        return True
    return api_key == valid_key


class SSLConfig:
    """Manage SSL/TLS certificate configuration"""

    @staticmethod
    def get_cert_paths():
        """Get paths to SSL certificate and key"""
        cert_dir = os.path.join(os.path.dirname(__file__), 'certs')
        cert_file = os.path.join(cert_dir, 'server.crt')
        key_file = os.path.join(cert_dir, 'server.key')
        return cert_file, key_file

    @staticmethod
    def has_certificates():
        """Check if SSL certificates exist"""
        cert_file, key_file = SSLConfig.get_cert_paths()
        return os.path.exists(cert_file) and os.path.exists(key_file)

    @staticmethod
    def get_ssl_context():
        """Get SSL context for Flask app"""
        try:
            import ssl
            cert_file, key_file = SSLConfig.get_cert_paths()

            if not SSLConfig.has_certificates():
                return None

            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_file, key_file)
            return context
        except Exception as e:
            print(f"Error loading SSL context: {e}")
            return None
