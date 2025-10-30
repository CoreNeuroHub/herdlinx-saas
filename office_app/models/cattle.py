from datetime import datetime
from office_app import db
from sqlalchemy import JSON

class WeightRecord(db.Model):
    __tablename__ = 'weight_records'
    
    id = db.Column(db.Integer, primary_key=True)
    cattle_id = db.Column(db.Integer, db.ForeignKey('cattle.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    recorded_by = db.Column(db.String(100), default='system')

class PairHistory(db.Model):
    __tablename__ = 'pair_history'
    
    id = db.Column(db.Integer, primary_key=True)
    cattle_id = db.Column(db.Integer, db.ForeignKey('cattle.id'), nullable=False)
    lf_tag = db.Column(db.String(100))
    uhf_tag = db.Column(db.String(100))
    paired_at = db.Column(db.DateTime, nullable=False)
    unpaired_at = db.Column(db.DateTime, nullable=False)
    updated_by = db.Column(db.String(100), default='system')

class Cattle(db.Model):
    __tablename__ = 'cattle'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    cattle_id = db.Column(db.String(100), nullable=False, unique=True)
    sex = db.Column(db.String(10), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    health_status = db.Column(db.String(50))
    lf_tag = db.Column(db.String(100))
    uhf_tag = db.Column(db.String(100))
    pen_id = db.Column(db.Integer, db.ForeignKey('pens.id'))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='active', nullable=False)
    induction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship for weight records
    weight_records = db.relationship('WeightRecord', backref='cattle', lazy=True, cascade='all, delete-orphan', order_by='WeightRecord.recorded_at.desc()')
    
    # Relationship for tag pair history
    pair_history = db.relationship('PairHistory', backref='cattle', lazy=True, cascade='all, delete-orphan', order_by='PairHistory.unpaired_at.desc()')
    
    @staticmethod
    def create_cattle(batch_id, cattle_id, sex, weight, 
                     health_status, lf_tag=None, uhf_tag=None, pen_id=None, notes=None):
        """Create a new cattle record"""
        cattle = Cattle(
            batch_id=batch_id,
            cattle_id=cattle_id,
            sex=sex,
            weight=weight,
            health_status=health_status,
            lf_tag=lf_tag or '',
            uhf_tag=uhf_tag or '',
            pen_id=pen_id,
            notes=notes or '',
            status='active',
            induction_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(cattle)
        db.session.flush()  # Get the ID
        
        # Create initial weight record
        weight_record = WeightRecord(
            cattle_id=cattle.id,
            weight=weight,
            recorded_at=datetime.utcnow(),
            recorded_by='system'
        )
        db.session.add(weight_record)
        db.session.commit()
        return cattle.id
    
    @staticmethod
    def find_by_id(cattle_record_id):
        """Find cattle by ID"""
        return Cattle.query.get(cattle_record_id)
    
    @staticmethod
    def find_by_cattle_id(cattle_id):
        """Find cattle by cattle ID"""
        return Cattle.query.filter_by(cattle_id=cattle_id).first()
    
    @staticmethod
    def find_all():
        """Find all cattle"""
        return Cattle.query.all()
    
    @staticmethod
    def find_by_batch(batch_id):
        """Find all cattle in a batch"""
        return Cattle.query.filter_by(batch_id=batch_id).all()
    
    @staticmethod
    def find_by_pen(pen_id):
        """Find all cattle in a pen"""
        return Cattle.query.filter_by(pen_id=pen_id, status='active').all()
    
    @staticmethod
    def update_cattle(cattle_record_id, update_data):
        """Update cattle information"""
        cattle = Cattle.query.get(cattle_record_id)
        if cattle:
            for key, value in update_data.items():
                setattr(cattle, key, value)
            cattle.updated_at = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def move_cattle(cattle_record_id, new_pen_id):
        """Move cattle to a different pen"""
        cattle = Cattle.query.get(cattle_record_id)
        if cattle:
            cattle.pen_id = new_pen_id
            cattle.updated_at = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def remove_cattle(cattle_record_id):
        """Remove cattle (mark as inactive)"""
        cattle = Cattle.query.get(cattle_record_id)
        if cattle:
            cattle.status = 'removed'
            cattle.updated_at = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def add_weight_record(cattle_record_id, weight, recorded_by='system'):
        """Add a new weight record to the cattle's weight history"""
        cattle = Cattle.query.get(cattle_record_id)
        if cattle:
            # Update current weight
            cattle.weight = weight
            cattle.updated_at = datetime.utcnow()
            
            # Add weight record
            weight_record = WeightRecord(
                cattle_id=cattle.id,
                weight=weight,
                recorded_at=datetime.utcnow(),
                recorded_by=recorded_by
            )
            db.session.add(weight_record)
            db.session.commit()
    
    @staticmethod
    def get_weight_history(cattle_record_id):
        """Get the complete weight history for a cattle record"""
        cattle = Cattle.query.get(cattle_record_id)
        if not cattle:
            return []
        return [{
            'weight': wr.weight,
            'recorded_at': wr.recorded_at,
            'recorded_by': wr.recorded_by
        } for wr in cattle.weight_records]
    
    @staticmethod
    def get_latest_weight(cattle_record_id):
        """Get the most recent weight for a cattle record"""
        weight_history = Cattle.get_weight_history(cattle_record_id)
        if not weight_history:
            return None
        return weight_history[0]['weight']  # Already ordered desc
    
    @staticmethod
    def find_with_filters(search=None, health_status=None, sex=None, pen_id=None, sort_by='cattle_id', sort_order='asc'):
        """Find cattle with filtering and sorting"""
        query = Cattle.query
        
        # Add search filter for cattle_id
        if search:
            query = query.filter(Cattle.cattle_id.ilike(f'%{search}%'))
        
        # Add health status filter
        if health_status:
            query = query.filter(Cattle.health_status == health_status)
        
        # Add sex filter
        if sex:
            query = query.filter(Cattle.sex == sex)
        
        # Add pen filter
        if pen_id:
            query = query.filter(Cattle.pen_id == pen_id)
        
        # Define sort field mapping
        sort_field_map = {
            'cattle_id': Cattle.cattle_id,
            'weight': Cattle.weight,
            'induction_date': Cattle.induction_date,
            'health_status': Cattle.health_status,
            'sex': Cattle.sex
        }
        
        sort_field = sort_field_map.get(sort_by, Cattle.cattle_id)
        
        # Apply sorting
        if sort_order == 'desc':
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        return query.all()
    
    @staticmethod
    def update_tag_pair(cattle_record_id, new_lf_tag, new_uhf_tag, updated_by='system'):
        """Update LF and UHF tag pair, saving previous pair to history"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return False
        
        current_lf_tag = cattle.lf_tag or ''
        current_uhf_tag = cattle.uhf_tag or ''
        new_lf_tag = new_lf_tag or ''
        new_uhf_tag = new_uhf_tag or ''
        
        # Check if tags are actually changing
        tags_changed = (current_lf_tag != new_lf_tag) or (current_uhf_tag != new_uhf_tag)
        
        if tags_changed:
            # If there was a previous tag pair, save it to history
            if current_lf_tag or current_uhf_tag:
                # Determine when the current tags were paired
                pair_history = cattle.pair_history
                if pair_history:
                    # If there's history, the current tags were paired at last update
                    paired_at = cattle.updated_at
                else:
                    # First pair was at creation time
                    paired_at = cattle.created_at
                
                # Create history record
                pair_record = PairHistory(
                    cattle_id=cattle.id,
                    lf_tag=current_lf_tag,
                    uhf_tag=current_uhf_tag,
                    paired_at=paired_at,
                    unpaired_at=datetime.utcnow(),
                    updated_by=updated_by
                )
                db.session.add(pair_record)
            
            # Update current tags
            cattle.lf_tag = new_lf_tag
            cattle.uhf_tag = new_uhf_tag
            cattle.updated_at = datetime.utcnow()
            db.session.commit()
        
        return True
    
    @staticmethod
    def get_tag_pair_history(cattle_record_id):
        """Get the complete tag pair history for a cattle record"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        return [{
            'lf_tag': ph.lf_tag,
            'uhf_tag': ph.uhf_tag,
            'paired_at': ph.paired_at,
            'unpaired_at': ph.unpaired_at,
            'updated_by': ph.updated_by
        } for ph in cattle.pair_history]
    
    def to_dict(self):
        """Convert cattle to dictionary"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'cattle_id': self.cattle_id,
            'sex': self.sex,
            'weight': self.weight,
            'health_status': self.health_status,
            'lf_tag': self.lf_tag,
            'uhf_tag': self.uhf_tag,
            'pen_id': self.pen_id,
            'notes': self.notes,
            'status': self.status,
            'induction_date': self.induction_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

