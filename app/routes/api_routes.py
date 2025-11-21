from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
from app.models.api_key import APIKey
from app.models.feedlot import Feedlot
from app.models.batch import Batch
from app.models.cattle import Cattle
from app.models.pen import Pen
from app.routes.auth_routes import login_required, admin_access_required
from app import db
from bson import ObjectId

api_bp = Blueprint('api', __name__)

def api_key_required(f):
    """Decorator to require API key authentication for API endpoints
    
    Extracts API key from X-API-Key header or api_key query parameter.
    Validates the key and attaches feedlot_id to the request context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'message': 'API key is required. Provide it in X-API-Key header or api_key query parameter.'
            }), 401
        
        # Validate API key
        is_valid, feedlot_id = APIKey.validate_key(api_key)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid or inactive API key.'
            }), 401
        
        # Attach feedlot_id to request context for use in route handlers
        request.feedlot_id = feedlot_id
        
        return f(*args, **kwargs)
    
    return decorated_function

@api_bp.route('/v1/feedlot/batches', methods=['POST'])
@api_key_required
def sync_batches():
    """Sync batch data from office app"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body must be JSON'
            }), 400
        
        feedlot_code = data.get('feedlot_code')
        if not feedlot_code:
            return jsonify({
                'success': False,
                'message': 'feedlot_code is required in request body'
            }), 400
        
        # Validate feedlot_code matches the API key's feedlot
        feedlot = Feedlot.find_by_id(request.feedlot_id)
        if not feedlot or feedlot.get('feedlot_code', '').upper() != feedlot_code.upper():
            return jsonify({
                'success': False,
                'message': 'feedlot_code does not match the API key\'s feedlot'
            }), 403
        
        # Get feedlot_code for database operations
        feedlot_code_normalized = feedlot.get('feedlot_code')
        if not feedlot_code_normalized:
            return jsonify({
                'success': False,
                'message': 'Feedlot code not found'
            }), 500
        
        batches_data = data.get('data', [])
        if not isinstance(batches_data, list):
            return jsonify({
                'success': False,
                'message': 'data must be an array'
            }), 400
        
        feedlot_id = request.feedlot_id
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        errors = []
        
        for batch_item in batches_data:
            try:
                records_processed += 1
                
                # Extract batch data from office app format
                batch_name = batch_item.get('name', '').strip()
                if not batch_name:
                    errors.append(f'Record {records_processed}: Batch name is required')
                    records_skipped += 1
                    continue
                
                # Check if batch already exists (by name and feedlot_id)
                existing_batches = Batch.find_by_feedlot(feedlot_code_normalized, feedlot_id)
                existing_batch = None
                for b in existing_batches:
                    if b.get('batch_number', '').strip() == batch_name:
                        existing_batch = b
                        break
                
                # Parse induction_date from created_at or use current date
                induction_date_str = batch_item.get('created_at') or batch_item.get('timestamp')
                if induction_date_str:
                    try:
                        # Try parsing ISO format or common date formats
                        if 'T' in induction_date_str:
                            induction_date = datetime.fromisoformat(induction_date_str.replace('Z', '+00:00'))
                        else:
                            induction_date = datetime.strptime(induction_date_str, '%Y-%m-%d')
                    except (ValueError, AttributeError):
                        induction_date = datetime.utcnow()
                else:
                    induction_date = datetime.utcnow()
                
                # Map office app fields to SaaS structure
                batch_number = batch_name
                funder = batch_item.get('funder', '') or ''
                notes = batch_item.get('notes', '') or ''
                
                # Handle pen creation/update from batch data
                pen_number = (batch_item.get('pen') or '').strip()
                pen_location = (batch_item.get('pen_location') or '').strip()
                
                pen_id = None
                if pen_number:
                    # Find or create pen
                    existing_pens = Pen.find_by_feedlot(feedlot_code_normalized, feedlot_id)
                    existing_pen = None
                    for p in existing_pens:
                        if p.get('pen_number', '').strip() == pen_number:
                            existing_pen = p
                            break
                    
                    if existing_pen:
                        # Update pen description if pen_location is provided
                        if pen_location:
                            Pen.update_pen(feedlot_code_normalized, str(existing_pen['_id']), {'description': pen_location})
                        pen_id = str(existing_pen['_id'])
                    else:
                        # Create new pen with default capacity (can be updated later via UI)
                        # Use pen_location as description if provided
                        pen_description = pen_location if pen_location else f'Pen {pen_number}'
                        pen_id = Pen.create_pen(feedlot_code_normalized, feedlot_id, pen_number, capacity=100, description=pen_description)
                
                if existing_batch:
                    # Update existing batch
                    update_data = {
                        'batch_number': batch_number,
                        'induction_date': induction_date,
                        'funder': funder,
                        'notes': notes
                    }
                    # Add pen_id if pen was found/created
                    if pen_id:
                        update_data['pen_id'] = ObjectId(pen_id)
                    Batch.update_batch(feedlot_code_normalized, str(existing_batch['_id']), update_data)
                    records_updated += 1
                else:
                    # Create new batch
                    batch_id = Batch.create_batch(feedlot_code_normalized, feedlot_id, batch_number, induction_date, funder, notes)
                    # Update batch with pen_id if pen was found/created
                    if pen_id:
                        Batch.update_batch(feedlot_code_normalized, batch_id, {'pen_id': ObjectId(pen_id)})
                    records_created += 1
                    
            except Exception as e:
                errors.append(f'Record {records_processed}: {str(e)}')
                records_skipped += 1
        
        return jsonify({
            'success': True,
            'message': f'Processed {records_processed} batch records',
            'records_processed': records_processed,
            'records_created': records_created,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@api_bp.route('/v1/feedlot/livestock', methods=['POST'])
@api_key_required
def sync_livestock():
    """Sync livestock (current state) from office app"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body must be JSON'
            }), 400
        
        feedlot_code = data.get('feedlot_code')
        if not feedlot_code:
            return jsonify({
                'success': False,
                'message': 'feedlot_code is required in request body'
            }), 400
        
        # Validate feedlot_code matches the API key's feedlot
        feedlot = Feedlot.find_by_id(request.feedlot_id)
        if not feedlot or feedlot.get('feedlot_code', '').upper() != feedlot_code.upper():
            return jsonify({
                'success': False,
                'message': 'feedlot_code does not match the API key\'s feedlot'
            }), 403
        
        # Get feedlot_code for database operations
        feedlot_code_normalized = feedlot.get('feedlot_code')
        if not feedlot_code_normalized:
            return jsonify({
                'success': False,
                'message': 'Feedlot code not found'
            }), 500
        
        livestock_data = data.get('data', [])
        if not isinstance(livestock_data, list):
            return jsonify({
                'success': False,
                'message': 'data must be an array'
            }), 400
        
        feedlot_id = request.feedlot_id
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        errors = []
        
        for livestock_item in livestock_data:
            try:
                records_processed += 1
                
                # Extract livestock data from office app format
                office_livestock_id = livestock_item.get('id')
                if not office_livestock_id:
                    errors.append(f'Record {records_processed}: Livestock ID is required')
                    records_skipped += 1
                    continue
                
                current_lf_id = livestock_item.get('current_lf_id', '').strip() or None
                current_epc = livestock_item.get('current_epc', '').strip() or None
                induction_event_id = livestock_item.get('induction_event_id')
                
                # Try to find existing cattle by office_livestock_id (stored in cattle_id or notes)
                # Or by tags
                existing_cattle = None
                
                # First, try to find by office_livestock_id stored in cattle_id
                office_id_str = str(office_livestock_id)
                all_cattle = Cattle.find_by_feedlot(feedlot_code_normalized, feedlot_id)
                for cattle in all_cattle:
                    if cattle.get('cattle_id') == office_id_str:
                        existing_cattle = cattle
                        break
                    # Also check by tags
                    if current_lf_id and cattle.get('lf_tag') == current_lf_id:
                        existing_cattle = cattle
                        break
                    if current_epc and cattle.get('uhf_tag') == current_epc:
                        existing_cattle = cattle
                        break
                
                if existing_cattle:
                    # Update tags if they've changed
                    cattle_record_id = str(existing_cattle['_id'])
                    if current_lf_id != existing_cattle.get('lf_tag') or current_epc != existing_cattle.get('uhf_tag'):
                        Cattle.update_tag_pair(feedlot_code_normalized, cattle_record_id, current_lf_id, current_epc, updated_by='api')
                    records_updated += 1
                else:
                    # Cattle not found - this should be created via induction_events first
                    # But if we have tags, we can try to create with minimal data
                    # However, we need batch_id which comes from induction_events
                    # For now, skip and log error
                    errors.append(f'Record {records_processed}: Livestock ID {office_livestock_id} not found. Create via induction_events first.')
                    records_skipped += 1
                    
            except Exception as e:
                errors.append(f'Record {records_processed}: {str(e)}')
                records_skipped += 1
        
        return jsonify({
            'success': True,
            'message': f'Processed {records_processed} livestock records',
            'records_processed': records_processed,
            'records_created': records_created,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@api_bp.route('/v1/feedlot/induction-events', methods=['POST'])
@api_key_required
def sync_induction_events():
    """Sync induction events from office app"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body must be JSON'
            }), 400
        
        feedlot_code = data.get('feedlot_code')
        if not feedlot_code:
            return jsonify({
                'success': False,
                'message': 'feedlot_code is required in request body'
            }), 400
        
        # Validate feedlot_code matches the API key's feedlot
        feedlot = Feedlot.find_by_id(request.feedlot_id)
        if not feedlot or feedlot.get('feedlot_code', '').upper() != feedlot_code.upper():
            return jsonify({
                'success': False,
                'message': 'feedlot_code does not match the API key\'s feedlot'
            }), 403
        
        # Get feedlot_code for database operations
        feedlot_code_normalized = feedlot.get('feedlot_code')
        if not feedlot_code_normalized:
            return jsonify({
                'success': False,
                'message': 'Feedlot code not found'
            }), 500
        
        events_data = data.get('data', [])
        if not isinstance(events_data, list):
            return jsonify({
                'success': False,
                'message': 'data must be an array'
            }), 400
        
        feedlot_id = request.feedlot_id
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        errors = []
        
        # Cache batches for this feedlot
        all_batches = Batch.find_by_feedlot(feedlot_code_normalized, feedlot_id)
        batch_cache = {b.get('batch_number', '').strip(): b for b in all_batches}
        
        for event_item in events_data:
            try:
                records_processed += 1
                
                livestock_id = event_item.get('livestock_id')
                batch_id_office = event_item.get('batch_id')  # Office app batch ID
                
                if not livestock_id:
                    errors.append(f'Record {records_processed}: livestock_id is required')
                    records_skipped += 1
                    continue
                
                if not batch_id_office:
                    errors.append(f'Record {records_processed}: batch_id is required')
                    records_skipped += 1
                    continue
                
                # Find batch in SaaS system
                # We need to map office batch_id to SaaS batch
                # For now, we'll need the office app to send batch name or we'll need a mapping
                # Let's assume the office app sends batch_name or we look it up
                batch_name = event_item.get('batch_name')
                if not batch_name:
                    # Try to find batch by office batch_id if we have a mapping
                    # For now, skip if no batch_name
                    errors.append(f'Record {records_processed}: batch_name is required to map to SaaS batch')
                    records_skipped += 1
                    continue
                
                saas_batch = batch_cache.get(batch_name.strip())
                if not saas_batch:
                    errors.append(f'Record {records_processed}: Batch "{batch_name}" not found in SaaS system')
                    records_skipped += 1
                    continue
                
                saas_batch_id = str(saas_batch['_id'])
                
                # Get pen_id from batch if available
                batch_pen_id = saas_batch.get('pen_id')
                # Convert to string (works for both ObjectId and string) or keep None
                pen_id_for_cattle = str(batch_pen_id) if batch_pen_id else None
                
                # Check if cattle already exists
                office_id_str = str(livestock_id)
                existing_cattle = Cattle.find_by_cattle_id(feedlot_code_normalized, feedlot_id, office_id_str)
                
                if existing_cattle:
                    # Update existing cattle (induction already happened)
                    # If batch has a pen and cattle doesn't, assign it
                    if pen_id_for_cattle and not existing_cattle.get('pen_id'):
                        Cattle.update_cattle(feedlot_code_normalized, str(existing_cattle['_id']), {'pen_id': ObjectId(pen_id_for_cattle)}, updated_by='api')
                    records_updated += 1
                else:
                    # Create new cattle record
                    # Parse timestamp
                    timestamp_str = event_item.get('timestamp') or event_item.get('created_at')
                    if timestamp_str:
                        try:
                            if 'T' in timestamp_str:
                                induction_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                induction_date = datetime.strptime(timestamp_str, '%Y-%m-%d')
                        except (ValueError, AttributeError):
                            induction_date = datetime.utcnow()
                    else:
                        induction_date = datetime.utcnow()
                    
                    # Create cattle with default values
                    # Required fields: cattle_id, sex, weight, health_status
                    cattle_id = office_id_str
                    sex = 'Unknown'  # Default, can be updated later
                    weight = 0.0  # Default, will be updated via checkin_events
                    health_status = 'Healthy'  # Default
                    
                    cattle_record_id = Cattle.create_cattle(
                        feedlot_code=feedlot_code_normalized,
                        feedlot_id=feedlot_id,
                        batch_id=saas_batch_id,
                        cattle_id=cattle_id,
                        sex=sex,
                        weight=weight,
                        health_status=health_status,
                        lf_tag=None,
                        uhf_tag=None,
                        pen_id=pen_id_for_cattle,
                        notes=None
                    )
                    
                    # Update induction_date
                    Cattle.update_cattle(feedlot_code_normalized, cattle_record_id, {'induction_date': induction_date}, updated_by='api')
                    
                    # Add audit log entry for import
                    Cattle.add_audit_log_entry(
                        feedlot_code_normalized,
                        cattle_record_id,
                        'imported',
                        f'Imported from office app (livestock_id: {livestock_id})',
                        'api',
                        {'livestock_id': livestock_id, 'induction_date': induction_date.isoformat() if isinstance(induction_date, datetime) else str(induction_date)}
                    )
                    
                    records_created += 1
                    
            except Exception as e:
                errors.append(f'Record {records_processed}: {str(e)}')
                records_skipped += 1
        
        return jsonify({
            'success': True,
            'message': f'Processed {records_processed} induction event records',
            'records_processed': records_processed,
            'records_created': records_created,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@api_bp.route('/v1/feedlot/pairing-events', methods=['POST'])
@api_key_required
def sync_pairing_events():
    """Sync pairing events from office app"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body must be JSON'
            }), 400
        
        feedlot_code = data.get('feedlot_code')
        if not feedlot_code:
            return jsonify({
                'success': False,
                'message': 'feedlot_code is required in request body'
            }), 400
        
        # Validate feedlot_code matches the API key's feedlot
        feedlot = Feedlot.find_by_id(request.feedlot_id)
        if not feedlot or feedlot.get('feedlot_code', '').upper() != feedlot_code.upper():
            return jsonify({
                'success': False,
                'message': 'feedlot_code does not match the API key\'s feedlot'
            }), 403
        
        # Get feedlot_code for database operations
        feedlot_code_normalized = feedlot.get('feedlot_code')
        if not feedlot_code_normalized:
            return jsonify({
                'success': False,
                'message': 'Feedlot code not found'
            }), 500
        
        events_data = data.get('data', [])
        if not isinstance(events_data, list):
            return jsonify({
                'success': False,
                'message': 'data must be an array'
            }), 400
        
        feedlot_id = request.feedlot_id
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        errors = []
        
        for event_item in events_data:
            try:
                records_processed += 1
                
                livestock_id = event_item.get('livestock_id')
                lf_id = event_item.get('lf_id', '').strip() or None
                epc = event_item.get('epc', '').strip() or None
                weight_kg = event_item.get('weight_kg')
                
                if not livestock_id:
                    errors.append(f'Record {records_processed}: livestock_id is required')
                    records_skipped += 1
                    continue
                
                # Find cattle by office livestock_id
                office_id_str = str(livestock_id)
                existing_cattle = Cattle.find_by_cattle_id(feedlot_code_normalized, feedlot_id, office_id_str)
                
                if not existing_cattle:
                    errors.append(f'Record {records_processed}: Livestock ID {livestock_id} not found. Create via induction_events first.')
                    records_skipped += 1
                    continue
                
                cattle_record_id = str(existing_cattle['_id'])
                
                # Update tags (this will add audit log entry automatically)
                Cattle.update_tag_pair(feedlot_code_normalized, cattle_record_id, lf_id, epc, updated_by='api')
                
                # Update weight if provided
                if weight_kg is not None:
                    try:
                        weight_float = float(weight_kg)
                        if weight_float > 0:
                            Cattle.add_weight_record(feedlot_code_normalized, cattle_record_id, weight_float, recorded_by='api')
                    except (ValueError, TypeError):
                        pass  # Skip invalid weight
                
                records_updated += 1
                    
            except Exception as e:
                errors.append(f'Record {records_processed}: {str(e)}')
                records_skipped += 1
        
        return jsonify({
            'success': True,
            'message': f'Processed {records_processed} pairing event records',
            'records_processed': records_processed,
            'records_created': records_created,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@api_bp.route('/v1/feedlot/checkin-events', methods=['POST'])
@api_key_required
def sync_checkin_events():
    """Sync check-in events (weight measurements) from office app"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body must be JSON'
            }), 400
        
        feedlot_code = data.get('feedlot_code')
        if not feedlot_code:
            return jsonify({
                'success': False,
                'message': 'feedlot_code is required in request body'
            }), 400
        
        # Validate feedlot_code matches the API key's feedlot
        feedlot = Feedlot.find_by_id(request.feedlot_id)
        if not feedlot or feedlot.get('feedlot_code', '').upper() != feedlot_code.upper():
            return jsonify({
                'success': False,
                'message': 'feedlot_code does not match the API key\'s feedlot'
            }), 403
        
        # Get feedlot_code for database operations
        feedlot_code_normalized = feedlot.get('feedlot_code')
        if not feedlot_code_normalized:
            return jsonify({
                'success': False,
                'message': 'Feedlot code not found'
            }), 500
        
        events_data = data.get('data', [])
        if not isinstance(events_data, list):
            return jsonify({
                'success': False,
                'message': 'data must be an array'
            }), 400
        
        feedlot_id = request.feedlot_id
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        errors = []
        
        for event_item in events_data:
            try:
                records_processed += 1
                
                livestock_id = event_item.get('livestock_id')
                weight_kg = event_item.get('weight_kg')
                
                if not livestock_id:
                    errors.append(f'Record {records_processed}: livestock_id is required')
                    records_skipped += 1
                    continue
                
                if weight_kg is None:
                    errors.append(f'Record {records_processed}: weight_kg is required')
                    records_skipped += 1
                    continue
                
                try:
                    weight_float = float(weight_kg)
                    if weight_float <= 0:
                        errors.append(f'Record {records_processed}: weight_kg must be greater than 0')
                        records_skipped += 1
                        continue
                except (ValueError, TypeError):
                    errors.append(f'Record {records_processed}: Invalid weight_kg value')
                    records_skipped += 1
                    continue
                
                # Find cattle by office livestock_id
                office_id_str = str(livestock_id)
                existing_cattle = Cattle.find_by_cattle_id(feedlot_code_normalized, feedlot_id, office_id_str)
                
                if not existing_cattle:
                    errors.append(f'Record {records_processed}: Livestock ID {livestock_id} not found. Create via induction_events first.')
                    records_skipped += 1
                    continue
                
                cattle_record_id = str(existing_cattle['_id'])
                
                # Add weight record
                Cattle.add_weight_record(feedlot_code_normalized, cattle_record_id, weight_float, recorded_by='api')
                records_created += 1
                    
            except Exception as e:
                errors.append(f'Record {records_processed}: {str(e)}')
                records_skipped += 1
        
        return jsonify({
            'success': True,
            'message': f'Processed {records_processed} check-in event records',
            'records_processed': records_processed,
            'records_created': records_created,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@api_bp.route('/v1/feedlot/repair-events', methods=['POST'])
@api_key_required
def sync_repair_events():
    """Sync repair events from office app"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body must be JSON'
            }), 400
        
        feedlot_code = data.get('feedlot_code')
        if not feedlot_code:
            return jsonify({
                'success': False,
                'message': 'feedlot_code is required in request body'
            }), 400
        
        # Validate feedlot_code matches the API key's feedlot
        feedlot = Feedlot.find_by_id(request.feedlot_id)
        if not feedlot or feedlot.get('feedlot_code', '').upper() != feedlot_code.upper():
            return jsonify({
                'success': False,
                'message': 'feedlot_code does not match the API key\'s feedlot'
            }), 403
        
        # Get feedlot_code for database operations
        feedlot_code_normalized = feedlot.get('feedlot_code')
        if not feedlot_code_normalized:
            return jsonify({
                'success': False,
                'message': 'Feedlot code not found'
            }), 500
        
        events_data = data.get('data', [])
        if not isinstance(events_data, list):
            return jsonify({
                'success': False,
                'message': 'data must be an array'
            }), 400
        
        feedlot_id = request.feedlot_id
        records_processed = 0
        records_created = 0
        records_updated = 0
        records_skipped = 0
        errors = []
        
        for event_item in events_data:
            try:
                records_processed += 1
                
                livestock_id = event_item.get('livestock_id')
                old_lf_id = (event_item.get('old_lf_id') or '').strip() or None
                new_lf_id = (event_item.get('new_lf_id') or '').strip() or None
                old_epc = (event_item.get('old_epc') or '').strip() or None
                new_epc = (event_item.get('new_epc') or '').strip() or None
                reason = (event_item.get('reason') or '').strip() or ''
                
                if not livestock_id:
                    errors.append(f'Record {records_processed}: livestock_id is required')
                    records_skipped += 1
                    continue
                
                # At least one tag must be repaired
                if not (new_lf_id or new_epc):
                    errors.append(f'Record {records_processed}: At least one new tag (new_lf_id or new_epc) is required')
                    records_skipped += 1
                    continue
                
                # Find cattle by office livestock_id
                office_id_str = str(livestock_id)
                existing_cattle = Cattle.find_by_cattle_id(feedlot_code_normalized, feedlot_id, office_id_str)
                
                if not existing_cattle:
                    errors.append(f'Record {records_processed}: Livestock ID {livestock_id} not found. Create via induction_events first.')
                    records_skipped += 1
                    continue
                
                cattle_record_id = str(existing_cattle['_id'])
                
                # Determine new tags to set
                # If new_lf_id is provided, use it; otherwise keep current
                final_lf_id = new_lf_id if new_lf_id else existing_cattle.get('lf_tag')
                # If new_epc is provided, use it; otherwise keep current
                final_epc = new_epc if new_epc else existing_cattle.get('uhf_tag')
                
                # Update tags (this will add audit log entry automatically)
                Cattle.update_tag_pair(feedlot_code_normalized, cattle_record_id, final_lf_id, final_epc, updated_by='api', reason=reason)
                
                records_updated += 1
                    
            except Exception as e:
                errors.append(f'Record {records_processed}: {str(e)}')
                records_skipped += 1
        
        return jsonify({
            'success': True,
            'message': f'Processed {records_processed} repair event records',
            'records_processed': records_processed,
            'records_created': records_created,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

# API key generation is now only available through the web UI (Settings → API Keys)
# This endpoint has been removed to restrict key generation to the secure web interface
# Use the Settings page in the web application to generate and manage API keys

