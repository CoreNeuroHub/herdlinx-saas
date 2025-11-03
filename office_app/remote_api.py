"""Remote API for distributed architecture

Provides REST API and WebSocket endpoints for remote UI access.
This module runs on the Raspberry Pi backend.
"""
from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from office_app.models.batch import Batch
from office_app.models.lora_payload_buffer import LoRaPayloadBuffer
from office_app.models.pen import Pen
from office_app.models.cattle import Cattle
from office_app.security import require_api_key, require_auth, TokenManager, APIKeyManager
from datetime import datetime
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

# Blueprint for REST API
remote_api_bp = Blueprint('remote_api', __name__, url_prefix='/api/remote')

# Global SocketIO instance (will be set in __init__)
socketio = None


def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins=['*'],  # Configure with actual server IP/domain
        ping_timeout=60,
        ping_interval=25
    )

    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('response', {'data': 'Connected to HerdLinx backend'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")

    return socketio


def broadcast_payload_received(payload_id, raw_payload):
    """Broadcast payload received event to all connected clients"""
    if socketio:
        socketio.emit('payload:received', {
            'payload_id': payload_id,
            'raw_payload': raw_payload,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)


def broadcast_payload_processed(payload_id, batch_id, batch_number):
    """Broadcast payload processed event"""
    if socketio:
        socketio.emit('payload:processed', {
            'payload_id': payload_id,
            'batch_id': batch_id,
            'batch_number': batch_number,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)


def broadcast_batch_created(batch_id, batch_number, source_type):
    """Broadcast batch created event"""
    if socketio:
        socketio.emit('batch:created', {
            'batch_id': batch_id,
            'batch_number': batch_number,
            'source_type': source_type,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)


# REST API Endpoints

@remote_api_bp.route('/auth/token', methods=['POST'])
@require_api_key
def get_auth_token():
    """
    Get JWT token using API key authentication

    Expected JSON:
    {
        "user_id": 1
    }

    Returns JWT token for subsequent requests
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)

        token = TokenManager.generate_token(user_id=user_id)

        return jsonify({
            'success': True,
            'token': token,
            'expires_in': 86400  # 24 hours in seconds
        }), 200

    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error generating token: {str(e)}'
        }), 500


@remote_api_bp.route('/batches', methods=['GET'])
@require_auth
def list_batches_api():
    """
    List all batches with optional filtering

    Query params:
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    - source_type: Filter by source (hxb, hxe)
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        source_type = request.args.get('source_type', '')

        limit = min(limit, 500)  # Max 500

        query = Batch.query

        if source_type:
            query = query.filter_by(source_type=source_type)

        total = query.count()
        batches = query.order_by(Batch.induction_date.desc()).offset(offset).limit(limit).all()

        return jsonify({
            'success': True,
            'data': [b.to_dict() for b in batches],
            'total': total,
            'count': len(batches)
        }), 200

    except Exception as e:
        logger.error(f"Error listing batches: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error listing batches: {str(e)}'
        }), 500


@remote_api_bp.route('/batches/<int:batch_id>', methods=['GET'])
@require_auth
def get_batch_api(batch_id):
    """Get specific batch details"""
    try:
        batch = Batch.find_by_id(batch_id)

        if not batch:
            return jsonify({
                'success': False,
                'message': 'Batch not found'
            }), 404

        # Get associated cattle
        cattle = Cattle.find_by_batch(batch_id)

        batch_data = batch.to_dict()
        batch_data['cattle'] = [c.to_dict() for c in cattle]

        return jsonify({
            'success': True,
            'data': batch_data
        }), 200

    except Exception as e:
        logger.error(f"Error getting batch: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting batch: {str(e)}'
        }), 500


@remote_api_bp.route('/payloads', methods=['GET'])
@require_auth
def list_payloads_api():
    """
    List buffered payloads with optional filtering

    Query params:
    - status: Filter by status (received, processing, processed, duplicate, error)
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        status = request.args.get('status', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        limit = min(limit, 500)

        query = LoRaPayloadBuffer.query

        if status:
            query = query.filter_by(status=status)

        total = query.count()
        payloads = query.order_by(LoRaPayloadBuffer.received_at.desc()).offset(offset).limit(limit).all()

        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in payloads],
            'total': total,
            'count': len(payloads)
        }), 200

    except Exception as e:
        logger.error(f"Error listing payloads: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error listing payloads: {str(e)}'
        }), 500


@remote_api_bp.route('/payloads/<int:payload_id>', methods=['GET'])
@require_auth
def get_payload_api(payload_id):
    """Get specific payload details"""
    try:
        payload = LoRaPayloadBuffer.find_by_id(payload_id)

        if not payload:
            return jsonify({
                'success': False,
                'message': 'Payload not found'
            }), 404

        return jsonify({
            'success': True,
            'data': payload.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error getting payload: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting payload: {str(e)}'
        }), 500


@remote_api_bp.route('/status', methods=['GET'])
@require_auth
def get_system_status():
    """Get system status and statistics"""
    try:
        total_batches = Batch.query.count()
        total_cattle = Cattle.query.count()
        total_payloads = LoRaPayloadBuffer.query.count()
        processed_payloads = LoRaPayloadBuffer.query.filter_by(status='processed').count()
        error_payloads = LoRaPayloadBuffer.query.filter_by(status='error').count()

        return jsonify({
            'success': True,
            'data': {
                'timestamp': datetime.utcnow().isoformat(),
                'batches': total_batches,
                'cattle': total_cattle,
                'total_payloads': total_payloads,
                'processed_payloads': processed_payloads,
                'error_payloads': error_payloads,
                'processing_rate': f"{(processed_payloads / total_payloads * 100):.1f}%" if total_payloads > 0 else "0%"
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting status: {str(e)}'
        }), 500


@remote_api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (no authentication required)"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# WebSocket Events

def register_socketio_handlers(sock):
    """Register WebSocket event handlers"""

    @sock.on('subscribe:payloads')
    def on_subscribe_payloads():
        """Subscribe to payload updates"""
        join_room('payloads')
        logger.info(f"Client {request.sid} subscribed to payloads")
        emit('response', {'message': 'Subscribed to payload updates'})

    @sock.on('unsubscribe:payloads')
    def on_unsubscribe_payloads():
        """Unsubscribe from payload updates"""
        leave_room('payloads')
        logger.info(f"Client {request.sid} unsubscribed from payloads")

    @sock.on('subscribe:batches')
    def on_subscribe_batches():
        """Subscribe to batch updates"""
        join_room('batches')
        logger.info(f"Client {request.sid} subscribed to batches")
        emit('response', {'message': 'Subscribed to batch updates'})

    @sock.on('unsubscribe:batches')
    def on_unsubscribe_batches():
        """Unsubscribe from batch updates"""
        leave_room('batches')
        logger.info(f"Client {request.sid} unsubscribed from batches")
