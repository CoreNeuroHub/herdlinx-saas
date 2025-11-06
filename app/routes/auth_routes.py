from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from app.models.user import User
from functools import wraps
import bcrypt
import os
import uuid
from werkzeug.utils import secure_filename

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
            # Store user profile data for quick access
            session['user_profile'] = {
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'profile_picture': user.get('profile_picture')
            }
            
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

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and edit user profile"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.find_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate required fields
        if not username or not email:
            flash('Username and email are required.', 'error')
            return render_template('auth/profile.html', user=user)
        
        # Check if username is being changed and if it's already taken
        if username != user.get('username'):
            existing_user = User.find_by_username(username)
            if existing_user and str(existing_user['_id']) != user_id:
                flash('Username already exists.', 'error')
                return render_template('auth/profile.html', user=user)
        
        # Check if email is being changed and if it's already taken
        if email != user.get('email'):
            existing_user = User.find_by_email(email)
            if existing_user and str(existing_user['_id']) != user_id:
                flash('Email already exists.', 'error')
                return render_template('auth/profile.html', user=user)
        
        # Prepare update data
        update_data = {
            'username': username,
            'email': email,
            'first_name': first_name if first_name else None,
            'last_name': last_name if last_name else None,
            'contact_number': contact_number if contact_number else None
        }
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Validate file type
                if not allowed_file(file.filename):
                    flash('Invalid file type. Please upload a PNG, JPG, JPEG, GIF, or WEBP image.', 'error')
                    return render_template('auth/profile.html', user=user)
                
                # Validate file size (max 5MB for images)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                if file_size > 5 * 1024 * 1024:  # 5MB
                    flash('File size too large. Please upload an image smaller than 5MB.', 'error')
                    return render_template('auth/profile.html', user=user)
                
                # Generate unique filename
                file_ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
                filename = secure_filename(filename)
                
                # Create profile_pictures directory if it doesn't exist
                profile_pics_dir = os.path.join(current_app.static_folder, 'profile_pictures')
                os.makedirs(profile_pics_dir, exist_ok=True)
                
                # Delete old profile picture if it exists
                old_picture = user.get('profile_picture')
                if old_picture:
                    # Handle both /static/... and static/... paths
                    # Extract filename from path like /static/profile_pictures/filename.jpg
                    old_path_clean = old_picture.lstrip('/').replace('static/', '').replace('profile_pictures/', '')
                    if old_path_clean:
                        old_path = os.path.join(profile_pics_dir, old_path_clean)
                        if os.path.exists(old_path) and os.path.isfile(old_path):
                            try:
                                os.remove(old_path)
                            except Exception:
                                pass  # Ignore errors when deleting old file
                
                # Save new profile picture
                file_path = os.path.join(profile_pics_dir, filename)
                file.save(file_path)
                
                # Store relative path in database
                update_data['profile_picture'] = f'/static/profile_pictures/{filename}'
        
        # Handle password change if provided
        if new_password:
            if not current_password:
                flash('Current password is required to change password.', 'error')
                return render_template('auth/profile.html', user=user)
            
            # Verify current password
            if not User.verify_password(user['password_hash'], current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('auth/profile.html', user=user)
            
            # Validate new password confirmation
            if new_password != confirm_password:
                flash('New password and confirmation do not match.', 'error')
                return render_template('auth/profile.html', user=user)
            
            # Validate password length
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'error')
                return render_template('auth/profile.html', user=user)
            
            # Hash new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            update_data['password_hash'] = hashed_password
        
        # Update user
        try:
            User.update_user(user_id, update_data)
            
            # Update session data if changed
            if username != session.get('username'):
                session['username'] = username
            
            # Refresh user profile in session
            updated_user = User.find_by_id(user_id)
            session['user_profile'] = {
                'first_name': updated_user.get('first_name'),
                'last_name': updated_user.get('last_name'),
                'profile_picture': updated_user.get('profile_picture')
            }
            
            flash('Profile updated successfully.', 'success')
            
            # Redirect based on user type
            user_type = session.get('user_type')
            if user_type == 'user':
                return redirect(url_for('feedlot.dashboard', feedlot_id=session.get('feedlot_id')))
            else:
                return redirect(url_for('top_level.dashboard'))
        except Exception as e:
            flash(f'Failed to update profile: {str(e)}', 'error')
            return render_template('auth/profile.html', user=user)
    
    # GET request - show profile form
    return render_template('auth/profile.html', user=user)

