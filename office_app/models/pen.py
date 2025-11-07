from datetime import datetime
from office_app import db
from sqlalchemy import func

class Pen(db.Model):
    __tablename__ = 'pens'
    
    id = db.Column(db.Integer, primary_key=True)
    pen_number = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    cattle = db.relationship('Cattle', backref='pen', lazy=True, foreign_keys='Cattle.pen_id')
    
    @staticmethod
    def create_pen(pen_number, capacity, description=None):
        """Create a new pen"""
        pen = Pen(
            pen_number=pen_number,
            capacity=capacity,
            description=description or '',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(pen)
        db.session.commit()
        return pen.id
    
    @staticmethod
    def find_by_id(pen_id):
        """Find pen by ID"""
        return Pen.query.get(pen_id)
    
    @staticmethod
    def find_all():
        """Find all pens"""
        return Pen.query.order_by(Pen.pen_number).all()
    
    @staticmethod
    def update_pen(pen_id, update_data):
        """Update pen information"""
        pen = Pen.query.get(pen_id)
        if pen:
            for key, value in update_data.items():
                setattr(pen, key, value)
            pen.updated_at = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def delete_pen(pen_id):
        """Delete a pen"""
        pen = Pen.query.get(pen_id)
        if pen:
            db.session.delete(pen)
            db.session.commit()
    
    @staticmethod
    def get_current_cattle_count(pen_id):
        """Get current number of cattle in a pen"""
        from office_app.models.cattle import Cattle
        return db.session.query(func.count(Cattle.id)).filter(
            Cattle.pen_id == pen_id,
            Cattle.status == 'active'
        ).scalar() or 0
    
    @staticmethod
    def is_capacity_available(pen_id, additional_cattle=1):
        """Check if pen has available capacity"""
        pen = Pen.query.get(pen_id)
        if not pen:
            return False
        
        current_count = Pen.get_current_cattle_count(pen_id)
        return (current_count + additional_cattle) <= pen.capacity
    
    def to_dict(self):
        """Convert pen to dictionary"""
        return {
            'id': self.id,
            'pen_number': self.pen_number,
            'capacity': self.capacity,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'current_count': Pen.get_current_cattle_count(self.id)
        }
