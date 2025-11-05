from datetime import datetime
from bson import ObjectId
from app import db

class Feedlot:
    @staticmethod
    def create_feedlot(name, location, contact_info=None):
        """Create a new feedlot"""
        feedlot_data = {
            'name': name,
            'location': location,
            'contact_info': contact_info or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.feedlots.insert_one(feedlot_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(feedlot_id):
        """Find feedlot by ID"""
        return db.feedlots.find_one({'_id': ObjectId(feedlot_id)})
    
    @staticmethod
    def find_all():
        """Find all feedlots"""
        return list(db.feedlots.find())
    
    @staticmethod
    def find_by_ids(feedlot_ids):
        """Find feedlots by a list of IDs"""
        if not feedlot_ids:
            return []
        return db.feedlots.find({'_id': {'$in': feedlot_ids}})
    
    @staticmethod
    def update_feedlot(feedlot_id, update_data):
        """Update feedlot information"""
        update_data['updated_at'] = datetime.utcnow()
        db.feedlots.update_one(
            {'_id': ObjectId(feedlot_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def get_statistics(feedlot_id):
        """Get feedlot statistics"""
        feedlot_id_obj = ObjectId(feedlot_id)
        
        total_pens = db.pens.count_documents({'feedlot_id': feedlot_id_obj})
        total_cattle = db.cattle.count_documents({'feedlot_id': feedlot_id_obj})
        total_batches = db.batches.count_documents({'feedlot_id': feedlot_id_obj})
        
        # Get cattle in each pen
        pipeline = [
            {'$match': {'feedlot_id': feedlot_id_obj}},
            {'$group': {
                '_id': '$pen_id',
                'count': {'$sum': 1}
            }}
        ]
        cattle_by_pen = list(db.cattle.aggregate(pipeline))
        
        return {
            'total_pens': total_pens,
            'total_cattle': total_cattle,
            'total_batches': total_batches,
            'cattle_by_pen': len(cattle_by_pen)
        }
    
    @staticmethod
    def save_pen_map(feedlot_id, grid_width, grid_height, pen_placements):
        """Save pen map configuration for a feedlot"""
        pen_map_data = {
            'grid_width': grid_width,
            'grid_height': grid_height,
            'pen_placements': pen_placements,  # List of {row, col, pen_id}
            'updated_at': datetime.utcnow()
        }
        
        db.feedlots.update_one(
            {'_id': ObjectId(feedlot_id)},
            {'$set': {'pen_map': pen_map_data, 'updated_at': datetime.utcnow()}}
        )
    
    @staticmethod
    def get_pen_map(feedlot_id):
        """Get pen map configuration for a feedlot"""
        feedlot = Feedlot.find_by_id(feedlot_id)
        if feedlot and feedlot.get('pen_map'):
            return feedlot['pen_map']
        return None

