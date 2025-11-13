from datetime import datetime
from bson import ObjectId
from app import db

class Pen:
    @staticmethod
    def create_pen(feedlot_id, pen_number, capacity, description=None):
        """Create a new pen"""
        pen_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'pen_number': pen_number,
            'capacity': capacity,
            'description': description or '',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.pens.insert_one(pen_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(pen_id):
        """Find pen by ID"""
        return db.pens.find_one({'_id': ObjectId(pen_id)})
    
    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all pens for a feedlot"""
        return list(db.pens.find({'feedlot_id': ObjectId(feedlot_id)}))
    
    @staticmethod
    def update_pen(pen_id, update_data):
        """Update pen information"""
        update_data['updated_at'] = datetime.utcnow()
        db.pens.update_one(
            {'_id': ObjectId(pen_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete_pen(pen_id):
        """Delete a pen"""
        db.pens.delete_one({'_id': ObjectId(pen_id)})
    
    @staticmethod
    def get_current_cattle_count(pen_id):
        """Get current number of cattle in a pen"""
        return db.cattle.count_documents({'pen_id': ObjectId(pen_id), 'status': 'active'})
    
    @staticmethod
    def is_capacity_available(pen_id, additional_cattle=1):
        """Check if pen has available capacity"""
        pen = Pen.find_by_id(pen_id)
        if not pen:
            return False
        
        current_count = Pen.get_current_cattle_count(pen_id)
        return (current_count + additional_cattle) <= pen['capacity']

