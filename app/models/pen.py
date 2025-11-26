from datetime import datetime
from bson import ObjectId
from app import get_feedlot_db

class Pen:
    @staticmethod
    def create_pen(feedlot_code, feedlot_id, pen_number, capacity, description=None):
        """Create a new pen
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            feedlot_id: The feedlot ID
            pen_number: Pen number
            capacity: Pen capacity
            description: Optional description
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        pen_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'pen_number': pen_number,
            'capacity': capacity,
            'description': description or '',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = feedlot_db.pens.insert_one(pen_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(feedlot_code, pen_id):
        """Find pen by ID
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            pen_id: The pen ID
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        return feedlot_db.pens.find_one({'_id': ObjectId(pen_id)})
    
    @staticmethod
    def find_by_feedlot(feedlot_code, feedlot_id):
        """Find all pens for a feedlot
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            feedlot_id: The feedlot ID
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        return list(feedlot_db.pens.find({'feedlot_id': ObjectId(feedlot_id)}))
    
    @staticmethod
    def update_pen(feedlot_code, pen_id, update_data):
        """Update pen information
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            pen_id: The pen ID
            update_data: Dictionary of fields to update
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        update_data['updated_at'] = datetime.utcnow()
        feedlot_db.pens.update_one(
            {'_id': ObjectId(pen_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete_pen(feedlot_code, pen_id):
        """Delete a pen
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            pen_id: The pen ID
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        feedlot_db.pens.delete_one({'_id': ObjectId(pen_id)})
    
    @staticmethod
    def get_current_cattle_count(feedlot_code, pen_id):
        """Get current number of cattle in a pen
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            pen_id: The pen ID
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        return feedlot_db.cattle.count_documents({'pen_id': ObjectId(pen_id), 'status': 'active'})
    
    @staticmethod
    def is_capacity_available(feedlot_code, pen_id, additional_cattle=1):
        """Check if pen has available capacity
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            pen_id: The pen ID
            additional_cattle: Number of additional cattle to check capacity for
        """
        pen = Pen.find_by_id(feedlot_code, pen_id)
        if not pen:
            return False
        
        current_count = Pen.get_current_cattle_count(feedlot_code, pen_id)
        return (current_count + additional_cattle) <= pen['capacity']

