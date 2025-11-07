from datetime import datetime
from bson import ObjectId
from app import db

class Feedlot:
    @staticmethod
    def create_feedlot(name, location, feedlot_code, contact_info=None, owner_id=None):
        """Create a new feedlot
        
        Args:
            name: Feedlot name
            location: Feedlot location
            feedlot_code: Unique feedlot code for office app integration (required, unique, case-insensitive)
            contact_info: Contact information dictionary
            owner_id: Optional owner user ID (must be business_owner type)
        """
        # Validate feedlot_code uniqueness (case-insensitive)
        if feedlot_code:
            existing = Feedlot.find_by_code(feedlot_code)
            if existing:
                raise ValueError(f"Feedlot code '{feedlot_code}' already exists.")
        
        feedlot_data = {
            'name': name,
            'location': location,
            'feedlot_code': feedlot_code.upper().strip() if feedlot_code else None,
            'contact_info': contact_info or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        if owner_id:
            feedlot_data['owner_id'] = ObjectId(owner_id)
        
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
    def find_by_code(feedlot_code):
        """Find feedlot by feedlot_code (case-insensitive)"""
        if not feedlot_code:
            return None
        return db.feedlots.find_one({'feedlot_code': feedlot_code.upper().strip()})
    
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
        """Get feedlot statistics - includes office synced data"""
        try:
            from app.models.batch import Batch
            from app.models.cattle import Cattle
            from app.adapters import get_office_adapter

            feedlot_id_obj = ObjectId(feedlot_id)

            # SAAS native statistics
            total_pens = db.pens.count_documents({'feedlot_id': feedlot_id_obj})
            native_cattle = db.cattle.count_documents({'feedlot_id': feedlot_id_obj})
            native_batches = db.batches.count_documents({'feedlot_id': feedlot_id_obj})

            # Office synced statistics
            office_adapter = get_office_adapter(db)
            office_batches = office_adapter.get_office_batches_all()
            total_office_batches = len(office_batches)

            # Count office livestock
            total_office_cattle = 0
            for batch in office_batches:
                batch_id = batch.get('_id')
                if isinstance(batch_id, int):
                    livestock = office_adapter.get_office_livestock_by_batch(batch_id)
                    total_office_cattle += len(livestock)

            # Get cattle in each pen (native only)
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
                'total_cattle': native_cattle + total_office_cattle,
                'native_cattle': native_cattle,
                'office_cattle': total_office_cattle,
                'total_batches': native_batches + total_office_batches,
                'native_batches': native_batches,
                'office_batches': total_office_batches,
                'cattle_by_pen': len(cattle_by_pen)
            }
        except Exception as e:
            print(f"Error in Feedlot.get_statistics: {e}")
            # Return defaults on error
            feedlot_id_obj = ObjectId(feedlot_id)
            return {
                'total_pens': 0,
                'total_cattle': 0,
                'total_batches': 0,
                'cattle_by_pen': 0
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
    
    @staticmethod
    def get_owner(feedlot_id):
        """Get the owner user for a feedlot"""
        from app.models.user import User
        feedlot = Feedlot.find_by_id(feedlot_id)
        if feedlot and feedlot.get('owner_id'):
            return User.find_by_id(str(feedlot['owner_id']))
        return None

