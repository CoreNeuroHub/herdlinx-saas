from datetime import datetime
from office_app import db
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    @staticmethod
    def create_user(username, email, password, is_admin=False):
        """Create a new user"""
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            is_admin=is_admin,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        return user.id
    
    @staticmethod
    def create_admin(username, email, password):
        """Create an admin user"""
        return User.create_user(username, email, password, is_admin=True)
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify user password"""
        if isinstance(stored_password, str):
            stored_password = stored_password.encode('utf-8')
        if isinstance(provided_password, str):
            provided_password = provided_password.encode('utf-8')
        return bcrypt.checkpw(provided_password, stored_password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

