#!/usr/bin/env python3
"""
Create test users in MongoDB for local testing

This script creates:
1. super_owner - Can see all feedlots
2. business_owner - Can see only assigned feedlots
3. Sample feedlots
"""

from pymongo import MongoClient
import bcrypt
from datetime import datetime
from bson import ObjectId

# Configuration
MONGODB_URI = 'mongodb://localhost:27017/'
MONGODB_DB = 'herdlinx_saas'

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_test_data():
    """Create test users and feedlots"""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✓ Connected to MongoDB")

        db = client[MONGODB_DB]

        # Create feedlots first
        feedlots_collection = db['feedlots']

        # Check if feedlots exist
        feedlot1 = feedlots_collection.find_one({'feedlot_code': 'FEEDLOT001'})
        if not feedlot1:
            feedlot1_result = feedlots_collection.insert_one({
                'name': 'Southwest Feedlot #1',
                'location': 'Texas',
                'feedlot_code': 'FEEDLOT001',
                'contact_info': {'phone': '555-0001', 'email': 'feedlot1@example.com'},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            feedlot1_id = feedlot1_result.inserted_id
            print(f"✓ Created feedlot: FEEDLOT001 (ID: {feedlot1_id})")
        else:
            feedlot1_id = feedlot1['_id']
            print(f"✓ Feedlot FEEDLOT001 already exists (ID: {feedlot1_id})")

        feedlot2 = feedlots_collection.find_one({'feedlot_code': 'FEEDLOT002'})
        if not feedlot2:
            feedlot2_result = feedlots_collection.insert_one({
                'name': 'Southwest Feedlot #2',
                'location': 'Oklahoma',
                'feedlot_code': 'FEEDLOT002',
                'contact_info': {'phone': '555-0002', 'email': 'feedlot2@example.com'},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            feedlot2_id = feedlot2_result.inserted_id
            print(f"✓ Created feedlot: FEEDLOT002 (ID: {feedlot2_id})")
        else:
            feedlot2_id = feedlot2['_id']
            print(f"✓ Feedlot FEEDLOT002 already exists (ID: {feedlot2_id})")

        # Create users
        users_collection = db['users']

        # Super Owner
        super_owner = users_collection.find_one({'username': 'admin'})
        if not super_owner:
            super_owner_result = users_collection.insert_one({
                'username': 'admin',
                'email': 'admin@herdlinx.com',
                'password_hash': hash_password('admin123'),
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'super_owner',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            print(f"✓ Created super_owner: admin / admin123")
        else:
            print(f"✓ Super owner 'admin' already exists")

        # Business Owner for Feedlot 1
        business_owner1 = users_collection.find_one({'username': 'feedlot1_owner'})
        if not business_owner1:
            business_owner1_result = users_collection.insert_one({
                'username': 'feedlot1_owner',
                'email': 'owner@feedlot1.com',
                'password_hash': hash_password('feedlot123'),
                'first_name': 'John',
                'last_name': 'Owner',
                'user_type': 'business_owner',
                'feedlot_ids': [feedlot1_id],
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            print(f"✓ Created business_owner: feedlot1_owner / feedlot123 (for FEEDLOT001)")
        else:
            print(f"✓ Business owner 'feedlot1_owner' already exists")

        # Business Owner for Feedlot 2
        business_owner2 = users_collection.find_one({'username': 'feedlot2_owner'})
        if not business_owner2:
            business_owner2_result = users_collection.insert_one({
                'username': 'feedlot2_owner',
                'email': 'owner@feedlot2.com',
                'password_hash': hash_password('feedlot456'),
                'first_name': 'Jane',
                'last_name': 'Manager',
                'user_type': 'business_owner',
                'feedlot_ids': [feedlot2_id],
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            print(f"✓ Created business_owner: feedlot2_owner / feedlot456 (for FEEDLOT002)")
        else:
            print(f"✓ Business owner 'feedlot2_owner' already exists")

        print("\n" + "="*60)
        print("TEST CREDENTIALS CREATED")
        print("="*60)
        print("\n1. Super Owner (Can see ALL feedlots):")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n2. Business Owner #1 (FEEDLOT001 only):")
        print("   Username: feedlot1_owner")
        print("   Password: feedlot123")
        print("\n3. Business Owner #2 (FEEDLOT002 only):")
        print("   Username: feedlot2_owner")
        print("   Password: feedlot456")
        print("\n" + "="*60)
        print("\nLogin at: http://127.0.0.1:5000/auth/login")
        print("="*60)

        client.close()

    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure MongoDB is running locally:")
        print("  mongod --dbpath ./data")
        return False

    return True

if __name__ == '__main__':
    import sys
    success = create_test_data()
    sys.exit(0 if success else 1)
