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
    """Create default admin user if it doesn't exist"""
    try:
        # Check if default admin user already exists
        existing_user = User.find_by_username('sft')
        
        if not existing_user:
            # Create the default admin user
            User.create_user(
                username='sft',
                email='sft@herdlinx.com',
                password='sftcattle',
                user_type='super_owner',
                feedlot_id=None
            )
            print("Default admin user 'sft' created successfully")
        else:
            print("Default admin user 'sft' already exists")
    except Exception as e:
        print(f"Error creating default admin user: {e}")

