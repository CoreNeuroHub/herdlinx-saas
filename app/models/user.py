from datetime import datetime
from bson import ObjectId
from app import db
import bcrypt

class User:
    @staticmethod
    def create_user(username, email, password, user_type, feedlot_id=None):
        """Create a new user"""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': hashed_password,
            'user_type': user_type,  # 'top_level' or 'feedlot'
            'feedlot_id': ObjectId(feedlot_id) if feedlot_id else None,
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        
        result = db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        return db.users.find_one({'username': username})
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return db.users.find_one({'email': email})
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        return db.users.find_one({'_id': ObjectId(user_id)})
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify user password"""
        if isinstance(stored_password, str):
            stored_password = stored_password.encode('utf-8')
        if isinstance(provided_password, str):
            provided_password = provided_password.encode('utf-8')
        return bcrypt.checkpw(provided_password, stored_password)
    
    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all users for a specific feedlot"""
        return list(db.users.find({'feedlot_id': ObjectId(feedlot_id)}))
    
    @staticmethod
    def update_user(user_id, update_data):
        """Update user information"""
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def deactivate_user(user_id):
        """Deactivate a user"""
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_active': False}}
        )

