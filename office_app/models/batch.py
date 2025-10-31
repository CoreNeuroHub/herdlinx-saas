from datetime import datetime
from office_app import db
from sqlalchemy import func

class Batch(db.Model):
    __tablename__ = 'batches'

    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), nullable=False)
    induction_date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(200))
    source_type = db.Column(db.String(10), nullable=True)  # 'hxb' for barn, 'hxe' for export
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    cattle = db.relationship('Cattle', backref='batch', lazy=True)
    
    @staticmethod
    def create_batch(batch_number, induction_date, source, notes=None, source_type=None):
        """Create a new batch"""
        batch = Batch(
            batch_number=batch_number,
            induction_date=induction_date,
            source=source or '',
            source_type=source_type,
            notes=notes or '',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(batch)
        db.session.commit()
        return batch.id
    
    @staticmethod
    def parse_payload(payload):
        """
        Parse batch payload in format: hxb:batchnumber:LF:UHF or hxe:batchnumber:LF:UHF

        Args:
            payload (str): Payload string in format source_type:batch_number:lf_tag:uhf_tag

        Returns:
            dict: Parsed data with keys: source_type, batch_number, lf_tag, uhf_tag
            None: If payload format is invalid
        """
        try:
            parts = payload.strip().split(':')
            if len(parts) != 4:
                return None

            source_type, batch_number, lf_tag, uhf_tag = parts

            # Validate source type
            if source_type not in ['hxb', 'hxe']:
                return None

            # Validate that batch_number, lf_tag, and uhf_tag are not empty
            if not batch_number or not lf_tag or not uhf_tag:
                return None

            return {
                'source_type': source_type,
                'batch_number': batch_number.strip(),
                'lf_tag': lf_tag.strip(),
                'uhf_tag': uhf_tag.strip()
            }
        except (ValueError, AttributeError):
            return None

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
            'source_type': self.source_type,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'cattle_count': Batch.get_cattle_count(self.id)
        }

