"""
Migration script to backfill cattle_ids array for existing batches.

This script queries all cattle with a batch_id and populates the corresponding
batch's cattle_ids array with historical cattle references.

Usage:
    python scripts/migrate_batch_cattle_ids.py

Make sure to set up your environment variables (MONGODB_URI) before running.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from bson import ObjectId
from datetime import datetime
from app import get_feedlot_db, db


def migrate_batch_cattle_ids():
    """
    Migrate existing batches to include cattle_ids array with all cattle
    that have been associated with each batch.
    """
    print("Starting batch cattle_ids migration...")
    
    # Get all feedlots from the main database
    feedlots = list(db.feedlots.find({'deleted_at': None}))
    print(f"Found {len(feedlots)} feedlots to process")
    
    total_batches_updated = 0
    total_cattle_linked = 0
    
    for feedlot in feedlots:
        feedlot_id = feedlot['_id']
        feedlot_code = feedlot.get('feedlot_code')
        feedlot_name = feedlot.get('name', 'Unknown')
        
        if not feedlot_code:
            print(f"  Skipping feedlot {feedlot_name} - no feedlot_code")
            continue
        
        print(f"\nProcessing feedlot: {feedlot_name} ({feedlot_code})")
        
        try:
            # Get feedlot-specific database
            feedlot_db = get_feedlot_db(feedlot_code)
            
            # Get all batches for this feedlot
            batches = list(feedlot_db.batches.find({'deleted_at': None}))
            print(f"  Found {len(batches)} batches")
            
            for batch in batches:
                batch_id = batch['_id']
                batch_number = batch.get('batch_number', 'Unknown')
                
                # Check if cattle_ids already exists and is populated
                existing_cattle_ids = batch.get('cattle_ids', [])
                
                # Find all cattle that belong to this batch (including deleted)
                cattle_in_batch = list(feedlot_db.cattle.find({
                    'batch_id': batch_id
                }))
                
                cattle_record_ids = [ObjectId(c['_id']) for c in cattle_in_batch]
                
                if not cattle_record_ids:
                    # No cattle in this batch, ensure cattle_ids is an empty array
                    if 'cattle_ids' not in batch:
                        feedlot_db.batches.update_one(
                            {'_id': batch_id},
                            {'$set': {'cattle_ids': [], 'updated_at': datetime.utcnow()}}
                        )
                    continue
                
                # Merge existing cattle_ids with found cattle (use $addToSet to avoid duplicates)
                # First, initialize cattle_ids if it doesn't exist
                if 'cattle_ids' not in batch:
                    feedlot_db.batches.update_one(
                        {'_id': batch_id},
                        {'$set': {'cattle_ids': [], 'updated_at': datetime.utcnow()}}
                    )
                
                # Add all cattle IDs using $addToSet to avoid duplicates
                for cattle_id in cattle_record_ids:
                    feedlot_db.batches.update_one(
                        {'_id': batch_id},
                        {'$addToSet': {'cattle_ids': cattle_id}}
                    )
                
                # Update timestamp
                feedlot_db.batches.update_one(
                    {'_id': batch_id},
                    {'$set': {'updated_at': datetime.utcnow()}}
                )
                
                new_cattle_count = len(cattle_record_ids)
                existing_count = len(existing_cattle_ids)
                added_count = new_cattle_count - existing_count if new_cattle_count > existing_count else 0
                
                if added_count > 0:
                    print(f"    Batch {batch_number}: Added {added_count} cattle (total: {new_cattle_count})")
                    total_batches_updated += 1
                    total_cattle_linked += added_count
                else:
                    print(f"    Batch {batch_number}: {new_cattle_count} cattle already linked")
                    
        except Exception as e:
            print(f"  Error processing feedlot {feedlot_name}: {str(e)}")
            continue
    
    print(f"\n{'='*50}")
    print("Migration complete!")
    print(f"  Batches updated: {total_batches_updated}")
    print(f"  Cattle links added: {total_cattle_linked}")
    print(f"{'='*50}")


if __name__ == '__main__':
    migrate_batch_cattle_ids()

