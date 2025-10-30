from datetime import datetime
from office_app import db
from sqlalchemy import func

class Batch(db.Model):
    __tablename__ = 'batches'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), nullable=False)
    induction_date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    cattle = db.relationship('Cattle', backref='batch', lazy=True)
    
    @staticmethod
    def create_batch(batch_number, induction_date, source, notes=None):
        """Create a new batch"""
        batch = Batch(
            batch_number=batch_number,
            induction_date=induction_date,
            source=source or '',
            notes=notes or '',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(batch)
        db.session.commit()
        return batch.id
    
    @staticmethod
    def find_by_id(batch_id):
        """Find batch by ID"""
        return Batch.query.get(batch_id)
    
    @staticmethod
    def find_all():
        """Find all batches"""
        return Batch.query.order_by(Batch.induction_date.desc()).all()
    
    @staticmethod
    def update_batch(batch_id, update_data):
        """Update batch information"""
        batch = Batch.query.get(batch_id)
        if batch:
            for key, value in update_data.items():
                setattr(batch, key, value)
            batch.updated_at = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def delete_batch(batch_id):
        """Delete a batch"""
        batch = Batch.query.get(batch_id)
        if batch:
            db.session.delete(batch)
            db.session.commit()
    
    @staticmethod
    def get_cattle_count(batch_id):
        """Get number of cattle in a batch"""
        from office_app.models.cattle import Cattle
        return db.session.query(func.count(Cattle.id)).filter(
            Cattle.batch_id == batch_id
        ).scalar() or 0
    
    def to_dict(self):
        """Convert batch to dictionary"""
        return {
            'id': self.id,
            'batch_number': self.batch_number,
            'induction_date': self.induction_date,
            'source': self.source,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'cattle_count': Batch.get_cattle_count(self.id)
        }

