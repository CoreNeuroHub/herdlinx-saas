#!/usr/bin/env python3
"""
SAAS Database Reset Script (Python)
Cleans SAAS MongoDB for fresh testing
"""

import sys
import argparse

def print_success(text):
    print(f"✓ {text}")

def print_warning(text):
    print(f"⚠ {text}")

def print_error(text):
    print(f"✗ {text}")

def main():
    parser = argparse.ArgumentParser(description='Clean SAAS MongoDB')
    parser.add_argument('--all', action='store_true', help='Delete users too (DANGER!)')
    parser.add_argument('--keep-feedlots', action='store_true', help='Keep feedlots and API keys')
    parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation')
    args = parser.parse_args()

    keep_users = not args.all
    keep_feedlots = args.keep_feedlots

    print("\n" + "=" * 60)
    print("SAAS MongoDB Reset")
    print("=" * 60 + "\n")

    print("This will clean MongoDB (herdlinx_saas):")
    print("  - Livestock")
    print("  - Batches")

    if not keep_feedlots:
        print("  - Feedlots")
        print("  - API Keys")

    if not keep_users:
        print("  - Users (WARNING!)")

    print()

    if keep_users:
        print_success("Users will be preserved")
    else:
        print_error("Users will be DELETED!")

    if keep_feedlots:
        print_warning("Feedlots and API keys will be preserved")

    print()

    if not args.yes:
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return

    try:
        from pymongo import MongoClient

        client = MongoClient('mongodb://localhost:27017/')
        db = client.herdlinx_saas

        print()

        # Remove livestock
        print("Removing livestock...")
        livestock_result = db.livestock.delete_many({})
        print(f"Deleted {livestock_result.deleted_count} livestock records")

        # Remove batches
        print("Removing batches...")
        batches_result = db.batches.delete_many({})
        print(f"Deleted {batches_result.deleted_count} batches")

        if not keep_feedlots:
            # Remove API keys
            print("Removing API keys...")
            api_keys_result = db.api_keys.delete_many({})
            print(f"Deleted {api_keys_result.deleted_count} API keys")

            # Remove feedlots
            print("Removing feedlots...")
            feedlots_result = db.feedlots.delete_many({})
            print(f"Deleted {feedlots_result.deleted_count} feedlots")

        if not keep_users:
            # Remove users
            print("Removing users...")
            users_result = db.users.delete_many({})
            print(f"Deleted {users_result.deleted_count} users")

        # Show final state
        print("\n=== Final Database State ===")
        print(f"Feedlots: {db.feedlots.count_documents({})}")
        print(f"Livestock: {db.livestock.count_documents({})}")
        print(f"Batches: {db.batches.count_documents({})}")
        print(f"API Keys: {db.api_keys.count_documents({})}")
        print(f"Users: {db.users.count_documents({})}")

        print()
        print_success("SAAS MongoDB cleaned")
        print()

        if not keep_feedlots:
            print("Next steps:")
            print("  1. Create feedlot in SAAS dashboard")
            print("  2. Generate API key for feedlot")
            print("  3. Update office/config.env with API key")
            print()

    except ImportError:
        print_error("pymongo not installed")
        print("Install with: pip install pymongo")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to clean MongoDB: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
