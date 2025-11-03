from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from office_app.models.pen import Pen
from office_app.models.batch import Batch
from office_app.models.cattle import Cattle
from office_app.models.lora_payload_buffer import LoRaPayloadBuffer, PayloadStatus
from office_app.routes.auth_routes import login_required, admin_required
from office_app.utils.payload_processor import PayloadProcessor
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
    
    # Get tag pair history
    tag_pair_history = Cattle.get_tag_pair_history(cattle_id)
    
    return render_template('office/cattle/view.html', 
                         cattle=cattle, 
                         pen=pen, 
                         batch=batch,
                         tag_pair_history=tag_pair_history)

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

@office_bp.route('/cattle/<int:cattle_id>/update_tags', methods=['GET', 'POST'])
@login_required
@admin_required
def update_tags(cattle_id):
    """Update/re-pair LF and UHF tags for cattle"""
    cattle = Cattle.find_by_id(cattle_id)

    if not cattle:
        flash('Cattle record not found.', 'error')
        return redirect(url_for('office.list_cattle'))

    if request.method == 'POST':
        new_lf_tag = request.form.get('lf_tag', '').strip()
        new_uhf_tag = request.form.get('uhf_tag', '').strip()
        updated_by = session.get('username', 'user')

        Cattle.update_tag_pair(cattle_id, new_lf_tag, new_uhf_tag, updated_by)
        flash('Tag pair updated successfully. Previous pair has been saved to history.', 'success')
        return redirect(url_for('office.view_cattle', cattle_id=cattle_id))

    return render_template('office/cattle/update_tags.html', cattle=cattle)

# Batch Payload API Routes
@office_bp.route('/api/batch/payload', methods=['POST'])
@login_required
@admin_required
def process_batch_payload():
    """
    Process batch payload in format: hxb:batchnumber:LF:UHF or hxe:batchnumber:LF:UHF

    Expected JSON payload:
    {
        "payload": "hxb:BATCH001:LF123:UHF456"
    }

    Returns:
    {
        "success": bool,
        "message": str,
        "batch_id": int (if successful),
        "batch_number": str (if successful),
        "source_type": str (if successful)
    }
    """
    try:
        data = request.get_json()

        if not data or 'payload' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing payload field in request'
            }), 400

        payload = data.get('payload', '').strip()

        if not payload:
            return jsonify({
                'success': False,
                'message': 'Payload cannot be empty'
            }), 400

        # Parse the payload
        parsed = Batch.parse_payload(payload)

        if not parsed:
            return jsonify({
                'success': False,
                'message': 'Invalid payload format. Expected: source_type:batch_number:lf_tag:uhf_tag (e.g., hxb:BATCH001:LF123:UHF456)'
            }), 400

        source_type = parsed['source_type']
        batch_number = parsed['batch_number']
        lf_tag = parsed['lf_tag']
        uhf_tag = parsed['uhf_tag']

        # Determine source based on source_type
        source_label = 'Barn (HXB)' if source_type == 'hxb' else 'Export (HXE)'

        # Check if batch already exists
        existing_batch = Batch.query.filter_by(batch_number=batch_number).first()

        if existing_batch:
            # Update existing batch with source_type if not already set
            if not existing_batch.source_type:
                existing_batch.source_type = source_type
                existing_batch.updated_at = datetime.utcnow()
                db.session.commit()

            batch_id = existing_batch.id
            message = f'Batch {batch_number} already exists. Updated source information.'
        else:
            # Create new batch
            batch_id = Batch.create_batch(
                batch_number=batch_number,
                induction_date=datetime.utcnow().date(),
                source=source_label,
                source_type=source_type,
                notes=f'Created from payload with tags - LF: {lf_tag}, UHF: {uhf_tag}'
            )
            message = f'Batch {batch_number} created successfully from {source_label}'

        return jsonify({
            'success': True,
            'message': message,
            'batch_id': batch_id,
            'batch_number': batch_number,
            'source_type': source_type,
            'source_label': source_label,
            'lf_tag': lf_tag,
            'uhf_tag': uhf_tag
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing payload: {str(e)}'
        }), 500

@office_bp.route('/api/batch/validate-payload', methods=['POST'])
@login_required
@admin_required
def validate_batch_payload():
    """
    Validate batch payload format without creating/updating batch

    Expected JSON payload:
    {
        "payload": "hxb:BATCH001:LF123:UHF456"
    }

    Returns:
    {
        "valid": bool,
        "message": str,
        "parsed_data": dict (if valid)
    }
    """
    try:
        data = request.get_json()

        if not data or 'payload' not in data:
            return jsonify({
                'valid': False,
                'message': 'Missing payload field in request'
            }), 400

        payload = data.get('payload', '').strip()

        if not payload:
            return jsonify({
                'valid': False,
                'message': 'Payload cannot be empty'
            }), 400

        # Parse the payload
        parsed = Batch.parse_payload(payload)

        if not parsed:
            return jsonify({
                'valid': False,
                'message': 'Invalid payload format. Expected: source_type:batch_number:lf_tag:uhf_tag (e.g., hxb:BATCH001:LF123:UHF456)'
            }), 400

        return jsonify({
            'valid': True,
            'message': 'Payload format is valid',
            'parsed_data': parsed
        }), 200

    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f'Error validating payload: {str(e)}'
        }), 500

# LoRa Payload Receiving and Display Routes
@office_bp.route('/api/lora/receive', methods=['POST'])
def receive_lora_payload():
    """
    Receive incoming LoRa payload from device.

    This endpoint accepts payloads in format: hxb:batchnumber:LF:UHF or hxe:batchnumber:LF:UHF
    Payloads are buffered and processed asynchronously.

    Expected JSON payload:
    {
        "payload": "hxb:BATCH001:LF123:UHF456"
    }

    Returns:
    {
        "success": bool,
        "message": str,
        "status": str (buffered, duplicate, error),
        "payload_id": int (if successful)
    }
    """
    try:
        data = request.get_json()

        if not data or 'payload' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing payload field in request'
            }), 400

        raw_payload = data.get('payload', '').strip()

        if not raw_payload:
            return jsonify({
                'success': False,
                'message': 'Payload cannot be empty'
            }), 400

        # Receive and buffer payload
        result = PayloadProcessor.receive_payload(raw_payload)

        http_status = 201 if result['success'] else (409 if result.get('status') == 'duplicate' else 400)
        return jsonify(result), http_status

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error receiving payload: {str(e)}'
        }), 500

@office_bp.route('/api/lora/buffer-status', methods=['GET'])
@login_required
@admin_required
def get_lora_buffer_status():
    """
    Get current LoRa payload buffer status.

    Returns statistics about buffered, processed, and errored payloads.
    """
    try:
        status = PayloadProcessor.get_buffer_status()
        return jsonify({
            'success': True,
            'data': status
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting buffer status: {str(e)}'
        }), 500

@office_bp.route('/api/lora/payloads', methods=['GET'])
@login_required
@admin_required
def list_lora_payloads():
    """
    List LoRa payloads with optional filtering.

    Query parameters:
    - status: Filter by status (received, processing, processed, duplicate, error)
    - limit: Limit results (default: 50, max: 500)
    - offset: Pagination offset (default: 0)

    Returns:
    {
        "success": bool,
        "data": [
            {
                "id": int,
                "raw_payload": str,
                "status": str,
                "batch_number": str,
                "received_at": str (ISO format),
                "processed_at": str (ISO format),
                ...
            }
        ],
        "total": int,
        "count": int
    }
    """
    try:
        status_filter = request.args.get('status', '').strip()
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Validate limit
        if limit < 1 or limit > 500:
            limit = 50

        # Build query
        query = LoRaPayloadBuffer.query

        if status_filter:
            query = query.filter_by(status=status_filter)

        # Get total count
        total = query.count()

        # Get paginated results
        payloads = query.order_by(LoRaPayloadBuffer.received_at.desc()).offset(offset).limit(limit).all()

        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in payloads],
            'total': total,
            'count': len(payloads)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error listing payloads: {str(e)}'
        }), 500

@office_bp.route('/api/lora/process', methods=['POST'])
@login_required
@admin_required
def manually_process_payloads():
    """
    Manually trigger payload processing.

    Useful for testing or forcing immediate processing of buffered payloads.

    Returns:
    {
        "success": bool,
        "stats": {
            "total": int,
            "processed": int,
            "duplicates": int,
            "errors": int,
            "failed_payloads": [...]
        }
    }
    """
    try:
        stats = PayloadProcessor.process_pending_payloads()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing payloads: {str(e)}'
        }), 500

@office_bp.route('/lora-dashboard')
@login_required
@admin_required
def lora_dashboard():
    """Display LoRa payload monitoring dashboard"""
    # Get buffer statistics
    buffer_status = PayloadProcessor.get_buffer_status()

    # Get recent payloads (last 50)
    recent_payloads = LoRaPayloadBuffer.get_recent_payloads(hours=24, limit=50)

    return render_template('office/lora_dashboard.html',
                         buffer_status=buffer_status,
                         recent_payloads=recent_payloads)

# Database Sync Status Routes (Server UI only)

@office_bp.route('/api/sync-status', methods=['GET'])
@login_required
@admin_required
def get_sync_status():
    """Get database sync service status (Server UI only)"""
    try:
        from office_app.sync_service import get_sync_service

        sync_service = get_sync_service()

        if not sync_service:
            return jsonify({
                'success': False,
                'message': 'Sync service not initialized (Pi backend only)'
            }), 400

        stats = sync_service.get_stats()

        return jsonify({
            'success': True,
            'data': stats
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting sync status: {str(e)}'
        }), 500

