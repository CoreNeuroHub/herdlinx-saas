from flask import Blueprint, render_template, request, redirect, url_for, session, flash
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
        name = request.form.get('name')
        location = request.form.get('location')
        contact_info = {
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'contact_person': request.form.get('contact_person')
        }
        
        feedlot_id = Feedlot.create_feedlot(name, location, contact_info)
        flash('Feedlot created successfully.', 'success')
        return redirect(url_for('top_level.dashboard'))
    
    return render_template('top_level/create_feedlot.html')

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

