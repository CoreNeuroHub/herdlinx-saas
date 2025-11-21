from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from bson import ObjectId
from datetime import datetime
from app.models.feedlot import Feedlot
from app.models.user import User
from app.models.api_key import APIKey
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
    """Feedlot Hub page showing all feedlots with search/filter"""
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
            feedlot_code_upper = feedlot_code.upper().strip()
            existing = Feedlot.find_by_code(feedlot_code_upper)
            if existing and str(existing['_id']) != feedlot_id:
                flash(f"Feedlot code '{feedlot_code}' already exists.", 'error')
                return render_template('top_level/edit_feedlot.html', feedlot=feedlot, business_owners=business_owners, user_type=user_type)
        
        update_data = {
            'name': request.form.get('name'),
            'location': request.form.get('location'),
            'feedlot_code': feedlot_code.upper().strip() if feedlot_code else None,
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
    
    return render_template('top_level/settings.html', user_type=user_type)

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

