from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from office_app.models.pen import Pen
from office_app.models.batch import Batch
from office_app.models.cattle import Cattle
from office_app.routes.auth_routes import login_required, admin_required
from office_app import db
from sqlalchemy import func

office_bp = Blueprint('office', __name__, url_prefix='/office')

def get_statistics():
    """Get office statistics"""
    total_pens = db.session.query(func.count(Pen.id)).scalar() or 0
    total_cattle = db.session.query(func.count(Cattle.id)).scalar() or 0
    total_batches = db.session.query(func.count(Batch.id)).scalar() or 0
    
    return {
        'total_pens': total_pens,
        'total_cattle': total_cattle,
        'total_batches': total_batches
    }

@office_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Office dashboard"""
    statistics = get_statistics()
    
    # Get recent batches
    recent_batches = Batch.find_all()[:5]
    
    return render_template('office/dashboard.html', 
                         statistics=statistics,
                         recent_batches=recent_batches)

# Pen Management Routes
@office_bp.route('/pens')
@login_required
@admin_required
def list_pens():
    """List all pens"""
    pens = Pen.find_all()
    
    # Add current cattle count to each pen
    for pen in pens:
        pen.current_count = Pen.get_current_cattle_count(pen.id)
    
    return render_template('office/pens/list.html', pens=pens)

@office_bp.route('/pens/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_pen():
    """Create a new pen"""
    if request.method == 'POST':
        pen_number = request.form.get('pen_number')
        capacity = int(request.form.get('capacity'))
        description = request.form.get('description')
        
        pen_id = Pen.create_pen(pen_number, capacity, description)
        flash('Pen created successfully.', 'success')
        return redirect(url_for('office.list_pens'))
    
    return render_template('office/pens/create.html')

@office_bp.route('/pens/<int:pen_id>/view')
@login_required
@admin_required
def view_pen(pen_id):
    """View pen details"""
    pen = Pen.find_by_id(pen_id)
    
    if not pen:
        flash('Pen not found.', 'error')
        return redirect(url_for('office.list_pens'))
    
    cattle = Cattle.find_by_pen(pen_id)
    pen.current_count = len(cattle)
    
    return render_template('office/pens/view.html', pen=pen, cattle=cattle)

@office_bp.route('/pens/<int:pen_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_pen(pen_id):
    """Edit pen details"""
    pen = Pen.find_by_id(pen_id)
    
    if not pen:
        flash('Pen not found.', 'error')
        return redirect(url_for('office.list_pens'))
    
    if request.method == 'POST':
        update_data = {
            'pen_number': request.form.get('pen_number'),
            'capacity': int(request.form.get('capacity')),
            'description': request.form.get('description')
        }
        
        Pen.update_pen(pen_id, update_data)
        flash('Pen updated successfully.', 'success')
        return redirect(url_for('office.view_pen', pen_id=pen_id))
    
    return render_template('office/pens/edit.html', pen=pen)

@office_bp.route('/pens/<int:pen_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_pen(pen_id):
    """Delete a pen"""
    Pen.delete_pen(pen_id)
    flash('Pen deleted successfully.', 'success')
    return redirect(url_for('office.list_pens'))

# Batch Management Routes
@office_bp.route('/batches')
@login_required
@admin_required
def list_batches():
    """List all batches"""
    batches = Batch.find_all()
    
    # Add cattle count to each batch
    for batch in batches:
        batch.cattle_count = Batch.get_cattle_count(batch.id)
    
    return render_template('office/batches/list.html', batches=batches)

@office_bp.route('/batches/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_batch():
    """Create a new batch"""
    if request.method == 'POST':
        batch_number = request.form.get('batch_number')
        induction_date_str = request.form.get('induction_date')
        source = request.form.get('source')
        notes = request.form.get('notes')
        
        # Convert date string to date object
        induction_date = datetime.strptime(induction_date_str, '%Y-%m-%d').date() if induction_date_str else None
        
        batch_id = Batch.create_batch(batch_number, induction_date, source, notes)
        flash('Batch created successfully.', 'success')
        return redirect(url_for('office.list_batches'))
    
    return render_template('office/batches/create.html')

@office_bp.route('/batches/<int:batch_id>/view')
@login_required
@admin_required
def view_batch(batch_id):
    """View batch details"""
    batch = Batch.find_by_id(batch_id)
    
    if not batch:
        flash('Batch not found.', 'error')
        return redirect(url_for('office.list_batches'))
    
    cattle = Cattle.find_by_batch(batch_id)
    batch.cattle_count = len(cattle)
    
    return render_template('office/batches/view.html', batch=batch, cattle=cattle)

# Cattle Management Routes
@office_bp.route('/cattle')
@login_required
@admin_required
def list_cattle():
    """List all cattle with search, filter, and sort"""
    # Get filter parameters
    search = request.args.get('search', '').strip()
    health_status_filter = request.args.get('health_status', '')
    sex_filter = request.args.get('sex', '')
    pen_filter = request.args.get('pen_id', '')
    sort_by = request.args.get('sort_by', 'cattle_id')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Get filtered cattle
    pen_id_int = int(pen_filter) if pen_filter else None
    cattle = Cattle.find_with_filters(
        search=search if search else None,
        health_status=health_status_filter if health_status_filter else None,
        sex=sex_filter if sex_filter else None,
        pen_id=pen_id_int,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get all pens for filter dropdown
    pens = Pen.find_all()
    
    # Get unique values for filter dropdowns
    all_cattle = Cattle.find_all()
    unique_health_statuses = list(set(c.health_status for c in all_cattle if c.health_status))
    unique_sexes = list(set(c.sex for c in all_cattle if c.sex))
    
    return render_template('office/cattle/list.html', 
                         cattle=cattle,
                         pens=pens,
                         unique_health_statuses=sorted(unique_health_statuses),
                         unique_sexes=sorted(unique_sexes),
                         current_search=search,
                         current_health_status=health_status_filter,
                         current_sex=sex_filter,
                         current_pen=pen_filter,
                         current_sort_by=sort_by,
                         current_sort_order=sort_order)

@office_bp.route('/cattle/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_cattle():
    """Create cattle record"""
    if request.method == 'POST':
        batch_id = int(request.form.get('batch_id'))
        cattle_id = request.form.get('cattle_id')
        sex = request.form.get('sex')
        weight = float(request.form.get('weight'))
        health_status = request.form.get('health_status')
        lf_tag = request.form.get('lf_tag')
        uhf_tag = request.form.get('uhf_tag')
        pen_id = int(request.form.get('pen_id')) if request.form.get('pen_id') else None
        notes = request.form.get('notes')
        
        # Check pen capacity if pen is assigned
        if pen_id and not Pen.is_capacity_available(pen_id):
            flash('Pen is at full capacity.', 'error')
            batches = Batch.find_all()
            pens = Pen.find_all()
            return render_template('office/cattle/create.html', 
                                 batches=batches, 
                                 pens=pens)
        
        cattle_record_id = Cattle.create_cattle(batch_id, cattle_id, sex, 
                                               weight, health_status, lf_tag, uhf_tag, pen_id, notes)
        flash('Cattle record created successfully.', 'success')
        return redirect(url_for('office.list_cattle'))
    
    batches = Batch.find_all()
    pens = Pen.find_all()
    
    return render_template('office/cattle/create.html', batches=batches, pens=pens)

@office_bp.route('/cattle/<int:cattle_id>/view')
@login_required
@admin_required
def view_cattle(cattle_id):
    """View cattle details"""
    cattle = Cattle.find_by_id(cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('office.list_cattle'))
    
    pen = Pen.find_by_id(cattle.pen_id) if cattle.pen_id else None
    batch = Batch.find_by_id(cattle.batch_id)
    
    return render_template('office/cattle/view.html', 
                         cattle=cattle, 
                         pen=pen, 
                         batch=batch)

@office_bp.route('/cattle/<int:cattle_id>/move', methods=['GET', 'POST'])
@login_required
@admin_required
def move_cattle(cattle_id):
    """Move cattle to different pen"""
    cattle = Cattle.find_by_id(cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('office.list_cattle'))
    
    if request.method == 'POST':
        new_pen_id = int(request.form.get('pen_id')) if request.form.get('pen_id') else None
        
        if new_pen_id and not Pen.is_capacity_available(new_pen_id):
            flash('Selected pen is at full capacity.', 'error')
            pens = Pen.find_all()
            return render_template('office/cattle/move.html', 
                                 cattle=cattle, 
                                 pens=pens)
        
        Cattle.move_cattle(cattle_id, new_pen_id)
        flash('Cattle moved successfully.', 'success')
        return redirect(url_for('office.view_cattle', cattle_id=cattle_id))
    
    pens = Pen.find_all()
    return render_template('office/cattle/move.html', cattle=cattle, pens=pens)

@office_bp.route('/cattle/<int:cattle_id>/add_weight', methods=['GET', 'POST'])
@login_required
@admin_required
def add_weight_record(cattle_id):
    """Add a weight record for cattle"""
    cattle = Cattle.find_by_id(cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('office.list_cattle'))
    
    if request.method == 'POST':
        weight = float(request.form.get('weight'))
        recorded_by = request.form.get('recorded_by', 'user')
        
        Cattle.add_weight_record(cattle_id, weight, recorded_by)
        flash('Weight record added successfully.', 'success')
        return redirect(url_for('office.view_cattle', cattle_id=cattle_id))
    
    return render_template('office/cattle/add_weight.html', cattle=cattle)

