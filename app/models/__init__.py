from app import db
from .user import User

def init_db():
    """Initialize master database collections (feedlots and users only)
    
    Note: Feedlot-specific databases (pens, batches, cattle) are initialized
    when feedlots are created via Feedlot.initialize_feedlot_database()
    """
    try:
        # Create indexes for master database collections only
        db.users.create_index('username', unique=True)
        db.users.create_index('email', unique=True)
        db.users.create_index('feedlot_id')
        
        # Feedlots collection indexes
        db.feedlots.create_index('feedlot_code', unique=True)
        db.feedlots.create_index('name')
        
        print("Master database initialized successfully")
    except Exception as e:
        print(f"Error initializing master database indexes: {e}")
        # Don't raise - allow app to continue

def create_default_admin():
    """Create default admin users if they don't exist"""
    try:
        # Create default users list
        default_users = [
            {
                'username': 'sft',
                'email': 'sft@herdlinx.com',
                'password': 'sftcattle',
                'user_type': 'super_admin'
            },
            {
                'username': 'brad',
                'email': 'brad@herdlinx.ca',
                'password': 'brad123',
                'user_type': 'super_owner'
            }
        ]
        
        for user_data in default_users:
            # Check if user already exists
            existing_user = User.find_by_username(user_data['username'])
            
            if not existing_user:
                # Create the default user
                User.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    user_type=user_data['user_type'],
                    feedlot_id=None
                )
                print(f"Default user '{user_data['username']}' ({user_data['user_type']}) created successfully")
            else:
                print(f"Default user '{user_data['username']}' already exists")
    except Exception as e:
        print(f"Error creating default admin users: {e}")

