from datetime import datetime
from bson import ObjectId
from app import db

class Cattle:
    @staticmethod
    def create_cattle(feedlot_id, batch_id, cattle_id, breed, weight, 
                     health_status, pen_id=None, notes=None):
        """Create a new cattle record"""
        cattle_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'batch_id': ObjectId(batch_id),
            'cattle_id': cattle_id,
            'breed': breed,
            'weight': weight,
            'health_status': health_status,
            'pen_id': ObjectId(pen_id) if pen_id else None,
            'notes': notes or '',
            'status': 'active',
            'induction_date': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.cattle.insert_one(cattle_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(cattle_record_id):
        """Find cattle by ID"""
        return db.cattle.find_one({'_id': ObjectId(cattle_record_id)})
    
    @staticmethod
    def find_by_cattle_id(feedlot_id, cattle_id):
        """Find cattle by cattle ID"""
        return db.cattle.find_one({
            'feedlot_id': ObjectId(feedlot_id),
            'cattle_id': cattle_id
        })
    
    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all cattle for a feedlot"""
        return list(db.cattle.find({'feedlot_id': ObjectId(feedlot_id)}))
    
    @staticmethod
    def find_by_batch(batch_id):
        """Find all cattle in a batch"""
        return list(db.cattle.find({'batch_id': ObjectId(batch_id)}))
    
    @staticmethod
    def find_by_pen(pen_id):
        """Find all cattle in a pen"""
        return list(db.cattle.find({'pen_id': ObjectId(pen_id), 'status': 'active'}))
    
    @staticmethod
    def update_cattle(cattle_record_id, update_data):
        """Update cattle information"""
        update_data['updated_at'] = datetime.utcnow()
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def move_cattle(cattle_record_id, new_pen_id):
        """Move cattle to a different pen"""
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {'$set': {
                'pen_id': ObjectId(new_pen_id),
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def remove_cattle(cattle_record_id):
        """Remove cattle (mark as inactive)"""
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {'$set': {
                'status': 'removed',
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def get_movement_history(cattle_record_id):
        """Get movement history for cattle"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        # This could be expanded with a movement log collection
        return cattle.get('movement_history', [])

