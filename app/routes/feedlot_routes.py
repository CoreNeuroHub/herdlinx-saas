from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from bson import ObjectId
from datetime import datetime
from app.models.feedlot import Feedlot
from app.models.pen import Pen
from app.models.batch import Batch
from app.models.cattle import Cattle
from app.models.manifest_template import ManifestTemplate
from app.models.manifest import Manifest
from app.routes.auth_routes import login_required, feedlot_access_required
from app.utils.manifest_generator import generate_manifest_data, generate_pdf

feedlot_bp = Blueprint('feedlot', __name__)

def get_feedlot_code(feedlot_id):
    """Helper function to get feedlot_code from feedlot_id"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if feedlot:
        return feedlot.get('feedlot_code')
    return None

def convert_objectids_to_strings(data):
    """Recursively convert ObjectId objects to strings for JSON serialization"""
    if isinstance(data, dict):
        return {key: convert_objectids_to_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectids_to_strings(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data

@feedlot_bp.route('/feedlot/<feedlot_id>/dashboard')
@login_required
@feedlot_access_required()
def dashboard(feedlot_id):
    """Feedlot dashboard"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    statistics = Feedlot.get_statistics(feedlot_id)
    
    # Get all batches
    all_batches = Batch.find_by_feedlot(feedlot_code, feedlot_id)
    
    # Normalize batch data: ensure event_date exists (for backward compatibility with induction_date)
    # Also add cattle count and ensure event_type exists
    for batch in all_batches:
        if 'event_date' not in batch and 'induction_date' in batch:
            batch['event_date'] = batch['induction_date']
        # Add cattle count
        batch['cattle_count'] = Batch.get_cattle_count(feedlot_code, str(batch['_id']))
        # Ensure event_type exists (default to 'induction' if not set)
        if 'event_type' not in batch:
            batch['event_type'] = 'induction'
        # Ensure event_date exists for sorting (use created_at as fallback)
        if 'event_date' not in batch:
            batch['event_date'] = batch.get('created_at')
    
    # Sort by event_date descending (latest first), then take top 5
    recent_batches = sorted(
        all_batches,
        key=lambda b: b.get('event_date') or b.get('created_at') or datetime.min,
        reverse=True
    )[:5]
    
    user_type = session.get('user_type')
    
    return render_template('feedlot/dashboard.html', 
                         feedlot=feedlot, 
                         statistics=statistics,
                         recent_batches=recent_batches,
                         user_type=user_type)

# Pen Management Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/pens')
@login_required
@feedlot_access_required()
def list_pens(feedlot_id):
    """List all pens for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    pens = Pen.find_by_feedlot(feedlot_id)
    
    # Add current cattle count to each pen
    for pen in pens:
        pen['current_count'] = Pen.get_current_cattle_count(str(pen['_id']), feedlot_code)
    
    # Get pen map configuration
    pen_map = Feedlot.get_pen_map(feedlot_id)
    
    # Create pen lookup dictionary for map display (convert ObjectId to string)
    pen_lookup = {}
    if pen_map:
        for pen in pens:
            pen_id_str = str(pen['_id'])
            # Convert all ObjectIds to strings for JSON serialization
            pen_copy = convert_objectids_to_strings(pen)
            pen_lookup[pen_id_str] = pen_copy
    
    return render_template('feedlot/pens/list.html', 
                         feedlot=feedlot, 
                         pens=pens,
                         pen_map=pen_map,
                         pen_lookup=pen_lookup)

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/create', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def create_pen(feedlot_id):
    """Create a new pen"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
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
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    pen = Pen.find_by_id(pen_id)
    
    if not pen:
        flash('Pen not found.', 'error')
        return redirect(url_for('feedlot.list_pens', feedlot_id=feedlot_id))
    
    cattle = Cattle.find_by_pen(feedlot_code, pen_id)
    pen['current_count'] = len(cattle)
    
    return render_template('feedlot/pens/view.html', feedlot=feedlot, pen=pen, cattle=cattle)

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/<pen_id>/edit', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def edit_pen(feedlot_id, pen_id):
    """Edit pen details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
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
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    Pen.delete_pen(pen_id)
    flash('Pen deleted successfully.', 'success')
    return redirect(url_for('feedlot.list_pens', feedlot_id=feedlot_id))

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/map', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def map_pens(feedlot_id):
    """Map pens on a grid layout"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    pens = Pen.find_by_feedlot(feedlot_id)
    
    if request.method == 'POST':
        data = request.get_json()
        grid_width = int(data.get('grid_width', 10))
        grid_height = int(data.get('grid_height', 10))
        pen_placements = data.get('pen_placements', [])
        
        Feedlot.save_pen_map(feedlot_id, grid_width, grid_height, pen_placements)
        return jsonify({'success': True, 'message': 'Pen map saved successfully.'}), 200
    
    # Get existing pen map if available
    pen_map = Feedlot.get_pen_map(feedlot_id)
    
    return render_template('feedlot/pens/map.html', 
                         feedlot=feedlot, 
                         pens=pens,
                         pen_map=pen_map)

@feedlot_bp.route('/feedlot/<feedlot_id>/pens/map/view')
@login_required
@feedlot_access_required()
def view_pen_map(feedlot_id):
    """View pen map (read-only display)"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    pens = Pen.find_by_feedlot(feedlot_id)
    pen_map = Feedlot.get_pen_map(feedlot_id)
    
    # Create pen lookup dictionary (convert ObjectId to string for JSON serialization)
    pen_lookup = {}
    for pen in pens:
        pen_id_str = str(pen['_id'])
        # Convert all ObjectIds to strings for JSON serialization
        pen_copy = convert_objectids_to_strings(pen)
        pen_lookup[pen_id_str] = pen_copy
    
    return render_template('feedlot/pens/map_view.html',
                         feedlot=feedlot,
                         pens=pens,
                         pen_map=pen_map,
                         pen_lookup=pen_lookup)

# Batch Management Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/batches')
@login_required
@feedlot_access_required()
def list_batches(feedlot_id):
    """List all batches for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    batches = Batch.find_by_feedlot(feedlot_code, feedlot_id)
    
    # Add cattle count to each batch and normalize event_date (for backward compatibility)
    for batch in batches:
        batch['cattle_count'] = Batch.get_cattle_count(feedlot_code, str(batch['_id']))
        # Normalize: ensure event_date exists (for backward compatibility with induction_date)
        if 'event_date' not in batch and 'induction_date' in batch:
            batch['event_date'] = batch['induction_date']
    
    return render_template('feedlot/batches/list.html', feedlot=feedlot, batches=batches)

@feedlot_bp.route('/feedlot/<feedlot_id>/batches/create', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def create_batch(feedlot_id):
    """Create a new batch"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        batch_number = request.form.get('batch_number')
        event_date_str = request.form.get('event_date')
        funder = request.form.get('funder')
        notes = request.form.get('notes')
        event_type = request.form.get('event_type', 'induction')
        
        # Validate event_type
        valid_event_types = ['induction', 'pairing', 'checkin', 'repair', 'export']
        if event_type not in valid_event_types:
            event_type = 'induction'
        
        # Convert date string to datetime object
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d') if event_date_str else None
        
        batch_id = Batch.create_batch(feedlot_code, feedlot_id, batch_number, event_date, funder, notes, event_type)
        flash('Batch created successfully.', 'success')
        return redirect(url_for('feedlot.list_batches', feedlot_id=feedlot_id))
    
    return render_template('feedlot/batches/create.html', feedlot=feedlot)

@feedlot_bp.route('/feedlot/<feedlot_id>/batches/<batch_id>/view')
@login_required
@feedlot_access_required()
def view_batch(feedlot_id, batch_id):
    """View batch details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    batch = Batch.find_by_id(feedlot_code, batch_id)
    
    if not batch:
        flash('Batch not found.', 'error')
        return redirect(url_for('feedlot.list_batches', feedlot_id=feedlot_id))
    
    # Normalize: ensure event_date exists (for backward compatibility with induction_date)
    if 'event_date' not in batch and 'induction_date' in batch:
        batch['event_date'] = batch['induction_date']
    
    cattle = Cattle.find_by_batch(feedlot_code, batch_id)
    batch['cattle_count'] = len(cattle)
    
    # Get historical cattle count from the batch's cattle_ids array
    batch['historical_cattle_count'] = Batch.get_historical_cattle_count(feedlot_code, batch_id)
    
    return render_template('feedlot/batches/view.html', feedlot=feedlot, batch=batch, cattle=cattle)

@feedlot_bp.route('/feedlot/<feedlot_id>/batches/<batch_id>/edit', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def edit_batch(feedlot_id, batch_id):
    """Edit batch details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    batch = Batch.find_by_id(feedlot_code, batch_id)
    
    if not batch:
        flash('Batch not found.', 'error')
        return redirect(url_for('feedlot.list_batches', feedlot_id=feedlot_id))
    
    # Normalize: ensure event_date exists (for backward compatibility with induction_date)
    if 'event_date' not in batch and 'induction_date' in batch:
        batch['event_date'] = batch['induction_date']
    
    if request.method == 'POST':
        batch_number = request.form.get('batch_number')
        event_date_str = request.form.get('event_date')
        funder = request.form.get('funder')
        notes = request.form.get('notes')
        event_type = request.form.get('event_type', 'induction')
        
        # Validate event_type
        valid_event_types = ['induction', 'pairing', 'checkin', 'repair', 'export']
        if event_type not in valid_event_types:
            event_type = 'induction'
        
        # Convert date string to datetime object
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d') if event_date_str else None
        
        update_data = {
            'batch_number': batch_number,
            'event_date': event_date,
            'funder': funder,
            'notes': notes or '',
            'event_type': event_type
        }
        
        Batch.update_batch(feedlot_code, batch_id, update_data)
        flash('Batch updated successfully.', 'success')
        return redirect(url_for('feedlot.view_batch', feedlot_id=feedlot_id, batch_id=batch_id))
    
    return render_template('feedlot/batches/edit.html', feedlot=feedlot, batch=batch)

@feedlot_bp.route('/feedlot/<feedlot_id>/batches/<batch_id>/delete', methods=['POST'])
@login_required
@feedlot_access_required()
def delete_batch(feedlot_id, batch_id):
    """Delete a batch"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    batch = Batch.find_by_id(feedlot_code, batch_id)
    
    if not batch:
        flash('Batch not found.', 'error')
        return redirect(url_for('feedlot.list_batches', feedlot_id=feedlot_id))
    
    Batch.delete_batch(feedlot_code, batch_id)
    flash('Batch deleted successfully.', 'success')
    return redirect(url_for('feedlot.list_batches', feedlot_id=feedlot_id))

# Cattle Management Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/cattle')
@login_required
@feedlot_access_required()
def list_cattle(feedlot_id):
    """List all cattle for a feedlot with search, filter, and sort"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    cattle_status_filter = request.args.get('cattle_status', '')
    sex_filter = request.args.get('sex', '')
    pen_filter = request.args.get('pen_id', '')
    sort_by = request.args.get('sort_by', 'cattle_id')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Get filtered cattle
    cattle = Cattle.find_by_feedlot_with_filters(
        feedlot_code,
        feedlot_id,
        search=search if search else None,
        cattle_status=cattle_status_filter if cattle_status_filter else None,
        sex=sex_filter if sex_filter else None,
        pen_id=pen_filter if pen_filter else None,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get all pens for filter dropdown
    pens = Pen.find_by_feedlot(feedlot_id)
    
    # Create pen lookup dictionary for efficient template access
    pen_map = {str(pen['_id']): pen for pen in pens}
    
    # Get unique values for filter dropdowns
    all_cattle = Cattle.find_by_feedlot(feedlot_code, feedlot_id)
    unique_cattle_statuses = list(set(c.get('cattle_status', '') for c in all_cattle if c.get('cattle_status')))
    unique_sexes = list(set(c.get('sex', '') for c in all_cattle if c.get('sex')))
    
    return render_template('feedlot/cattle/list.html', 
                         feedlot=feedlot, 
                         cattle=cattle,
                         pens=pens,
                         pen_map=pen_map,
                         unique_cattle_statuses=sorted(unique_cattle_statuses),
                         unique_sexes=sorted(unique_sexes),
                         current_search=search,
                         current_cattle_status=cattle_status_filter,
                         current_sex=sex_filter,
                         current_pen=pen_filter,
                         current_sort_by=sort_by,
                         current_sort_order=sort_order)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/create', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def create_cattle(feedlot_id):
    """Create cattle record"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        batch_id = request.form.get('batch_id') or None
        cattle_id = request.form.get('cattle_id')
        sex = request.form.get('sex')
        weight = float(request.form.get('weight'))
        cattle_status = request.form.get('cattle_status')
        lf_tag = request.form.get('lf_tag')
        uhf_tag = request.form.get('uhf_tag')
        pen_id = request.form.get('pen_id') or None
        notes = request.form.get('notes')
        color = request.form.get('color')
        breed = request.form.get('breed')
        brand_drawings = request.form.get('brand_drawings')
        brand_locations = request.form.get('brand_locations')
        other_marks = request.form.get('other_marks')
        
        # Check pen capacity if pen is assigned
        if pen_id and not Pen.is_capacity_available(pen_id, feedlot_code):
            flash('Pen is at full capacity.', 'error')
            batches = Batch.find_by_feedlot(feedlot_code, feedlot_id)
            pens = Pen.find_by_feedlot(feedlot_id)
            return render_template('feedlot/cattle/create.html', 
                                 feedlot=feedlot, 
                                 batches=batches, 
                                 pens=pens)
        
        created_by = session.get('username', 'user')
        cattle_record_id = Cattle.create_cattle(feedlot_code, feedlot_id, cattle_id, sex, 
                                               weight, cattle_status, batch_id=batch_id, lf_tag=lf_tag, uhf_tag=uhf_tag, pen_id=pen_id, notes=notes,
                                               color=color, breed=breed, brand_drawings=brand_drawings, brand_locations=brand_locations, other_marks=other_marks, created_by=created_by)
        flash('Cattle record created successfully.', 'success')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    batches = Batch.find_by_feedlot(feedlot_code, feedlot_id)
    pens = Pen.find_by_feedlot(feedlot_id)
    
    return render_template('feedlot/cattle/create.html', feedlot=feedlot, batches=batches, pens=pens)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/<cattle_id>/view')
@login_required
@feedlot_access_required()
def view_cattle(feedlot_id, cattle_id):
    """View cattle details"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    cattle = Cattle.find_by_id(feedlot_code, cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    pen = Pen.find_by_id(cattle['pen_id']) if cattle.get('pen_id') else None
    batch = Batch.find_by_id(feedlot_code, cattle['batch_id']) if cattle.get('batch_id') else None
    
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
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    cattle = Cattle.find_by_id(feedlot_code, cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        new_pen_id = request.form.get('pen_id')
        moved_by = session.get('username', 'user')
        
        if new_pen_id and not Pen.is_capacity_available(new_pen_id, feedlot_code):
            flash('Selected pen is at full capacity.', 'error')
            pens = Pen.find_by_feedlot(feedlot_id)
            return render_template('feedlot/cattle/move.html', 
                                 feedlot=feedlot, 
                                 cattle=cattle, 
                                 pens=pens)
        
        Cattle.move_cattle(feedlot_code, cattle_id, new_pen_id, moved_by)
        flash('Cattle moved successfully.', 'success')
        return redirect(url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id))
    
    pens = Pen.find_by_feedlot(feedlot_id)
    return render_template('feedlot/cattle/move.html', feedlot=feedlot, cattle=cattle, pens=pens)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/<cattle_id>/add_weight', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def add_weight_record(feedlot_id, cattle_id):
    """Add a weight record for cattle"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    cattle = Cattle.find_by_id(feedlot_code, cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        weight = float(request.form.get('weight'))
        recorded_by = request.form.get('recorded_by', 'user')
        
        Cattle.add_weight_record(feedlot_code, cattle_id, weight, recorded_by)
        flash('Weight record added successfully.', 'success')
        return redirect(url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id))
    
    return render_template('feedlot/cattle/add_weight.html', feedlot=feedlot, cattle=cattle)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/<cattle_id>/add_note', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def add_note(feedlot_id, cattle_id):
    """Add a note for cattle"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    cattle = Cattle.find_by_id(feedlot_code, cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        note = request.form.get('note', '').strip()
        recorded_by = session.get('username', 'user')
        
        if not note:
            flash('Note cannot be empty.', 'error')
            return render_template('feedlot/cattle/add_note.html', feedlot=feedlot, cattle=cattle)
        
        Cattle.add_note(feedlot_code, cattle_id, note, recorded_by)
        flash('Note added successfully.', 'success')
        return redirect(url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id))
    
    return render_template('feedlot/cattle/add_note.html', feedlot=feedlot, cattle=cattle)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/<cattle_id>/update_tags', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def update_tags(feedlot_id, cattle_id):
    """Update/re-pair LF and UHF tags for cattle"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    cattle = Cattle.find_by_id(feedlot_code, cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        new_lf_tag = request.form.get('lf_tag', '').strip()
        new_uhf_tag = request.form.get('uhf_tag', '').strip()
        updated_by = session.get('username', 'user')
        
        Cattle.update_tag_pair(feedlot_code, cattle_id, new_lf_tag, new_uhf_tag, updated_by)
        flash('Tag pair updated successfully. Previous pair has been saved to history.', 'success')
        return redirect(url_for('feedlot.view_cattle', feedlot_id=feedlot_id, cattle_id=cattle_id))
    
    return render_template('feedlot/cattle/update_tags.html', feedlot=feedlot, cattle=cattle)

@feedlot_bp.route('/feedlot/<feedlot_id>/cattle/<cattle_id>/delete', methods=['POST'])
@login_required
@feedlot_access_required()
def delete_cattle(feedlot_id, cattle_id):
    """Delete a cattle record"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('auth.login'))
    
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('auth.login'))
    
    cattle = Cattle.find_by_id(feedlot_code, cattle_id)
    
    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))
    
    deleted_by = session.get('username', 'user')
    Cattle.delete_cattle(feedlot_code, cattle_id, deleted_by)
    flash('Cattle record deleted successfully.', 'success')
    return redirect(url_for('feedlot.list_cattle', feedlot_id=feedlot_id))

# Manifest Export Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/export', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def export_manifest(feedlot_id):
    """Export manifest for cattle"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('feedlot.dashboard', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        # Get selected cattle
        feedlot_code = feedlot.get('feedlot_code')
        if not feedlot_code:
            flash('Feedlot code not found.', 'error')
            return redirect(url_for('feedlot.export_manifest', feedlot_id=feedlot_id))
        
        # Get selected cattle IDs from form
        cattle_ids = request.form.getlist('cattle_ids')
        cattle_list = []
        for cattle_id in cattle_ids:
            cattle = Cattle.find_by_id(feedlot_code, cattle_id)
            if cattle:
                cattle_list.append(cattle)
        
        if not cattle_list:
            flash('No cattle selected for export.', 'error')
            return redirect(url_for('feedlot.export_manifest', feedlot_id=feedlot_id))
        
        # Get template or manual data
        template_id = request.form.get('template_id')
        template_data = None
        if template_id and template_id != 'none':
            template = ManifestTemplate.find_by_id(template_id)
            if template:
                template_data = {
                    'owner_name': template.get('owner_name', ''),
                    'owner_phone': template.get('owner_phone', ''),
                    'owner_address': template.get('owner_address', ''),
                    'dealer_name': template.get('dealer_name', ''),
                    'dealer_phone': template.get('dealer_phone', ''),
                    'dealer_address': template.get('dealer_address', ''),
                    'default_destination_name': template.get('default_destination_name', ''),
                    'default_destination_address': template.get('default_destination_address', ''),
                    'default_transporter_name': template.get('default_transporter_name', ''),
                    'default_transporter_phone': template.get('default_transporter_phone', ''),
                    'default_transporter_trailer': template.get('default_transporter_trailer', ''),
                    'default_purpose': template.get('default_purpose', 'transport_only'),
                    'default_premises_id_before': template.get('default_premises_id_before', ''),
                    'default_premises_id_destination': template.get('default_premises_id_destination', ''),
                }
        
        # Get manual entry data if no template
        manual_data = None
        if not template_data:
            manual_data = {
                'date': request.form.get('date', datetime.now().strftime('%Y-%m-%d')),
                'owner_name': request.form.get('owner_name', ''),
                'owner_phone': request.form.get('owner_phone', ''),
                'owner_address': request.form.get('owner_address', ''),
                'dealer_name': request.form.get('dealer_name', ''),
                'dealer_phone': request.form.get('dealer_phone', ''),
                'dealer_address': request.form.get('dealer_address', ''),
                'on_account_of': request.form.get('on_account_of', ''),
                'location_before': request.form.get('location_before', feedlot.get('name', '')),
                'premises_id_before': request.form.get('premises_id_before', ''),
                'reason_for_transport': request.form.get('reason_for_transport', 'transport_to'),
                'destination_name': request.form.get('destination_name', ''),
                'destination_address': request.form.get('destination_address', ''),
                'transporter_name': request.form.get('transporter_name', ''),
                'transporter_phone': request.form.get('transporter_phone', ''),
                'transporter_trailer': request.form.get('transporter_trailer', ''),
                'purpose': request.form.get('purpose', 'transport_only'),
                'premises_id_destination': request.form.get('premises_id_destination', ''),
            }
        
        # Generate manifest data
        manifest_data = generate_manifest_data(cattle_list, template_data, feedlot, manual_data)
        
        # Get cattle IDs for history tracking
        cattle_ids = [str(cattle['_id']) for cattle in cattle_list]
        
        # Save manifest to history
        template_id = request.form.get('template_id') if request.form.get('template_id') != 'none' else None
        created_by = session.get('username', 'unknown')
        manifest_record_id = Manifest.create_manifest(
            feedlot_id=feedlot_id,
            manifest_data=manifest_data,
            cattle_ids=cattle_ids,
            template_id=template_id,
            created_by=created_by
        )
        
        # Always generate HTML format
        return render_template('feedlot/manifest/manifest_html.html', 
                             manifest_data=manifest_data,
                             feedlot_id=feedlot_id,
                             manifest_id=manifest_record_id)
    
    # GET request - show export form
    feedlot_code = feedlot.get('feedlot_code')
    if not feedlot_code:
        flash('Feedlot code not found.', 'error')
        return redirect(url_for('feedlot.dashboard', feedlot_id=feedlot_id))
    
    pens = Pen.find_by_feedlot(feedlot_id)
    
    # Filter cattle by status = 'Export'
    all_cattle = Cattle.find_by_feedlot_with_filters(
        feedlot_code, 
        feedlot_id, 
        cattle_status='Export'
    )
    
    # Convert ObjectIds to strings for cattle _id, batch_id and pen_id for easier template handling
    for cattle in all_cattle:
        cattle['_id'] = str(cattle['_id'])
        if cattle.get('batch_id'):
            cattle['batch_id'] = str(cattle['batch_id'])
        if cattle.get('pen_id'):
            cattle['pen_id'] = str(cattle['pen_id'])
    
    # Filter batches by event_type = 'export'
    all_batches = Batch.find_by_feedlot(feedlot_code, feedlot_id)
    export_batches = [b for b in all_batches if b.get('event_type') == 'export']
    
    # Convert batch ObjectIds to strings
    for batch in export_batches:
        batch['_id'] = str(batch['_id'])
    
    # Convert pen ObjectIds to strings
    for pen in pens:
        pen['_id'] = str(pen['_id'])
        pen['cattle_count'] = Pen.get_current_cattle_count(pen['_id'], feedlot_code)
    
    templates = ManifestTemplate.find_by_feedlot(feedlot_id)
    
    return render_template('feedlot/manifest/export.html',
                         feedlot=feedlot,
                         pens=pens,
                         cattle=all_cattle,
                         batches=export_batches,
                         templates=templates)

@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/templates')
@login_required
@feedlot_access_required()
def list_manifest_templates(feedlot_id):
    """List manifest templates for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('feedlot.dashboard', feedlot_id=feedlot_id))
    
    templates = ManifestTemplate.find_by_feedlot(feedlot_id)
    return render_template('feedlot/manifest/templates.html',
                         feedlot=feedlot,
                         templates=templates)

@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/templates/create', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def create_manifest_template(feedlot_id):
    """Create a new manifest template"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('feedlot.dashboard', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        template_id = ManifestTemplate.create_template(
            feedlot_id=feedlot_id,
            name=request.form.get('name'),
            owner_name=request.form.get('owner_name'),
            owner_phone=request.form.get('owner_phone'),
            owner_address=request.form.get('owner_address'),
            dealer_name=request.form.get('dealer_name'),
            dealer_phone=request.form.get('dealer_phone'),
            dealer_address=request.form.get('dealer_address'),
            default_destination_name=request.form.get('default_destination_name'),
            default_destination_address=request.form.get('default_destination_address'),
            default_transporter_name=request.form.get('default_transporter_name'),
            default_transporter_phone=request.form.get('default_transporter_phone'),
            default_transporter_trailer=request.form.get('default_transporter_trailer'),
            default_purpose=request.form.get('default_purpose', 'transport_only'),
            default_premises_id_before=request.form.get('default_premises_id_before'),
            default_premises_id_destination=request.form.get('default_premises_id_destination'),
            is_default=request.form.get('is_default') == 'on'
        )
        flash('Manifest template created successfully.', 'success')
        return redirect(url_for('feedlot.list_manifest_templates', feedlot_id=feedlot_id))
    
    return render_template('feedlot/manifest/template_form.html', feedlot=feedlot, template=None)

@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/templates/<template_id>/edit', methods=['GET', 'POST'])
@login_required
@feedlot_access_required()
def edit_manifest_template(feedlot_id, template_id):
    """Edit a manifest template"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    template = ManifestTemplate.find_by_id(template_id)
    
    if not feedlot or not template:
        flash('Feedlot or template not found.', 'error')
        return redirect(url_for('feedlot.list_manifest_templates', feedlot_id=feedlot_id))
    
    if request.method == 'POST':
        update_data = {
            'name': request.form.get('name'),
            'owner_name': request.form.get('owner_name'),
            'owner_phone': request.form.get('owner_phone'),
            'owner_address': request.form.get('owner_address'),
            'dealer_name': request.form.get('dealer_name'),
            'dealer_phone': request.form.get('dealer_phone'),
            'dealer_address': request.form.get('dealer_address'),
            'default_destination_name': request.form.get('default_destination_name'),
            'default_destination_address': request.form.get('default_destination_address'),
            'default_transporter_name': request.form.get('default_transporter_name'),
            'default_transporter_phone': request.form.get('default_transporter_phone'),
            'default_transporter_trailer': request.form.get('default_transporter_trailer'),
            'default_purpose': request.form.get('default_purpose', 'transport_only'),
            'default_premises_id_before': request.form.get('default_premises_id_before'),
            'default_premises_id_destination': request.form.get('default_premises_id_destination'),
            'is_default': request.form.get('is_default') == 'on'
        }
        ManifestTemplate.update_template(template_id, update_data)
        flash('Manifest template updated successfully.', 'success')
        return redirect(url_for('feedlot.list_manifest_templates', feedlot_id=feedlot_id))
    
    return render_template('feedlot/manifest/template_form.html', feedlot=feedlot, template=template)

@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/templates/<template_id>/delete', methods=['POST'])
@login_required
@feedlot_access_required()
def delete_manifest_template(feedlot_id, template_id):
    """Delete a manifest template"""
    ManifestTemplate.delete_template(template_id)
    flash('Manifest template deleted successfully.', 'success')
    return redirect(url_for('feedlot.list_manifest_templates', feedlot_id=feedlot_id))

# Manifest History Routes
@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/history')
@login_required
@feedlot_access_required()
def list_manifest_history(feedlot_id):
    """List manifest history for a feedlot"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    if not feedlot:
        flash('Feedlot not found.', 'error')
        return redirect(url_for('feedlot.dashboard', feedlot_id=feedlot_id))
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    skip = (page - 1) * per_page
    
    # Get manifests
    manifests = Manifest.find_by_feedlot(feedlot_id, limit=per_page, skip=skip)
    total_count = Manifest.count_by_feedlot(feedlot_id)
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('feedlot/manifest/history.html',
                         feedlot=feedlot,
                         manifests=manifests,
                         page=page,
                         per_page=per_page,
                         total_count=total_count,
                         total_pages=total_pages)

@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/history/<manifest_id>/view')
@login_required
@feedlot_access_required()
def view_manifest_history(feedlot_id, manifest_id):
    """View a specific manifest from history"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    manifest = Manifest.find_by_id(manifest_id)
    
    if not feedlot or not manifest:
        flash('Feedlot or manifest not found.', 'error')
        return redirect(url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id))
    
    # Verify manifest belongs to feedlot
    if str(manifest['feedlot_id']) != feedlot_id:
        flash('Manifest not found.', 'error')
        return redirect(url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id))
    
    manifest_data = manifest.get('manifest_data', {})
    
    return render_template('feedlot/manifest/view_history.html',
                         feedlot=feedlot,
                         manifest=manifest,
                         manifest_data=manifest_data)

@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/history/<manifest_id>/download')
@login_required
@feedlot_access_required()
def download_manifest_history(feedlot_id, manifest_id):
    """Download a manifest from history as PDF"""
    feedlot = Feedlot.find_by_id(feedlot_id)
    manifest = Manifest.find_by_id(manifest_id)
    
    if not feedlot or not manifest:
        flash('Feedlot or manifest not found.', 'error')
        return redirect(url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id))
    
    # Verify manifest belongs to feedlot
    if str(manifest['feedlot_id']) != feedlot_id:
        flash('Manifest not found.', 'error')
        return redirect(url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id))
    
    manifest_data = manifest.get('manifest_data', {})
    
    # Generate PDF
    pdf_buffer = generate_pdf(manifest_data)
    
    # Create filename with manifest date
    manifest_date = manifest_data.get('part_b', {}).get('date', datetime.now().strftime('%Y%m%d'))
    filename = f"manifest_{feedlot_id}_{manifest_date}_{manifest_id[:8]}.pdf"
    
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@feedlot_bp.route('/feedlot/<feedlot_id>/manifest/history/<manifest_id>/delete', methods=['POST'])
@login_required
@feedlot_access_required()
def delete_manifest_history(feedlot_id, manifest_id):
    """Delete a manifest from history"""
    manifest = Manifest.find_by_id(manifest_id)
    
    if not manifest:
        flash('Manifest not found.', 'error')
        return redirect(url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id))
    
    # Verify manifest belongs to feedlot
    if str(manifest['feedlot_id']) != feedlot_id:
        flash('Manifest not found.', 'error')
        return redirect(url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id))
    
    Manifest.delete_manifest(manifest_id)
    flash('Manifest deleted successfully.', 'success')
    return redirect(url_for('feedlot.list_manifest_history', feedlot_id=feedlot_id))

