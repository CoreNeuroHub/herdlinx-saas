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
                headers = dict(request.headers)
                
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
                
                request_info = f"API Request: {method} {path}"
                logger.info(request_info)
                print(request_info)
                
                headers_str = json.dumps(headers, indent=2, default=str)
                logger.info(f"Headers: {headers_str}")
                print(f"Headers: {headers_str}")
                
                if payload:
                    payload_str = json.dumps(payload, indent=2, default=str)
                    logger.info(f"Payload: {payload_str}")
                    print(f"Payload: {payload_str}")
                else:
                    logger.info("Payload: (empty or not JSON)")
                    print("Payload: (empty or not JSON)")
                
                logger.info(separator)
                print(separator)
            except Exception as e:
                logger.error(f"Error logging request: {str(e)}")

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
                'livestock': '/api/v1/feedlot/livestock',
                'induction_events': '/api/v1/feedlot/induction-events',
                'pairing_events': '/api/v1/feedlot/pairing-events',
                'checkin_events': '/api/v1/feedlot/checkin-events',
                'repair_events': '/api/v1/feedlot/repair-events'
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
    print("  POST /api/v1/feedlot/livestock        - Sync livestock")
    print("  POST /api/v1/feedlot/induction-events - Sync induction events")
    print("  POST /api/v1/feedlot/pairing-events   - Sync pairing events")
    print("  POST /api/v1/feedlot/checkin-events   - Sync check-in events")
    print("  POST /api/v1/feedlot/repair-events    - Sync repair events")
    print("=" * 60)
    print("\nAuthentication: X-API-Key header required\n")

    app.run(debug=True, host='0.0.0.0', port=5021)
