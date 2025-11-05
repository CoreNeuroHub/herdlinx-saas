from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from bson import ObjectId
from datetime import datetime
from app.models.feedlot import Feedlot
from app.models.user import User
from app.routes.auth_routes import login_required, super_admin_required, admin_access_required
from app import db
import bcrypt

top_level_bp = Blueprint('top_level', __name__)

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
    total_batches = 0
    total_users = 0
    
    if feedlots:
        feedlot_ids = [ObjectId(str(f['_id'])) for f in feedlots]
        total_pens = db.pens.count_documents({'feedlot_id': {'$in': feedlot_ids}})
        total_cattle = db.cattle.count_documents({'feedlot_id': {'$in': feedlot_ids}})
        total_batches = db.batches.count_documents({'feedlot_id': {'$in': feedlot_ids}})
        
        # Count users associated with these feedlots
        user_query = {'$or': [
            {'feedlot_id': {'$in': feedlot_ids}},
            {'feedlot_ids': {'$in': feedlot_ids}}
        ]}
        total_users = db.users.count_documents(user_query)
    
    # Get recent feedlots (last 5)
    recent_feedlots = sorted(feedlots, key=lambda x: x.get('created_at', datetime(1970, 1, 1)), reverse=True)[:5]
    
    dashboard_stats = {
        'total_feedlots': total_feedlots,
        'total_pens': total_pens,
        'total_cattle': total_cattle,
        'total_batches': total_batches,
        'total_users': total_users,
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
        
        # Get statistics for this feedlot
        total_pens = db.pens.count_documents({'feedlot_id': ObjectId(feedlot_id)})
        total_cattle = db.cattle.count_documents({'feedlot_id': ObjectId(feedlot_id)})
        
        # Get owner information
        owner = Feedlot.get_owner(feedlot_id)
        
        # Create enriched feedlot dict
        enriched_feedlot = dict(feedlot)
        enriched_feedlot['total_pens'] = total_pens
        enriched_feedlot['total_cattle'] = total_cattle
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
            contact_info = {
                'phone': request.form.get('phone') or None,
                'email': request.form.get('email') or None,
                'contact_person': request.form.get('contact_person') or None
            }
            
            # Validate required fields
            if not name or not location:
                error_msg = 'Feedlot name and location are required.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                if not is_ajax:
                    return redirect(url_for('top_level.dashboard'))
                return jsonify({'success': False, 'message': error_msg}), 400
            
            feedlot_id = Feedlot.create_feedlot(name, location, contact_info)
            
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
    """View feedlot details"""
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
    
    statistics = Feedlot.get_statistics(feedlot_id)
    owner = Feedlot.get_owner(feedlot_id)
    return render_template('top_level/view_feedlot.html', feedlot=feedlot, statistics=statistics, owner=owner)

@top_level_bp.route('/feedlot/<feedlot_id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_feedlot(feedlot_id):
    """Edit feedlot details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    # Get all business owners for the dropdown
    business_owners = User.find_business_owners()
    
    if request.method == 'POST':
        update_data = {
            'name': request.form.get('name'),
            'location': request.form.get('location'),
            'contact_info': {
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'contact_person': request.form.get('contact_person')
            }
        }
        
        # Handle owner assignment
        owner_id = request.form.get('owner_id', '').strip()
        if owner_id:
            # Validate that the selected user is a business owner
            owner = User.find_by_id(owner_id)
            if owner and owner.get('user_type') == 'business_owner':
                update_data['owner_id'] = ObjectId(owner_id)
            else:
                flash('Selected user must be a business owner.', 'error')
                return render_template('top_level/edit_feedlot.html', feedlot=feedlot, business_owners=business_owners)
        
        # Update feedlot with all fields
        Feedlot.update_feedlot(feedlot_id, update_data)
        
        # If owner_id was cleared (empty), remove the field from database
        if not owner_id:
            db.feedlots.update_one(
                {'_id': ObjectId(feedlot_id)},
                {'$unset': {'owner_id': ''}}
            )
        
        flash('Feedlot updated successfully.', 'success')
        return redirect(url_for('top_level.view_feedlot', feedlot_id=feedlot_id))
    
    return render_template('top_level/edit_feedlot.html', feedlot=feedlot, business_owners=business_owners)

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
    return render_template('top_level/feedlot_users.html', feedlot=feedlot, users=users)

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
        return redirect(url_for('top_level.manage_users'))
    
    except Exception as e:
        error_msg = f'Failed to update user: {str(e)}'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'error')
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

