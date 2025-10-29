from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from bson import ObjectId
from datetime import datetime
from app.models.feedlot import Feedlot
from app.models.pen import Pen
from app.models.batch import Batch
from app.models.cattle import Cattle
from app.routes.auth_routes import login_required, feedlot_access_required

feedlot_bp = Blueprint('feedlot', __name__)

@feedlot_bp.route('/feedlot/<feedlot_id>/dashboard')
@login_required
@feedlot_access_required()
def dashboard(feedlot_id):
    """Feedlot dashboard"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    statistics = Feedlot.get_statistics(feedlot_id)
    
    # Get recent batches
    recent_batches = Batch.find_by_feedlot(feedlot_id)[-5:]
    
    return render_template('feedlot/dashboard.html', 
                         feedlot=feedlot, 
                         statistics=statistics,
                         recent_batches=recent_batches)

# Pen Management Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/pens')
@login_required
@feedlot_access_required()
def list_pens(feedlot_id):
    """List all pens for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    pens = Pen.find_by_feedlot(feedlot_id)
    
    # Add current cattle count to each pen
    for pen in pens:
        pen['current_count'] = Pen.get_current_cattle_count(str(pen['_id']))
    
    return render_template('feedlot/pens/list.html', feedlot=feedlot, pens=pens)

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/create', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def create_pen(feedlot_id):
    """Create a new pen"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    
    if request.method == 'POST':
        pen_number = request.form.get('pen_number')
        capacity = int(request.form.get('capacity'))
        description = request.form.get('description')
        
        pen_id = Pen.create_pen(feedlot_id, pen_number, capacity, description)
        flash('Pen created successfully.', 'success')
        return redirect(url_for('feedlot.list_pens', feedlot_id=feedlot_id))
    
    return render_template('feedlot/pens/create.html', feedlot=feedlot)

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/<pen_id>/view')
@login_required
@feedlot_access_required()
def view_pen(feedlot_id, pen_id):
    """View pen details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    pen = Pen.find_by_id(pen_id)
    
    if not pen:
        flash('Pen not found.', 'error')
        return redirect(url_for('feedlot.list_pens', feedlot_id=feedlot_id))
    
    cattle = Cattle.find_by_pen(pen_id)
    pen['current_count'] = len(cattle)
    
    return render_template('feedlot/pens/view.html', feedlot=feedlot, pen=pen, cattle=cattle)

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/<pen_id>/edit', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def edit_pen(feedlot_id, pen_id):
    """Edit pen details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    pen = Pen.find_by_id(pen_id)
    
    if not pen:
        flash('Pen not found.', 'error')
        return redirect(url_for('feedlot.list_pens', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        update_data = {
            'pen_number': request.form.get('pen_number'),
            'capacity': int(request.form.get('capacity')),
            'description': request.form.get('description')
        }
        
        Pen.update_pen(pen_id, update_data)
        flash('Pen updated successfully.', 'success')
        return redirect(url_for('feedlot.view_pen', feedlot_id=feedlot_id, pen_id=pen_id))
    
    return render_template('feedlot/pens/edit.html', feedlot=feedlot, pen=pen)

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/<pen_id>/delete', methods=['POST'])
@login_required
@feedlot_access_required()
def delete_pen(feedlot_id, pen_id):
    """Delete a pen"""
    Pen.delete_pen(pen_id)
    flash('Pen deleted successfully.', 'success')
    return redirect(url_for('feedlot.list_pens', feedlot_id=feedlot_id))

# Batch Management Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/batches')
@login_required
@feedlot_access_required()
def list_batches(feedlot_id):
    """List all batches for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    batches = Batch.find_by_feedlot(feedlot_id)
    
    # Add cattle count to each batch
    for batch in batches:
        batch['cattle_count'] = Batch.get_cattle_count(str(batch['_id']))
    
    return render_template('feedlot/batches/list.html', feedlot=feedlot, batches=batches)

@feedlot_bp.route('/feedlot/<feedlot_id>/batches/create', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def create_batch(feedlot_id):
    """Create a new batch"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    
    if request.method == 'POST':
        batch_number = request.form.get('batch_number')
        induction_date_str = request.form.get('induction_date')
        source = request.form.get('source')
        notes = request.form.get('notes')
        
        # Convert date string to datetime object
        induction_date = datetime.strptime(induction_date_str, '%Y-%m-%d') if induction_date_str else None
        
        batch_id = Batch.create_batch(feedlot_id, batch_number, induction_date, source, notes)
        flash('Batch created successfully.', 'success')
        return redirect(url_for('feedlot.list_batches', feedlot_id=feedlot_id))
    
    return render_template('feedlot/batches/create.html', feedlot=feedlot)

@feedlot_bp.route('/feedlot/<feedlot_id>/batches/<batch_id>/view')
@login_required
@feedlot_access_required()
def view_batch(feedlot_id, batch_id):
    """View batch details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    batch = Batch.find_by_id(batch_id)
    
    if not batch:
        flash('Batch not found.', 'error')
        return redirect(url_for('feedlot.list_batches', feedlot_id=feedlot_id))
    
    cattle = Cattle.find_by_batch(batch_id)
    batch['cattle_count'] = len(cattle)
    
    return render_template('feedlot/batches/view.html', feedlot=feedlot, batch=batch, cattle=cattle)

# Cattle Management Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/cattle')
@login_required
@feedlot_access_required()
def list_cattle(feedlot_id):
    """List all cattle for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    all_cattle = Cattle.find_by_feedlot(feedlot_id)
    
    return render_template('feedlot/cattle/list.html', feedlot=feedlot, cattle=all_cattle)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/create', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def create_cattle(feedlot_id):
    """Create cattle record"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    
    if request.method == 'POST':
        batch_id = request.form.get('batch_id')
        cattle_id = request.form.get('cattle_id')
        breed = request.form.get('breed')
        weight = float(request.form.get('weight'))
        health_status = request.form.get('health_status')
        pen_id = request.form.get('pen_id') or None
        notes = request.form.get('notes')
        
        # Check pen capacity if pen is assigned
        if pen_id and not Pen.is_capacity_available(pen_id):
            flash('Pen is at full capacity.', 'error')
            batches = Batch.find_by_feedlot(feedlot_id)
            pens = Pen.find_by_feedlot(feedlot_id)
            return render_template('feedlot/cattle/create.html', 
                                 feedlot=feedlot, 
                                 batches=batches, 
                                 pens=pens)
        
        cattle_record_id = Cattle.create_cattle(feedlot_id, batch_id, cattle_id, breed, 
                                               weight, health_status, pen_id, notes)
        flash('Cattle record created successfully.', 'success')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    batches = Batch.find_by_feedlot(feedlot_id)
    pens = Pen.find_by_feedlot(feedlot_id)
    
    return render_template('feedlot/cattle/create.html', feedlot=feedlot, batches=batches, pens=pens)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/<cattle_id>/view')
@login_required
@feedlot_access_required()
def view_cattle(feedlot_id, cattle_id):
    """View cattle details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    cattle = Cattle.find_by_id(cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    pen = Pen.find_by_id(cattle['pen_id']) if cattle.get('pen_id') else None
    batch = Batch.find_by_id(cattle['batch_id'])
    
    return render_template('feedlot/cattle/view.html', 
                         feedlot=feedlot, 
                         cattle=cattle, 
                         pen=pen, 
                         batch=batch)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/<cattle_id>/move', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def move_cattle(feedlot_id, cattle_id):
    """Move cattle to different pen"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    cattle = Cattle.find_by_id(cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        new_pen_id = request.form.get('pen_id')
        
        if new_pen_id and not Pen.is_capacity_available(new_pen_id):
            flash('Selected pen is at full capacity.', 'error')
            pens = Pen.find_by_feedlot(feedlot_id)
            return render_template('feedlot/cattle/move.html', 
                                 feedlot=feedlot, 
                                 cattle=cattle, 
                                 pens=pens)
        
        Cattle.move_cattle(cattle_id, new_pen_id)
        flash('Cattle moved successfully.', 'success')
        return redirect(url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id))
    
    pens = Pen.find_by_feedlot(feedlot_id)
    return render_template('feedlot/cattle/move.html', feedlot=feedlot, cattle=cattle, pens=pens)

