from datetime import datetime
from bson import ObjectId
from app import db
from app.models.pen import Pen

class Cattle:
    @staticmethod
    def create_cattle(feedlot_id, batch_id, cattle_id, sex, weight, 
                     health_status, lf_tag=None, uhf_tag=None, pen_id=None, notes=None,
                     color=None, breed=None, brand_drawings=None, brand_locations=None, other_marks=None, created_by='system'):
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
            'color': color or '',
            'breed': breed or '',
            'brand_drawings': brand_drawings or '',
            'brand_locations': brand_locations or '',
            'other_marks': other_marks or '',
            'status': 'active',
            'induction_date': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'weight_history': [{
                'weight': weight,
                'recorded_at': datetime.utcnow(),
                'recorded_by': created_by
            }],
            'notes_history': [],  # Track notes history
            'tag_pair_history': [],  # Track previous LF/UHF tag pairs
            'audit_log': []  # Track all cattle activities
        }
        
        result = db.cattle.insert_one(cattle_data)
        cattle_record_id = str(result.inserted_id)
        
        # Add initial audit log entry for creation
        Cattle.add_audit_log_entry(cattle_record_id, 'created', f'Cattle record created (ID: {cattle_id})', created_by)
        
        return cattle_record_id
    
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
    def update_cattle(cattle_record_id, update_data, updated_by='system'):
        """Update cattle information"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return
        
        # Track changes for audit log
        changes = []
        old_values = {}
        new_values = {}
        
        # Fields to track (excluding internal fields)
        trackable_fields = ['sex', 'health_status', 'color', 'breed', 'brand_drawings', 
                          'brand_locations', 'other_marks', 'notes', 'induction_date', 'pen_id']
        
        for field in trackable_fields:
            if field in update_data:
                old_value = cattle.get(field)
                new_value = update_data[field]
                
                # Skip if value hasn't actually changed
                if old_value != new_value:
                    old_values[field] = old_value
                    new_values[field] = new_value
                    
                    # Format change description
                    if field == 'pen_id':
                        old_pen = Pen.find_by_id(old_value) if old_value else None
                        new_pen = Pen.find_by_id(new_value) if new_value else None
                        old_name = old_pen.get('pen_number', str(old_value)) if old_pen else None
                        new_name = new_pen.get('pen_number', str(new_value)) if new_pen else None
                        changes.append(f"{field}: {old_name or 'none'} → {new_name or 'none'}")
                    elif field == 'induction_date':
                        old_str = old_value.strftime('%Y-%m-%d') if isinstance(old_value, datetime) else str(old_value)
                        new_str = new_value.strftime('%Y-%m-%d') if isinstance(new_value, datetime) else str(new_value)
                        changes.append(f"{field}: {old_str} → {new_str}")
                    else:
                        changes.append(f"{field}: {old_value or 'none'} → {new_value or 'none'}")
        
        update_data['updated_at'] = datetime.utcnow()
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {'$set': update_data}
        )
        
        # Add audit log entry if there were changes
        if changes:
            description = f'Cattle information updated: {", ".join(changes)}'
            Cattle.add_audit_log_entry(
                cattle_record_id,
                'information_updated',
                description,
                updated_by,
                {'old_values': old_values, 'new_values': new_values}
            )
    
    @staticmethod
    def move_cattle(cattle_record_id, new_pen_id, moved_by='system'):
        """Move cattle to a different pen"""
        cattle = Cattle.find_by_id(cattle_record_id)
        old_pen_id = cattle.get('pen_id') if cattle else None
        
        # Get pen names for audit log
        old_pen = Pen.find_by_id(old_pen_id) if old_pen_id else None
        new_pen = Pen.find_by_id(new_pen_id) if new_pen_id else None
        
        old_pen_name = old_pen.get('pen_number', str(old_pen_id)) if old_pen else None
        new_pen_name = new_pen.get('pen_number', str(new_pen_id)) if new_pen else None
        
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {'$set': {
                'pen_id': ObjectId(new_pen_id) if new_pen_id else None,
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Add audit log entry for pen movement
        description = f'Moved to pen {new_pen_name}' if new_pen_name else 'Removed from pen'
        if old_pen_name:
            description = f'Moved from pen {old_pen_name} to pen {new_pen_name}' if new_pen_name else f'Removed from pen {old_pen_name}'
        Cattle.add_audit_log_entry(
            cattle_record_id, 
            'pen_moved', 
            description, 
            moved_by,
            {'old_pen_id': str(old_pen_id) if old_pen_id else None, 'new_pen_id': str(new_pen_id) if new_pen_id else None, 'old_pen_name': old_pen_name, 'new_pen_name': new_pen_name}
        )
    
    @staticmethod
    def remove_cattle(cattle_record_id, removed_by='system'):
        """Remove cattle (mark as inactive)"""
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {'$set': {
                'status': 'removed',
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Add audit log entry for removal
        Cattle.add_audit_log_entry(
            cattle_record_id,
            'removed',
            'Cattle record marked as removed',
            removed_by,
            {'status': 'removed'}
        )
    
    @staticmethod
    def add_weight_record(cattle_record_id, weight, recorded_by='system'):
        """Add a new weight record to the cattle's weight history"""
        cattle = Cattle.find_by_id(cattle_record_id)
        previous_weight = cattle.get('weight') if cattle else None
        
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
        
        # Add audit log entry for weight addition
        description = f'Weight recorded: {weight} kg'
        if previous_weight:
            description += f' (previous: {previous_weight} kg)'
        Cattle.add_audit_log_entry(
            cattle_record_id, 
            'weight_recorded', 
            description, 
            recorded_by,
            {'weight': weight, 'previous_weight': previous_weight}
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
    def add_note(cattle_record_id, note, recorded_by='system'):
        """Add a new note to the cattle's notes history"""
        note_record = {
            'note': note,
            'recorded_at': datetime.utcnow(),
            'recorded_by': recorded_by
        }
        
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {
                '$set': {
                    'updated_at': datetime.utcnow()
                },
                '$push': {'notes_history': note_record}
            }
        )
        
        # Add audit log entry for note addition
        description = f'Note added: {note[:50]}{"..." if len(note) > 50 else ""}'
        Cattle.add_audit_log_entry(
            cattle_record_id, 
            'note_added', 
            description, 
            recorded_by,
            {'note': note}
        )
    
    @staticmethod
    def get_notes_history(cattle_record_id):
        """Get the complete notes history for a cattle record"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        return cattle.get('notes_history', [])

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
    def update_tag_pair(cattle_record_id, new_lf_tag, new_uhf_tag, updated_by='system', reason=None):
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
                
                # Add audit log entry for tag re-pairing
                description = f'Tags re-paired: LF {current_lf_tag or "none"} → {new_lf_tag or "none"}, UHF {current_uhf_tag or "none"} → {new_uhf_tag or "none"}'
                if reason:
                    description += f' (Reason: {reason})'
                Cattle.add_audit_log_entry(
                    cattle_record_id, 
                    'tag_repair', 
                    description, 
                    updated_by,
                    {'old_lf_tag': current_lf_tag, 'new_lf_tag': new_lf_tag, 'old_uhf_tag': current_uhf_tag, 'new_uhf_tag': new_uhf_tag, 'reason': reason}
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
                
                # Add audit log entry for initial pairing
                description = f'Tags paired: LF {new_lf_tag or "none"}, UHF {new_uhf_tag or "none"}'
                Cattle.add_audit_log_entry(
                    cattle_record_id, 
                    'tag_pairing', 
                    description, 
                    updated_by,
                    {'lf_tag': new_lf_tag, 'uhf_tag': new_uhf_tag}
                )
        
        return True
    
    @staticmethod
    def get_tag_pair_history(cattle_record_id):
        """Get the complete tag pair history for a cattle record"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        return cattle.get('tag_pair_history', [])
    
    @staticmethod
    def add_audit_log_entry(cattle_record_id, activity_type, description, performed_by='system', details=None):
        """Add an entry to the cattle audit log"""
        audit_entry = {
            'activity_type': activity_type,
            'description': description,
            'performed_by': performed_by,
            'timestamp': datetime.utcnow(),
            'details': details or {}
        }
        
        db.cattle.update_one(
            {'_id': ObjectId(cattle_record_id)},
            {'$push': {'audit_log': audit_entry}}
        )
    
    @staticmethod
    def get_audit_log(cattle_record_id):
        """Get the complete audit log for a cattle record"""
        cattle = Cattle.find_by_id(cattle_record_id)
        if not cattle:
            return []
        
        return cattle.get('audit_log', [])

