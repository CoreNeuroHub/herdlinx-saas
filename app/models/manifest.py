from datetime import datetime
from bson import ObjectId
from app import db

class Manifest:
    @staticmethod
    def create_manifest(feedlot_id, manifest_data, cattle_ids, template_id=None, created_by=None):
        """Create a new manifest record"""
        manifest_record = {
            'feedlot_id': ObjectId(feedlot_id),
            'manifest_data': manifest_data,  # Full manifest data structure
            'cattle_ids': [ObjectId(cid) if isinstance(cid, str) else cid for cid in cattle_ids],  # List of cattle IDs included
            'template_id': ObjectId(template_id) if template_id else None,
            'created_by': created_by,
            'total_head': manifest_data.get('part_b', {}).get('total_head', 0),
            'destination_name': manifest_data.get('part_b', {}).get('destination_name', ''),
            'date': manifest_data.get('part_b', {}).get('date', datetime.utcnow().strftime('%Y-%m-%d')),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.manifests.insert_one(manifest_record)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(manifest_id):
        """Find manifest by ID"""
        return db.manifests.find_one({'_id': ObjectId(manifest_id)})
    
    @staticmethod
    def find_by_feedlot(feedlot_id, limit=None, skip=0):
        """Find all manifests for a feedlot, ordered by most recent first"""
        query = {'feedlot_id': ObjectId(feedlot_id)}
        cursor = db.manifests.find(query).sort('created_at', -1)
        
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    @staticmethod
    def count_by_feedlot(feedlot_id):
        """Count manifests for a feedlot"""
        return db.manifests.count_documents({'feedlot_id': ObjectId(feedlot_id)})
    
    @staticmethod
    def delete_manifest(manifest_id):
        """Delete a manifest"""
        db.manifests.delete_one({'_id': ObjectId(manifest_id)})
    
    @staticmethod
    def find_recent(feedlot_id, limit=10):
        """Find recent manifests for a feedlot"""
        return Manifest.find_by_feedlot(feedlot_id, limit=limit)

