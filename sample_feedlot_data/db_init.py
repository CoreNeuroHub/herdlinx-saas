#!/usr/bin/env python3
"""
Database initialization script for HerdLinx Office App.
Creates all tables, indexes, views, default users, and settings.
"""

import sqlite3
import hashlib
import sys
import os


def hash_password(password, salt=None):
    """Hash password with SHA-256 and salt."""
    if salt is None:
        salt = os.urandom(16).hex()
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def init_database(db_path="herdlinx.db"):
    """Initialize the database with all tables, indexes, views, and default data."""
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    print("Creating tables...")
    
    # 1. Users table
    cursor.execute("""
        CREATE TABLE users(
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name          TEXT NOT NULL,
            role          TEXT NOT NULL CHECK(role IN ('Owner', 'Admin', 'User')),
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login    TEXT
        )
    """)
    
    # 2. Settings table
    cursor.execute("""
        CREATE TABLE settings(
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # 3. Batches table
    cursor.execute("""
        CREATE TABLE batches(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT,
            funder       TEXT,
            lot          TEXT,
            pen          TEXT,
            lot_group    TEXT,
            pen_location TEXT,
            sex          TEXT,
            tag_color    TEXT,
            visual_id    TEXT,
            notes        TEXT,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            active       INTEGER DEFAULT 1
        )
    """)
    
    # 4. Livestock table (created without FK constraint due to circular dependency)
    cursor.execute("""
        CREATE TABLE livestock(
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            induction_event_id   INTEGER,
            current_lf_id        TEXT,
            current_epc          TEXT,
            metadata             TEXT,
            created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at           TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. Induction events table
    cursor.execute("""
        CREATE TABLE induction_events(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            livestock_id INTEGER UNIQUE,
            batch_id     INTEGER NOT NULL,
            timestamp    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(livestock_id) REFERENCES livestock(id),
            FOREIGN KEY(batch_id) REFERENCES batches(id)
        )
    """)
    
    # Add foreign key constraint to livestock after induction_events exists
    # Note: SQLite doesn't support ALTER TABLE ADD CONSTRAINT, so we'll handle
    # the relationship in application logic. The constraint is logical, not enforced.
    
    # 6. Pairing events table
    cursor.execute("""
        CREATE TABLE pairing_events(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            livestock_id INTEGER NOT NULL,
            lf_id        TEXT NOT NULL,
            epc          TEXT NOT NULL,
            weight_kg    REAL,
            timestamp    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(livestock_id) REFERENCES livestock(id)
        )
    """)
    
    # 7. Check-in events table
    cursor.execute("""
        CREATE TABLE checkin_events(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            livestock_id INTEGER NOT NULL,
            lf_id        TEXT,
            epc          TEXT,
            weight_kg    REAL NOT NULL,
            timestamp    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(livestock_id) REFERENCES livestock(id)
        )
    """)
    
    # 8. Repair events table
    cursor.execute("""
        CREATE TABLE repair_events(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            livestock_id INTEGER NOT NULL,
            old_lf_id    TEXT,
            new_lf_id    TEXT,
            old_epc      TEXT,
            new_epc      TEXT,
            reason       TEXT,
            timestamp    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(livestock_id) REFERENCES livestock(id)
        )
    """)
    
    print("Creating indexes...")
    
    # Create indexes
    indexes = [
        "CREATE INDEX idx_induction_livestock_id ON induction_events(livestock_id)",
        "CREATE INDEX idx_induction_batch_id ON induction_events(batch_id)",
        "CREATE INDEX idx_pairing_livestock_id ON pairing_events(livestock_id)",
        "CREATE INDEX idx_pairing_timestamp ON pairing_events(timestamp)",
        "CREATE INDEX idx_checkin_livestock_id ON checkin_events(livestock_id)",
        "CREATE INDEX idx_checkin_timestamp ON checkin_events(timestamp)",
        "CREATE INDEX idx_repair_livestock_id ON repair_events(livestock_id)",
        "CREATE INDEX idx_livestock_lf ON livestock(current_lf_id)",
        "CREATE INDEX idx_livestock_epc ON livestock(current_epc)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    print("Creating view...")
    
    # Create lora_package view
    cursor.execute("""
        CREATE VIEW lora_package AS
            SELECT
                l.id as livestock_id,
                l.current_epc as epc,
                l.current_lf_id as lf_id,
                b.id as batch_id,
                b.name as batch_name,
                b.funder,
                b.lot,
                b.pen,
                l.metadata as visual_id,
                l.created_at as paired_at,
                (SELECT weight_kg FROM checkin_events
                 WHERE livestock_id=l.id
                 ORDER BY timestamp DESC LIMIT 1) as latest_weight
            FROM livestock l
            JOIN induction_events ie ON l.induction_event_id = ie.id
            JOIN batches b ON ie.batch_id = b.id
            WHERE l.current_epc IS NOT NULL
            ORDER BY l.created_at DESC
    """)
    
    print("Inserting default users...")
    
    # Insert default users
    default_users = [
        ("owner", "owner123", "System Owner", "Owner"),
        ("admin", "admin123", "System Admin", "Admin"),
        ("user", "user123", "Regular User", "User")
    ]
    
    for username, password, name, role in default_users:
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, name, role)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, name, role))
    
    print("Inserting default settings...")
    
    # Insert default settings
    default_settings = [
        ("uhf_power", "2200"),
        ("ui_theme", "light"),
        ("pairing_window_s", "3.0"),
        ("lora_tx_rate", "5.0"),
        ("lora_serial_port", "/dev/ttyUSB0"),
        ("lora_baud_rate", "9600")
    ]
    
    for key, value in default_settings:
        cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))
    
    conn.commit()
    conn.close()
    
    print(f"\nDatabase initialized successfully: {db_path}")
    print("\nDefault users created:")
    print("  - owner/owner123 (Owner)")
    print("  - admin/admin123 (Admin)")
    print("  - user/user123 (User)")


def verify_database(db_path="herdlinx.db"):
    """Verify that all required tables exist."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    required_tables = [
        "users", "settings", "batches", "livestock",
        "induction_events", "pairing_events", "checkin_events", "repair_events"
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    missing_tables = set(required_tables) - existing_tables
    
    if missing_tables:
        print(f"Missing tables: {', '.join(missing_tables)}")
        conn.close()
        return False
    
    print("All required tables exist.")
    conn.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_database()
    else:
        init_database()

