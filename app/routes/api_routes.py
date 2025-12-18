from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime
from app.models.api_key import APIKey
from app.models.feedlot import Feedlot
from app.models.batch import Batch
from app.models.cattle import Cattle
from app.models.pen import Pen
from app.models.manifest import Manifest
from app.utils.manifest_generator import generate_manifest_data
from app.routes.auth_routes import login_required, admin_access_required
from app import db
from bson import ObjectId
import json

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

@api_bp.route('/v1/feedlot/induction-events', methods=['POST'])
@api_key_required
def sync_induction_events():
    """Sync induction events from office app - now includes batch creation"""
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
        if not feedlot or feedlot.get('feedlot_code', '').lower() != feedlot_code.lower():
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
        batches_created = 0
        batches_updated = 0
        errors = []
        
        # Cache batches for this feedlot
        all_batches = Batch.find_by_feedlot(feedlot_code_normalized, feedlot_id)
        batch_cache = {b.get('batch_number', '').strip(): b for b in all_batches}
        
        for event_item in events_data:
            try:
                records_processed += 1
                
                livestock_id = event_item.get('livestock_id')
                if not livestock_id:
                    errors.append(f'Record {records_processed}: livestock_id is required')
                    records_skipped += 1
                    continue
                
                # Extract batch_name from event - this is now required for batch creation
                batch_name = (event_item.get('batch_name') or '').strip()
                if not batch_name:
                    errors.append(f'Record {records_processed}: batch_name is required')
                    records_skipped += 1
                    continue
                
                # Extract pen information from event (used in both batch creation and cattle assignment)
                pen_number = (event_item.get('pen') or '').strip()
                pen_location = (event_item.get('pen_location') or '').strip()
                
                # Find or create batch
                # Look up batch in cache (case-insensitive lookup for robustness)
                saas_batch = batch_cache.get(batch_name)
                # If not found by exact match, try case-insensitive lookup
                if not saas_batch:
                    for cached_batch_name, cached_batch in batch_cache.items():
                        if cached_batch_name.lower() == batch_name.lower():
                            saas_batch = cached_batch
                            break
                
                if not saas_batch:
                    # Create new batch from event data
                    # Parse timestamp for event_date
                    timestamp_str = event_item.get('timestamp') or event_item.get('created_at')
                    if timestamp_str:
                        try:
                            # Handle format like "2025-12-04 14:18:11.265273"
                            if ' ' in timestamp_str and '.' in timestamp_str:
                                timestamp_str = timestamp_str.split('.')[0]  # Remove microseconds
                                event_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            elif 'T' in timestamp_str:
                                event_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                event_date = datetime.strptime(timestamp_str, '%Y-%m-%d')
                        except (ValueError, AttributeError):
                            event_date = datetime.utcnow()
                    else:
                        event_date = datetime.utcnow()
                    
                    # Extract batch information from event
                    funder = (event_item.get('funder') or '').strip()
                    if funder == 'None' or funder.lower() == 'none':
                        funder = ''
                    notes = (event_item.get('notes') or '').strip()
                    
                    # Extract event_type from event, default to 'induction' for induction-events endpoint
                    event_type = (event_item.get('event_type') or 'induction').strip().lower()
                    valid_event_types = ['induction', 'pairing', 'checkin', 'repair', 'export']
                    if event_type not in valid_event_types:
                        event_type = 'induction'
                    
                    # Handle pen creation/update from event data
                    
                    pen_id = None
                    if pen_number:
                        # Find or create pen
                        existing_pens = Pen.find_by_feedlot(feedlot_id)
                        existing_pen = None
                        for p in existing_pens:
                            if p.get('pen_number', '').strip() == pen_number:
                                existing_pen = p
                                break
                        
                        if existing_pen:
                            # Update pen description if pen_location is provided
                            if pen_location:
                                Pen.update_pen(str(existing_pen['_id']), {'description': pen_location})
                            pen_id = str(existing_pen['_id'])
                        else:
                            # Create new pen with default capacity (can be updated later via UI)
                            pen_description = pen_location if pen_location else f'Pen {pen_number}'
                            pen_id = Pen.create_pen(feedlot_id, pen_number, capacity=100, description=pen_description)
                    
                    # Create new batch if it doesn't exist
                    try:
                        batch_id = Batch.create_batch(feedlot_code_normalized, feedlot_id, batch_name, event_date, funder, notes, event_type)
                        if not batch_id:
                            raise Exception('Batch creation returned no ID')
                        
                        # Update batch with pen_id if pen was found/created
                        if pen_id:
                            Batch.update_batch(feedlot_code_normalized, batch_id, {'pen_id': ObjectId(pen_id)})
                        
                        # Refresh batch cache to include the newly created batch
                        saas_batch = Batch.find_by_id(feedlot_code_normalized, batch_id)
                        if not saas_batch:
                            raise Exception(f'Failed to retrieve created batch with ID {batch_id}')
                        
                        # Add to cache using batch_number from the database (should match batch_name)
                        batch_number_from_db = saas_batch.get('batch_number', '').strip()
                        if batch_number_from_db:
                            batch_cache[batch_number_from_db] = saas_batch
                        # Also add with batch_name as key for lookup consistency
                        batch_cache[batch_name] = saas_batch
                        batches_created += 1
                    except Exception as batch_error:
                        # If batch creation fails, we can't proceed with cattle creation
                        errors.append(f'Record {records_processed}: Failed to create batch "{batch_name}": {str(batch_error)}')
                        records_skipped += 1
                        continue
                else:
                    # Batch exists - check if we need to update it
                    saas_batch_id = str(saas_batch['_id'])
                    
                    # Update batch if new information is available
                    update_batch_data = {}
                    
                    # Update event_type if provided and different
                    event_type = (event_item.get('event_type') or '').strip().lower()
                    if event_type:
                        valid_event_types = ['induction', 'pairing', 'checkin', 'repair', 'export']
                        if event_type in valid_event_types and saas_batch.get('event_type') != event_type:
                            update_batch_data['event_type'] = event_type
                    
                    # Update funder if provided and different
                    funder = (event_item.get('funder') or '').strip()
                    if funder == 'None' or funder.lower() == 'none':
                        funder = ''
                    if funder and saas_batch.get('funder') != funder:
                        update_batch_data['funder'] = funder
                    
                    # Update notes if provided
                    notes = (event_item.get('notes') or '').strip()
                    if notes and saas_batch.get('notes') != notes:
                        update_batch_data['notes'] = notes
                    
                    # Handle pen creation/update (pen_number and pen_location already extracted above)
                    pen_id = None
                    if pen_number:
                        existing_pens = Pen.find_by_feedlot(feedlot_id)
                        existing_pen = None
                        for p in existing_pens:
                            if p.get('pen_number', '').strip() == pen_number:
                                existing_pen = p
                                break
                        
                        if existing_pen:
                            if pen_location:
                                Pen.update_pen(str(existing_pen['_id']), {'description': pen_location})
                            pen_id = str(existing_pen['_id'])
                        else:
                            pen_description = pen_location if pen_location else f'Pen {pen_number}'
                            pen_id = Pen.create_pen(feedlot_id, pen_number, capacity=100, description=pen_description)
                        
                        # Update batch pen_id if pen was found/created and batch doesn't have one
                        if pen_id and not saas_batch.get('pen_id'):
                            update_batch_data['pen_id'] = ObjectId(pen_id)
                    
                    if update_batch_data:
                        Batch.update_batch(feedlot_code_normalized, saas_batch_id, update_batch_data)
                        batches_updated += 1
                
                # Ensure saas_batch is set (should always be set at this point)
                if not saas_batch:
                    errors.append(f'Record {records_processed}: Batch "{batch_name}" not found after creation/lookup')
                    records_skipped += 1
                    continue
                
                saas_batch_id = str(saas_batch['_id'])
                
                # Get pen_id from batch or event
                batch_pen_id = saas_batch.get('pen_id')
                pen_id_for_cattle = str(batch_pen_id) if batch_pen_id else None
                
                # If event has pen info but batch doesn't, use event pen
                if not pen_id_for_cattle and pen_number:
                    existing_pens = Pen.find_by_feedlot(feedlot_id)
                    for p in existing_pens:
                        if p.get('pen_number', '').strip() == pen_number:
                            pen_id_for_cattle = str(p['_id'])
                            break
                
                # Check if cattle already exists
                office_id_str = str(livestock_id)
                existing_cattle = Cattle.find_by_cattle_id(feedlot_code_normalized, feedlot_id, office_id_str)
                
                if existing_cattle:
                    # Update existing cattle
                    cattle_record_id = str(existing_cattle['_id'])
                    update_cattle_data = {}
                    
                    # Update pen if provided and different
                    if pen_id_for_cattle and str(existing_cattle.get('pen_id')) != pen_id_for_cattle:
                        update_cattle_data['pen_id'] = ObjectId(pen_id_for_cattle)
                    
                    # Update sex if provided
                    sex = (event_item.get('sex') or '').strip()
                    if sex and existing_cattle.get('sex') != sex:
                        update_cattle_data['sex'] = sex
                    
                    # Update weight if provided and valid
                    weight = event_item.get('weight')
                    if weight is not None:
                        try:
                            weight_float = float(weight)
                            if weight_float > 0 and existing_cattle.get('weight') != weight_float:
                                update_cattle_data['weight'] = weight_float
                        except (ValueError, TypeError):
                            pass
                    
                    # Update tags if provided
                    lf_id = (event_item.get('lf_id') or '').strip() or None
                    epc = (event_item.get('epc') or '').strip() or None
                    if lf_id or epc:
                        current_lf = existing_cattle.get('lf_tag') or None
                        current_epc = existing_cattle.get('uhf_tag') or None
                        if lf_id != current_lf or epc != current_epc:
                            Cattle.update_tag_pair(feedlot_code_normalized, cattle_record_id, lf_id, epc, updated_by='api')
                    
                    # Update notes if provided
                    notes = (event_item.get('notes') or '').strip()
                    if notes and existing_cattle.get('notes') != notes:
                        update_cattle_data['notes'] = notes
                    
                    # Update tag_color (maps to color field) if provided
                    tag_color = (event_item.get('tag_color') or '').strip()
                    if tag_color and existing_cattle.get('color') != tag_color:
                        update_cattle_data['color'] = tag_color
                    
                    # Update visual_id if provided
                    visual_id = (event_item.get('visual_id') or '').strip()
                    if visual_id and existing_cattle.get('visual_id') != visual_id:
                        update_cattle_data['visual_id'] = visual_id
                    
                    # Update lot if provided
                    lot = (event_item.get('lot') or '').strip()
                    if lot and existing_cattle.get('lot') != lot:
                        update_cattle_data['lot'] = lot
                    
                    # Update lot_group if provided
                    lot_group = (event_item.get('lot_group') or '').strip()
                    if lot_group and existing_cattle.get('lot_group') != lot_group:
                        update_cattle_data['lot_group'] = lot_group
                    
                    if update_cattle_data:
                        Cattle.update_cattle(feedlot_code_normalized, cattle_record_id, update_cattle_data, updated_by='api')
                    
                    records_updated += 1
                else:
                    # Create new cattle record
                    # Parse timestamp
                    timestamp_str = event_item.get('timestamp') or event_item.get('created_at')
                    if timestamp_str:
                        try:
                            # Handle format like "2025-12-04 14:18:11.265273"
                            if ' ' in timestamp_str and '.' in timestamp_str:
                                timestamp_str = timestamp_str.split('.')[0]  # Remove microseconds
                                induction_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            elif 'T' in timestamp_str:
                                induction_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                induction_date = datetime.strptime(timestamp_str, '%Y-%m-%d')
                        except (ValueError, AttributeError):
                            induction_date = datetime.utcnow()
                    else:
                        induction_date = datetime.utcnow()
                    
                    # Extract cattle data from event
                    cattle_id = office_id_str
                    sex = (event_item.get('sex') or '').strip() or 'Unknown'
                    weight = event_item.get('weight')
                    try:
                        weight_float = float(weight) if weight is not None else 0.0
                        if weight_float < 0:
                            weight_float = 0.0
                    except (ValueError, TypeError):
                        weight_float = 0.0
                    
                    cattle_status = 'Healthy'  # Default
                    lf_tag = (event_item.get('lf_id') or '').strip() or None
                    uhf_tag = (event_item.get('epc') or '').strip() or None
                    notes = (event_item.get('notes') or '').strip() or None
                    
                    # Extract additional fields from payload
                    tag_color = (event_item.get('tag_color') or '').strip() or None
                    visual_id = (event_item.get('visual_id') or '').strip() or None
                    lot = (event_item.get('lot') or '').strip() or None
                    lot_group = (event_item.get('lot_group') or '').strip() or None
                    
                    cattle_record_id = Cattle.create_cattle(
                        feedlot_code=feedlot_code_normalized,
                        feedlot_id=feedlot_id,
                        cattle_id=cattle_id,
                        sex=sex,
                        weight=weight_float,
                        cattle_status=cattle_status,
                        batch_id=saas_batch_id,
                        lf_tag=lf_tag,
                        uhf_tag=uhf_tag,
                        pen_id=pen_id_for_cattle,
                        notes=notes,
                        color=tag_color,
                        visual_id=visual_id,
                        lot=lot,
                        lot_group=lot_group
                    )
                    
                    # Update induction_date
                    Cattle.update_cattle(feedlot_code_normalized, cattle_record_id, {'induction_date': induction_date}, updated_by='api')
                    
                    # Add audit log entry for import
                    Cattle.add_audit_log_entry(
                        feedlot_code_normalized,
                        cattle_record_id,
                        'imported',
                        f'Imported from office app (livestock_id: {livestock_id}, event_id: {event_item.get("event_id", "N/A")})',
                        'api',
                        {
                            'livestock_id': livestock_id,
                            'event_id': event_item.get('event_id'),
                            'induction_date': induction_date.isoformat() if isinstance(induction_date, datetime) else str(induction_date)
                        }
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
            'batches_created': batches_created,
            'batches_updated': batches_updated,
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
        if not feedlot or feedlot.get('feedlot_code', '').lower() != feedlot_code.lower():
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
        if not feedlot or feedlot.get('feedlot_code', '').lower() != feedlot_code.lower():
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
                    if weight_float < 0:
                        errors.append(f'Record {records_processed}: weight_kg cannot be negative')
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
        if not feedlot or feedlot.get('feedlot_code', '').lower() != feedlot_code.lower():
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

@api_bp.route('/v1/feedlot/export-events', methods=['POST'])
@api_key_required
def sync_export_events():
    """Sync export events from office app - marks cattle as Export status, creates export batch, and optionally creates manifest records"""
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
        if not feedlot or feedlot.get('feedlot_code', '').lower() != feedlot_code.lower():
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
        manifests_created = 0
        manifest_ids = []
        batches_created = 0
        batches_updated = 0
        
        # Cache batches for this feedlot (for batch creation/lookup)
        all_batches = Batch.find_by_feedlot(feedlot_code_normalized, feedlot_id)
        batch_cache = {b.get('batch_number', '').strip(): b for b in all_batches}
        
        # Track auto-generated batch sequence for this request
        auto_batch_sequence = {}  # date_str -> next sequence number
        
        # Helper function to generate auto batch name
        def generate_auto_batch_name():
            """Generate an auto batch name in format EXPORT-YYYY-MM-DD-###"""
            date_str = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Initialize sequence for this date if not yet set
            if date_str not in auto_batch_sequence:
                # Count existing export batches for today to determine starting sequence
                prefix = f"EXPORT-{date_str}-"
                existing_count = 0
                for batch_name in batch_cache.keys():
                    if batch_name.startswith(prefix):
                        try:
                            seq_num = int(batch_name[len(prefix):])
                            existing_count = max(existing_count, seq_num)
                        except ValueError:
                            pass
                auto_batch_sequence[date_str] = existing_count + 1
            
            seq = auto_batch_sequence[date_str]
            auto_batch_sequence[date_str] = seq + 1
            return f"EXPORT-{date_str}-{seq:03d}"
        
        # Helper function to extract manifest fields from event item
        def extract_manifest_fields(event_item):
            """Extract all manifest fields from event item, normalizing empty values"""
            manifest_fields = {}
            
            # Part A
            manifest_fields['purpose'] = (event_item.get('purpose') or '').strip()
            manifest_fields['transport_for_sale_by'] = (event_item.get('transport_for_sale_by') or '').strip()
            
            # Part B
            manifest_fields['date'] = (event_item.get('date') or '').strip()
            manifest_fields['owner_name'] = (event_item.get('owner_name') or '').strip()
            manifest_fields['owner_phone'] = (event_item.get('owner_phone') or '').strip()
            manifest_fields['owner_address'] = (event_item.get('owner_address') or '').strip()
            manifest_fields['dealer_name'] = (event_item.get('dealer_name') or '').strip()
            manifest_fields['dealer_phone'] = (event_item.get('dealer_phone') or '').strip()
            manifest_fields['dealer_address'] = (event_item.get('dealer_address') or '').strip()
            manifest_fields['on_account_of'] = (event_item.get('on_account_of') or '').strip()
            manifest_fields['location_before'] = (event_item.get('location_before') or '').strip()
            manifest_fields['premises_id_before'] = (event_item.get('premises_id_before') or '').strip()
            manifest_fields['reason_for_transport'] = (event_item.get('reason_for_transport') or '').strip()
            manifest_fields['destination_name'] = (event_item.get('destination_name') or '').strip()
            manifest_fields['destination_address'] = (event_item.get('destination_address') or '').strip()
            
            # Part C
            manifest_fields['owner_signature'] = (event_item.get('owner_signature') or '').strip()
            manifest_fields['owner_signature_date'] = (event_item.get('owner_signature_date') or '').strip()
            
            # Part D
            manifest_fields['inspector_name'] = (event_item.get('inspector_name') or '').strip()
            manifest_fields['inspector_number'] = (event_item.get('inspector_number') or '').strip()
            manifest_fields['inspection_date'] = (event_item.get('inspection_date') or '').strip()
            manifest_fields['inspection_time'] = (event_item.get('inspection_time') or '').strip()
            manifest_fields['inspection_notes'] = (event_item.get('inspection_notes') or '').strip()
            
            # Part E
            manifest_fields['transporter_name'] = (event_item.get('transporter_name') or '').strip()
            manifest_fields['transporter_trailer'] = (event_item.get('transporter_trailer') or '').strip()
            manifest_fields['transporter_phone'] = (event_item.get('transporter_phone') or '').strip()
            manifest_fields['transporter_signature'] = (event_item.get('transporter_signature') or '').strip()
            manifest_fields['transporter_signature_date'] = (event_item.get('transporter_signature_date') or '').strip()
            
            # Part F
            manifest_fields['security_interest_declared'] = event_item.get('security_interest_declared', False)
            manifest_fields['security_interest_details'] = (event_item.get('security_interest_details') or '').strip()
            
            # Part G
            manifest_fields['received_date'] = (event_item.get('received_date') or '').strip()
            manifest_fields['received_time'] = (event_item.get('received_time') or '').strip()
            manifest_fields['head_received'] = event_item.get('head_received')
            manifest_fields['receiver_name'] = (event_item.get('receiver_name') or '').strip()
            manifest_fields['receiver_signature'] = (event_item.get('receiver_signature') or '').strip()
            manifest_fields['premises_id_destination'] = (event_item.get('premises_id_destination') or '').strip()
            
            return manifest_fields
        
        # Helper function to create grouping key from manifest fields
        def create_manifest_key(manifest_fields):
            """Create a hashable key from manifest fields for grouping"""
            # Convert to tuple of sorted items, excluding None/empty values for consistent grouping
            key_dict = {k: v for k, v in manifest_fields.items() if v not in (None, '', False)}
            return json.dumps(key_dict, sort_keys=True)
        
        # Process events and group by manifest data
        processed_events = []  # Store successfully processed events with their cattle and manifest data
        manifest_groups = {}  # Group events by manifest key
        
        for event_item in events_data:
            try:
                records_processed += 1
                
                epc = (event_item.get('epc') or '').strip()
                timestamp_str = event_item.get('timestamp')
                
                if not epc:
                    errors.append(f'Record {records_processed}: epc (UHF tag) is required')
                    records_skipped += 1
                    continue
                
                # Find cattle by UHF tag
                existing_cattle = Cattle.find_by_uhf_tag(feedlot_code_normalized, feedlot_id, epc)
                
                if not existing_cattle:
                    errors.append(f'Record {records_processed}: Cattle with UHF tag {epc} not found')
                    records_skipped += 1
                    continue
                
                cattle_record_id = str(existing_cattle['_id'])
                
                # Check if already exported
                current_status = existing_cattle.get('cattle_status')
                if current_status == 'Export':
                    # Already exported, skip but don't count as error
                    records_skipped += 1
                    continue
                
                # Store the previous batch_id for audit logging
                previous_batch_id = existing_cattle.get('batch_id')
                
                # Extract manifest fields
                manifest_fields = extract_manifest_fields(event_item)
                
                # Parse timestamp if provided
                export_timestamp = datetime.utcnow()
                if timestamp_str:
                    try:
                        # Handle format like "2025-12-04 14:18:11.265273"
                        if ' ' in timestamp_str and '.' in timestamp_str:
                            timestamp_str = timestamp_str.split('.')[0]  # Remove microseconds
                            export_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        elif 'T' in timestamp_str:
                            export_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            export_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d')
                    except (ValueError, AttributeError):
                        export_timestamp = datetime.utcnow()
                
                # Handle batch creation/lookup for export batch
                batch_name = (event_item.get('batch_name') or '').strip()
                if not batch_name:
                    # Auto-generate batch name if not provided
                    batch_name = generate_auto_batch_name()
                
                # Look up batch in cache (case-insensitive lookup for robustness)
                saas_batch = batch_cache.get(batch_name)
                if not saas_batch:
                    for cached_batch_name, cached_batch in batch_cache.items():
                        if cached_batch_name.lower() == batch_name.lower():
                            saas_batch = cached_batch
                            break
                
                export_batch_id = None
                if not saas_batch:
                    # Create new export batch
                    try:
                        # Extract optional batch fields from event
                        funder = (event_item.get('funder') or '').strip()
                        if funder == 'None' or funder.lower() == 'none':
                            funder = ''
                        notes = (event_item.get('notes') or '').strip()
                        
                        batch_id = Batch.create_batch(
                            feedlot_code_normalized,
                            feedlot_id,
                            batch_name,
                            export_timestamp,
                            funder,
                            notes,
                            event_type='export'
                        )
                        if not batch_id:
                            raise Exception('Batch creation returned no ID')
                        
                        # Refresh batch from database and add to cache
                        saas_batch = Batch.find_by_id(feedlot_code_normalized, batch_id)
                        if not saas_batch:
                            raise Exception(f'Failed to retrieve created batch with ID {batch_id}')
                        
                        batch_number_from_db = saas_batch.get('batch_number', '').strip()
                        if batch_number_from_db:
                            batch_cache[batch_number_from_db] = saas_batch
                        batch_cache[batch_name] = saas_batch
                        batches_created += 1
                        export_batch_id = batch_id
                    except Exception as batch_error:
                        errors.append(f'Record {records_processed}: Failed to create export batch "{batch_name}": {str(batch_error)}')
                        # Continue processing without batch assignment
                        export_batch_id = None
                else:
                    # Batch exists
                    export_batch_id = str(saas_batch['_id'])
                    
                    # Update batch if new information is available
                    update_batch_data = {}
                    
                    # Update funder if provided and different
                    funder = (event_item.get('funder') or '').strip()
                    if funder == 'None' or funder.lower() == 'none':
                        funder = ''
                    if funder and saas_batch.get('funder') != funder:
                        update_batch_data['funder'] = funder
                    
                    # Update notes if provided
                    notes = (event_item.get('notes') or '').strip()
                    if notes and saas_batch.get('notes') != notes:
                        update_batch_data['notes'] = notes
                    
                    if update_batch_data:
                        Batch.update_batch(feedlot_code_normalized, export_batch_id, update_batch_data)
                        batches_updated += 1
                
                # Update cattle status to Export and assign to export batch
                update_cattle_data = {'cattle_status': 'Export'}
                if export_batch_id:
                    update_cattle_data['batch_id'] = ObjectId(export_batch_id)
                
                Cattle.update_cattle(
                    feedlot_code_normalized,
                    cattle_record_id,
                    update_cattle_data,
                    updated_by='api'
                )
                
                # Add audit log entry for export
                audit_details = {
                    'uhf_tag': epc,
                    'export_timestamp': export_timestamp.isoformat() if isinstance(export_timestamp, datetime) else str(export_timestamp),
                    'previous_status': current_status
                }
                if export_batch_id:
                    audit_details['export_batch_id'] = export_batch_id
                    audit_details['export_batch_name'] = batch_name
                if previous_batch_id:
                    audit_details['previous_batch_id'] = str(previous_batch_id)
                
                Cattle.add_audit_log_entry(
                    feedlot_code_normalized,
                    cattle_record_id,
                    'exported',
                    f'Cattle marked as Export and assigned to batch "{batch_name}" (UHF tag: {epc})',
                    'api',
                    audit_details
                )
                
                records_updated += 1
                
                # Store event for manifest creation
                # Check if manifest data exists (at least one non-empty field)
                has_manifest_data = any(v for v in manifest_fields.values() if v not in (None, '', False))
                
                if has_manifest_data:
                    manifest_key = create_manifest_key(manifest_fields)
                    if manifest_key not in manifest_groups:
                        manifest_groups[manifest_key] = {
                            'manifest_fields': manifest_fields,
                            'cattle_ids': []
                        }
                    manifest_groups[manifest_key]['cattle_ids'].append(cattle_record_id)
                
                processed_events.append({
                    'cattle_id': cattle_record_id,
                    'cattle': existing_cattle,
                    'manifest_fields': manifest_fields,
                    'has_manifest_data': has_manifest_data,
                    'export_batch_id': export_batch_id,
                    'export_batch_name': batch_name
                })
                    
            except Exception as e:
                errors.append(f'Record {records_processed}: {str(e)}')
                records_skipped += 1
        
        # Create manifest records for each group
        for manifest_key, group_data in manifest_groups.items():
            try:
                if not group_data['cattle_ids']:
                    continue
                
                # Fetch full cattle records for this group
                cattle_list = []
                for cattle_id in group_data['cattle_ids']:
                    cattle = Cattle.find_by_id(feedlot_code_normalized, cattle_id)
                    if cattle:
                        cattle_list.append(cattle)
                
                if not cattle_list:
                    continue
                
                # Prepare manifest data - convert manifest_fields dict to format expected by generate_manifest_data
                manifest_fields = group_data['manifest_fields']
                
                # Use generate_manifest_data to create the manifest structure
                manifest_data = generate_manifest_data(
                    cattle_list=cattle_list,
                    template_data=manifest_fields,
                    feedlot_data=feedlot,
                    manual_data=None
                )
                
                # Create manifest record
                manifest_id = Manifest.create_manifest(
                    feedlot_id=str(feedlot_id),
                    manifest_data=manifest_data,
                    cattle_ids=group_data['cattle_ids'],
                    template_id=None,
                    created_by='api'
                )
                
                manifests_created += 1
                manifest_ids.append(manifest_id)
                
            except Exception as e:
                errors.append(f'Manifest creation error: {str(e)}')
        
        return jsonify({
            'success': True,
            'message': f'Processed {records_processed} export event records',
            'records_processed': records_processed,
            'records_created': records_created,
            'records_updated': records_updated,
            'records_skipped': records_skipped,
            'batches_created': batches_created,
            'batches_updated': batches_updated,
            'manifests_created': manifests_created,
            'manifest_ids': manifest_ids,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500


@api_bp.route('/v2/event', methods=['POST'])
@api_key_required
def handle_event():
    """Unified v2 event endpoint that routes to v1 handlers based on event code"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body must be JSON'
        }), 400

    event_code = (data.get('event') or '').strip().lower()
    if not event_code:
        return jsonify({
            'success': False,
            'message': 'event is required in request body'
        }), 400

    # Map event codes to existing handlers (reuse v1 logic)
    handler_map = {
        'induction': sync_induction_events.__wrapped__,
        'repair': sync_repair_events.__wrapped__,
        'checkin': sync_checkin_events.__wrapped__,
        'export': sync_export_events.__wrapped__,
        'pair': sync_pairing_events.__wrapped__,
        'pairing': sync_pairing_events.__wrapped__,  # alias for backward compatibility
    }

    handler = handler_map.get(event_code)
    if not handler:
        return jsonify({
            'success': False,
            'message': 'Invalid event. Supported events: induction, repair, checkin, export, pair'
        }), 400

    # The decorators have already attached feedlot context; call underlying handler logic
    return handler()
# API key generation is now only available through the web UI (Settings → API Keys)
# This endpoint has been removed to restrict key generation to the secure web interface
# Use the Settings page in the web application to generate and manage API keys

