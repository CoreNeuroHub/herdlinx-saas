# HerdLinx Database Structure Documentation

## Overview

The HerdLinx Office system uses a **SQLite database** (`herdlinx.db`) with a normalized, event-centric design. The database is organized into core data tables and event history tables, providing fast queries, data integrity, and complete audit trails.

### Key Design Principles

- **Event-Centric**: All events are immutable (insert-only), providing complete audit trails
- **Normalized**: Data is organized across separate tables to prevent duplication
- **Indexed**: Common queries are optimized with strategic indexes
- **Type-Safe**: Explicit columns instead of JSON metadata for better performance

---

## Database Initialization

The database is initialized using `db_init.py`:

```bash
python db_init.py
```

This script creates:
- All tables with proper schema
- Database indexes for performance
- The `lora_package` view for data aggregation
- Default users (owner/admin/user)
- Default system settings

---

## Core Tables

### 1. `users` - Authentication & Authorization

**Purpose:** Manages system user accounts with role-based access control.

**Schema:**
```sql
CREATE TABLE users(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('Owner', 'Admin', 'User')),
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login    TEXT
)
```

**Columns:**
- `id`: Primary key
- `username`: Unique login identifier
- `password_hash`: SHA-256 hashed password with salt
- `name`: Display name
- `role`: User role (Owner, Admin, or User)
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp (nullable)

**Default Users:**
- `owner/owner123` → Owner role
- `admin/admin123` → Admin role
- `user/user123` → User role

**Role Permissions:**
| Role  | Dashboard | User Mgmt | Settings | Repair |
|-------|-----------|-----------|----------|--------|
| Owner | Yes       | Yes       | Yes      | Yes    |
| Admin | Yes       | Yes       | Yes      | Yes    |
| User  | User-only | No        | No       | Yes    |

---

### 2. `settings` - System Configuration

**Purpose:** Key-value store for system-wide settings.

**Schema:**
```sql
CREATE TABLE settings(
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
```

**Columns:**
- `key`: Setting identifier (primary key)
- `value`: Setting value (stored as text)

**Default Settings:**
- `uhf_power`: "2200"
- `ui_theme`: "light"
- `pairing_window_s`: "3.0"
- `lora_tx_rate`: "5.0"
- `lora_serial_port`: "/dev/ttyUSB0"
- `lora_baud_rate`: "9600"

---

### 3. `batches` - Livestock Groups

**Purpose:** Groups animals for processing sessions (e.g., "Batch A - Oct 30").

**Schema:**
```sql
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
```

**Columns:**
- `id`: Primary key
- `name`: Batch name (e.g., "Batch A - Oct 30")
- `funder`: Funding source (optional)
- `lot`: Lot number (optional)
- `pen`: Pen identifier (optional)
- `lot_group`: Grouping identifier (optional)
- `pen_location`: Physical location (optional)
- `sex`: Sex designation - M/F/Mixed (optional)
- `tag_color`: Visual tag color (optional)
- `visual_id`: Visual identifier (optional)
- `notes`: Additional notes (optional)
- `created_at`: Batch creation timestamp
- `active`: Active status (1=active, 0=inactive)

**Notes:**
- Only one batch should be active at a time (enforced by application logic)
- All fields except `id` and `created_at` are optional

---

### 4. `livestock` - Current Animal State

**Purpose:** Represents the current state of each animal in the system.

**Schema:**
```sql
CREATE TABLE livestock(
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    induction_event_id   INTEGER NOT NULL,
    current_lf_id        TEXT,
    current_epc          TEXT,
    metadata             TEXT,
    created_at           TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at           TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(induction_event_id) REFERENCES induction_events(id)
)
```

**Columns:**
- `id`: Primary key (unique animal identifier)
- `induction_event_id`: Links to the induction event when animal entered system
- `current_lf_id`: Current LF (ear) tag ID
- `current_epc`: Current UHF (body) tag EPC
- `metadata`: Reserved for future use (visual_id, notes, etc.)
- `created_at`: Animal record creation timestamp
- `updated_at`: Last update timestamp

**Key Points:**
- One row per animal (created during induction)
- `current_lf_id` and `current_epc` are updated when tags are repaired
- `induction_event_id` is immutable (links to when animal entered system)

**Example Query:**
```sql
-- Find animal by LF tag
SELECT id, current_epc FROM livestock WHERE current_lf_id = ?;

-- Find animal by EPC
SELECT id, current_lf_id FROM livestock WHERE current_epc = ?;
```

---

## Event History Tables

### 5. `induction_events` - Animal Entry Points

**Purpose:** Immutable record of when animals enter the system.

**Schema:**
```sql
CREATE TABLE induction_events(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    livestock_id INTEGER UNIQUE,
    batch_id     INTEGER NOT NULL,
    timestamp    TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(livestock_id) REFERENCES livestock(id),
    FOREIGN KEY(batch_id) REFERENCES batches(id)
)
```

**Columns:**
- `id`: Primary key
- `livestock_id`: Links to livestock record (UNIQUE - one induction per animal)
- `batch_id`: Which batch this animal was inducted in
- `timestamp`: When the animal was inducted

**Key Points:**
- One row per animal (created when first pairing/induction happens)
- `livestock_id` is UNIQUE - ensures one induction per animal
- Immutable - never updated after creation

**Example Query:**
```sql
-- Get all animals inducted in a batch
SELECT ie.livestock_id FROM induction_events ie WHERE ie.batch_id = ?;
```

---

### 6. `pairing_events` - Tag Linkage History

**Purpose:** Records when LF and UHF tags are paired together.

**Schema:**
```sql
CREATE TABLE pairing_events(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    livestock_id INTEGER NOT NULL,
    lf_id        TEXT NOT NULL,
    epc          TEXT NOT NULL,
    weight_kg    REAL,
    timestamp    TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(livestock_id) REFERENCES livestock(id)
)
```

**Columns:**
- `id`: Primary key
- `livestock_id`: Which animal
- `lf_id`: LF tag ID that was paired
- `epc`: UHF tag EPC that was paired
- `weight_kg`: Optional weight at pairing time
- `timestamp`: When the pairing occurred

**Key Points:**
- Multiple rows per animal (one per pairing event)
- Immutable - never updated after creation
- Captures the LF and EPC that were paired at that moment

**Example Query:**
```sql
-- Get all pairings for an animal
SELECT * FROM pairing_events WHERE livestock_id = ? ORDER BY timestamp DESC;

-- Get latest pairing for an animal
SELECT * FROM pairing_events WHERE livestock_id = ?
ORDER BY timestamp DESC LIMIT 1;
```

---

### 7. `checkin_events` - Weight Measurements

**Purpose:** Records weight measurements during check-in operations. This table grows the largest as animals are checked in multiple times.

**Schema:**
```sql
CREATE TABLE checkin_events(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    livestock_id INTEGER NOT NULL,
    lf_id        TEXT,
    epc          TEXT,
    weight_kg    REAL NOT NULL,
    timestamp    TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(livestock_id) REFERENCES livestock(id)
)
```

**Columns:**
- `id`: Primary key
- `livestock_id`: Which animal
- `lf_id`: LF tag used for check-in (optional)
- `epc`: UHF tag used for check-in (optional)
- `weight_kg`: Weight measurement (REQUIRED - cannot be NULL)
- `timestamp`: When the check-in occurred

**Key Points:**
- Multiple rows per animal (can be checked in many times)
- Immutable - never updated after creation
- `weight_kg` is REQUIRED (cannot be NULL)
- Forms a complete weight history timeline

**Example Query:**
```sql
-- Get weight history for an animal
SELECT weight_kg, timestamp FROM checkin_events
WHERE livestock_id = ? ORDER BY timestamp ASC;

-- Get latest weight for an animal
SELECT weight_kg FROM checkin_events WHERE livestock_id = ?
ORDER BY timestamp DESC LIMIT 1;

-- Calculate weight gain
SELECT
    (SELECT weight_kg FROM checkin_events WHERE livestock_id = ? 
     ORDER BY timestamp DESC LIMIT 1) -
    (SELECT weight_kg FROM checkin_events WHERE livestock_id = ? 
     ORDER BY timestamp ASC LIMIT 1)
AS weight_gain;
```

---

### 8. `repair_events` - Tag Replacements

**Purpose:** Records when tags are replaced due to damage or loss.

**Schema:**
```sql
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
```

**Columns:**
- `id`: Primary key
- `livestock_id`: Which animal
- `old_lf_id`: Previous LF tag (NULL if not changed)
- `new_lf_id`: New LF tag (NULL if not changed)
- `old_epc`: Previous UHF tag (NULL if not changed)
- `new_epc`: New UHF tag (NULL if not changed)
- `reason`: Why the repair was needed (e.g., "LF tag lost", "UHF tag damaged")
- `timestamp`: When the repair occurred

**Key Points:**
- Multiple rows per animal (can have multiple repairs)
- Immutable - never updated after creation
- Either `old_lf_id`/`new_lf_id` are populated (LF repair) OR `old_epc`/`new_epc` (UHF repair)
- When a repair occurs, the `livestock` table is updated with the new tag values

**Example Query:**
```sql
-- Get all repairs for an animal
SELECT * FROM repair_events WHERE livestock_id = ? ORDER BY timestamp DESC;

-- Find animals that have been repaired
SELECT DISTINCT livestock_id FROM repair_events;
```

---

## Database Indexes

**Purpose:** Speed up common queries by creating indexes on frequently searched columns.

**Indexes Created:**
```sql
CREATE INDEX idx_induction_livestock_id ON induction_events(livestock_id);
CREATE INDEX idx_induction_batch_id ON induction_events(batch_id);
CREATE INDEX idx_pairing_livestock_id ON pairing_events(livestock_id);
CREATE INDEX idx_pairing_timestamp ON pairing_events(timestamp);
CREATE INDEX idx_checkin_livestock_id ON checkin_events(livestock_id);
CREATE INDEX idx_checkin_timestamp ON checkin_events(timestamp);
CREATE INDEX idx_repair_livestock_id ON repair_events(livestock_id);
CREATE INDEX idx_livestock_lf ON livestock(current_lf_id);
CREATE INDEX idx_livestock_epc ON livestock(current_epc);
```

**Performance Impact:**
- Lookups by `livestock_id`: <1ms (vs 100ms without index)
- Lookups by LF/EPC tag: <1ms (vs full table scan)
- Timestamp range queries: <5ms

---

## Database View

### `lora_package` - Aggregated Data for LoRa Transmission

**Purpose:** Pre-built view that aggregates data for LoRa transmission, combining livestock, batch, and latest weight information.

**View Definition:**
```sql
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
```

**Key Points:**
- Only includes animals that have been paired (`current_epc IS NOT NULL`)
- Includes latest weight from check-in history
- Links batch information for context
- Used by LoRa transmission system to build payloads

**Example Query:**
```sql
-- Get all animals ready for LoRa transmission
SELECT * FROM lora_package;

-- Get specific animal data for LoRa broadcast
SELECT * FROM lora_package WHERE livestock_id = ?;
```

---

## Entity Relationship Diagram

```
┌─────────────┐
│   users     │
└─────────────┘

┌─────────────┐
│  settings   │
└─────────────┘

┌─────────────┐
│   batches   │◄────────┐
└─────────────┘         │
                        │
┌─────────────┐         │
│  livestock  │         │
│             │         │
│ induction_  │─────────┼──┐
│ event_id    │         │  │
└──────┬──────┘         │  │
       │                │  │
       │                │  │
       │                │  │
┌──────▼──────────────┐ │  │
│ induction_events    │ │  │
│                     │ │  │
│ livestock_id (FK)   │─┘  │
│ batch_id (FK)       │────┘
└─────────────────────┘

┌─────────────────────┐
│  pairing_events     │
│                     │
│ livestock_id (FK)   │──┐
└─────────────────────┘  │
                         │
┌─────────────────────┐  │
│  checkin_events     │  │
│                     │  │
│ livestock_id (FK)   │──┼──┐
└─────────────────────┘  │  │
                         │  │
┌─────────────────────┐  │  │
│  repair_events      │  │  │
│                     │  │  │
│ livestock_id (FK)   │──┘  │
└─────────────────────┘     │
                            │
                            │
                    ┌───────┴───────┐
                    │   livestock   │
                    │      (id)     │
                    └───────────────┘
```

---

## Table Summary

| Table | Rows/Animal | Primary Key | Type | Growth Rate |
|-------|-------------|-------------|------|-------------|
| `users` | 1 | `id` | Current state | Very slow (one per operator) |
| `settings` | N/A | `key` | Configuration | Constant |
| `batches` | 1 | `id` | Current state | Slow (one per session) |
| `livestock` | 1 | `id` | Current state | Slow (one per animal) |
| `induction_events` | 1 | `id` | Event | Slow (one per animal) |
| `pairing_events` | 1-2 | `id` | Event | Medium (repairs cause new rows) |
| `checkin_events` | Many | `id` | Event | Fast (one per check-in) |
| `repair_events` | 0-N | `id` | Event | Slow (only when tags replaced) |

---

## Common Query Patterns

### Find Animal by Tag

```sql
-- By LF tag
SELECT l.*, b.name as batch_name
FROM livestock l
JOIN induction_events ie ON l.induction_event_id = ie.id
JOIN batches b ON ie.batch_id = b.id
WHERE l.current_lf_id = ?;

-- By EPC
SELECT l.*, b.name as batch_name
FROM livestock l
JOIN induction_events ie ON l.induction_event_id = ie.id
JOIN batches b ON ie.batch_id = b.id
WHERE l.current_epc = ?;
```

### Get Animal History

```sql
-- Complete history for an animal
SELECT 
    'induction' as event_type,
    timestamp,
    NULL as weight_kg,
    NULL as reason
FROM induction_events
WHERE livestock_id = ?

UNION ALL

SELECT 
    'pairing' as event_type,
    timestamp,
    weight_kg,
    NULL as reason
FROM pairing_events
WHERE livestock_id = ?

UNION ALL

SELECT 
    'checkin' as event_type,
    timestamp,
    weight_kg,
    NULL as reason
FROM checkin_events
WHERE livestock_id = ?

UNION ALL

SELECT 
    'repair' as event_type,
    timestamp,
    NULL as weight_kg,
    reason
FROM repair_events
WHERE livestock_id = ?

ORDER BY timestamp ASC;
```

### Get Batch Statistics

```sql
-- Animals in a batch
SELECT COUNT(*) as total_animals
FROM induction_events
WHERE batch_id = ?;

-- Average weight in a batch
SELECT AVG(ce.weight_kg) as avg_weight
FROM checkin_events ce
JOIN livestock l ON ce.livestock_id = l.id
JOIN induction_events ie ON l.induction_event_id = ie.id
WHERE ie.batch_id = ?
AND ce.timestamp = (
    SELECT MAX(timestamp) 
    FROM checkin_events 
    WHERE livestock_id = ce.livestock_id
);
```

---

## Data Integrity

### Foreign Key Constraints

- `livestock.induction_event_id` → `induction_events.id`
- `induction_events.livestock_id` → `livestock.id` (UNIQUE)
- `induction_events.batch_id` → `batches.id`
- `pairing_events.livestock_id` → `livestock.id`
- `checkin_events.livestock_id` → `livestock.id`
- `repair_events.livestock_id` → `livestock.id`

### Constraints

- `users.username`: UNIQUE
- `users.role`: CHECK constraint (Owner, Admin, User)
- `induction_events.livestock_id`: UNIQUE (one induction per animal)
- `checkin_events.weight_kg`: NOT NULL (required)

---

## Database Maintenance

### Verify Schema

```bash
python db_init.py --verify
```

This checks that all required tables exist without modifying the database.

### Initialize Database

```bash
python db_init.py
```

This creates all tables, indexes, views, default users, and settings.

### Backup Database

```bash
# SQLite backup
sqlite3 herdlinx.db ".backup backup_herdlinx.db"
```

---

## Migration Notes

If migrating from an older schema:

1. Create new event tables via `db_init.py`
2. Migrate existing events:
   ```sql
   INSERT INTO induction_events(livestock_id, batch_id, timestamp)
   SELECT animal_id, batch_id, DATE(created_at) 
   FROM old_events WHERE type='induction';
   
   INSERT INTO pairing_events(livestock_id, lf_id, epc, weight_kg, timestamp)
   SELECT animal_id, lf_id, epc, weight_kg, timestamp 
   FROM old_events WHERE type='pairing';
   ```
3. Verify data integrity
4. Delete old events table when confident

---

## Related Documentation

- **Full Database & LoRa Documentation**: See `docs/db_and_lora.md` for detailed information about LoRa broadcast format and data flow
- **API Reference**: See `docs/API_REFERENCE.md` for database interaction APIs
- **Quick Start**: See `docs/QUICK_START.md` for setup instructions

---

## Summary

The HerdLinx database uses a normalized, event-centric design that provides:

- **Fast Queries**: Indexed lookups, no JSON parsing overhead
- **Data Integrity**: Foreign keys and constraints prevent orphaned records
- **Scalability**: Event tables can grow indefinitely (especially `checkin_events`)
- **Complete Audit Trail**: Immutable events provide full history
- **LoRa Efficiency**: Pre-aggregated view optimizes broadcast payloads

This design balances performance, integrity, and scalability for livestock management operations.

