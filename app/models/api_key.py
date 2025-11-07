from datetime import datetime
from bson import ObjectId
from app import db
import secrets
import hashlib

class APIKey:
    @staticmethod
    def generate_key():
        """Generate a secure random API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_key(api_key):
        """Hash an API key using SHA-256"""
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create_api_key(feedlot_id, description=None):
        """Create a new API key for a feedlot
        
        Args:
            feedlot_id: Feedlot ID to associate the key with
            description: Optional description for the key
        
        Returns:
            tuple: (api_key_string, api_key_document_id)
            The api_key_string should be returned to the user immediately as it won't be stored in plain text
        """
        # Generate a new API key
        api_key_string = APIKey.generate_key()
        api_key_hash = APIKey.hash_key(api_key_string)
        
        api_key_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'api_key_hash': api_key_hash,
            'description': description or '',
            'created_at': datetime.utcnow(),
            'last_used_at': None,
            'is_active': True
        }
        
        result = db.api_keys.insert_one(api_key_data)
        return api_key_string, str(result.inserted_id)
    
    @staticmethod
    def find_by_key(api_key):
        """Find API key by the actual key value (validates hash)
        
        Args:
            api_key: The plain text API key
        
        Returns:
            API key document if found and active, None otherwise
        """
        if not api_key:
            return None
        
        api_key_hash = APIKey.hash_key(api_key)
        key_doc = db.api_keys.find_one({
            'api_key_hash': api_key_hash,
            'is_active': True
        })
        
        return key_doc
    
    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all API keys for a feedlot"""
        return list(db.api_keys.find({
            'feedlot_id': ObjectId(feedlot_id)
        }).sort('created_at', -1))
    
    @staticmethod
    def find_by_id(key_id):
        """Find API key by ID"""
        return db.api_keys.find_one({'_id': ObjectId(key_id)})
    
    @staticmethod
    def update_last_used(api_key):
        """Update the last_used_at timestamp for an API key"""
        api_key_hash = APIKey.hash_key(api_key)
        db.api_keys.update_one(
            {'api_key_hash': api_key_hash},
            {'$set': {'last_used_at': datetime.utcnow()}}
        )
    
    @staticmethod
    def deactivate_key(key_id):
        """Deactivate an API key"""
        db.api_keys.update_one(
            {'_id': ObjectId(key_id)},
            {'$set': {'is_active': False}}
        )
    
    @staticmethod
    def activate_key(key_id):
        """Activate an API key"""
        db.api_keys.update_one(
            {'_id': ObjectId(key_id)},
            {'$set': {'is_active': True}}
        )
    
    @staticmethod
    def delete_key(key_id):
        """Delete an API key"""
        db.api_keys.delete_one({'_id': ObjectId(key_id)})
    
    @staticmethod
    def validate_key(api_key):
        """Validate an API key and return the associated feedlot_id if valid
        
        Args:
            api_key: The plain text API key
        
        Returns:
            tuple: (is_valid, feedlot_id)
            is_valid: Boolean indicating if key is valid
            feedlot_id: Feedlot ID if valid, None otherwise
        """
        key_doc = APIKey.find_by_key(api_key)
        if key_doc:
            # Update last used timestamp
            APIKey.update_last_used(api_key)
            return True, str(key_doc['feedlot_id'])
        return False, None

