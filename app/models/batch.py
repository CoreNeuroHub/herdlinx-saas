from datetime import datetime
from bson import ObjectId
from app import db

class Batch:
    @staticmethod
    def create_batch(feedlot_id, batch_number, induction_date, source, notes=None):
        """Create a new batch"""
        batch_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'batch_number': batch_number,
            'induction_date': induction_date,
            'source': source,
            'notes': notes or '',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.batches.insert_one(batch_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(batch_id):
        """Find batch by ID"""
        return db.batches.find_one({'_id': ObjectId(batch_id)})
    
    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all batches for a feedlot"""
        return list(db.batches.find({'feedlot_id': ObjectId(feedlot_id)}))
    
    @staticmethod
    def update_batch(batch_id, update_data):
        """Update batch information"""
        update_data['updated_at'] = datetime.utcnow()
        db.batches.update_one(
            {'_id': ObjectId(batch_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete_batch(batch_id):
        """Delete a batch"""
        db.batches.delete_one({'_id': ObjectId(batch_id)})
    
    @staticmethod
    def get_cattle_count(batch_id):
        """Get number of cattle in a batch"""
        return db.cattle.count_documents({'batch_id': ObjectId(batch_id)})

