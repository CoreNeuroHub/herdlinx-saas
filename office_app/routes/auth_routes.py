from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from office_app.models.user import User
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

def admin_required(f):
    """Decorator to require admin user"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        user = User.find_by_id(session['user_id'])
        if not user or not user.is_admin:
            flash('Access denied. Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for admin users"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.find_by_username(username)
        
        if user and User.verify_password(user.password_hash, password):
            if not user.is_active:
                flash('Account is inactive.', 'error')
                return render_template('auth/login.html')
            
            if not user.is_admin:
                flash('Access denied. Admin access required.', 'error')
                return render_template('auth/login.html')
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            return redirect(url_for('office.dashboard'))
        
        flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/')
def index():
    """Redirect root to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('office.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    """Logout functionality"""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

