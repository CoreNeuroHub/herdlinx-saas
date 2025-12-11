from datetime import datetime
from bson import ObjectId
from app import db, get_feedlot_db

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
    def find_by_id(pen_id, include_deleted=False):
        """Find pen by ID
        
        Args:
            pen_id: The pen ID
            include_deleted: If True, include soft-deleted pens. Defaults to False.
        """
        query = {'_id': ObjectId(pen_id)}
        if not include_deleted:
            query['deleted_at'] = None
        return db.pens.find_one(query)
    
    @staticmethod
    def find_by_feedlot(feedlot_id, include_deleted=False):
        """Find all pens for a feedlot
        
        Args:
            feedlot_id: The feedlot ID
            include_deleted: If True, include soft-deleted pens. Defaults to False.
        """
        query = {'feedlot_id': ObjectId(feedlot_id)}
        if not include_deleted:
            query['deleted_at'] = None
        return list(db.pens.find(query))
    
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
        """Soft delete a pen (marks as deleted but doesn't remove from database)
        
        Args:
            pen_id: The pen ID
        """
        db.pens.update_one(
            {'_id': ObjectId(pen_id)},
            {'$set': {
                'deleted_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def get_current_cattle_count(pen_id, feedlot_code):
        """Get current number of cattle in a pen
        
        Args:
            pen_id: The pen ID
            feedlot_code: The feedlot code (required for database selection)
        """
        if not feedlot_code:
            return 0
        
        feedlot_db = get_feedlot_db(feedlot_code)
        return feedlot_db.cattle.count_documents({
            'pen_id': ObjectId(pen_id), 
            'status': 'active',
            'deleted_at': None
        })
    
    @staticmethod
    def is_capacity_available(pen_id, feedlot_code, additional_cattle=1):
        """Check if pen has available capacity
        
        Args:
            pen_id: The pen ID
            feedlot_code: The feedlot code (required for database selection)
            additional_cattle: Number of additional cattle to check capacity for (default: 1)
        """
        pen = Pen.find_by_id(pen_id)
        if not pen or pen.get('deleted_at'):
            return False
        
        current_count = Pen.get_current_cattle_count(pen_id, feedlot_code)
        return (current_count + additional_cattle) <= pen['capacity']

