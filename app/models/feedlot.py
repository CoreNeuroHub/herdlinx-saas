from datetime import datetime
from bson import ObjectId
from app import db

class Feedlot:
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
            'feedlot_code': feedlot_code.upper().strip() if feedlot_code else None,
            'contact_info': contact_info or {},
            'land_description': land_description or None,
            'premises_id': premises_id or None,
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

