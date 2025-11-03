"""Database Sync API for Pi Backend

Provides endpoints for remote servers to sync database changes.
This enables database replication across distributed deployments.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from office_app.models.batch import Batch
from office_app.models.cattle import Cattle
from office_app.models.pen import Pen
from office_app.security import require_auth
import logging

logger = logging.getLogger(__name__)

sync_api_bp = Blueprint('sync_api', __name__, url_prefix='/api/sync')


@sync_api_bp.route('/changes', methods=['GET'])
@require_auth
def get_changes():
    """
    Get all database changes since a specific timestamp.

    Used by remote servers to sync database.

    Query parameters:
    - since: ISO timestamp (e.g., 2024-01-15T10:30:00)
    - limit: Max records to return (default: 1000)

    Returns:
    {
        "success": true,
        "timestamp": "2024-01-15T10:35:00",
        "data": {
            "batches": [...],
            "cattle": [...],
            "pens": [...]
        }
    }
    """
    try:
        since_str = request.args.get('since', '')
        limit = int(request.args.get('limit', 1000))
        limit = min(limit, 5000)  # Max 5000 records

        # Parse since timestamp
        since_timestamp = None
        if since_str:
            try:
                since_timestamp = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid since timestamp: {since_str}")
                since_timestamp = None

        # Query changes
        query_filter = {}
        if since_timestamp:
            query_filter['updated_at_gte'] = since_timestamp

        # Get batches
        batches_query = Batch.query
        if since_timestamp:
            batches_query = batches_query.filter(Batch.updated_at >= since_timestamp)
        batches = batches_query.order_by(Batch.updated_at.desc()).limit(limit).all()

        # Get cattle
        cattle_query = Cattle.query
        if since_timestamp:
            cattle_query = cattle_query.filter(Cattle.updated_at >= since_timestamp)
        cattle = cattle_query.order_by(Cattle.updated_at.desc()).limit(limit).all()

        # Get pens
        pens_query = Pen.query
        if since_timestamp:
            pens_query = pens_query.filter(Pen.updated_at >= since_timestamp)
        pens = pens_query.order_by(Pen.updated_at.desc()).limit(limit).all()

        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'batches': [b.to_dict() for b in batches],
                'cattle': [c.to_dict() for c in cattle],
                'pens': [p.to_dict() for p in pens]
            },
            'counts': {
                'batches': len(batches),
                'cattle': len(cattle),
                'pens': len(pens)
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting sync changes: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting changes: {str(e)}'
        }), 500


@sync_api_bp.route('/full-export', methods=['GET'])
@require_auth
def export_full_database():
    """
    Export entire database for initial sync or backup.

    Returns:
    {
        "success": true,
        "exported_at": "2024-01-15T10:35:00",
        "data": {
            "batches": [...],
            "cattle": [...],
            "pens": [...]
        }
    }
    """
    try:
        # Get all data
        batches = Batch.query.order_by(Batch.created_at.desc()).all()
        cattle = Cattle.query.order_by(Cattle.created_at.desc()).all()
        pens = Pen.query.order_by(Pen.created_at.desc()).all()

        return jsonify({
            'success': True,
            'exported_at': datetime.utcnow().isoformat(),
            'data': {
                'batches': [b.to_dict() for b in batches],
                'cattle': [c.to_dict() for c in cattle],
                'pens': [p.to_dict() for p in pens]
            },
            'counts': {
                'batches': len(batches),
                'cattle': len(cattle),
                'pens': len(pens)
            }
        }), 200

    except Exception as e:
        logger.error(f"Error exporting database: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error exporting database: {str(e)}'
        }), 500


@sync_api_bp.route('/schema', methods=['GET'])
def get_schema():
    """
    Get database schema version.

    Used to ensure Server and Pi have compatible schemas.

    Returns:
    {
        "success": true,
        "schema_version": "1.0",
        "tables": ["batches", "cattle", "pens", "users", ...]
    }
    """
    try:
        from office_app import db

        # Get all table names
        tables = db.inspect(db.engine).get_table_names() if hasattr(db, 'inspect') else []

        return jsonify({
            'success': True,
            'schema_version': '1.0',
            'tables': sorted(tables),
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting schema: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting schema: {str(e)}'
        }), 500
