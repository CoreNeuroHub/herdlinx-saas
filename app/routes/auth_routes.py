from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models.user import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator to require super owner or super admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_type = session.get('user_type')
        valid_types = ['super_owner', 'super_admin']
        if user_type not in valid_types:
            flash('Access denied. Super owner or super admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_access_required(f):
    """Decorator to require super owner, super admin, business owner, or business admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_type = session.get('user_type')
        valid_types = ['super_owner', 'super_admin', 'business_owner', 'business_admin']
        if user_type not in valid_types:
            flash('Access denied. Super owner, super admin, business owner, or business admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def feedlot_access_required(feedlot_id_param='feedlot_id'):
    """Decorator to verify user has access to specific feedlot"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_type = session.get('user_type')
            user_feedlot_id = session.get('feedlot_id')
            user_feedlot_ids = session.get('feedlot_ids', [])
            
            # Validate user type - reject old/invalid types
            valid_types = ['super_owner', 'super_admin', 'business_owner', 'business_admin', 'user']
            if user_type not in valid_types:
                flash('Invalid user type. Please contact an administrator.', 'error')
                return redirect(url_for('auth.login'))
            
            # Super owner and super admin can access any feedlot
            if user_type in ['super_owner', 'super_admin']:
                return f(*args, **kwargs)
            
            feedlot_id = kwargs.get(feedlot_id_param)
            
            # Business owner and business admin users can access their assigned feedlots
            if user_type in ['business_owner', 'business_admin']:
                if str(feedlot_id) not in [str(fid) for fid in user_feedlot_ids]:
                    flash('Access denied. You do not have access to this feedlot.', 'error')
                    return redirect(url_for('top_level.dashboard'))
                return f(*args, **kwargs)
            
            # Regular users can only access their own feedlot
            if user_type == 'user':
                if str(user_feedlot_id) != str(feedlot_id):
                    flash('Access denied.', 'error')
                    return redirect(url_for('feedlot.dashboard', feedlot_id=user_feedlot_id))
                return f(*args, **kwargs)
            
            # If we get here, user type is valid but not handled above
            flash('Access denied.', 'error')
            return redirect(url_for('auth.login'))
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for super owner, super admin, business owner, business admin, and users"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.find_by_username(username)
        
        if user and User.verify_password(user['password_hash'], password):
            if not user.get('is_active', True):
                flash('Account is inactive.', 'error')
                return render_template('auth/login.html')
            
            user_type = user.get('user_type')
            # Validate user type - reject old/invalid types
            valid_types = ['super_owner', 'super_admin', 'business_owner', 'business_admin', 'user']
            if user_type not in valid_types:
                flash('Invalid user account. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
            
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['user_type'] = user_type
            
            if user_type in ['super_owner', 'super_admin']:
                return redirect(url_for('top_level.dashboard'))
            elif user_type in ['business_owner', 'business_admin']:
                # Store feedlot_ids as list of strings
                feedlot_ids = user.get('feedlot_ids', [])
                session['feedlot_ids'] = [str(fid) for fid in feedlot_ids]
                return redirect(url_for('top_level.dashboard'))
            elif user_type == 'user':
                session['feedlot_id'] = str(user['feedlot_id'])
                return redirect(url_for('feedlot.dashboard', feedlot_id=user['feedlot_id']))
        
        flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Logout functionality"""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Registration page for creating new users (requires login)"""
    from app.models.feedlot import Feedlot
    
    # Super owner, super admin, business owner, and business admin can register users
    user_type = session.get('user_type')
    
    if user_type not in ['super_owner', 'super_admin', 'business_owner', 'business_admin']:
        error_msg = 'Access denied. Super owner, super admin, business owner, or business admin access required.'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 403
        flash(error_msg, 'error')
        if user_type == 'user':
            return redirect(url_for('feedlot.dashboard', feedlot_id=session.get('feedlot_id')))
        else:
            return redirect(url_for('top_level.dashboard'))
    
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            new_user_type = request.form.get('user_type', 'user')
            feedlot_id = request.form.get('feedlot_id') or request.args.get('feedlot_id')
            feedlot_ids = request.form.getlist('feedlot_ids')  # For multiple feedlots (business_admin, business_owner)
            
            # Validate required fields
            if not username or not email or not password:
                error_msg = 'Username, email, and password are required.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                feedlots = Feedlot.find_all()
                return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
            
            # Business owner and business admin cannot create super owner or super admin users
            if user_type in ['business_owner', 'business_admin'] and new_user_type in ['super_owner', 'super_admin']:
                error_msg = 'Business owner and business admin cannot create super owner or super admin users.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 403
                flash(error_msg, 'error')
                feedlots = Feedlot.find_all()
                return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
            
            # Validate feedlot assignment based on user type
            if new_user_type in ['business_admin', 'business_owner']:
                if not feedlot_ids:
                    error_msg = f'At least one feedlot must be assigned to {new_user_type.replace("_", " ")} users.'
                    if is_ajax:
                        return jsonify({'success': False, 'message': error_msg}), 400
                    flash(error_msg, 'error')
                    feedlots = Feedlot.find_all()
                    return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
                # If current user is business owner or business admin, ensure they can only assign their own feedlots
                if user_type in ['business_owner', 'business_admin']:
                    user_feedlot_ids = [str(fid) for fid in session.get('feedlot_ids', [])]
                    if not all(fid in user_feedlot_ids for fid in feedlot_ids):
                        error_msg = 'You can only assign feedlots that you have access to.'
                        if is_ajax:
                            return jsonify({'success': False, 'message': error_msg}), 403
                        flash(error_msg, 'error')
                        feedlots = Feedlot.find_all()
                        return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
            elif new_user_type == 'user':
                if not feedlot_id:
                    error_msg = 'Feedlot ID is required for users.'
                    if is_ajax:
                        return jsonify({'success': False, 'message': error_msg}), 400
                    flash(error_msg, 'error')
                    feedlots = Feedlot.find_all()
                    return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
                # If current user is business owner or business admin, ensure they can only assign their own feedlots
                if user_type in ['business_owner', 'business_admin']:
                    user_feedlot_ids = [str(fid) for fid in session.get('feedlot_ids', [])]
                    if str(feedlot_id) not in user_feedlot_ids:
                        error_msg = 'You can only assign feedlots that you have access to.'
                        if is_ajax:
                            return jsonify({'success': False, 'message': error_msg}), 403
                        flash(error_msg, 'error')
                        feedlots = Feedlot.find_all()
                        return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
            
            # Check for duplicate username
            if User.find_by_username(username):
                error_msg = 'Username already exists.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                feedlots = Feedlot.find_all()
                return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
            
            # Check for duplicate email
            if User.find_by_email(email):
                error_msg = 'Email already exists.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                feedlots = Feedlot.find_all()
                return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
            
            # Create the user
            if new_user_type in ['business_admin', 'business_owner']:
                user_id = User.create_user(username, email, password, new_user_type, feedlot_ids=feedlot_ids)
            elif new_user_type in ['super_owner', 'super_admin']:
                user_id = User.create_user(username, email, password, new_user_type)
            else:
                user_id = User.create_user(username, email, password, new_user_type, feedlot_id=feedlot_id)
            success_msg = f'User "{username}" created successfully as {new_user_type.replace("_", " ")} user.'
            
            if is_ajax:
                return jsonify({'success': True, 'message': success_msg}), 200
            flash(success_msg, 'success')
            
            if new_user_type in ['super_owner', 'super_admin']:
                return redirect(url_for('top_level.dashboard'))
            else:
                return redirect(url_for('top_level.feedlot_users', feedlot_id=feedlot_id))
        
        except Exception as e:
            error_msg = f'Failed to create user: {str(e)}'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 500
            flash(error_msg, 'error')
            feedlots = Feedlot.find_all()
            return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
    
    # GET request - redirect to dashboard since we're using a modal now
    return redirect(url_for('top_level.dashboard'))

