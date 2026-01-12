"""
Breadcrumbs utility for generating navigation breadcrumbs based on current route
Uses Flask's routing system (request.endpoint and request.view_args) for reliable route detection
"""
from flask import request, url_for
from app.models.feedlot import Feedlot
from app.models.pen import Pen
from app.models.batch import Batch
from app.models.cattle import Cattle
from bson import ObjectId


def get_feedlot_name(feedlot_id, current_feedlot=None):
    """Get feedlot name, preferring current_feedlot if available"""
    if current_feedlot and str(current_feedlot.get('_id')) == str(feedlot_id):
        return current_feedlot.get('name', 'Feedlot')
    try:
        feedlot = Feedlot.find_by_id(feedlot_id)
        return feedlot.get('name', 'Feedlot') if feedlot else 'Feedlot'
    except Exception:
        return 'Feedlot'


def get_pen_label(pen_id):
    """Get pen label for breadcrumb"""
    try:
        pen = Pen.find_by_id(pen_id)
        if pen:
            pen_number = pen.get('pen_number', pen_id)
            return f"Pen {pen_number}"
        return 'Pen'
    except Exception:
        return 'Pen'


def get_batch_label(batch_id):
    """Get batch label for breadcrumb"""
    try:
        batch = Batch.find_by_id(batch_id)
        if batch:
            batch_number = batch.get('batch_number', batch_id)
            return f"Batch {batch_number}"
        return 'Batch'
    except Exception:
        return 'Batch'


def get_cattle_label(cattle_id):
    """Get cattle label for breadcrumb"""
    try:
        cattle = Cattle.find_by_id(cattle_id)
        if cattle:
            cattle_id_value = cattle.get('cattle_id', cattle_id)
            return f"Cattle {cattle_id_value}"
        return 'Cattle'
    except Exception:
        return 'Cattle'


def get_template_label(template_id):
    """Get manifest template label for breadcrumb"""
    try:
        template = ManifestTemplate.find_by_id(template_id)
        if template:
            return template.get('name', 'Template')
        return 'Template'
    except Exception:
        return 'Template'


# Breadcrumb configuration mapping endpoints to breadcrumb definitions
# Each breadcrumb item can have:
# - 'label': Static label or callable that takes (view_args, current_feedlot) and returns label
# - 'url_endpoint': Flask endpoint name (None for current page)
# - 'url_kwargs': Dict of URL parameters or callable that returns dict
BREADCRUMB_CONFIG = {
    # Top-level routes
    'top_level.dashboard': [
        {'label': 'Dashboard', 'url_endpoint': None}
    ],
    'top_level.feedlot_hub': [
        {'label': 'Your Feedlots', 'url_endpoint': None}
    ],
    'top_level.view_feedlot': [
        {'label': 'Your Feedlots', 'url_endpoint': 'top_level.feedlot_hub'},
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 'url_endpoint': None}
    ],
    'top_level.edit_feedlot': [
        {'label': 'Your Feedlots', 'url_endpoint': 'top_level.feedlot_hub'},
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Edit', 'url_endpoint': None}
    ],
    'top_level.feedlot_branding': [
        {'label': 'Your Feedlots', 'url_endpoint': 'top_level.feedlot_hub'},
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Branding', 'url_endpoint': None}
    ],
    'top_level.feedlot_users': [
        {'label': 'Your Feedlots', 'url_endpoint': 'top_level.feedlot_hub'},
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Users', 'url_endpoint': None}
    ],
    'top_level.manage_users': [
        {'label': 'Users', 'url_endpoint': None}
    ],
    'top_level.edit_user': [
        {'label': 'Users', 'url_endpoint': 'top_level.manage_users'},
        {'label': 'Edit User', 'url_endpoint': None}
    ],
    'top_level.settings': [
        {'label': 'Settings', 'url_endpoint': None}
    ],
    'top_level.api_keys': [
        {'label': 'Settings', 'url_endpoint': 'top_level.settings'},
        {'label': 'API Keys', 'url_endpoint': None}
    ],
    
    # Feedlot-level routes
    'feedlot.dashboard': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 'url_endpoint': None}
    ],
    
    # Pen routes
    'feedlot.list_pens': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Pens', 'url_endpoint': None}
    ],
    'feedlot.create_pen': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Pens', 'url_endpoint': 'feedlot.list_pens', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Create', 'url_endpoint': None}
    ],
    'feedlot.view_pen': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Pens', 'url_endpoint': 'feedlot.list_pens', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_pen_label(view_args.get('pen_id')), 'url_endpoint': None}
    ],
    'feedlot.edit_pen': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Pens', 'url_endpoint': 'feedlot.list_pens', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_pen_label(view_args.get('pen_id')), 
         'url_endpoint': 'feedlot.view_pen', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id'), 'pen_id': view_args.get('pen_id')}},
        {'label': 'Edit', 'url_endpoint': None}
    ],
    'feedlot.map_pens': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Pens', 'url_endpoint': 'feedlot.list_pens', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Map', 'url_endpoint': None}
    ],
    'feedlot.view_pen_map': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Pens', 'url_endpoint': 'feedlot.list_pens', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Map', 'url_endpoint': 'feedlot.map_pens', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Map View', 'url_endpoint': None}
    ],
    
    # Batch routes
    'feedlot.list_batches': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Batches', 'url_endpoint': None}
    ],
    'feedlot.create_batch': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Batches', 'url_endpoint': 'feedlot.list_batches', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Create', 'url_endpoint': None}
    ],
    'feedlot.view_batch': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Batches', 'url_endpoint': 'feedlot.list_batches', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_batch_label(view_args.get('batch_id')), 'url_endpoint': None}
    ],
    'feedlot.edit_batch': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Batches', 'url_endpoint': 'feedlot.list_batches', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_batch_label(view_args.get('batch_id')), 
         'url_endpoint': 'feedlot.view_batch', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id'), 'batch_id': view_args.get('batch_id')}},
        {'label': 'Edit', 'url_endpoint': None}
    ],
    
    # Cattle routes
    'feedlot.list_cattle': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Cattle', 'url_endpoint': None}
    ],
    'feedlot.create_cattle': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Cattle', 'url_endpoint': 'feedlot.list_cattle', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Create', 'url_endpoint': None}
    ],
    'feedlot.view_cattle': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Cattle', 'url_endpoint': 'feedlot.list_cattle', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_cattle_label(view_args.get('cattle_id')), 'url_endpoint': None}
    ],
    'feedlot.move_cattle': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Cattle', 'url_endpoint': 'feedlot.list_cattle', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_cattle_label(view_args.get('cattle_id')), 
         'url_endpoint': 'feedlot.view_cattle', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id'), 'cattle_id': view_args.get('cattle_id')}},
        {'label': 'Move', 'url_endpoint': None}
    ],
    'feedlot.add_weight_record': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Cattle', 'url_endpoint': 'feedlot.list_cattle', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_cattle_label(view_args.get('cattle_id')), 
         'url_endpoint': 'feedlot.view_cattle', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id'), 'cattle_id': view_args.get('cattle_id')}},
        {'label': 'Add Weight', 'url_endpoint': None}
    ],
    'feedlot.add_note': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Cattle', 'url_endpoint': 'feedlot.list_cattle', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_cattle_label(view_args.get('cattle_id')), 
         'url_endpoint': 'feedlot.view_cattle', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id'), 'cattle_id': view_args.get('cattle_id')}},
        {'label': 'Add Note', 'url_endpoint': None}
    ],
    'feedlot.update_tags': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Cattle', 'url_endpoint': 'feedlot.list_cattle', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': lambda view_args, current_feedlot: get_cattle_label(view_args.get('cattle_id')), 
         'url_endpoint': 'feedlot.view_cattle', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id'), 'cattle_id': view_args.get('cattle_id')}},
        {'label': 'Update Tags', 'url_endpoint': None}
    ],
    
    # Manifest routes
    'feedlot.export_manifest': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Manifest', 'url_endpoint': None},
        {'label': 'Export', 'url_endpoint': None}
    ],
    'feedlot.list_manifest_templates': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Manifest', 'url_endpoint': None},
        {'label': 'Templates', 'url_endpoint': None}
    ],
    'feedlot.create_manifest_template': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Manifest', 'url_endpoint': None},
        {'label': 'Templates', 'url_endpoint': 'feedlot.list_manifest_templates', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Create', 'url_endpoint': None}
    ],
    'feedlot.edit_manifest_template': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Manifest', 'url_endpoint': None},
        {'label': 'Templates', 'url_endpoint': 'feedlot.list_manifest_templates', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Edit Template', 'url_endpoint': None}
    ],
    'feedlot.list_manifest_history': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Manifest', 'url_endpoint': None},
        {'label': 'History', 'url_endpoint': None}
    ],
    'feedlot.view_manifest_history': [
        {'label': lambda view_args, current_feedlot: get_feedlot_name(view_args.get('feedlot_id'), current_feedlot), 
         'url_endpoint': 'feedlot.dashboard', 
         'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'Manifest', 'url_endpoint': None},
        {'label': 'History', 'url_endpoint': 'feedlot.list_manifest_history', 'url_kwargs': lambda view_args: {'feedlot_id': view_args.get('feedlot_id')}},
        {'label': 'View', 'url_endpoint': None}
    ],
}


def generate_breadcrumbs(current_feedlot=None, request_obj=None):
    """
    Generate breadcrumbs based on the current route using Flask's routing system
    
    Args:
        current_feedlot: Feedlot object if in feedlot context
        request_obj: Flask request object (optional, defaults to request)
        
    Returns:
        List of breadcrumb items, each with 'label' and 'url' keys
    """
    if request_obj is None:
        request_obj = request
    
    # Get the current endpoint and view arguments
    endpoint = request_obj.endpoint
    view_args = request_obj.view_args or {}
    
    # If no endpoint or endpoint not in config, return empty list
    if not endpoint or endpoint not in BREADCRUMB_CONFIG:
        return []
    
    # Get breadcrumb configuration for this endpoint
    breadcrumb_defs = BREADCRUMB_CONFIG[endpoint]
    breadcrumbs = []
    
    # Process each breadcrumb definition
    for def_item in breadcrumb_defs:
        # Resolve label (can be string or callable)
        if callable(def_item.get('label')):
            label = def_item['label'](view_args, current_feedlot)
        else:
            label = def_item.get('label', '')
        
        # Resolve URL
        url = None
        url_endpoint = def_item.get('url_endpoint')
        if url_endpoint:
            # Resolve URL kwargs (can be dict or callable)
            url_kwargs = def_item.get('url_kwargs', {})
            if callable(url_kwargs):
                url_kwargs = url_kwargs(view_args)
            elif not isinstance(url_kwargs, dict):
                url_kwargs = {}
            
            # Convert ObjectId values to strings for URL generation
            processed_kwargs = {}
            for key, value in url_kwargs.items():
                if isinstance(value, ObjectId):
                    processed_kwargs[key] = str(value)
                else:
                    processed_kwargs[key] = value
            
            try:
                url = url_for(url_endpoint, **processed_kwargs)
            except Exception:
                # If URL generation fails, set url to None
                url = None
        
        breadcrumbs.append({
            'label': label,
            'url': url
        })
    
    return breadcrumbs
