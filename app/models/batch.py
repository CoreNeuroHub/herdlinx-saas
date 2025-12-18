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
            'cattle_ids': [],  # Historical record of all cattle ever associated with this batch
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
        """Get number of cattle currently in a batch (excludes deleted)
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        return feedlot_db.cattle.count_documents({
            'batch_id': ObjectId(batch_id),
            'deleted_at': None
        })
    
    @staticmethod
    def add_cattle_to_batch(feedlot_code, batch_id, cattle_record_id):
        """Add a cattle record ID to the batch's historical cattle_ids array
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
            cattle_record_id: The cattle record ID to add
        """
        feedlot_db = get_feedlot_db(feedlot_code)
        feedlot_db.batches.update_one(
            {'_id': ObjectId(batch_id)},
            {
                '$addToSet': {'cattle_ids': ObjectId(cattle_record_id)},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
    
    @staticmethod
    def get_batch_cattle_ids(feedlot_code, batch_id):
        """Get all historical cattle IDs associated with this batch
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
            
        Returns:
            List of cattle record ObjectIds that have ever been in this batch
        """
        batch = Batch.find_by_id(feedlot_code, batch_id, include_deleted=True)
        if not batch:
            return []
        return batch.get('cattle_ids', [])
    
    @staticmethod
    def get_historical_cattle_count(feedlot_code, batch_id):
        """Get total number of cattle ever associated with this batch
        
        Args:
            feedlot_code: The feedlot code (required for database selection)
            batch_id: The batch ID
            
        Returns:
            Count of all cattle that have ever been in this batch
        """
        cattle_ids = Batch.get_batch_cattle_ids(feedlot_code, batch_id)
        return len(cattle_ids)

