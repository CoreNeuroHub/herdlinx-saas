#!/usr/bin/env python3
"""
Sync data from SQLite database to HerdLinx SaaS API.
Reads data from the office app database and sends it to the API endpoints.
"""

import sqlite3
import requests
import json
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime


class APISyncer:
    """Handles syncing data from SQLite to the SaaS API."""
    
    def __init__(self, api_base_url: str, api_key: str, feedlot_code: str, db_path: str = "herdlinx.db"):
        """
        Initialize the API syncer.
        
        Args:
            api_base_url: Base URL for the API (e.g., "https://your-domain.com/api/v1/feedlot")
            api_key: API key for authentication
            feedlot_code: Feedlot code to use in requests
            db_path: Path to SQLite database
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.feedlot_code = feedlot_code.upper()
        self.db_path = db_path
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """
        Make a POST request to the API.
        
        Args:
            endpoint: API endpoint (e.g., "/batches")
            data: Request data
            
        Returns:
            Response JSON as dictionary
        """
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response text: {e.response.text}")
            raise
    
    def sync_batches(self) -> Dict:
        """Sync batches from database to API."""
        print("\nSyncing batches...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, funder, lot, pen, lot_group, pen_location, 
                   sex, tag_color, visual_id, notes, created_at, active
            FROM batches
            ORDER BY created_at
        """)
        
        batches = []
        for row in cursor.fetchall():
            batches.append({
                "name": row["name"],
                "funder": row["funder"],
                "lot": row["lot"],
                "pen": row["pen"],
                "lot_group": row["lot_group"],
                "pen_location": row["pen_location"],
                "sex": row["sex"],
                "tag_color": row["tag_color"],
                "visual_id": row["visual_id"],
                "notes": row["notes"],
                "created_at": row["created_at"],
                "active": row["active"]
            })
        
        conn.close()
        
        if not batches:
            print("  No batches to sync.")
            return {"success": True, "records_processed": 0}
        
        data = {
            "feedlot_code": self.feedlot_code,
            "data": batches
        }
        
        result = self._make_request("/batches", data)
        print(f"  Processed {result.get('records_processed', 0)} batches")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        
        return result
    
    def sync_induction_events(self) -> Dict:
        """Sync induction events from database to API."""
        print("\nSyncing induction events...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ie.id, ie.livestock_id, ie.batch_id, ie.timestamp, b.name as batch_name
            FROM induction_events ie
            JOIN batches b ON ie.batch_id = b.id
            ORDER BY ie.timestamp
        """)
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "id": row["id"],
                "livestock_id": row["livestock_id"],
                "batch_id": row["batch_id"],
                "batch_name": row["batch_name"],
                "timestamp": row["timestamp"]
            })
        
        conn.close()
        
        if not events:
            print("  No induction events to sync.")
            return {"success": True, "records_processed": 0}
        
        data = {
            "feedlot_code": self.feedlot_code,
            "data": events
        }
        
        result = self._make_request("/induction-events", data)
        print(f"  Processed {result.get('records_processed', 0)} induction events")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        
        return result
    
    def sync_pairing_events(self) -> Dict:
        """Sync pairing events from database to API."""
        print("\nSyncing pairing events...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, livestock_id, lf_id, epc, weight_kg, timestamp
            FROM pairing_events
            ORDER BY timestamp
        """)
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "id": row["id"],
                "livestock_id": row["livestock_id"],
                "lf_id": row["lf_id"],
                "epc": row["epc"],
                "weight_kg": row["weight_kg"],
                "timestamp": row["timestamp"]
            })
        
        conn.close()
        
        if not events:
            print("  No pairing events to sync.")
            return {"success": True, "records_processed": 0}
        
        data = {
            "feedlot_code": self.feedlot_code,
            "data": events
        }
        
        result = self._make_request("/pairing-events", data)
        print(f"  Processed {result.get('records_processed', 0)} pairing events")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        
        return result
    
    def sync_livestock(self) -> Dict:
        """Sync current livestock state from database to API."""
        print("\nSyncing livestock (current state)...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, induction_event_id, current_lf_id, current_epc, 
                   metadata, created_at, updated_at
            FROM livestock
            ORDER BY id
        """)
        
        livestock = []
        for row in cursor.fetchall():
            livestock.append({
                "id": row["id"],
                "induction_event_id": row["induction_event_id"],
                "current_lf_id": row["current_lf_id"],
                "current_epc": row["current_epc"],
                "metadata": row["metadata"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        conn.close()
        
        if not livestock:
            print("  No livestock to sync.")
            return {"success": True, "records_processed": 0}
        
        data = {
            "feedlot_code": self.feedlot_code,
            "data": livestock
        }
        
        result = self._make_request("/livestock", data)
        print(f"  Processed {result.get('records_processed', 0)} livestock records")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        
        return result
    
    def sync_checkin_events(self) -> Dict:
        """Sync check-in events from database to API."""
        print("\nSyncing check-in events...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, livestock_id, lf_id, epc, weight_kg, timestamp
            FROM checkin_events
            ORDER BY timestamp
        """)
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "id": row["id"],
                "livestock_id": row["livestock_id"],
                "lf_id": row["lf_id"],
                "epc": row["epc"],
                "weight_kg": row["weight_kg"],
                "timestamp": row["timestamp"]
            })
        
        conn.close()
        
        if not events:
            print("  No check-in events to sync.")
            return {"success": True, "records_processed": 0}
        
        data = {
            "feedlot_code": self.feedlot_code,
            "data": events
        }
        
        result = self._make_request("/checkin-events", data)
        print(f"  Processed {result.get('records_processed', 0)} check-in events")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        
        return result
    
    def sync_repair_events(self) -> Dict:
        """Sync repair events from database to API."""
        print("\nSyncing repair events...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, livestock_id, old_lf_id, new_lf_id, old_epc, new_epc, 
                   reason, timestamp
            FROM repair_events
            ORDER BY timestamp
        """)
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "id": row["id"],
                "livestock_id": row["livestock_id"],
                "old_lf_id": row["old_lf_id"],
                "new_lf_id": row["new_lf_id"],
                "old_epc": row["old_epc"],
                "new_epc": row["new_epc"],
                "reason": row["reason"],
                "timestamp": row["timestamp"]
            })
        
        conn.close()
        
        if not events:
            print("  No repair events to sync.")
            return {"success": True, "records_processed": 0}
        
        data = {
            "feedlot_code": self.feedlot_code,
            "data": events
        }
        
        result = self._make_request("/repair-events", data)
        print(f"  Processed {result.get('records_processed', 0)} repair events")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        
        return result
    
    def sync_all(self):
        """Sync all data in the recommended order."""
        print("="*60)
        print("Starting full sync to API")
        print("="*60)
        print(f"API Base URL: {self.api_base_url}")
        print(f"Feedlot Code: {self.feedlot_code}")
        print(f"Database: {self.db_path}")
        print("="*60)
        
        results = {}
        
        try:
            # Recommended sync order per API documentation
            results["batches"] = self.sync_batches()
            results["induction_events"] = self.sync_induction_events()
            results["pairing_events"] = self.sync_pairing_events()
            results["livestock"] = self.sync_livestock()
            results["checkin_events"] = self.sync_checkin_events()
            results["repair_events"] = self.sync_repair_events()
            
            print("\n" + "="*60)
            print("Sync Summary")
            print("="*60)
            
            total_processed = 0
            total_created = 0
            total_updated = 0
            total_skipped = 0
            
            for endpoint, result in results.items():
                if result.get("success"):
                    processed = result.get("records_processed", 0)
                    created = result.get("records_created", 0)
                    updated = result.get("records_updated", 0)
                    skipped = result.get("records_skipped", 0)
                    
                    total_processed += processed
                    total_created += created
                    total_updated += updated
                    total_skipped += skipped
                    
                    print(f"{endpoint:20s} | Processed: {processed:4d} | "
                          f"Created: {created:4d} | Updated: {updated:4d} | "
                          f"Skipped: {skipped:4d}")
            
            print("="*60)
            print(f"Total Processed: {total_processed}")
            print(f"Total Created:   {total_created}")
            print(f"Total Updated:   {total_updated}")
            print(f"Total Skipped:   {total_skipped}")
            print("="*60)
            print("\nSync completed successfully!")
            
        except Exception as e:
            print(f"\nError during sync: {e}")
            sys.exit(1)


def main():
    """Main function."""
    # Configuration - can be set via environment variables or command line args
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:5000/api/v1/feedlot")
    api_key = os.getenv("API_KEY", "xzeevsft-TDfd8NO_Z408LO7M2mMrIWqajAvQSDLzpM")
    feedlot_code = os.getenv("FEEDLOT_CODE", "AAA111")
    db_path = os.getenv("DB_PATH", "herdlinx.db")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: sync_to_api.py [API_BASE_URL] [API_KEY] [FEEDLOT_CODE] [DB_PATH]")
            print("\nOr set environment variables:")
            print("  API_BASE_URL - Base URL for the API")
            print("  API_KEY - API key for authentication")
            print("  FEEDLOT_CODE - Feedlot code to use")
            print("  DB_PATH - Path to SQLite database (default: herdlinx.db)")
            print("\nExample:")
            print("  export API_BASE_URL='https://your-domain.com/api/v1/feedlot'")
            print("  export API_KEY='your_api_key_here'")
            print("  export FEEDLOT_CODE='FEEDLOT001'")
            print("  python sync_to_api.py")
            return
        
        if len(sys.argv) >= 2:
            api_base_url = sys.argv[1]
        if len(sys.argv) >= 3:
            api_key = sys.argv[2]
        if len(sys.argv) >= 4:
            feedlot_code = sys.argv[3]
        if len(sys.argv) >= 5:
            db_path = sys.argv[4]
    
    # Validate configuration
    if not api_key:
        print("Error: API key is required.")
        print("Set API_KEY environment variable or pass as argument.")
        print("Run with --help for usage information.")
        sys.exit(1)
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found: {db_path}")
        print("Please run db_init.py and populate_sample_data.py first.")
        sys.exit(1)
    
    # Create syncer and run sync
    syncer = APISyncer(api_base_url, api_key, feedlot_code, db_path)
    syncer.sync_all()


if __name__ == "__main__":
    main()

