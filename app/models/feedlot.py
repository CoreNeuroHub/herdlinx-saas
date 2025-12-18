from datetime import datetime
from bson import ObjectId
from app import db, get_feedlot_db

class Feedlot:
    @staticmethod
    def get_database_name(feedlot_code):
        """Generate database name for a feedlot
        
        Args:
            feedlot_code: The feedlot code
        
        Returns:
            Database name string (feedlot_{feedlot_code})
        """
        if not feedlot_code:
            raise ValueError("feedlot_code is required")
        return f"feedlot_{feedlot_code.lower().strip()}"
    
    @staticmethod
    def get_feedlot_code_from_id(feedlot_id):
        """Get feedlot_code from feedlot_id
        
        Args:
            feedlot_id: The feedlot ID
        
        Returns:
            feedlot_code string or None if not found
        """
        feedlot = Feedlot.find_by_id(feedlot_id)
        if feedlot:
            return feedlot.get('feedlot_code')
        return None
    
    @staticmethod
    def initialize_feedlot_database(feedlot_code):
        """Initialize a feedlot-specific database with collections and indexes
        
        Args:
            feedlot_code: The feedlot code
        
        Returns:
            Database instance
        """
        if not feedlot_code:
            raise ValueError("feedlot_code is required")
        
        # Get feedlot database
        feedlot_db = get_feedlot_db(feedlot_code)
        
        # Initialize collections and indexes
        # Pens collection
        feedlot_db.pens.create_index('feedlot_id')
        feedlot_db.pens.create_index([('feedlot_id', 1), ('pen_number', 1)], unique=True)
        
        # Batches collection
        feedlot_db.batches.create_index('feedlot_id')
        feedlot_db.batches.create_index([('feedlot_id', 1), ('batch_number', 1)], unique=True)
        
        # Cattle collection
        feedlot_db.cattle.create_index('feedlot_id')
        feedlot_db.cattle.create_index('batch_id')
        feedlot_db.cattle.create_index('pen_id')
        feedlot_db.cattle.create_index([('feedlot_id', 1), ('cattle_id', 1)], unique=True)
        
        # Manifest templates collection
        feedlot_db.manifest_templates.create_index('feedlot_id')
        feedlot_db.manifest_templates.create_index([('feedlot_id', 1), ('is_default', 1)])
        
        # Manifests collection
        feedlot_db.manifests.create_index('feedlot_id')
        feedlot_db.manifests.create_index([('feedlot_id', 1), ('created_at', -1)])
        feedlot_db.manifests.create_index('created_at')
        
        return feedlot_db
    @staticmethod
    def create_feedlot(name, location, feedlot_code, contact_info=None, owner_id=None, land_description=None, premises_id=None):
        """Create a new feedlot
        
        Args:
            name: Feedlot name
            location: Feedlot location
            feedlot_code: Unique feedlot code for office app integration (required, unique, case-insensitive)
            contact_info: Contact information dictionary
            owner_id: Optional owner user ID (must be business_owner type)
            land_description: Land description
            premises_id: Premises Identification (PID) number
        """
        # Validate feedlot_code uniqueness (case-insensitive)
        if feedlot_code:
            existing = Feedlot.find_by_code(feedlot_code)
            if existing:
                raise ValueError(f"Feedlot code '{feedlot_code}' already exists.")
        
        feedlot_data = {
            'name': name,
            'location': location,
            'feedlot_code': feedlot_code.lower().strip() if feedlot_code else None,
            'contact_info': contact_info or {},
            'land_description': land_description or None,
            'premises_id': premises_id or None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        if owner_id:
            feedlot_data['owner_id'] = ObjectId(owner_id)
        
        result = db.feedlots.insert_one(feedlot_data)
        feedlot_id = str(result.inserted_id)
        
        # Initialize feedlot-specific database
        try:
            Feedlot.initialize_feedlot_database(feedlot_code.lower().strip())
        except Exception as e:
            # Log error but don't fail feedlot creation
            print(f"Warning: Failed to initialize feedlot database for {feedlot_code}: {e}")
        
        return feedlot_id
    
    @staticmethod
    def find_by_id(feedlot_id, include_deleted=False):
        """Find feedlot by ID
        
        Args:
            feedlot_id: The feedlot ID
            include_deleted: If True, include soft-deleted feedlots. Defaults to False.
        """
        query = {'_id': ObjectId(feedlot_id)}
        if not include_deleted:
            query['deleted_at'] = None
        return db.feedlots.find_one(query)
    
    @staticmethod
    def find_all(include_deleted=False):
        """Find all feedlots
        
        Args:
            include_deleted: If True, include soft-deleted feedlots. Defaults to False.
        """
        query = {}
        if not include_deleted:
            query['deleted_at'] = None
        return list(db.feedlots.find(query))
    
    @staticmethod
    def find_by_ids(feedlot_ids, include_deleted=False):
        """Find feedlots by a list of IDs
        
        Args:
            feedlot_ids: List of feedlot IDs
            include_deleted: If True, include soft-deleted feedlots. Defaults to False.
        """
        if not feedlot_ids:
            return []
        query = {'_id': {'$in': feedlot_ids}}
        if not include_deleted:
            query['deleted_at'] = None
        return db.feedlots.find(query)
    
    @staticmethod
    def find_by_code(feedlot_code, include_deleted=False):
        """Find feedlot by feedlot_code (case-insensitive)
        
        Args:
            feedlot_code: The feedlot code
            include_deleted: If True, include soft-deleted feedlots. Defaults to False.
        """
        if not feedlot_code:
            return None
        query = {'feedlot_code': feedlot_code.lower().strip()}
        if not include_deleted:
            query['deleted_at'] = None
        return db.feedlots.find_one(query)
    
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
        # Get feedlot_code from feedlot_id
        feedlot_code = Feedlot.get_feedlot_code_from_id(feedlot_id)
        if not feedlot_code:
            return {
                'total_pens': 0,
                'total_cattle': 0,
                'total_batches': 0,
                'cattle_by_pen': 0
            }
        
        # Get feedlot-specific database
        feedlot_db = get_feedlot_db(feedlot_code)
        feedlot_id_obj = ObjectId(feedlot_id)
        
        # Pens are stored in the master database, use Pen model to query correctly
        from app.models.pen import Pen
        pens = Pen.find_by_feedlot(feedlot_id)
        total_pens = len(pens)
        
        total_cattle = feedlot_db.cattle.count_documents({'feedlot_id': feedlot_id_obj, 'deleted_at': None})
        total_batches = feedlot_db.batches.count_documents({'feedlot_id': feedlot_id_obj, 'deleted_at': None})
        
        # Get cattle in each pen
        pipeline = [
            {'$match': {'feedlot_id': feedlot_id_obj, 'deleted_at': None}},
            {'$group': {
                '_id': '$pen_id',
                'count': {'$sum': 1}
            }}
        ]
        cattle_by_pen = list(feedlot_db.cattle.aggregate(pipeline))
        
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
    
    @staticmethod
    def get_owner(feedlot_id):
        """Get the owner user for a feedlot"""
        from app.models.user import User
        feedlot = Feedlot.find_by_id(feedlot_id)
        if feedlot and feedlot.get('owner_id'):
            return User.find_by_id(str(feedlot['owner_id']))
        return None
    
    @staticmethod
    def update_branding(feedlot_id, branding_data):
        """Update branding configuration for a feedlot
        
        Args:
            feedlot_id: Feedlot ID
            branding_data: Dictionary containing branding fields:
                - logo_path: Path to logo file
                - favicon_path: Path to favicon file
                - primary_color: Hex color code
                - secondary_color: Hex color code
                - company_name: Custom company name
        """
        update_data = {
            'branding': branding_data,
            'updated_at': datetime.utcnow()
        }
        db.feedlots.update_one(
            {'_id': ObjectId(feedlot_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def get_branding(feedlot_id):
        """Retrieve branding configuration for a feedlot"""
        feedlot = Feedlot.find_by_id(feedlot_id)
        if feedlot and feedlot.get('branding'):
            return feedlot['branding']
        return None
    
    @staticmethod
    def delete_branding_assets(feedlot_id, asset_type=None):
        """Delete branding asset files
        
        Args:
            feedlot_id: Feedlot ID
            asset_type: 'logo', 'favicon', or None to delete all
        """
        import os
        from flask import current_app
        
        feedlot = Feedlot.find_by_id(feedlot_id)
        if not feedlot or not feedlot.get('branding'):
            return
        
        branding = feedlot['branding']
        static_folder = current_app.static_folder
        
        if asset_type is None or asset_type == 'logo':
            logo_path = branding.get('logo_path')
            if logo_path:
                # Remove /static/ prefix if present
                if logo_path.startswith('/static/'):
                    logo_path = logo_path[8:]
                elif logo_path.startswith('static/'):
                    logo_path = logo_path[7:]
                
                full_path = os.path.join(static_folder, logo_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception:
                        pass  # Ignore errors during cleanup
        
        if asset_type is None or asset_type == 'favicon':
            favicon_path = branding.get('favicon_path')
            if favicon_path:
                # Remove /static/ prefix if present
                if favicon_path.startswith('/static/'):
                    favicon_path = favicon_path[8:]
                elif favicon_path.startswith('static/'):
                    favicon_path = favicon_path[7:]
                
                full_path = os.path.join(static_folder, favicon_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception:
                        pass  # Ignore errors during cleanup
    
    @staticmethod
    def delete_feedlot(feedlot_id):
        """Soft delete a feedlot (marks as deleted but doesn't remove from database)
        
        Args:
            feedlot_id: The feedlot ID
        """
        db.feedlots.update_one(
            {'_id': ObjectId(feedlot_id)},
            {'$set': {
                'deleted_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def update_last_api_sync(feedlot_id):
        """Update the last_api_sync_at timestamp for a feedlot
        
        Called when API calls modify data for this feedlot, allowing
        the frontend to detect changes and refresh the UI.
        
        Args:
            feedlot_id: The feedlot ID
        """
        db.feedlots.update_one(
            {'_id': ObjectId(feedlot_id)},
            {'$set': {
                'last_api_sync_at': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def get_last_api_sync(feedlot_id):
        """Get the last_api_sync_at timestamp for a feedlot
        
        Args:
            feedlot_id: The feedlot ID
        
        Returns:
            datetime or None if never synced
        """
        feedlot = Feedlot.find_by_id(feedlot_id)
        if feedlot:
            return feedlot.get('last_api_sync_at')
        return None

