"""
Office API Server - Dedicated server for office system data ingestion

This server runs on port 5021 and handles all data synchronization
from office Raspberry Pi systems to the SAAS MongoDB database.

Endpoints:
- POST /v1/feedlot/batches - Sync batch data
- POST /v1/feedlot/livestock - Sync livestock current state
- POST /v1/feedlot/induction-events - Sync induction events
- POST /v1/feedlot/pairing-events - Sync pairing events (tags + weight)
- POST /v1/feedlot/checkin-events - Sync checkin events (weight measurements)
- POST /v1/feedlot/repair-events - Sync repair events (tag replacements)

Authentication: API Key (X-API-Key header or api_key query parameter)

Usage:
    python run_api.py
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("HerdLinx Office API Server")
    print("=" * 60)
    print(f"Starting on http://0.0.0.0:5021")
    print("Ready to receive data from office Raspberry Pi systems")
    print()
    print("API Endpoints:")
    print("  POST /v1/feedlot/batches")
    print("  POST /v1/feedlot/livestock")
    print("  POST /v1/feedlot/induction-events")
    print("  POST /v1/feedlot/pairing-events")
    print("  POST /v1/feedlot/checkin-events")
    print("  POST /v1/feedlot/repair-events")
    print()
    print("Authentication: X-API-Key header required")
    print("=" * 60)

    app.run(debug=False, host='0.0.0.0', port=5021)
