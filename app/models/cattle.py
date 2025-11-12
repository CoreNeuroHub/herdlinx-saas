from datetime import datetime
from bson import ObjectId
from app import db
from app.adapters import get_office_adapter

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
            }],
            'tag_pair_history': []  # Track previous LF/UHF tag pairs
        }
        
        result = db.cattle.insert_one(cattle_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(cattle_record_id):
        """Find cattle by ID - supports both ObjectId and integer office IDs"""
        try:
            # Try as ObjectId first (native SAAS cattle)
            if isinstance(cattle_record_id, str) and len(cattle_record_id) == 24:
                result = db.cattle.find_one({'_id': ObjectId(cattle_record_id)})
                if result:
                    return result

            # Try as integer (office synced livestock)
            if isinstance(cattle_record_id, int) or (isinstance(cattle_record_id, str) and cattle_record_id.isdigit()):
                office_adapter = get_office_adapter(db)
                office_livestock = office_adapter.get_office_livestock_by_id(int(cattle_record_id))
                if office_livestock:
                    return office_livestock

            return None
        except Exception as e:
            print(f"Error in Cattle.find_by_id: {e}")
            return None
    
    @staticmethod
    def find_by_cattle_id(feedlot_id, cattle_id):
        """Find cattle by cattle ID"""
        return db.cattle.find_one({
            'feedlot_id': ObjectId(feedlot_id),
            'cattle_id': cattle_id
        })
    
    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all cattle for a feedlot - includes office synced livestock"""
        try:
            feedlot_oid = ObjectId(feedlot_id) if isinstance(feedlot_id, str) else feedlot_id

            # Get native SAAS cattle
            native_cattle = list(db.cattle.find({'feedlot_id': feedlot_oid}))

            # Get feedlot_code for this feedlot
            feedlot = db.feedlots.find_one({'_id': feedlot_oid})
            feedlot_code = feedlot.get('feedlot_code') if feedlot else None

            # Get office synced livestock filtered by feedlot_code
            office_cattle = []
            if feedlot_code:
                office_adapter = get_office_adapter(db)
                office_cattle = office_adapter.get_office_livestock_by_feedlot_code(feedlot_code)

            # Combine, preferring native cattle if duplicate
            all_cattle = native_cattle.copy()
            native_cattle_ids = {str(c.get('_id')) for c in native_cattle if '_id' in c}

            for office_item in office_cattle:
                if str(office_item.get('_id')) not in native_cattle_ids:
                    all_cattle.append(office_item)

            return all_cattle
        except Exception as e:
            print(f"Error in Cattle.find_by_feedlot: {e}")
            return []
    
    @staticmethod
    def find_by_batch(batch_id):
        """Find all cattle in a batch - supports both ObjectId and integer office IDs"""
        try:
            office_adapter = get_office_adapter(db)

            # Try as office batch ID (integer)
            if isinstance(batch_id, int) or (isinstance(batch_id, str) and batch_id.isdigit()):
                office_livestock = office_adapter.get_office_livestock_by_batch(int(batch_id))
                if office_livestock:
                    return office_livestock

            # Try as SAAS ObjectId
            if isinstance(batch_id, str) and len(batch_id) == 24:
                return list(db.cattle.find({'batch_id': ObjectId(batch_id)}))

            return []
        except Exception as e:
            print(f"Error in Cattle.find_by_batch: {e}")
            return []
    
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
    
    @staticmethod
    def update_tag_pair(cattle_record_id, new_lf_tag, new_uhf_tag, updated_by='system'):
        """Update LF and UHF tag pair, saving previous pair to history"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return False
        
        current_lf_tag = cattle.get('lf_tag', '') or ''
        current_uhf_tag = cattle.get('uhf_tag', '') or ''
        new_lf_tag = new_lf_tag or ''
        new_uhf_tag = new_uhf_tag or ''
        
        # Check if tags are actually changing
        tags_changed = (current_lf_tag != new_lf_tag) or (current_uhf_tag != new_uhf_tag)
        
        if tags_changed:
            # If there was a previous tag pair (both tags exist), save it to history
            if current_lf_tag or current_uhf_tag:
                tag_pair_record = {
                    'lf_tag': current_lf_tag,
                    'uhf_tag': current_uhf_tag,
                    'paired_at': cattle.get('created_at', datetime.utcnow()),  # Use creation date if no history
                    'unpaired_at': datetime.utcnow(),
                    'updated_by': updated_by
                }
                
                # Get the last tag pair record if exists to get the actual pairing date
                tag_history = cattle.get('tag_pair_history', [])
                if tag_history:
                    # If there's history, the current tags were paired when last updated
                    last_update = cattle.get('updated_at', datetime.utcnow())
                    tag_pair_record['paired_at'] = last_update
                elif cattle.get('created_at'):
                    # First pair was at creation time
                    tag_pair_record['paired_at'] = cattle.get('created_at')
                
                # Update cattle with new tags and add old pair to history
                db.cattle.update_one(
                    {'_id': ObjectId(cattle_record_id)},
                    {
                        '$set': {
                            'lf_tag': new_lf_tag,
                            'uhf_tag': new_uhf_tag,
                            'updated_at': datetime.utcnow()
                        },
                        '$push': {'tag_pair_history': tag_pair_record}
                    }
                )
            else:
                # No previous tags, just update (this is initial pairing)
                db.cattle.update_one(
                    {'_id': ObjectId(cattle_record_id)},
                    {
                        '$set': {
                            'lf_tag': new_lf_tag,
                            'uhf_tag': new_uhf_tag,
                            'updated_at': datetime.utcnow()
                        }
                    }
                )
        
        return True
    
    @staticmethod
    def get_tag_pair_history(cattle_record_id):
        """Get the complete tag pair history for a cattle record"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        return cattle.get('tag_pair_history', [])

