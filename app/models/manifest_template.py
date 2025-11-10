from datetime import datetime
from bson import ObjectId
from app import db

class ManifestTemplate:
    @staticmethod
    def create_template(feedlot_id, name, owner_name=None, owner_phone=None, owner_address=None,
                       dealer_name=None, dealer_phone=None, dealer_address=None,
                       default_destination_name=None, default_destination_address=None,
                       default_transporter_name=None, default_transporter_phone=None, default_transporter_trailer=None,
                       default_purpose=None, default_premises_id_before=None, default_premises_id_destination=None,
                       is_default=False):
        """Create a new manifest template"""
        template_data = {
            'feedlot_id': ObjectId(feedlot_id),
            'name': name,
            'owner_name': owner_name or '',
            'owner_phone': owner_phone or '',
            'owner_address': owner_address or '',
            'dealer_name': dealer_name or '',
            'dealer_phone': dealer_phone or '',
            'dealer_address': dealer_address or '',
            'default_destination_name': default_destination_name or '',
            'default_destination_address': default_destination_address or '',
            'default_transporter_name': default_transporter_name or '',
            'default_transporter_phone': default_transporter_phone or '',
            'default_transporter_trailer': default_transporter_trailer or '',
            'default_purpose': default_purpose or 'transport_only',
            'default_premises_id_before': default_premises_id_before or '',
            'default_premises_id_destination': default_premises_id_destination or '',
            'is_default': is_default,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # If this is set as default, unset other defaults for this feedlot
        if is_default:
            db.manifest_templates.update_many(
                {'feedlot_id': ObjectId(feedlot_id), 'is_default': True},
                {'$set': {'is_default': False}}
            )
        
        result = db.manifest_templates.insert_one(template_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(template_id):
        """Find template by ID"""
        return db.manifest_templates.find_one({'_id': ObjectId(template_id)})
    
    @staticmethod
    def find_by_feedlot(feedlot_id):
        """Find all templates for a feedlot"""
        return list(db.manifest_templates.find({'feedlot_id': ObjectId(feedlot_id)}).sort('is_default', -1))
    
    @staticmethod
    def find_default(feedlot_id):
        """Find the default template for a feedlot"""
        return db.manifest_templates.find_one({
            'feedlot_id': ObjectId(feedlot_id),
            'is_default': True
        })
    
    @staticmethod
    def update_template(template_id, update_data):
        """Update template information"""
        update_data['updated_at'] = datetime.utcnow()
        
        # If setting as default, unset other defaults
        if update_data.get('is_default'):
            template = ManifestTemplate.find_by_id(template_id)
            if template:
                db.manifest_templates.update_many(
                    {'feedlot_id': template['feedlot_id'], 'is_default': True, '_id': {'$ne': ObjectId(template_id)}},
                    {'$set': {'is_default': False}}
                )
        
        db.manifest_templates.update_one(
            {'_id': ObjectId(template_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete_template(template_id):
        """Delete a template"""
        db.manifest_templates.delete_one({'_id': ObjectId(template_id)})
    
    @staticmethod
    def set_as_default(template_id):
        """Set a template as the default for its feedlot"""
        template = ManifestTemplate.find_by_id(template_id)
        if template:
            # Unset other defaults
            db.manifest_templates.update_many(
                {'feedlot_id': template['feedlot_id'], 'is_default': True, '_id': {'$ne': ObjectId(template_id)}},
                {'$set': {'is_default': False}}
            )
            # Set this one as default
            db.manifest_templates.update_one(
                {'_id': ObjectId(template_id)},
                {'$set': {'is_default': True, 'updated_at': datetime.utcnow()}}
            )

