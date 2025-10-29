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

def top_level_required(f):
    """Decorator to require top-level user"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'top_level':
            flash('Access denied. Top-level access required.', 'error')
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
            
            # Top-level users can access any feedlot
            if user_type == 'top_level':
                return f(*args, **kwargs)
            
            # Feedlot users can only access their own feedlot
            if user_type == 'feedlot':
                feedlot_id = kwargs.get(feedlot_id_param)
                if str(user_feedlot_id) != str(feedlot_id):
                    flash('Access denied.', 'error')
                    return redirect(url_for('feedlot.dashboard', feedlot_id=user_feedlot_id))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for both top-level and feedlot users"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.find_by_username(username)
        
        if user and User.verify_password(user['password_hash'], password):
            if not user.get('is_active', True):
                flash('Account is inactive.', 'error')
                return render_template('auth/login.html')
            
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            
            if user['user_type'] == 'top_level':
                return redirect(url_for('top_level.dashboard'))
            elif user['user_type'] == 'feedlot':
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
    
    # Only top-level users can register other users
    user_type = session.get('user_type')
    
    if user_type != 'top_level':
        error_msg = 'Access denied. Top-level user required.'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 403
        flash(error_msg, 'error')
        if user_type == 'feedlot':
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
            new_user_type = request.form.get('user_type', 'feedlot')
            feedlot_id = request.form.get('feedlot_id') or request.args.get('feedlot_id')
            
            # Validate required fields
            if not username or not email or not password:
                error_msg = 'Username, email, and password are required.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                feedlots = Feedlot.find_all()
                return render_template('auth/register.html', feedlots=feedlots, selected_feedlot_id=feedlot_id)
            
            # Validate feedlot_id for feedlot users
            if new_user_type == 'feedlot' and not feedlot_id:
                error_msg = 'Feedlot ID is required for feedlot users.'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
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
            user_id = User.create_user(username, email, password, new_user_type, feedlot_id)
            success_msg = f'User "{username}" created successfully as {new_user_type} user.'
            
            if is_ajax:
                return jsonify({'success': True, 'message': success_msg}), 200
            flash(success_msg, 'success')
            
            if new_user_type == 'top_level':
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

