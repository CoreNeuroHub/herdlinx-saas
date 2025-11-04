from app import db
from .user import User

def init_db():
    """Initialize database collections"""
    try:
        # Create indexes
        db.users.create_index('username', unique=True)
        db.users.create_index('email', unique=True)
        db.users.create_index('feedlot_id')
        
        db.pens.create_index('feedlot_id')
        db.pens.create_index([('feedlot_id', 1), ('pen_number', 1)], unique=True)
        
        db.batches.create_index('feedlot_id')
        db.batches.create_index([('feedlot_id', 1), ('batch_number', 1)], unique=True)
        
        db.cattle.create_index('feedlot_id')
        db.cattle.create_index('batch_id')
        db.cattle.create_index('pen_id')
        db.cattle.create_index([('feedlot_id', 1), ('cattle_id', 1)], unique=True)
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database indexes: {e}")
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

