from datetime import datetime
from bson import ObjectId
from app import get_feedlot_db

class Batch:
    @staticmethod
    def create_batch(feedlot_code, feedlot_id, batch_number, event_date, funder, notes=None, event_type='induction'):
        """Create a new batch
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            feedlot_id: The feedlot ID
            batch_number: Batch number
            event_date: Event date
            funder: Funder information
            notes: Optional notes
            event_type: Event type (induction, pairing, checkin, repair, export). Defaults to 'induction'
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        batch_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'batch_number': batch_number,
            'event_date': event_date,
            'funder': funder,
            'notes': notes or '',
            'event_type': event_type,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = feedlot_db.batches.insert_one(batch_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(feedlot_code, batch_id, include_deleted=False):
        """Find batch by ID
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
            include_deleted: If True, include soft-deleted batches. Defaults to False.
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        query = {'_id': ObjectId(batch_id)}
        if not include_deleted:
            query['deleted_at'] = None
        return feedlot_db.batches.find_one(query)
    
    @staticmethod
    def find_by_feedlot(feedlot_code, feedlot_id, include_deleted=False):
        """Find all batches for a feedlot
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            feedlot_id: The feedlot ID
            include_deleted: If True, include soft-deleted batches. Defaults to False.
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        query = {'feedlot_id': ObjectId(feedlot_id)}
        if not include_deleted:
            query['deleted_at'] = None
        return list(feedlot_db.batches.find(query))
    
    @staticmethod
    def update_batch(feedlot_code, batch_id, update_data):
        """Update batch information
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
            update_data: Dictionary of fields to update
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        update_data['updated_at'] = datetime.utcnow()
        feedlot_db.batches.update_one(
            {'_id': ObjectId(batch_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete_batch(feedlot_code, batch_id):
        """Soft delete a batch (marks as deleted but doesn't remove from database)
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        feedlot_db.batches.update_one(
            {'_id': ObjectId(batch_id)},
            {'$set': {
                'deleted_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def get_cattle_count(feedlot_code, batch_id):
        """Get number of cattle in a batch
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        return feedlot_db.cattle.count_documents({
            'batch_id': ObjectId(batch_id),
            'deleted_at': None
        })

