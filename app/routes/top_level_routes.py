from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from bson import ObjectId
from datetime import datetime
from app.models.feedlot import Feedlot
from app.models.user import User
from app.models.api_key import APIKey
from app.models.pen import Pen
from app.models.batch import Batch
from app.models.cattle import Cattle
from app.models.manifest_template import ManifestTemplate
from app.routes.auth_routes import login_required, super_admin_required, admin_access_required
from app import db
import bcrypt
import re
import os
import uuid
from werkzeug.utils import secure_filename

top_level_bp = Blueprint('top_level', __name__)

def allowed_file(filename):
    """Check if file extension is allowed for branding files"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def can_edit_feedlot(feedlot_id, user_type, user_feedlot_ids):
    """Check if user can edit a feedlot
    
    Args:
        feedlot_id: Feedlot ID to check
        user_type: User type from session
        user_feedlot_ids: List of feedlot IDs user has access to
    
    Returns:
        bool: True if user can edit, False otherwise
    """
    # Super Owner and Super Admin can edit any feedlot
    if user_type in ['super_owner', 'super_admin']:
        return True
    
    # Business Owner can only edit their assigned feedlots
    if user_type == 'business_owner':
        return str(feedlot_id) in [str(fid) for fid in user_feedlot_ids]
    
    return False

@top_level_bp.route('/')
@top_level_bp.route('/dashboard')
@login_required
@admin_access_required
def dashboard():
    """Dashboard showing widgets with feedlot statistics (for super owner/super admin)"""
    from app.models.pen import Pen
    from app.models.batch import Batch
    from app.models.cattle import Cattle
    
    user_type = session.get('user_type')
    
    # Get feedlots for statistics
    if user_type in ['business_owner', 'business_admin']:
        # Filter feedlots to only show assigned ones
        user_feedlot_ids = session.get('feedlot_ids', [])
        if user_feedlot_ids:
            feedlot_object_ids = [ObjectId(fid) for fid in user_feedlot_ids]
            feedlots = list(Feedlot.find_by_ids(feedlot_object_ids))
        else:
            feedlots = []
    else:
        # Super owner and super admin see all feedlots
        feedlots = Feedlot.find_all()
    
    # Calculate aggregate statistics across all feedlots
    total_feedlots = len(feedlots)
    total_pens = 0
    total_cattle = 0
    total_users = 0
    users_per_feedlot = []
    
    if feedlots:
        feedlot_ids = [ObjectId(str(f['_id'])) for f in feedlots]
        
        # Aggregate statistics from each feedlot's database
        for feedlot in feedlots:
            feedlot_id = str(feedlot['_id'])
            stats = Feedlot.get_statistics(feedlot_id)
            total_pens += stats.get('total_pens', 0)
            total_cattle += stats.get('total_cattle', 0)
        
        # Count users associated with these feedlots (users are in master DB)
        user_query = {'$or': [
            {'feedlot_id': {'$in': feedlot_ids}},
            {'feedlot_ids': {'$in': feedlot_ids}}
        ]}
        total_users = db.users.count_documents(user_query)
        
        # Calculate users per feedlot
        for feedlot in feedlots:
            feedlot_id = ObjectId(str(feedlot['_id']))
            feedlot_name = feedlot.get('name', 'Unknown')
            
            # Count users for this feedlot (single feedlot_id or in feedlot_ids array)
            user_count = db.users.count_documents({
                '$or': [
                    {'feedlot_id': feedlot_id},
                    {'feedlot_ids': feedlot_id}
                ]
            })
            
            users_per_feedlot.append({
                'feedlot_name': feedlot_name,
                'user_count': user_count
            })
    
    # Get recent feedlots (last 5)
    recent_feedlots = sorted(feedlots, key=lambda x: x.get('created_at', datetime(1970, 1, 1)), reverse=True)[:5]
    
    dashboard_stats = {
        'total_feedlots': total_feedlots,
        'total_pens': total_pens,
        'total_cattle': total_cattle,
        'total_users': total_users,
        'users_per_feedlot': users_per_feedlot,
        'recent_feedlots': recent_feedlots
    }
    
    # Get user's dashboard preferences
    user_id = session.get('user_id')
    dashboard_preferences = User.get_dashboard_preferences(user_id) if user_id else {}
    
    return render_template('top_level/dashboard.html', 
                         feedlots=feedlots, 
                         user_type=user_type, 
                         dashboard_stats=dashboard_stats,
                         dashboard_preferences=dashboard_preferences)

@top_level_bp.route('/feedlot-hub')
@login_required
@admin_access_required
def feedlot_hub():
    """Your Feedlots page showing all feedlots with search/filter"""
    from app.models.pen import Pen
    from app.models.cattle import Cattle
    
    user_type = session.get('user_type')
    
    if user_type in ['business_owner', 'business_admin']:
        # Filter feedlots to only show assigned ones
        user_feedlot_ids = session.get('feedlot_ids', [])
        if user_feedlot_ids:
            feedlot_object_ids = [ObjectId(fid) for fid in user_feedlot_ids]
            feedlots = list(Feedlot.find_by_ids(feedlot_object_ids))
        else:
            feedlots = []
    else:
        # Super owner and super admin see all feedlots
        feedlots = Feedlot.find_all()
    
    # Enrich feedlots with statistics and owner information
    enriched_feedlots = []
    for feedlot in feedlots:
        feedlot_id = str(feedlot['_id'])
        
        # Get statistics for this feedlot (uses feedlot-specific database)
        stats = Feedlot.get_statistics(feedlot_id)
        
        # Get owner information
        owner = Feedlot.get_owner(feedlot_id)
        
        # Create enriched feedlot dict
        enriched_feedlot = dict(feedlot)
        enriched_feedlot['total_pens'] = stats.get('total_pens', 0)
        enriched_feedlot['total_cattle'] = stats.get('total_cattle', 0)
        enriched_feedlot['owner'] = owner
        
        enriched_feedlots.append(enriched_feedlot)
    
    # Get unique locations for filter dropdown
    unique_locations = sorted(list(set([f.get('location', '') for f in enriched_feedlots if f.get('location')])))
    
    user_type = session.get('user_type')
    return render_template('top_level/feedlot_hub.html', feedlots=enriched_feedlots, user_type=user_type, unique_locations=unique_locations)

@top_level_bp.route('/feedlot/create', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_feedlot():
    """Create a new feedlot"""
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            name = request.form.get('name')
            location = request.form.get('location')
            feedlot_code = request.form.get('feedlot_code', '').strip()
            land_description = request.form.get('land_description', '').strip() or None
            premises_id = request.form.get('premises_id', '').strip() or None
            contact_info = {
                'phone': request.form.get('phone') or None,
                'email': request.form.get('email') or None,
                'contact_person': request.form.get('contact_person') or None
            }
            
            # Validate required fields
            if not name or not location or not feedlot_code:
                error_msg = 'Feedlot name, location, and feedlot code are required.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                if not is_ajax:
                    return redirect(url_for('top_level.dashboard'))
                return jsonify({'success': False, 'message': error_msg}), 400
            
            feedlot_id = Feedlot.create_feedlot(name, location, feedlot_code, contact_info, None, land_description, premises_id)
            
            success_msg = 'Feedlot created successfully.'
            if is_ajax:
                return jsonify({'success': True, 'message': success_msg}), 200
            flash(success_msg, 'success')
            return redirect(url_for('top_level.dashboard'))
        
        except Exception as e:
            error_msg = f'Failed to create feedlot: {str(e)}'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 500
            flash(error_msg, 'error')
            if not is_ajax:
                return redirect(url_for('top_level.dashboard'))
            return jsonify({'success': False, 'message': error_msg}), 500
    
    # GET request - redirect to dashboard since we're using a modal now
    return redirect(url_for('top_level.dashboard'))

@top_level_bp.route('/feedlot/create-wizard', methods=['POST'])
@login_required
@super_admin_required
def create_feedlot_wizard():
    """Create a new feedlot using the multi-step wizard
    
    Accepts JSON payload with:
    - feedlot: {name, location, feedlot_code, land_description, premises_id}
    - users: [{username, email, password, user_type}, ...]
    - branding: {logo_base64, favicon_base64, primary_color, secondary_color, company_name, use_default}
    - generate_api_key: boolean
    - api_key_description: optional string
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body must be JSON'}), 400
        
        # Extract feedlot data
        feedlot_data = data.get('feedlot', {})
        name = feedlot_data.get('name', '').strip()
        location = feedlot_data.get('location', '').strip()
        feedlot_code = feedlot_data.get('feedlot_code', '').strip()
        land_description = feedlot_data.get('land_description', '').strip() or None
        premises_id = feedlot_data.get('premises_id', '').strip() or None
        
        # Validate required fields
        if not name or not location or not feedlot_code:
            return jsonify({'success': False, 'message': 'Feedlot name, location, and feedlot code are required.'}), 400
        
        # Validate feedlot_code format
        if not re.match(r'^[a-z0-9_-]+$', feedlot_code.lower()):
            return jsonify({'success': False, 'message': 'Feedlot code must contain only lowercase letters, numbers, hyphens, and underscores.'}), 400
        
        # Check if feedlot_code already exists
        existing = Feedlot.find_by_code(feedlot_code)
        if existing:
            return jsonify({'success': False, 'message': f"Feedlot code '{feedlot_code}' already exists."}), 400
        
        # Step 1: Create the feedlot
        feedlot_id = Feedlot.create_feedlot(
            name=name,
            location=location,
            feedlot_code=feedlot_code,
            contact_info={},  # No contact info in wizard
            owner_id=None,
            land_description=land_description,
            premises_id=premises_id
        )
        
        created_users = []
        owner_id = None
        
        # Step 2: Create users
        users_data = data.get('users', [])
        for user_data in users_data:
            username = user_data.get('username', '').strip()
            email = user_data.get('email', '').strip()
            password = user_data.get('password', '')
            user_type = user_data.get('user_type', 'user')
            
            if not username or not email or not password:
                continue  # Skip invalid users
            
            # Check if username or email already exists
            if User.find_by_username(username):
                continue  # Skip duplicate username
            if User.find_by_email(email):
                continue  # Skip duplicate email
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create user with feedlot assignment
            user_insert_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'user_type': user_type,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Assign feedlot based on user type
            if user_type in ['business_owner', 'business_admin']:
                user_insert_data['feedlot_ids'] = [ObjectId(feedlot_id)]
            else:
                user_insert_data['feedlot_id'] = ObjectId(feedlot_id)
            
            result = db.users.insert_one(user_insert_data)
            created_user_id = str(result.inserted_id)
            
            created_users.append({
                'id': created_user_id,
                'username': username,
                'email': email,
                'user_type': user_type
            })
            
            # Track business owner for feedlot assignment
            if user_type == 'business_owner' and owner_id is None:
                owner_id = created_user_id
        
        # Assign first business owner as feedlot owner
        if owner_id:
            Feedlot.update_feedlot(feedlot_id, {'owner_id': ObjectId(owner_id)})
        
        # Step 3: Handle branding
        branding_data = data.get('branding', {})
        use_default_branding = branding_data.get('use_default', True)
        
        if not use_default_branding:
            branding_update = {}
            
            # Handle logo base64 upload
            logo_base64 = branding_data.get('logo_base64', '').strip()
            if logo_base64:
                logo_path = _save_base64_image(feedlot_id, logo_base64, 'logo')
                if logo_path:
                    branding_update['logo_path'] = logo_path
            
            # Handle favicon base64 upload
            favicon_base64 = branding_data.get('favicon_base64', '').strip()
            if favicon_base64:
                favicon_path = _save_base64_image(feedlot_id, favicon_base64, 'favicon')
                if favicon_path:
                    branding_update['favicon_path'] = favicon_path
            
            # Handle colors
            primary_color = branding_data.get('primary_color', '').strip()
            if primary_color:
                branding_update['primary_color'] = primary_color if primary_color.startswith('#') else f'#{primary_color}'
            else:
                branding_update['primary_color'] = '#2D8B8B'
            
            secondary_color = branding_data.get('secondary_color', '').strip()
            if secondary_color:
                branding_update['secondary_color'] = secondary_color if secondary_color.startswith('#') else f'#{secondary_color}'
            else:
                branding_update['secondary_color'] = '#0A2540'
            
            # Handle company name
            company_name = branding_data.get('company_name', '').strip()
            if company_name:
                branding_update['company_name'] = company_name
            
            if branding_update:
                Feedlot.update_branding(feedlot_id, branding_update)
        
        # Step 4: Generate API key if requested
        api_key_string = None
        generate_api_key = data.get('generate_api_key', False)
        if generate_api_key:
            api_key_description = data.get('api_key_description', '').strip() or None
            api_key_string, api_key_id = APIKey.create_api_key(feedlot_id, api_key_description)
        
        # Build response
        response_data = {
            'success': True,
            'message': 'Feedlot created successfully.',
            'feedlot_id': feedlot_id,
            'feedlot_name': name,
            'feedlot_code': feedlot_code.lower(),
            'users_created': len(created_users),
            'users': created_users
        }
        
        if api_key_string:
            response_data['api_key'] = api_key_string
            response_data['api_key_warning'] = 'Save this API key immediately. It will not be shown again.'
        
        return jsonify(response_data), 200
    
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in create_feedlot_wizard: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to create feedlot: {str(e)}'}), 500

def _save_base64_image(feedlot_id, base64_data, image_type):
    """Helper function to save base64 encoded image
    
    Args:
        feedlot_id: Feedlot ID for filename
        base64_data: Base64 encoded image data (may include data URL prefix)
        image_type: 'logo' or 'favicon'
    
    Returns:
        Relative path to saved file or None if failed
    """
    import base64
    
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            header, base64_data = base64_data.split(',', 1)
            # Extract file extension from header
            if 'png' in header:
                ext = 'png'
            elif 'jpeg' in header or 'jpg' in header:
                ext = 'jpg'
            elif 'gif' in header:
                ext = 'gif'
            elif 'webp' in header:
                ext = 'webp'
            elif 'svg' in header:
                ext = 'svg'
            else:
                ext = 'png'  # Default
        else:
            ext = 'png'  # Default
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Check file size (max 5MB)
        if len(image_data) > 5 * 1024 * 1024:
            return None
        
        # Generate unique filename
        filename = f"{feedlot_id}_{uuid.uuid4().hex[:8]}.{ext}"
        filename = secure_filename(filename)
        
        # Create directory
        if image_type == 'logo':
            target_dir = os.path.join(current_app.static_folder, 'feedlot_branding', 'logos')
            relative_path = f'feedlot_branding/logos/{filename}'
        else:
            target_dir = os.path.join(current_app.static_folder, 'feedlot_branding', 'favicons')
            relative_path = f'feedlot_branding/favicons/{filename}'
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(target_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return relative_path
    
    except Exception as e:
        current_app.logger.error(f"Error saving base64 image: {str(e)}")
        return None

@top_level_bp.route('/feedlot/<feedlot_id>/view')
@login_required
@admin_access_required
def view_feedlot(feedlot_id):
    """View feedlot details - redirects to feedlot dashboard"""
    # Check if business owner or business admin has access to this feedlot
    user_type = session.get('user_type')
    if user_type in ['business_owner', 'business_admin']:
        user_feedlot_ids = [str(fid) for fid in session.get('feedlot_ids', [])]
        if str(feedlot_id) not in user_feedlot_ids:
            flash('Access denied. You do not have access to this feedlot.', 'error')
            return redirect(url_for('top_level.dashboard'))
    
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Redirect to feedlot dashboard instead of showing view page
    return redirect(url_for('feedlot.dashboard', feedlot_id=feedlot_id))

@top_level_bp.route('/feedlot/<feedlot_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_access_required
def edit_feedlot(feedlot_id):
    """Edit feedlot details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Check access control
    user_type = session.get('user_type')
    user_feedlot_ids = session.get('feedlot_ids', [])
    
    if not can_edit_feedlot(feedlot_id, user_type, user_feedlot_ids):
        flash('Access denied. You do not have permission to edit this feedlot.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Get all business owners for the dropdown (only for super admin/owner)
    business_owners = []
    if user_type in ['super_owner', 'super_admin']:
        business_owners = User.find_business_owners()
    
    if request.method == 'POST':
        feedlot_code = request.form.get('feedlot_code', '').strip()
        
        # Validate feedlot_code uniqueness if it's being changed
        if feedlot_code:
            feedlot_code_lower = feedlot_code.lower().strip()
            existing = Feedlot.find_by_code(feedlot_code_lower)
            if existing and str(existing['_id']) != feedlot_id:
                flash(f"Feedlot code '{feedlot_code}' already exists.", 'error')
                return render_template('top_level/edit_feedlot.html', feedlot=feedlot, business_owners=business_owners, user_type=user_type)
        
        update_data = {
            'name': request.form.get('name'),
            'location': request.form.get('location'),
            'feedlot_code': feedlot_code.lower().strip() if feedlot_code else None,
            'land_description': request.form.get('land_description', '').strip() or None,
            'premises_id': request.form.get('premises_id', '').strip() or None,
            'contact_info': {
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'contact_person': request.form.get('contact_person')
            }
        }
        
        # Handle owner assignment (only for super admin/owner)
        if user_type in ['super_owner', 'super_admin']:
            owner_id = request.form.get('owner_id', '').strip()
            if owner_id:
                # Validate that the selected user is a business owner
                owner = User.find_by_id(owner_id)
                if owner and owner.get('user_type') == 'business_owner':
                    update_data['owner_id'] = ObjectId(owner_id)
                else:
                    flash('Selected user must be a business owner.', 'error')
                    return render_template('top_level/edit_feedlot.html', feedlot=feedlot, business_owners=business_owners, user_type=user_type)
            else:
                # If owner_id was cleared (empty), remove the field from database
                db.feedlots.update_one(
                    {'_id': ObjectId(feedlot_id)},
                    {'$unset': {'owner_id': ''}}
                )
        
        # Update feedlot with all fields
        Feedlot.update_feedlot(feedlot_id, update_data)
        
        flash('Feedlot updated successfully.', 'success')
        return redirect(url_for('feedlot.dashboard', feedlot_id=feedlot_id))
    
    return render_template('top_level/edit_feedlot.html', feedlot=feedlot, business_owners=business_owners, user_type=user_type)

@top_level_bp.route('/feedlot/<feedlot_id>/delete', methods=['POST'])
@login_required
@admin_access_required
def delete_feedlot(feedlot_id):
    """Delete a feedlot and all associated data"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Check access control
    user_type = session.get('user_type')
    user_feedlot_ids = session.get('feedlot_ids', [])
    
    if not can_edit_feedlot(feedlot_id, user_type, user_feedlot_ids):
        flash('Access denied. You do not have permission to delete this feedlot.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    try:
        from pymongo import MongoClient
        from config import Config
        
        feedlot_code = feedlot.get('feedlot_code')
        feedlot_name = feedlot.get('name', 'Unknown')
        
        # Drop feedlot-specific database if feedlot_code exists
        if feedlot_code:
            try:
                client = MongoClient(Config.MONGODB_URI)
                normalized_code = feedlot_code.lower().strip()
                db_name = f"feedlot_{normalized_code}"
                client.drop_database(db_name)
            except Exception as e:
                current_app.logger.error(f"Error dropping feedlot database {db_name}: {str(e)}")
        
        # Delete all API keys for this feedlot
        api_keys = APIKey.find_by_feedlot(feedlot_id)
        for api_key in api_keys:
            try:
                APIKey.delete_key(str(api_key['_id']))
            except Exception as e:
                current_app.logger.error(f"Error deleting API key {api_key['_id']}: {str(e)}")
        
        # Delete all pens for this feedlot (pens are in main database)
        pens = Pen.find_by_feedlot(feedlot_id)
        for pen in pens:
            try:
                Pen.delete_pen(str(pen['_id']))
            except Exception as e:
                current_app.logger.error(f"Error deleting pen {pen['_id']}: {str(e)}")
        
        # Remove feedlot_id from users (both single feedlot_id and feedlot_ids array)
        feedlot_object_id = ObjectId(feedlot_id)
        db.users.update_many(
            {'feedlot_id': feedlot_object_id},
            {'$unset': {'feedlot_id': ''}}
        )
        db.users.update_many(
            {'feedlot_ids': feedlot_object_id},
            {'$pull': {'feedlot_ids': feedlot_object_id}}
        )
        
        # Delete branding assets
        Feedlot.delete_branding_assets(feedlot_id)
        
        # Delete the feedlot record
        db.feedlots.delete_one({'_id': ObjectId(feedlot_id)})
        
        flash(f'Feedlot "{feedlot_name}" and all associated data have been deleted successfully.', 'success')
        return redirect(url_for('top_level.dashboard'))
    
    except Exception as e:
        current_app.logger.error(f"Error deleting feedlot {feedlot_id}: {str(e)}")
        flash(f'Failed to delete feedlot: {str(e)}', 'error')
        return redirect(url_for('top_level.edit_feedlot', feedlot_id=feedlot_id))

@top_level_bp.route('/feedlot/<feedlot_id>/branding', methods=['GET', 'POST'])
@login_required
@admin_access_required
def feedlot_branding(feedlot_id):
    """Manage feedlot branding"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Check access control
    user_type = session.get('user_type')
    user_feedlot_ids = session.get('feedlot_ids', [])
    
    if not can_edit_feedlot(feedlot_id, user_type, user_feedlot_ids):
        flash('Access denied. You do not have permission to edit this feedlot.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Get existing branding
    existing_branding = Feedlot.get_branding(feedlot_id) or {}
    
    if request.method == 'POST':
        branding_data = {}
        
        # Handle logo upload
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                if not allowed_file(logo_file.filename):
                    flash('Invalid logo file type. Please upload PNG, JPG, JPEG, GIF, WEBP, or SVG.', 'error')
                    return render_template('top_level/feedlot_branding.html', feedlot=feedlot, branding=existing_branding, user_type=user_type)
                
                # Validate file size (max 5MB)
                logo_file.seek(0, os.SEEK_END)
                file_size = logo_file.tell()
                logo_file.seek(0)
                if file_size > 5 * 1024 * 1024:  # 5MB
                    flash('Logo file size too large. Please upload an image smaller than 5MB.', 'error')
                    return render_template('top_level/feedlot_branding.html', feedlot=feedlot, branding=existing_branding, user_type=user_type)
                
                # Delete old logo if exists
                Feedlot.delete_branding_assets(feedlot_id, 'logo')
                
                # Generate unique filename
                file_ext = logo_file.filename.rsplit('.', 1)[1].lower()
                filename = f"{feedlot_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                filename = secure_filename(filename)
                
                # Create logos directory if it doesn't exist
                logos_dir = os.path.join(current_app.static_folder, 'feedlot_branding', 'logos')
                os.makedirs(logos_dir, exist_ok=True)
                
                # Save logo file
                logo_path = os.path.join(logos_dir, filename)
                logo_file.save(logo_path)
                
                # Store relative path
                branding_data['logo_path'] = f'feedlot_branding/logos/{filename}'
        
        # Handle favicon upload
        if 'favicon' in request.files:
            favicon_file = request.files['favicon']
            if favicon_file and favicon_file.filename:
                if not allowed_file(favicon_file.filename):
                    flash('Invalid favicon file type. Please upload PNG, JPG, JPEG, GIF, WEBP, or SVG.', 'error')
                    return render_template('top_level/feedlot_branding.html', feedlot=feedlot, branding=existing_branding, user_type=user_type)
                
                # Validate file size (max 5MB)
                favicon_file.seek(0, os.SEEK_END)
                file_size = favicon_file.tell()
                favicon_file.seek(0)
                if file_size > 5 * 1024 * 1024:  # 5MB
                    flash('Favicon file size too large. Please upload an image smaller than 5MB.', 'error')
                    return render_template('top_level/feedlot_branding.html', feedlot=feedlot, branding=existing_branding, user_type=user_type)
                
                # Delete old favicon if exists
                Feedlot.delete_branding_assets(feedlot_id, 'favicon')
                
                # Generate unique filename
                file_ext = favicon_file.filename.rsplit('.', 1)[1].lower()
                filename = f"{feedlot_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                filename = secure_filename(filename)
                
                # Create favicons directory if it doesn't exist
                favicons_dir = os.path.join(current_app.static_folder, 'feedlot_branding', 'favicons')
                os.makedirs(favicons_dir, exist_ok=True)
                
                # Save favicon file
                favicon_path = os.path.join(favicons_dir, filename)
                favicon_file.save(favicon_path)
                
                # Store relative path
                branding_data['favicon_path'] = f'feedlot_branding/favicons/{filename}'
        
        # Handle color inputs
        primary_color = request.form.get('primary_color', '').strip()
        if primary_color:
            # Validate hex color format
            if primary_color.startswith('#'):
                branding_data['primary_color'] = primary_color
            else:
                branding_data['primary_color'] = f'#{primary_color}'
        
        secondary_color = request.form.get('secondary_color', '').strip()
        if secondary_color:
            # Validate hex color format
            if secondary_color.startswith('#'):
                branding_data['secondary_color'] = secondary_color
            else:
                branding_data['secondary_color'] = f'#{secondary_color}'
        
        # Handle company name
        company_name = request.form.get('company_name', '').strip()
        if company_name:
            branding_data['company_name'] = company_name
        elif 'company_name' in existing_branding:
            branding_data['company_name'] = existing_branding.get('company_name')
        
        # Merge with existing branding to preserve unchanged fields (especially logo/favicon paths if not updated)
        if existing_branding:
            for key, value in existing_branding.items():
                if key not in branding_data:
                    branding_data[key] = value
        
        # Ensure we have default colors if not set (for new branding or if colors weren't provided)
        if 'primary_color' not in branding_data:
            branding_data['primary_color'] = '#2D8B8B'  # Default teal
        if 'secondary_color' not in branding_data:
            branding_data['secondary_color'] = '#0A2540'  # Default navy
        
        # Update branding
        Feedlot.update_branding(feedlot_id, branding_data)
        
        flash('Branding updated successfully.', 'success')
        return redirect(url_for('top_level.feedlot_branding', feedlot_id=feedlot_id))
    
    return render_template('top_level/feedlot_branding.html', feedlot=feedlot, branding=existing_branding, user_type=user_type)

@top_level_bp.route('/feedlot/<feedlot_id>/users')
@login_required
@admin_access_required
def feedlot_users(feedlot_id):
    """Manage users for a feedlot"""
    # Check if business owner or business admin has access to this feedlot
    user_type = session.get('user_type')
    if user_type in ['business_owner', 'business_admin']:
        user_feedlot_ids = [str(fid) for fid in session.get('feedlot_ids', [])]
        if str(feedlot_id) not in user_feedlot_ids:
            flash('Access denied. You do not have access to this feedlot.', 'error')
            return redirect(url_for('top_level.dashboard'))
    
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    users = User.find_by_feedlot(feedlot_id)
    user_type = session.get('user_type')
    
    # Get feedlots for the edit modal (only for top-level users)
    if user_type in ['super_owner', 'super_admin']:
        feedlots = Feedlot.find_all()
    else:
        feedlots = []
    
    return render_template('top_level/feedlot_users.html', feedlot=feedlot, users=users, user_type=user_type, feedlots=feedlots)

@top_level_bp.route('/user/<user_id>/activate', methods=['POST'])
@login_required
@super_admin_required
def activate_user(user_id):
    """Activate a user"""
    user = User.find_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    User.update_user(user_id, {'is_active': True})
    flash('User activated successfully.', 'success')
    
    # Redirect back to the page they came from
    referer = request.headers.get('Referer')
    if referer and '/feedlot/' in referer and '/users' in referer:
        return redirect(referer)
    return redirect(url_for('top_level.dashboard'))

@top_level_bp.route('/user/<user_id>/deactivate', methods=['POST'])
@login_required
@super_admin_required
def deactivate_user(user_id):
    """Deactivate a user"""
    user = User.find_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Prevent self-deactivation
    if str(user['_id']) == session.get('user_id'):
        flash('You cannot deactivate your own account.', 'error')
        return redirect(request.headers.get('Referer', url_for('top_level.dashboard')))
    
    User.update_user(user_id, {'is_active': False})
    flash('User deactivated successfully.', 'success')
    
    # Redirect back to the page they came from
    referer = request.headers.get('Referer')
    if referer and '/feedlot/' in referer and '/users' in referer:
        return redirect(referer)
    return redirect(url_for('top_level.dashboard'))

@top_level_bp.route('/users')
@login_required
@admin_access_required
def manage_users():
    """Manage all users (super owner/super admin and business users)"""
    user_type = session.get('user_type')
    
    # Get feedlots for the modal form
    if user_type in ['business_owner', 'business_admin']:
        # Filter feedlots to only show assigned ones
        user_feedlot_ids = session.get('feedlot_ids', [])
        if user_feedlot_ids:
            feedlot_object_ids = [ObjectId(fid) for fid in user_feedlot_ids]
            feedlots = list(Feedlot.find_by_ids(feedlot_object_ids))
        else:
            feedlots = []
    else:
        # Super owner and super admin see all feedlots
        feedlots = Feedlot.find_all()
    
    # Get all users based on user type
    if user_type in ['business_owner', 'business_admin']:
        # Business owner and business admin can see users for their assigned feedlots
        user_feedlot_ids = session.get('feedlot_ids', [])
        if user_feedlot_ids:
            feedlot_object_ids = [ObjectId(fid) for fid in user_feedlot_ids]
            # Find users associated with these feedlots
            users = []
            for feedlot_id in feedlot_object_ids:
                feedlot_users = User.find_by_feedlot(str(feedlot_id))
                users.extend(feedlot_users)
            # Remove duplicates
            seen_ids = set()
            unique_users = []
            for user in users:
                user_id = str(user['_id'])
                if user_id not in seen_ids:
                    seen_ids.add(user_id)
                    unique_users.append(user)
            users = unique_users
        else:
            users = []
    else:
        # Super owner and super admin see all users
        users = list(db.users.find())
    
    return render_template('top_level/manage_users.html', users=users, user_type=user_type, feedlots=feedlots)

@top_level_bp.route('/user/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_user(user_id):
    """Edit a user profile"""
    user = User.find_by_id(user_id)
    if not user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'User not found.'}), 404
        flash('User not found.', 'error')
        return redirect(url_for('top_level.manage_users'))
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'GET':
        # Return user data as JSON for AJAX requests
        if is_ajax:
            # Convert ObjectId to string for JSON serialization
            user_data = {
                'username': user.get('username', ''),
                'email': user.get('email', ''),
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'contact_number': user.get('contact_number', ''),
                'user_type': user.get('user_type', 'user'),
                'is_active': user.get('is_active', True),
                'feedlot_id': str(user.get('feedlot_id', '')) if user.get('feedlot_id') else '',
                'feedlot_ids': [str(fid) for fid in user.get('feedlot_ids', [])] if user.get('feedlot_ids') else []
            }
            return jsonify({'success': True, 'user': user_data})
        else:
            # For non-AJAX GET requests, redirect to manage users
            return redirect(url_for('top_level.manage_users'))
    
    # Handle POST request for updating user
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        user_type = request.form.get('user_type', '').strip()
        is_active = request.form.get('is_active') == '1'
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate required fields
        if not username or not email or not user_type:
            error_msg = 'Username, email, and user type are required.'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('top_level.manage_users'))
        
        # Check if username is being changed and if it's already taken
        if username != user.get('username'):
            existing_user = User.find_by_username(username)
            if existing_user and str(existing_user['_id']) != user_id:
                error_msg = 'Username already exists.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(url_for('top_level.manage_users'))
        
        # Check if email is being changed and if it's already taken
        if email != user.get('email'):
            existing_user = User.find_by_email(email)
            if existing_user and str(existing_user['_id']) != user_id:
                error_msg = 'Email already exists.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(url_for('top_level.manage_users'))
        
        # Prepare update data
        update_data = {
            'username': username,
            'email': email,
            'first_name': first_name if first_name else None,
            'last_name': last_name if last_name else None,
            'contact_number': contact_number if contact_number else None,
            'user_type': user_type,
            'is_active': is_active
        }
        
        # Handle feedlot assignments based on user type
        if user_type in ['business_admin', 'business_owner']:
            # Get selected feedlot IDs from checkboxes
            feedlot_ids = request.form.getlist('edit_feedlot_ids')
            if feedlot_ids:
                update_data['feedlot_ids'] = [ObjectId(fid) for fid in feedlot_ids]
                # Clear single feedlot_id if it exists
                update_data['feedlot_id'] = None
            else:
                update_data['feedlot_ids'] = []
                update_data['feedlot_id'] = None
        elif user_type == 'user':
            # Single feedlot assignment
            feedlot_id = request.form.get('feedlot_id', '').strip()
            if feedlot_id:
                update_data['feedlot_id'] = ObjectId(feedlot_id)
            else:
                update_data['feedlot_id'] = None
            # Clear multiple feedlot_ids if it exists
            update_data['feedlot_ids'] = []
        else:
            # Super owner or super admin - no feedlots
            update_data['feedlot_id'] = None
            update_data['feedlot_ids'] = []
        
        # Handle password change if provided
        if new_password:
            # Validate password confirmation
            if new_password != confirm_password:
                error_msg = 'New password and confirmation do not match.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(url_for('top_level.manage_users'))
            
            # Validate password length
            if len(new_password) < 6:
                error_msg = 'New password must be at least 6 characters long.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(url_for('top_level.manage_users'))
            
            # Hash new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            update_data['password_hash'] = hashed_password
        
        # Update user
        User.update_user(user_id, update_data)
        
        success_msg = 'User updated successfully.'
        if is_ajax:
            return jsonify({'success': True, 'message': success_msg}), 200
        flash(success_msg, 'success')
        
        # Redirect back to feedlot users page if coming from there
        referer = request.headers.get('Referer')
        if referer and '/feedlot/' in referer and '/users' in referer:
            # Extract feedlot_id from referer URL
            match = re.search(r'/feedlot/([^/]+)/users', referer)
            if match:
                feedlot_id = match.group(1)
                return redirect(url_for('top_level.feedlot_users', feedlot_id=feedlot_id))
        
        return redirect(url_for('top_level.manage_users'))
    
    except Exception as e:
        error_msg = f'Failed to update user: {str(e)}'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'error')
        
        # Redirect back to feedlot users page if coming from there
        referer = request.headers.get('Referer')
        if referer and '/feedlot/' in referer and '/users' in referer:
            match = re.search(r'/feedlot/([^/]+)/users', referer)
            if match:
                feedlot_id = match.group(1)
                return redirect(url_for('top_level.feedlot_users', feedlot_id=feedlot_id))
        
        return redirect(url_for('top_level.manage_users'))

@top_level_bp.route('/dashboard/preferences', methods=['POST'])
@login_required
@admin_access_required
def save_dashboard_preferences():
    """Save user's dashboard widget preferences"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated.'}), 401
        
        data = request.get_json()
        preferences = {
            'widget_order': data.get('widget_order', []),
            'widget_visibility': data.get('widget_visibility', {}),
            'widget_sizes': data.get('widget_sizes', {})
        }
        
        User.save_dashboard_preferences(user_id, preferences)
        return jsonify({'success': True, 'message': 'Dashboard preferences saved successfully.'}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to save preferences: {str(e)}'}), 500

@top_level_bp.route('/settings')
@login_required
@admin_access_required
def settings():
    """Main settings page (all admin users)"""
    user_type = session.get('user_type')
    
    # Get feedlots for the erase feedlot data modal (only for super owner/super admin)
    feedlots = []
    if user_type in ['super_owner', 'super_admin']:
        feedlots = Feedlot.find_all()
    
    return render_template('top_level/settings.html', user_type=user_type, feedlots=feedlots)

@top_level_bp.route('/settings/api-keys')
@login_required
@admin_access_required
def api_keys():
    """API Keys management page (top-level users only)"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        flash('Access denied. API Keys management is only available for top-level users.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Get all feedlots
    feedlots = Feedlot.find_all()
    
    # Enrich feedlots with their API keys
    enriched_feedlots = []
    for feedlot in feedlots:
        feedlot_id = str(feedlot['_id'])
        api_keys = APIKey.find_by_feedlot(feedlot_id)
        
        enriched_feedlot = dict(feedlot)
        enriched_feedlot['api_keys'] = api_keys
        enriched_feedlots.append(enriched_feedlot)
    
    return render_template('top_level/api_keys.html', feedlots=enriched_feedlots, user_type=user_type)

@top_level_bp.route('/settings/api-keys/generate', methods=['POST'])
@login_required
@admin_access_required
def generate_api_key():
    """Generate a new API key for a feedlot (top-level users only)"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Request body must be JSON'}), 400
        
        feedlot_id = data.get('feedlot_id')
        if not feedlot_id:
            return jsonify({'success': False, 'message': 'feedlot_id is required'}), 400
        
        # Verify feedlot exists
        feedlot = Feedlot.find_by_id(feedlot_id)
        if not feedlot:
            return jsonify({'success': False, 'message': 'Feedlot not found'}), 404
        
        description = data.get('description', '').strip() or None
        
        # Generate API key
        api_key_string, api_key_id = APIKey.create_api_key(feedlot_id, description)
        
        return jsonify({
            'success': True,
            'message': 'API key generated successfully',
            'api_key': api_key_string,
            'api_key_id': api_key_id,
            'feedlot_id': feedlot_id,
            'feedlot_name': feedlot.get('name'),
            'feedlot_code': feedlot.get('feedlot_code'),
            'warning': 'Save this API key immediately. It will not be shown again.'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error generating API key: {str(e)}'}), 500

@top_level_bp.route('/settings/api-keys/<key_id>/deactivate', methods=['POST'])
@login_required
@admin_access_required
def deactivate_api_key(key_id):
    """Deactivate an API key (top-level users only)"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    
    try:
        api_key = APIKey.find_by_id(key_id)
        if not api_key:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
        
        APIKey.deactivate_key(key_id)
        return jsonify({'success': True, 'message': 'API key deactivated successfully'}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deactivating API key: {str(e)}'}), 500

@top_level_bp.route('/settings/api-keys/<key_id>/activate', methods=['POST'])
@login_required
@admin_access_required
def activate_api_key(key_id):
    """Activate an API key (top-level users only)"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    
    try:
        api_key = APIKey.find_by_id(key_id)
        if not api_key:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
        
        APIKey.activate_key(key_id)
        return jsonify({'success': True, 'message': 'API key activated successfully'}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error activating API key: {str(e)}'}), 500

@top_level_bp.route('/settings/api-keys/<key_id>/delete', methods=['POST'])
@login_required
@admin_access_required
def delete_api_key(key_id):
    """Delete an API key (top-level users only)"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        return jsonify({'success': False, 'message': 'Access denied.'}), 403
    
    try:
        api_key = APIKey.find_by_id(key_id)
        if not api_key:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
        
        APIKey.delete_key(key_id)
        return jsonify({'success': True, 'message': 'API key deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting API key: {str(e)}'}), 500

@top_level_bp.route('/settings/load-test-data', methods=['POST'])
@login_required
@super_admin_required
def load_test_data():
    """Load test data - generate sample feedlots, batches, pens, and cattle (top-level users only)"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Access denied.'}), 403
        flash('Access denied. Load test data is only available for top-level users.', 'error')
        return redirect(url_for('top_level.settings'))
    
    try:
        import random
        from datetime import datetime, timedelta
        
        # Sample data lists
        feedlot_names = [
            "High River Feeders",
            "Lethbridge Cattle Co.",
            "Calgary Feedlot Services",
            "Red Deer Valley Feeders",
            "Medicine Hat Feedlot"
        ]
        
        locations = [
            "High River, AB",
            "Lethbridge, AB",
            "Calgary, AB",
            "Red Deer, AB",
            "Medicine Hat, AB"
        ]
        
        funders = [
            "Alberta Beef Producers",
            "Canadian Cattle Association",
            "Feedlot Financing Inc.",
            "Western Livestock Co.",
            "Prairie Feedlot Partners"
        ]
        
        breeds = [
            "Angus", "Hereford", "Charolais", "Simmental", "Limousin",
            "Red Angus", "Black Angus", "Gelbvieh", "Maine-Anjou", "Shorthorn"
        ]
        
        tag_colors = ["Red", "Yellow", "Blue", "Green", "White", "Orange"]
        
        # Generate 1-5 feedlots
        num_feedlots = random.randint(1, 5)
        created_feedlots = []
        
        for i in range(num_feedlots):
            # Generate unique feedlot code
            feedlot_code = f"test{random.randint(1000, 9999)}"
            # Ensure uniqueness
            while Feedlot.find_by_code(feedlot_code):
                feedlot_code = f"test{random.randint(1000, 9999)}"
            
            name = feedlot_names[i] if i < len(feedlot_names) else f"Test Feedlot {i+1}"
            location = locations[i] if i < len(locations) else f"Location {i+1}, AB"
            
            contact_info = {
                'phone': f"403-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                'email': f"contact@{feedlot_code.lower()}.com",
                'contact_person': f"Manager {i+1}"
            }
            
            feedlot_id = Feedlot.create_feedlot(
                name=name,
                location=location,
                feedlot_code=feedlot_code,
                contact_info=contact_info,
                owner_id=None,
                land_description=f"Test land description for {name}",
                premises_id=f"PID{random.randint(100000, 999999)}"
            )
            
            feedlot_code_normalized = feedlot_code.lower().strip()
            # Get the feedlot object for later use
            feedlot = Feedlot.find_by_id(feedlot_id)
            created_feedlots.append({
                'id': feedlot_id,
                'code': feedlot_code_normalized,
                'name': name
            })
            
            # Generate 1-10 pens per feedlot
            num_pens = random.randint(1, 10)
            created_pens = []
            existing_pens = Pen.find_by_feedlot(feedlot_id)
            existing_pen_numbers = {pen.get('pen_number') for pen in existing_pens}
            
            pen_counter = 1
            for pen_num in range(1, num_pens + 1):
                # Generate unique pen number
                pen_number = f"P{pen_counter:02d}"
                while pen_number in existing_pen_numbers:
                    pen_counter += 1
                    pen_number = f"P{pen_counter:02d}"
                existing_pen_numbers.add(pen_number)
                
                capacity = random.randint(50, 200)
                description = f"Pen {pen_number} - Test pen"
                pen_id = Pen.create_pen(feedlot_id, pen_number, capacity, description)
                created_pens.append({
                    'id': pen_id,
                    'number': pen_number,
                    'capacity': capacity
                })
                pen_counter += 1
            
            # Generate 1-10 batches per feedlot
            num_batches = random.randint(1, 10)
            created_batches = []
            existing_batches = Batch.find_by_feedlot(feedlot_code_normalized, feedlot_id)
            existing_batch_numbers = {batch.get('batch_number') for batch in existing_batches}
            
            base_date = datetime.utcnow() - timedelta(days=random.randint(30, 180))
            batch_counter = 1
            
            for batch_num in range(1, num_batches + 1):
                # Generate unique batch number
                batch_number = f"B{batch_counter:03d}"
                while batch_number in existing_batch_numbers:
                    batch_counter += 1
                    batch_number = f"B{batch_counter:03d}"
                existing_batch_numbers.add(batch_number)
                
                event_date = base_date + timedelta(days=random.randint(0, 30))
                funder = random.choice(funders)
                # Randomly choose between 'induction' and 'export' event types
                event_type = random.choice(['induction', 'export'])
                batch_id = Batch.create_batch(
                    feedlot_code=feedlot_code_normalized,
                    feedlot_id=feedlot_id,
                    batch_number=batch_number,
                    event_date=event_date,
                    funder=funder,
                    notes=f"Test batch {batch_number}",
                    event_type=event_type
                )
                created_batches.append({
                    'id': batch_id,
                    'number': batch_number,
                    'event_type': event_type
                })
                batch_counter += 1
            
            # Generate 50-300 cattle per feedlot
            num_cattle = random.randint(50, 300)
            created_cattle = 0
            existing_cattle = Cattle.find_by_feedlot(feedlot_code_normalized, feedlot_id)
            existing_cattle_ids = {cattle.get('cattle_id') for cattle in existing_cattle}
            
            # Sample notes for random addition
            sample_notes = [
                "Good health, active",
                "Requires monitoring",
                "Excellent condition",
                "Recent weight gain",
                "Standard processing",
                "No issues observed",
                "Healthy appetite",
                "Normal behavior",
                "Regular checkup completed",
                "Feeding schedule maintained"
            ]
            
            for cattle_num in range(1, num_cattle + 1):
                # Generate unique cattle ID
                cattle_id = f"C{feedlot_code_normalized.upper()}{cattle_num:04d}"
                while cattle_id in existing_cattle_ids:
                    cattle_num += 1
                    cattle_id = f"C{feedlot_code_normalized.upper()}{cattle_num:04d}"
                existing_cattle_ids.add(cattle_id)
                
                # Randomly assign to batch (70% chance) or leave unassigned
                batch_id = None
                batch_event_type = None
                if random.random() < 0.7 and created_batches:
                    selected_batch = random.choice(created_batches)
                    batch_id = selected_batch['id']
                    batch_event_type = selected_batch['event_type']
                
                # Randomly assign to pen (60% chance) or leave unassigned
                pen_id = None
                if random.random() < 0.6 and created_pens:
                    pen_id = random.choice(created_pens)['id']
                
                # Generate cattle data
                sex = random.choice(['Heifer', 'Steer', 'Unknown'])
                initial_weight = round(random.uniform(200.0, 400.0), 2)
                
                # Set cattle status based on batch type
                # If assigned to a batch: 'induction' -> 'Healthy', 'export' -> 'Export'
                # If not assigned to a batch: random choice
                if batch_event_type == 'induction':
                    cattle_status = 'Healthy'
                elif batch_event_type == 'export':
                    cattle_status = 'Export'
                else:
                    cattle_status = random.choice(['Healthy', 'Export'])
                
                breed = random.choice(breeds)
                color = random.choice(tag_colors)
                
                # Always generate both LF and UHF tags
                lf_tag = f"LF{random.randint(1000000, 9999999)}"
                uhf_tag = f"EPC{''.join(random.choices('0123456789ABCDEF', k=20))}"
                
                # Initial notes (50% chance of having notes)
                initial_notes = ""
                if random.random() < 0.5:
                    initial_notes = random.choice(sample_notes)
                
                # Create cattle record
                cattle_record_id = Cattle.create_cattle(
                    feedlot_code=feedlot_code_normalized,
                    feedlot_id=feedlot_id,
                    cattle_id=cattle_id,
                    sex=sex,
                    weight=initial_weight,
                    cattle_status=cattle_status,
                    batch_id=batch_id,
                    lf_tag=lf_tag,
                    uhf_tag=uhf_tag,
                    pen_id=pen_id,
                    notes=initial_notes,
                    color=color,
                    breed=breed,
                    created_by='test_data_generator'
                )
                
                # Randomly add weight history (30% chance, 1-3 additional entries)
                if random.random() < 0.3:
                    num_weight_entries = random.randint(1, 3)
                    current_weight = initial_weight
                    
                    for _ in range(num_weight_entries):
                        # Weight gain: 2-10 kg per entry
                        weight_gain = random.uniform(2.0, 10.0)
                        current_weight = round(current_weight + weight_gain, 2)
                        
                        # Use add_weight_record method (will use current timestamp)
                        Cattle.add_weight_record(
                            feedlot_code=feedlot_code_normalized,
                            cattle_record_id=cattle_record_id,
                            weight=current_weight,
                            recorded_by='test_data_generator'
                        )
                
                # Randomly add notes (40% chance, 1-2 additional notes)
                if random.random() < 0.4:
                    num_note_entries = random.randint(1, 2)
                    for _ in range(num_note_entries):
                        note = random.choice(sample_notes)
                        Cattle.add_note(
                            feedlot_code=feedlot_code_normalized,
                            cattle_record_id=cattle_record_id,
                            note=note,
                            recorded_by='test_data_generator'
                        )
                
                created_cattle += 1
            
            # Generate 2-5 manifest templates per feedlot
            num_templates = random.randint(2, 5)
            template_names = [
                "Standard Export Template",
                "Local Transport Template",
                "Dealer Transfer Template",
                "Processing Plant Template",
                "Custom Template"
            ]
            
            owners = [
                {"name": "Alberta Beef Producers", "phone": "403-555-0100", "address": "123 Main St, Calgary, AB"},
                {"name": "Western Livestock Co.", "phone": "403-555-0200", "address": "456 Ranch Rd, Lethbridge, AB"},
                {"name": "Prairie Feedlot Partners", "phone": "403-555-0300", "address": "789 Farm Ave, Red Deer, AB"}
            ]
            
            dealers = [
                {"name": "Canadian Cattle Dealers", "phone": "403-555-1000", "address": "321 Market St, Calgary, AB"},
                {"name": "Alberta Livestock Exchange", "phone": "403-555-1100", "address": "654 Trade Blvd, Edmonton, AB"}
            ]
            
            destinations = [
                {"name": "Calgary Processing Plant", "address": "1000 Industrial Way, Calgary, AB", "premises_id": f"PID{random.randint(100000, 999999)}"},
                {"name": "Lethbridge Export Facility", "address": "2000 Export Dr, Lethbridge, AB", "premises_id": f"PID{random.randint(100000, 999999)}"},
                {"name": "Red Deer Distribution Center", "address": "3000 Distribution Ave, Red Deer, AB", "premises_id": f"PID{random.randint(100000, 999999)}"}
            ]
            
            transporters = [
                {"name": "Alberta Transport Services", "phone": "403-555-2000", "trailer": f"TRL-{random.randint(1000, 9999)}"},
                {"name": "Western Hauling Co.", "phone": "403-555-2100", "trailer": f"TRL-{random.randint(1000, 9999)}"},
                {"name": "Prairie Logistics", "phone": "403-555-2200", "trailer": f"TRL-{random.randint(1000, 9999)}"}
            ]
            
            purposes = ['transport_only', 'sale', 'slaughter', 'breeding', 'exhibition']
            
            for template_num in range(1, num_templates + 1):
                template_name = template_names[template_num - 1] if template_num <= len(template_names) else f"Template {template_num}"
                
                owner = random.choice(owners)
                dealer = random.choice(dealers) if random.random() < 0.7 else None
                destination = random.choice(destinations)
                transporter = random.choice(transporters)
                purpose = random.choice(purposes)
                
                # First template is set as default
                is_default = (template_num == 1)
                
                ManifestTemplate.create_template(
                    feedlot_id=feedlot_id,
                    name=template_name,
                    owner_name=owner['name'],
                    owner_phone=owner['phone'],
                    owner_address=owner['address'],
                    dealer_name=dealer['name'] if dealer else None,
                    dealer_phone=dealer['phone'] if dealer else None,
                    dealer_address=dealer['address'] if dealer else None,
                    default_destination_name=destination['name'],
                    default_destination_address=destination['address'],
                    default_transporter_name=transporter['name'],
                    default_transporter_phone=transporter['phone'],
                    default_transporter_trailer=transporter['trailer'],
                    default_purpose=purpose,
                    default_premises_id_before=feedlot.get('premises_id', ''),
                    default_premises_id_destination=destination['premises_id'],
                    is_default=is_default
                )
        
        success_msg = f'Test data loaded successfully: {num_feedlots} feedlots, {created_cattle} cattle created.'
        
        # Always return JSON for this endpoint (called via fetch)
        return jsonify({
            'success': True,
            'message': success_msg,
            'redirect_url': url_for('top_level.dashboard')
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error loading test data: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_msg = f'Failed to load test data: {str(e)}'
        
        # Always return JSON for this endpoint (called via fetch)
        return jsonify({'success': False, 'message': error_msg}), 500

@top_level_bp.route('/settings/erase-all-data', methods=['POST'])
@login_required
@super_admin_required
def erase_all_data():
    """Erase all data - delete all feedlots, pens, batches, cattle, API keys except users (top-level users only)"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        flash('Access denied. Erase data is only available for top-level users.', 'error')
        return redirect(url_for('top_level.settings'))
    
    try:
        from pymongo import MongoClient
        from config import Config
        
        # Get MongoDB client to drop databases
        client = MongoClient(Config.MONGODB_URI)
        
        # Get all feedlots before deleting them
        feedlots = Feedlot.find_all()
        
        # Drop each feedlot-specific database
        for feedlot in feedlots:
            feedlot_code = feedlot.get('feedlot_code')
            if feedlot_code:
                try:
                    # Normalize feedlot_code to lowercase for consistency
                    normalized_code = feedlot_code.lower().strip()
                    db_name = f"feedlot_{normalized_code}"
                    
                    # Drop the entire feedlot database
                    client.drop_database(db_name)
                    
                except Exception as e:
                    # Log error but continue with other feedlots
                    current_app.logger.error(f"Error dropping feedlot database {db_name}: {str(e)}")
        
        # Delete all feedlots from main database
        db.feedlots.delete_many({})
        
        # Delete all API keys from main database
        db.api_keys.delete_many({})
        
        # Also check for pens in main database (in case they exist there)
        if hasattr(db, 'pens'):
            db.pens.delete_many({})
        
        flash('All data erased successfully. All feedlots and their data have been deleted. Users were preserved.', 'success')
        return redirect(url_for('top_level.settings'))
    
    except Exception as e:
        current_app.logger.error(f"Error erasing all data: {str(e)}")
        flash(f'Failed to erase data: {str(e)}', 'error')
        return redirect(url_for('top_level.settings'))

@top_level_bp.route('/settings/erase-feedlot-data', methods=['POST'])
@login_required
@super_admin_required
def erase_feedlot_data():
    """Erase data for a specific feedlot - delete pens, batches, cattle but keep the feedlot and users"""
    user_type = session.get('user_type')
    
    # Only allow top-level users
    if user_type not in ['super_owner', 'super_admin']:
        flash('Access denied. Erase data is only available for top-level users.', 'error')
        return redirect(url_for('top_level.settings'))
    
    feedlot_id = request.form.get('feedlot_id')
    if not feedlot_id:
        flash('Please select a feedlot.', 'error')
        return redirect(url_for('top_level.settings'))
    
    try:
        from app import get_feedlot_db
        
        # Get the feedlot
        feedlot = Feedlot.find_by_id(feedlot_id)
        if not feedlot:
            flash('Feedlot not found.', 'error')
            return redirect(url_for('top_level.settings'))
        
        feedlot_name = feedlot.get('name', 'Unknown')
        feedlot_code = feedlot.get('feedlot_code')
        
        if not feedlot_code:
            flash('Feedlot code not found. Cannot erase data.', 'error')
            return redirect(url_for('top_level.settings'))
        
        # Normalize feedlot_code
        normalized_code = feedlot_code.lower().strip()
        
        # Get feedlot-specific database
        feedlot_db = get_feedlot_db(normalized_code)
        
        # Count items before deletion for reporting
        cattle_count = feedlot_db.cattle.count_documents({})
        batches_count = feedlot_db.batches.count_documents({})
        pens_count = db.pens.count_documents({'feedlot_id': ObjectId(feedlot_id)})
        
        # Delete all cattle from feedlot-specific database
        feedlot_db.cattle.delete_many({})
        
        # Delete all batches from feedlot-specific database
        feedlot_db.batches.delete_many({})
        
        # Delete all manifests from feedlot-specific database (if exists)
        if 'manifests' in feedlot_db.list_collection_names():
            feedlot_db.manifests.delete_many({})
        
        # Delete all pens for this feedlot from main database
        db.pens.delete_many({'feedlot_id': ObjectId(feedlot_id)})
        
        flash(f'Data erased for feedlot "{feedlot_name}": {cattle_count} cattle, {batches_count} batches, and {pens_count} pens deleted. Feedlot and users were preserved.', 'success')
        return redirect(url_for('top_level.settings'))
    
    except Exception as e:
        current_app.logger.error(f"Error erasing feedlot data for {feedlot_id}: {str(e)}")
        flash(f'Failed to erase feedlot data: {str(e)}', 'error')
        return redirect(url_for('top_level.settings'))

