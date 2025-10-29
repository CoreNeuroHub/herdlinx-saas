from datetime import datetime
from bson import ObjectId
from app import db

class Cattle:
    @staticmethod
    def create_cattle(feedlot_id, batch_id, cattle_id, sex, weight, 
                     health_status, lf_tag=None, uhf_tag=None, pen_id=None, notes=None):
        """Create a new cattle record"""
        cattle_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'batch_id': ObjectId(batch_id),
            'cattle_id': cattle_id,
            'sex': sex,
            'weight': weight,
            'health_status': health_status,
            'lf_tag': lf_tag or '',
            'uhf_tag': uhf_tag or '',
            'pen_id': ObjectId(pen_id) if pen_id else None,
            'notes': notes or '',
            'status': 'active',
            'induction_date': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'weight_history': [{
                'weight': weight,
                'recorded_at': datetime.utcnow(),
                'recorded_by': 'system'  # This could be enhanced to track who recorded the weight
            }]
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
    def add_weight_record(cattle_record_id, weight, recorded_by='system'):
        """Add a new weight record to the cattle's weight history"""
        weight_record = {
            'weight': weight,
            'recorded_at': datetime.utcnow(),
            'recorded_by': recorded_by
        }
        
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {
                '$set': {
                    'weight': weight,  # Update current weight
                    'updated_at': datetime.utcnow()
                },
                '$push': {'weight_history': weight_record}
            }
        )
    
    @staticmethod
    def get_weight_history(cattle_record_id):
        """Get the complete weight history for a cattle record"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        return cattle.get('weight_history', [])
    
    @staticmethod
    def get_latest_weight(cattle_record_id):
        """Get the most recent weight for a cattle record"""
        weight_history = Cattle.get_weight_history(cattle_record_id)
        if not weight_history:
            return None
        
        # Sort by recorded_at descending and get the first (most recent)
        latest_record = max(weight_history, key=lambda x: x['recorded_at'])
        return latest_record['weight']

    @staticmethod
    def get_movement_history(cattle_record_id):
        """Get movement history for cattle"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        # This could be expanded with a movement log collection
        return cattle.get('movement_history', [])
    
    @staticmethod
    def find_by_feedlot_with_filters(feedlot_id, search=None, health_status=None, sex=None, pen_id=None, sort_by='cattle_id', sort_order='asc'):
        """Find cattle with filtering and sorting"""
        query = {'feedlot_id': ObjectId(feedlot_id)}
        
        # Add search filter for cattle_id
        if search:
            query['cattle_id'] = {'$regex': search, '$options': 'i'}
        
        # Add health status filter
        if health_status:
            query['health_status'] = health_status
        
        # Add sex filter
        if sex:
            query['sex'] = sex
        
        # Add pen filter
        if pen_id:
            query['pen_id'] = ObjectId(pen_id)
        
        # Define sort order
        sort_direction = 1 if sort_order == 'asc' else -1
        
        # Define sort field mapping
        sort_field_map = {
            'cattle_id': 'cattle_id',
            'weight': 'weight',
            'induction_date': 'induction_date',
            'health_status': 'health_status',
            'sex': 'sex'
        }
        
        sort_field = sort_field_map.get(sort_by, 'cattle_id')
        sort_criteria = [(sort_field, sort_direction)]
        
        return list(db.cattle.find(query).sort(sort_criteria))

