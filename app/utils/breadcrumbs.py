"""
Breadcrumbs utility for generating navigation breadcrumbs based on current route
"""
from flask import request, url_for
from app.models.feedlot import Feedlot
from app.models.pen import Pen
from app.models.batch import Batch
from app.models.cattle import Cattle
from bson import ObjectId


def generate_breadcrumbs(current_feedlot=None, request_obj=None):
    """
    Generate breadcrumbs based on the current route
    
    Args:
        current_feedlot: Feedlot object if in feedlot context
        request_obj: Flask request object (optional, defaults to request)
        
    Returns:
        List of breadcrumb items, each with 'label' and 'url' keys
    """
    if request_obj is None:
        request_obj = request
    
    breadcrumbs = []
    path = request_obj.path
    
    # Determine home URL based on context
    if current_feedlot:
        # Feedlot context - home is feedlot dashboard
        feedlot_id = str(current_feedlot['_id']) if isinstance(current_feedlot.get('_id'), ObjectId) else current_feedlot.get('_id')
        breadcrumbs.append({
            'label': 'Home',
            'url': url_for('feedlot.dashboard', feedlot_id=feedlot_id)
        })
    else:
        # Top-level context - home is top-level dashboard
        breadcrumbs.append({
            'label': 'Home',
            'url': url_for('top_level.dashboard')
        })
    
    # Parse path to determine breadcrumb structure
    path_parts = [p for p in path.split('/') if p]
    
    # Determine if this is a feedlot-level route or top-level route
    # Feedlot-level routes: /feedlot/<id>/dashboard, /feedlot/<id>/pens, /feedlot/<id>/batches, /feedlot/<id>/cattle, /feedlot/<id>/manifest
    # Top-level routes: /feedlot/<id>/view, /feedlot/<id>/edit, /feedlot/<id>/users, /dashboard, /feedlot-hub, /settings, /users
    
    is_feedlot_level_route = False
    if len(path_parts) >= 3 and path_parts[0] == 'feedlot':
        feedlot_route_type = path_parts[2] if len(path_parts) > 2 else None
        if feedlot_route_type in ['dashboard', 'pens', 'batches', 'cattle', 'manifest']:
            is_feedlot_level_route = True
    
    # Top-level routes
    if not is_feedlot_level_route:
        # Top-level routes
        if 'dashboard' in path and 'feedlot' not in path:
            breadcrumbs.append({'label': 'Dashboard', 'url': None})
        elif 'feedlot-hub' in path:
            breadcrumbs.append({'label': 'Feedlot Hub', 'url': None})
        elif 'feedlot' in path and 'view' in path:
            breadcrumbs.append({'label': 'Feedlot Hub', 'url': url_for('top_level.feedlot_hub')})
            feedlot_id = path_parts[path_parts.index('feedlot') + 1] if 'feedlot' in path_parts else None
            if feedlot_id:
                try:
                    feedlot = Feedlot.find_by_id(feedlot_id) if feedlot_id else None
                    label = feedlot.get('name', 'Feedlot') if feedlot else 'Feedlot'
                except Exception:
                    label = 'Feedlot'
                breadcrumbs.append({'label': label, 'url': None})
        elif 'feedlot' in path and 'edit' in path:
            breadcrumbs.append({'label': 'Feedlot Hub', 'url': url_for('top_level.feedlot_hub')})
            feedlot_id = path_parts[path_parts.index('feedlot') + 1] if 'feedlot' in path_parts else None
            if feedlot_id:
                try:
                    feedlot = Feedlot.find_by_id(feedlot_id) if feedlot_id else None
                    label = feedlot.get('name', 'Feedlot') if feedlot else 'Feedlot'
                except Exception:
                    label = 'Feedlot'
                breadcrumbs.append({'label': label, 'url': url_for('top_level.view_feedlot', feedlot_id=feedlot_id)})
                breadcrumbs.append({'label': 'Edit', 'url': None})
        elif 'feedlot' in path and 'users' in path:
            breadcrumbs.append({'label': 'Feedlot Hub', 'url': url_for('top_level.feedlot_hub')})
            feedlot_id = path_parts[path_parts.index('feedlot') + 1] if 'feedlot' in path_parts else None
            if feedlot_id:
                try:
                    feedlot = Feedlot.find_by_id(feedlot_id) if feedlot_id else None
                    label = feedlot.get('name', 'Feedlot') if feedlot else 'Feedlot'
                except Exception:
                    label = 'Feedlot'
                breadcrumbs.append({'label': label, 'url': url_for('top_level.view_feedlot', feedlot_id=feedlot_id)})
                breadcrumbs.append({'label': 'Users', 'url': None})
        elif 'users' in path and 'manage' not in path:
            breadcrumbs.append({'label': 'Users', 'url': None})
        elif 'users' in path:
            breadcrumbs.append({'label': 'Manage Users', 'url': None})
        elif 'settings' in path:
            breadcrumbs.append({'label': 'Settings', 'url': None})
            if 'api-keys' in path:
                breadcrumbs.append({'label': 'API Keys', 'url': None})
    
    # Feedlot-level routes
    elif is_feedlot_level_route:
        feedlot_id = path_parts[1]
        
        # Add feedlot name
        if current_feedlot:
            feedlot_name = current_feedlot.get('name', 'Feedlot')
        else:
            try:
                feedlot = Feedlot.find_by_id(feedlot_id)
                feedlot_name = feedlot.get('name', 'Feedlot') if feedlot else 'Feedlot'
            except Exception:
                feedlot_name = 'Feedlot'
        
        breadcrumbs.append({
            'label': feedlot_name,
            'url': url_for('feedlot.dashboard', feedlot_id=feedlot_id)
        })
        
        # Parse feedlot routes
        if 'dashboard' in path:
            breadcrumbs.append({'label': 'Dashboard', 'url': None})
        elif 'pens' in path:
            breadcrumbs.append({'label': 'Pens', 'url': url_for('feedlot.list_pens', feedlot_id=feedlot_id)})
            
            if 'create' in path:
                breadcrumbs.append({'label': 'Create', 'url': None})
            elif 'view' in path:
                pen_id = path_parts[path_parts.index('pens') + 1] if 'pens' in path_parts and len(path_parts) > path_parts.index('pens') + 1 else None
                if pen_id:
                    try:
                        pen = Pen.find_by_id(pen_id)
                        pen_label = f"Pen {pen.get('pen_number', pen_id)}" if pen else 'Pen'
                    except Exception:
                        pen_label = 'Pen'
                    breadcrumbs.append({'label': pen_label, 'url': None})
            elif 'edit' in path:
                pen_id = path_parts[path_parts.index('pens') + 1] if 'pens' in path_parts and len(path_parts) > path_parts.index('pens') + 1 else None
                if pen_id:
                    try:
                        pen = Pen.find_by_id(pen_id)
                        pen_label = f"Pen {pen.get('pen_number', pen_id)}" if pen else 'Pen'
                    except Exception:
                        pen_label = 'Pen'
                    breadcrumbs.append({'label': pen_label, 'url': url_for('feedlot.view_pen', feedlot_id=feedlot_id, pen_id=pen_id)})
                    breadcrumbs.append({'label': 'Edit', 'url': None})
            elif 'map' in path:
                if 'view' in path:
                    breadcrumbs.append({'label': 'Map View', 'url': None})
                else:
                    breadcrumbs.append({'label': 'Map', 'url': None})
        elif 'batches' in path:
            breadcrumbs.append({'label': 'Batches', 'url': url_for('feedlot.list_batches', feedlot_id=feedlot_id)})
            
            if 'create' in path:
                breadcrumbs.append({'label': 'Create', 'url': None})
            elif 'view' in path:
                batch_id = path_parts[path_parts.index('batches') + 1] if 'batches' in path_parts and len(path_parts) > path_parts.index('batches') + 1 else None
                if batch_id:
                    try:
                        batch = Batch.find_by_id(batch_id)
                        batch_label = f"Batch {batch.get('batch_number', batch_id)}" if batch else 'Batch'
                    except Exception:
                        batch_label = 'Batch'
                    breadcrumbs.append({'label': batch_label, 'url': None})
        elif 'cattle' in path:
            breadcrumbs.append({'label': 'Cattle', 'url': url_for('feedlot.list_cattle', feedlot_id=feedlot_id)})
            
            if 'create' in path:
                breadcrumbs.append({'label': 'Create', 'url': None})
            elif 'view' in path:
                cattle_id = path_parts[path_parts.index('cattle') + 1] if 'cattle' in path_parts and len(path_parts) > path_parts.index('cattle') + 1 else None
                if cattle_id:
                    try:
                        cattle = Cattle.find_by_id(cattle_id)
                        cattle_label = f"Cattle {cattle.get('cattle_id', cattle_id)}" if cattle else 'Cattle'
                    except Exception:
                        cattle_label = 'Cattle'
                    breadcrumbs.append({'label': cattle_label, 'url': None})
            elif 'move' in path:
                cattle_id = path_parts[path_parts.index('cattle') + 1] if 'cattle' in path_parts and len(path_parts) > path_parts.index('cattle') + 1 else None
                if cattle_id:
                    try:
                        cattle = Cattle.find_by_id(cattle_id)
                        cattle_label = f"Cattle {cattle.get('cattle_id', cattle_id)}" if cattle else 'Cattle'
                    except Exception:
                        cattle_label = 'Cattle'
                    breadcrumbs.append({'label': cattle_label, 'url': url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id)})
                    breadcrumbs.append({'label': 'Move', 'url': None})
            elif 'add_weight' in path:
                cattle_id = path_parts[path_parts.index('cattle') + 1] if 'cattle' in path_parts and len(path_parts) > path_parts.index('cattle') + 1 else None
                if cattle_id:
                    try:
                        cattle = Cattle.find_by_id(cattle_id)
                        cattle_label = f"Cattle {cattle.get('cattle_id', cattle_id)}" if cattle else 'Cattle'
                    except Exception:
                        cattle_label = 'Cattle'
                    breadcrumbs.append({'label': cattle_label, 'url': url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id)})
                    breadcrumbs.append({'label': 'Add Weight', 'url': None})
            elif 'update_tags' in path:
                cattle_id = path_parts[path_parts.index('cattle') + 1] if 'cattle' in path_parts and len(path_parts) > path_parts.index('cattle') + 1 else None
                if cattle_id:
                    try:
                        cattle = Cattle.find_by_id(cattle_id)
                        cattle_label = f"Cattle {cattle.get('cattle_id', cattle_id)}" if cattle else 'Cattle'
                    except Exception:
                        cattle_label = 'Cattle'
                    breadcrumbs.append({'label': cattle_label, 'url': url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id)})
                    breadcrumbs.append({'label': 'Update Tags', 'url': None})
        elif 'manifest' in path:
            breadcrumbs.append({'label': 'Manifest', 'url': None})
            
            if 'export' in path:
                breadcrumbs.append({'label': 'Export', 'url': None})
            elif 'history' in path:
                breadcrumbs.append({'label': 'History', 'url': url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id)})
                if 'view' in path:
                    breadcrumbs.append({'label': 'View', 'url': None})
            elif 'templates' in path:
                breadcrumbs.append({'label': 'Templates', 'url': url_for('feedlot.list_manifest_templates', feedlot_id=feedlot_id)})
                if 'create' in path:
                    breadcrumbs.append({'label': 'Create', 'url': None})
                elif 'edit' in path:
                    template_id = path_parts[path_parts.index('templates') + 1] if 'templates' in path_parts and len(path_parts) > path_parts.index('templates') + 1 else None
                    if template_id:
                        breadcrumbs.append({'label': 'Edit Template', 'url': None})
    
    return breadcrumbs

