from datetime import datetime
from bson import ObjectId
from app import db
import bcrypt

class User:
    @staticmethod
    def create_user(username, email, password, user_type, feedlot_id=None, feedlot_ids=None):
        """Create a new user
        
        Args:
            username: Username for the user
            email: Email address
            password: Plain text password (will be hashed)
            user_type: 'super_owner', 'super_admin', 'business_owner', 'business_admin', or 'user'
            feedlot_id: Single feedlot ID (for 'user' type)
            feedlot_ids: List of feedlot IDs (for 'business_admin' or 'business_owner' users)
        """
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': hashed_password,
            'user_type': user_type,  # 'super_owner', 'super_admin', 'business_owner', 'business_admin', or 'user'
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        
        # Handle feedlot assignments based on user type
        if user_type in ['business_admin', 'business_owner']:
            # business_admin and business_owner can have multiple feedlots
            if feedlot_ids:
                user_data['feedlot_ids'] = [ObjectId(fid) for fid in feedlot_ids]
            else:
                user_data['feedlot_ids'] = []
        elif user_type == 'user':
            # Regular users have a single feedlot
            user_data['feedlot_id'] = ObjectId(feedlot_id) if feedlot_id else None
        
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
        """Find all users for a specific feedlot (includes users, business admins, and business owners)"""
        feedlot_obj_id = ObjectId(feedlot_id)
        # Find users who have this feedlot assigned (either as single feedlot_id or in feedlot_ids array)
        return list(db.users.find({
            '$or': [
                {'feedlot_id': feedlot_obj_id},
                {'feedlot_ids': feedlot_obj_id}
            ]
        }))
    
    @staticmethod
    def find_business_admins():
        """Find all business admin users"""
        return list(db.users.find({'user_type': 'business_admin'}))
    
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

