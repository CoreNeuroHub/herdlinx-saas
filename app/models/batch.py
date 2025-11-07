from datetime import datetime
from bson import ObjectId
from app import db
from app.adapters import get_office_adapter

class Batch:
    """Batch model - supports both native SAAS and office synced data"""

    @staticmethod
    def create_batch(feedlot_id, batch_number, induction_date, funder, notes=None):
        """Create a new batch"""
        batch_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'batch_number': batch_number,
            'induction_date': induction_date,
            'funder': funder,
            'notes': notes or '',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        result = db.batches.insert_one(batch_data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(batch_id):
        """Find batch by ID - supports both ObjectId and integer office IDs"""
        try:
            # Try as ObjectId first (native SAAS batches)
            if isinstance(batch_id, str) and len(batch_id) == 24:
                result = db.batches.find_one({'_id': ObjectId(batch_id)})
                if result:
                    return result

            # Try as integer (office synced batches)
            if isinstance(batch_id, int) or (isinstance(batch_id, str) and batch_id.isdigit()):
                office_adapter = get_office_adapter(db)
                office_batch = office_adapter.get_office_batch_by_id(int(batch_id))
                if office_batch:
                    return office_batch

            # Try direct lookup if it's already an integer in native batches
            try:
                result = db.batches.find_one({'_id': batch_id})
                if result:
                    return result
            except:
                pass

            return None
        except Exception as e:
            print(f"Error in Batch.find_by_id: {e}")
            return None

    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all batches for a feedlot"""
        try:
            feedlot_oid = ObjectId(feedlot_id) if isinstance(feedlot_id, str) else feedlot_id

            # Get native SAAS batches
            native_batches = list(db.batches.find({'feedlot_id': feedlot_oid}))

            # Get office synced batches (all of them if feedlot_id not set)
            office_adapter = get_office_adapter(db)
            office_batches = office_adapter.get_office_batches_all()

            # Combine, preferring native batches if duplicate
            all_batches = native_batches.copy()
            office_batch_ids = {b['_id'] for b in native_batches if '_id' in b}

            for office_batch in office_batches:
                if office_batch.get('_id') not in office_batch_ids:
                    all_batches.append(office_batch)

            return all_batches
        except Exception as e:
            print(f"Error in Batch.find_by_feedlot: {e}")
            return []

    @staticmethod
    def update_batch(batch_id, update_data):
        """Update batch information"""
        try:
            update_data['updated_at'] = datetime.utcnow()

            # Try ObjectId update first
            try:
                if isinstance(batch_id, str) and len(batch_id) == 24:
                    result = db.batches.update_one(
                        {'_id': ObjectId(batch_id)},
                        {'$set': update_data}
                    )
                    if result.matched_count > 0:
                        return
            except:
                pass

            # Try integer ID (shouldn't update office data directly)
            # Office data should be synced, not updated in SAAS
            print(f"Warning: Attempted to update office batch {batch_id}")
        except Exception as e:
            print(f"Error in Batch.update_batch: {e}")

    @staticmethod
    def delete_batch(batch_id):
        """Delete a batch - only native SAAS batches"""
        try:
            if isinstance(batch_id, str) and len(batch_id) == 24:
                db.batches.delete_one({'_id': ObjectId(batch_id)})
        except Exception as e:
            print(f"Error in Batch.delete_batch: {e}")

    @staticmethod
    def get_cattle_count(batch_id):
        """Get number of cattle in a batch"""
        try:
            office_adapter = get_office_adapter(db)

            # Try as office batch ID (integer)
            if isinstance(batch_id, int) or (isinstance(batch_id, str) and batch_id.isdigit()):
                livestock_records = office_adapter.get_office_livestock_by_batch(int(batch_id))
                return len(livestock_records)

            # Try as SAAS ObjectId
            if isinstance(batch_id, str) and len(batch_id) == 24:
                return db.cattle.count_documents({'batch_id': ObjectId(batch_id)})

            return 0
        except Exception as e:
            print(f"Error in Batch.get_cattle_count: {e}")
            return 0

