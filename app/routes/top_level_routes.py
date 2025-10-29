from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models.feedlot import Feedlot
from app.models.user import User
from app.routes.auth_routes import login_required, top_level_required

top_level_bp = Blueprint('top_level', __name__)

@top_level_bp.route('/')
@top_level_bp.route('/dashboard')
@login_required
@top_level_required
def dashboard():
    """Top-level dashboard showing all feedlots"""
    feedlots = Feedlot.find_all()
    return render_template('top_level/dashboard.html', feedlots=feedlots)

@top_level_bp.route('/feedlot/create', methods=['GET', 'POST'])
@login_required
@top_level_required
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
@top_level_required
def view_feedlot(feedlot_id):
    """View feedlot details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    statistics = Feedlot.get_statistics(feedlot_id)
    return render_template('top_level/view_feedlot.html', feedlot=feedlot, statistics=statistics)

@top_level_bp.route('/feedlot/<feedlot_id>/edit', methods=['GET', 'POST'])
@login_required
@top_level_required
def edit_feedlot(feedlot_id):
    """Edit feedlot details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
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
        
        Feedlot.update_feedlot(feedlot_id, update_data)
        flash('Feedlot updated successfully.', 'success')
        return redirect(url_for('top_level.view_feedlot', feedlot_id=feedlot_id))
    
    return render_template('top_level/edit_feedlot.html', feedlot=feedlot)

@top_level_bp.route('/feedlot/<feedlot_id>/users')
@login_required
@top_level_required
def feedlot_users(feedlot_id):
    """Manage users for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('top_level.dashboard'))
    
    users = User.find_by_feedlot(feedlot_id)
    return render_template('top_level/feedlot_users.html', feedlot=feedlot, users=users)

@top_level_bp.route('/user/<user_id>/activate', methods=['POST'])
@login_required
@top_level_required
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
@top_level_required
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

