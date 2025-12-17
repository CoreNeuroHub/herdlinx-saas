"""
API Server - Runs on port 5021
Dedicated server for Office Pi synchronization endpoints
"""
import json
import logging
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from app import get_db, db

# Configure logging to explicitly output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)

def create_api_app():
    """Create Flask app with only API routes"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for API endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Log all incoming requests to API endpoints
    @app.before_request
    def log_request():
        """Log incoming request details including payload"""
        if request.path.startswith('/api'):
            try:
                # Get request data
                method = request.method
                path = request.path
                
                # Get JSON payload if available
                payload = None
                if request.is_json:
                    payload = request.get_json(silent=True)
                elif request.data:
                    try:
                        payload = json.loads(request.data.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        payload = request.data.decode('utf-8', errors='replace')
                
                # Log request details to both logger and console
                separator = "=" * 60
                logger.info(separator)
                print(separator)
                
                request_info = f"INCOMING REQUEST: {method} {path}"
                logger.info(request_info)
                print(request_info)
                
                if payload:
                    payload_str = json.dumps(payload, indent=2, default=str)
                    logger.info(f"PAYLOAD:\n{payload_str}")
                    print(f"PAYLOAD:\n{payload_str}")
                else:
                    logger.info("PAYLOAD: (empty or not JSON)")
                    print("PAYLOAD: (empty or not JSON)")
                
                logger.info(separator)
                print(separator)
            except Exception as e:
                logger.error(f"Error logging request: {str(e)}")
                print(f"Error logging request: {str(e)}")
    
    # Log all responses to API endpoints
    @app.after_request
    def log_response(response):
        """Log response details including database operation results"""
        if request.path.startswith('/api'):
            try:
                separator = "=" * 60
                
                # Get response data
                status_code = response.status_code
                response_data = None
                
                # Try to parse response JSON
                if response.is_json:
                    try:
                        response_data = response.get_json()
                    except:
                        pass
                elif response.data:
                    try:
                        response_data = json.loads(response.data.decode('utf-8'))
                    except:
                        pass
                
                # Log response details
                logger.info(separator)
                print(separator)
                
                status_prefix = "[SUCCESS]" if 200 <= status_code < 300 else "[FAILED]"
                response_info = f"{status_prefix} RESPONSE: {status_code} {request.method} {request.path}"
                logger.info(response_info)
                print(response_info)
                
                if response_data:
                    # Extract database operation results
                    success = response_data.get('success', False)
                    message = response_data.get('message', '')
                    records_processed = response_data.get('records_processed', 0)
                    records_created = response_data.get('records_created', 0)
                    records_updated = response_data.get('records_updated', 0)
                    records_skipped = response_data.get('records_skipped', 0)
                    batches_created = response_data.get('batches_created', 0)
                    batches_updated = response_data.get('batches_updated', 0)
                    errors = response_data.get('errors', [])
                    
                    # Display success status
                    db_status = "[SUCCESS] DATABASE OPERATION: SUCCESS" if success else "[FAILED] DATABASE OPERATION: FAILED"
                    logger.info(db_status)
                    print(db_status)
                    
                    # Display summary
                    summary_parts = []
                    if message:
                        summary_parts.append(f"Message: {message}")
                    if records_processed > 0:
                        summary_parts.append(f"Processed: {records_processed}")
                    if records_created > 0:
                        summary_parts.append(f"Created: {records_created}")
                    if records_updated > 0:
                        summary_parts.append(f"Updated: {records_updated}")
                    if records_skipped > 0:
                        summary_parts.append(f"Skipped: {records_skipped}")
                    if batches_created > 0:
                        summary_parts.append(f"Batches Created: {batches_created}")
                    if batches_updated > 0:
                        summary_parts.append(f"Batches Updated: {batches_updated}")
                    
                    if summary_parts:
                        summary = " | ".join(summary_parts)
                        logger.info(f"SUMMARY: {summary}")
                        print(f"SUMMARY: {summary}")
                    
                    # Display errors if any
                    if errors:
                        errors_str = "\n".join([f"  - {error}" for error in errors])
                        logger.warning(f"ERRORS:\n{errors_str}")
                        print(f"ERRORS:\n{errors_str}")
                    
                    # Full response for debugging
                    response_str = json.dumps(response_data, indent=2, default=str)
                    logger.info(f"FULL RESPONSE:\n{response_str}")
                    print(f"FULL RESPONSE:\n{response_str}")
                else:
                    logger.info("RESPONSE: (no JSON data)")
                    print("RESPONSE: (no JSON data)")
                
                logger.info(separator)
                print(separator)
                print()  # Add blank line for readability
                
            except Exception as e:
                logger.error(f"Error logging response: {str(e)}")
                print(f"Error logging response: {str(e)}")
        
        return response

    # Register only the API blueprint
    from app.routes.api_routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Health check endpoint
    @app.route('/health')
    def health():
        """API health check endpoint"""
        try:
            # Test MongoDB connection
            get_db()
            return jsonify({
                'status': 'healthy',
                'service': 'herdlinx-api',
                'database': 'connected'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'herdlinx-api',
                'database': 'disconnected',
                'error': str(e)
            }), 500

    # Root endpoint
    @app.route('/')
    def root():
        """API root endpoint"""
        return jsonify({
            'service': 'HerdLinx API Server',
            'version': '1.0',
            'endpoints': {
                'health': '/health',
                'batches': '/api/v1/feedlot/batches',
                'induction_events': '/api/v1/feedlot/induction-events',
                'pairing_events': '/api/v1/feedlot/pairing-events',
                'checkin_events': '/api/v1/feedlot/checkin-events',
                'repair_events': '/api/v1/feedlot/repair-events',
                'v2_event': '/api/v2/event'
            },
            'authentication': 'API Key required (X-API-Key header)',
            'documentation': 'https://docs.herdlinx.com/api'
        }), 200

    return app

if __name__ == '__main__':
    app = create_api_app()
    print("=" * 60)
    print("HerdLinx API Server Starting")
    print("=" * 60)
    print(f"Port: 5021")
    print(f"MongoDB: {Config.MONGODB_URI[:30]}...")
    print("=" * 60)
    print("\nAvailable Endpoints:")
    print("  GET  /health                          - Health check")
    print("  POST /api/v1/feedlot/batches          - Sync batches")
    print("  POST /api/v1/feedlot/induction-events - Sync induction events")
    print("  POST /api/v1/feedlot/pairing-events   - Sync pairing events")
    print("  POST /api/v1/feedlot/checkin-events   - Sync check-in events")
    print("  POST /api/v1/feedlot/repair-events    - Sync repair events")
    print("  POST /api/v2/event                    - Unified event endpoint")
    print("=" * 60)
    print("\nAuthentication: X-API-Key header required\n")

    app.run(debug=True, host='0.0.0.0', port=5021)
