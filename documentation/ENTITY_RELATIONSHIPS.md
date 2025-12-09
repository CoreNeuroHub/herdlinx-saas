# Entity Relationships Documentation

## Overview

This document describes the relationships between the core entities in the HerdLinx SaaS application: **Feedlots**, **Pens**, **Batches**, and **Cattle**. Understanding these relationships is crucial for data modeling, querying, and maintaining data integrity.

---

## Database Architecture

The application uses a **multi-tenant MongoDB architecture** with the following structure:

- **Main Database**: Contains feedlot records and top-level user accounts
- **Feedlot-Specific Databases**: Each feedlot has its own database (`feedlot_{feedlot_code}`) containing pens, batches, and cattle records

This design provides:
- **Data Isolation**: Each feedlot's data is completely separated
- **Scalability**: Feedlot databases can be scaled independently
- **Security**: Multi-tenant data isolation at the database level

---

## Entity Hierarchy

```
Feedlot (Top Level)
├── Pens (Physical Locations)
│   └── Cattle (Assigned to Pens - Optional)
├── Batches (Induction Groups)
│   └── Cattle (Inducted in Batches - Optional)
└── Cattle (Individual Records)
    ├── Belongs to a Feedlot (Required)
    ├── Can belong to a Batch (Optional)
    └── Can be assigned to a Pen (Optional)
```

---

## Core Entities

### 1. Feedlot

**Database**: Main database (`db.feedlots`)

**Purpose**: Represents a feedlot instance (tenant) in the multi-tenant SaaS system.

**Key Fields**:
- `_id`: Unique feedlot identifier (ObjectId)
- `feedlot_code`: Unique code used to identify the feedlot-specific database (case-insensitive, unique)
- `name`: Feedlot name
- `location`: Physical location
- `owner_id`: Reference to the business owner user
- `premises_id`: Premises Identification (PID) number
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Database Naming**: Each feedlot has its own database named `feedlot_{feedlot_code}` (lowercase, trimmed).

**Relationships**:
- **One-to-Many** with Pens
- **One-to-Many** with Batches
- **One-to-Many** with Cattle

---

### 2. Pen

**Database**: Feedlot-specific database (`feedlot_db.pens`)

**Purpose**: Represents a physical pen location within a feedlot where cattle can be housed.

**Key Fields**:
- `_id`: Unique pen identifier (ObjectId)
- `feedlot_id`: Reference to the parent feedlot (ObjectId, required)
- `pen_number`: Unique pen identifier within the feedlot (string, unique per feedlot)
- `capacity`: Maximum number of cattle the pen can hold (integer)
- `description`: Optional description of the pen
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_id`: For querying all pens in a feedlot
- `(feedlot_id, pen_number)`: Unique constraint ensuring pen numbers are unique per feedlot

**Relationships**:
- **Many-to-One** with Feedlot (required)
- **One-to-Many** with Cattle (optional - cattle can be moved between pens or exist without a pen)

**Capacity Management**:
- Pens track their capacity and current cattle count
- The system can check if a pen has available capacity before assigning cattle
- Cattle can be moved between pens, updating the capacity counts accordingly

---

### 3. Batch

**Database**: Feedlot-specific database (`feedlot_db.batches`)

**Purpose**: Represents a group of cattle that were inducted together or processed as a unit.

**Key Fields**:
- `_id`: Unique batch identifier (ObjectId)
- `feedlot_id`: Reference to the parent feedlot (ObjectId, required)
- `batch_number`: Unique batch identifier within the feedlot (string, unique per feedlot)
- `event_date`: Date when the batch event occurred (datetime)
- `funder`: Information about who funded the batch (string)
- `event_type`: Type of event (string: 'induction', 'pairing', 'checkin', 'repair')
- `notes`: Optional notes about the batch
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_id`: For querying all batches in a feedlot
- `(feedlot_id, batch_number)`: Unique constraint ensuring batch numbers are unique per feedlot

**Relationships**:
- **Many-to-One** with Feedlot (required)
- **One-to-Many** with Cattle (optional - cattle can exist without a batch)

**Event Types**:
- `induction`: Initial cattle induction into the feedlot
- `pairing`: Tag pairing event
- `checkin`: Check-in event
- `repair`: Tag repair event

---

### 4. Cattle

**Database**: Feedlot-specific database (`feedlot_db.cattle`)

**Purpose**: Represents an individual cattle record with complete tracking information.

**Key Fields**:
- `_id`: Unique cattle record identifier (ObjectId)
- `feedlot_id`: Reference to the parent feedlot (ObjectId, **required**)
- `batch_id`: Reference to the batch this cattle belongs to (ObjectId, **optional**)
- `pen_id`: Reference to the pen where this cattle is currently located (ObjectId, **optional**)
- `cattle_id`: Unique cattle identifier within the feedlot (string, unique per feedlot)
- `sex`: Sex of the cattle (string)
- `weight`: Current weight (number)
- `health_status`: Health status (string)
- `lf_tag`: Low Frequency tag identifier (string, optional)
- `uhf_tag`: Ultra High Frequency tag identifier (string, optional)
- `color`: Color description (string, optional)
- `breed`: Breed information (string, optional)
- `visual_id`: Visual identification (string, optional)
- `lot`: Lot identifier (string, optional)
- `lot_group`: Lot group identifier (string, optional)
- `brand_drawings`: Brand drawings information (string, optional)
- `brand_locations`: Brand locations (string, optional)
- `other_marks`: Other identifying marks (string, optional)
- `notes`: General notes (string, optional)
- `status`: Current status (string: 'active' or 'removed')
- `induction_date`: Date when cattle was inducted (datetime)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Historical Data**:
- `weight_history`: Array of weight records with timestamps
- `notes_history`: Array of notes with timestamps
- `tag_pair_history`: Array of previous LF/UHF tag pairs
- `audit_log`: Complete audit trail of all cattle activities

**Indexes**:
- `feedlot_id`: For querying all cattle in a feedlot
- `batch_id`: For querying all cattle in a batch
- `pen_id`: For querying all cattle in a pen
- `(feedlot_id, cattle_id)`: Unique constraint ensuring cattle IDs are unique per feedlot

**Relationships**:
- **Many-to-One** with Feedlot (required)
- **Many-to-One** with Batch (optional - cattle can exist without a batch)
- **Many-to-One** with Pen (optional - cattle can be moved between pens or have no pen assignment)

---

## Relationship Details

### Feedlot → Pens (One-to-Many)

**Relationship Type**: One-to-Many (Required)

**Description**: Each feedlot can have multiple pens, but each pen belongs to exactly one feedlot.

**Implementation**:
- Pens are stored in the feedlot-specific database
- Each pen has a `feedlot_id` field referencing the feedlot
- Pen numbers must be unique within a feedlot

**Query Example**:
```python
# Find all pens for a feedlot
pens = Pen.find_by_feedlot(feedlot_id)
```

**Constraints**:
- Pen numbers are unique per feedlot (enforced by database index)
- Pens cannot exist without a feedlot

---

### Feedlot → Batches (One-to-Many)

**Relationship Type**: One-to-Many (Required)

**Description**: Each feedlot can have multiple batches, but each batch belongs to exactly one feedlot.

**Implementation**:
- Batches are stored in the feedlot-specific database
- Each batch has a `feedlot_id` field referencing the feedlot
- Batch numbers must be unique within a feedlot

**Query Example**:
```python
# Find all batches for a feedlot
batches = Batch.find_by_feedlot(feedlot_code, feedlot_id)
```

**Constraints**:
- Batch numbers are unique per feedlot (enforced by database index)
- Batches cannot exist without a feedlot

---

### Feedlot → Cattle (One-to-Many)

**Relationship Type**: One-to-Many (Required)

**Description**: Each feedlot can have multiple cattle records, but each cattle record belongs to exactly one feedlot.

**Implementation**:
- Cattle are stored in the feedlot-specific database
- Each cattle record has a `feedlot_id` field referencing the feedlot
- Cattle IDs must be unique within a feedlot

**Query Example**:
```python
# Find all cattle for a feedlot
cattle = Cattle.find_by_feedlot(feedlot_code, feedlot_id)
```

**Constraints**:
- Cattle IDs are unique per feedlot (enforced by database index)
- Cattle cannot exist without a feedlot

---

### Batch → Cattle (One-to-Many, Optional)

**Relationship Type**: One-to-Many (Optional)

**Description**: Each batch can contain multiple cattle, but cattle can exist without belonging to any batch.

**Implementation**:
- Each cattle record has an optional `batch_id` field referencing the batch
- The `batch_id` field can be `None` if cattle is not associated with a batch
- Cattle are typically created as part of a batch during induction, but can also be created independently

**Query Example**:
```python
# Find all cattle in a batch
cattle = Cattle.find_by_batch(feedlot_code, batch_id)

# Get count of cattle in a batch
count = Batch.get_cattle_count(feedlot_code, batch_id)
```

**Constraints**:
- Cattle can have a `batch_id` or `None` (optional field)
- Cattle can exist without a batch
- Cattle cannot belong to multiple batches

**Business Logic**:
- When cattle are inducted as part of a batch, they are associated with that batch
- Cattle can be created independently without a batch association
- The batch tracks the event date, funder, and event type for grouped operations
- Cattle can be added to or removed from batches as needed

---

### Pen → Cattle (One-to-Many, Optional)

**Relationship Type**: One-to-Many (Optional)

**Description**: Each pen can contain multiple cattle, but cattle can be moved between pens or exist without a pen assignment.

**Implementation**:
- Each cattle record has an optional `pen_id` field referencing the pen
- The `pen_id` field can be `None` if cattle is not assigned to a pen
- Cattle can be moved between pens using the `move_cattle()` method
- Only active cattle are counted in pen capacity

**Query Example**:
```python
# Find all cattle in a pen
cattle = Cattle.find_by_pen(feedlot_code, pen_id)

# Get current cattle count in a pen
count = Pen.get_current_cattle_count(pen_id)

# Check if pen has available capacity
has_capacity = Pen.is_capacity_available(pen_id, additional_cattle=5)
```

**Constraints**:
- Pen assignment is optional (cattle can have `pen_id = None`)
- Cattle can be moved between pens
- Pen capacity must be respected (current count + additional ≤ capacity)
- Only active cattle (`status = 'active'`) are counted toward pen capacity

**Business Logic**:
- When cattle are moved to a pen, the system checks capacity
- Cattle movements are tracked in the audit log
- Cattle can be removed from pens (set `pen_id` to `None`)
- Historical pen assignments are tracked in the cattle's audit log

---

## Data Flow Examples

### Example 1: Independent Cattle Creation

1. **Create Feedlot**: A feedlot is created with a unique `feedlot_code`
2. **Create Cattle**: Individual cattle records can be created:
   - Each cattle must have a `feedlot_id` (required)
   - Each cattle can optionally have a `batch_id` (optional)
   - Each cattle can optionally have a `pen_id` (optional)
   - Each cattle has a unique `cattle_id` within the feedlot

### Example 2: Batch Induction

1. **Create Feedlot**: A feedlot is created with a unique `feedlot_code`
2. **Create Pens**: Multiple pens are created for the feedlot
3. **Create Batch**: A batch is created for the induction event
4. **Create Cattle**: Individual cattle records are created:
   - Each cattle has a `batch_id` referencing the batch (optional but common)
   - Each cattle can optionally have a `pen_id`
   - Each cattle has a unique `cattle_id` within the feedlot

### Example 3: Moving Cattle Between Pens

1. **Query Current Pen**: Get current pen assignment for cattle
2. **Check Capacity**: Verify new pen has available capacity
3. **Update Cattle**: Update `pen_id` field on cattle record
4. **Audit Log**: Record the movement in cattle's audit log
5. **Capacity Update**: Pen capacity counts are automatically updated

### Example 4: Querying Cattle by Multiple Criteria

```python
# Find all active cattle in a specific pen
cattle_in_pen = Cattle.find_by_pen(feedlot_code, pen_id)

# Find all cattle from a specific batch
cattle_in_batch = Cattle.find_by_batch(feedlot_code, batch_id)

# Find all cattle in a feedlot with filters
cattle = Cattle.find_by_feedlot_with_filters(
    feedlot_code, 
    feedlot_id,
    search='C001',
    health_status='healthy',
    pen_id=pen_id,
    sort_by='weight',
    sort_order='desc'
)
```

---

## Data Integrity Rules

### Required Relationships

1. **Cattle → Feedlot**: Every cattle record must have a `feedlot_id`
2. **Pen → Feedlot**: Every pen must have a `feedlot_id`
3. **Batch → Feedlot**: Every batch must have a `feedlot_id`

### Optional Relationships

1. **Cattle → Batch**: Cattle can exist without a batch assignment (`batch_id` can be `None`)
2. **Cattle → Pen**: Cattle can exist without a pen assignment (`pen_id` can be `None`)

### Uniqueness Constraints

1. **Feedlot Code**: Must be unique across all feedlots (case-insensitive)
2. **Pen Number**: Must be unique within a feedlot
3. **Batch Number**: Must be unique within a feedlot
4. **Cattle ID**: Must be unique within a feedlot

### Referential Integrity

- When a feedlot is deleted, all associated pens, batches, and cattle should be handled (cascade or archive)
- When a batch is deleted, associated cattle records with that `batch_id` should have their `batch_id` set to `None` or be handled appropriately
- When a pen is deleted, cattle with that `pen_id` should have their `pen_id` set to `None` or be reassigned

---

## Query Patterns

### Common Queries

1. **Get all cattle in a feedlot**:
   ```python
   cattle = Cattle.find_by_feedlot(feedlot_code, feedlot_id)
   ```

2. **Get all cattle in a batch** (if batch exists):
   ```python
   cattle = Cattle.find_by_batch(feedlot_code, batch_id)
   ```

3. **Get all cattle in a pen** (if pen exists):
   ```python
   cattle = Cattle.find_by_pen(feedlot_code, pen_id)
   ```

4. **Get all pens for a feedlot**:
   ```python
   pens = Pen.find_by_feedlot(feedlot_id)
   ```

5. **Get all batches for a feedlot**:
   ```python
   batches = Batch.find_by_feedlot(feedlot_code, feedlot_id)
   ```

6. **Get feedlot statistics**:
   ```python
   stats = Feedlot.get_statistics(feedlot_id)
   # Returns: total_pens, total_cattle, total_batches, cattle_by_pen
   ```

### Advanced Queries

1. **Find cattle by multiple criteria**:
   ```python
   cattle = Cattle.find_by_feedlot_with_filters(
       feedlot_code, feedlot_id,
       search='C001',
       health_status='healthy',
       sex='female',
       pen_id=pen_id,
       sort_by='weight',
       sort_order='desc'
   )
   ```

2. **Check pen capacity**:
   ```python
   has_capacity = Pen.is_capacity_available(pen_id, additional_cattle=10)
   current_count = Pen.get_current_cattle_count(pen_id)
   ```

3. **Get batch cattle count**:
   ```python
   count = Batch.get_cattle_count(feedlot_code, batch_id)
   ```

4. **Find cattle without a batch**:
   ```python
   # Query cattle where batch_id is None
   feedlot_db = get_feedlot_db(feedlot_code)
   cattle_without_batch = list(feedlot_db.cattle.find({
       'feedlot_id': ObjectId(feedlot_id),
       'batch_id': None
   }))
   ```

5. **Find cattle without a pen**:
   ```python
   # Query cattle where pen_id is None
   feedlot_db = get_feedlot_db(feedlot_code)
   cattle_without_pen = list(feedlot_db.cattle.find({
       'feedlot_id': ObjectId(feedlot_id),
       'pen_id': None,
       'status': 'active'
   }))
   ```

---

## Summary

### Relationship Matrix

| Entity | Relationship | Target Entity | Type | Required |
|--------|-------------|---------------|------|----------|
| Feedlot | One-to-Many | Pens | Parent-Child | Yes |
| Feedlot | One-to-Many | Batches | Parent-Child | Yes |
| Feedlot | One-to-Many | Cattle | Parent-Child | Yes |
| Batch | One-to-Many | Cattle | Parent-Child | No |
| Pen | One-to-Many | Cattle | Parent-Child | No |

### Key Points

1. **Feedlot is the top-level entity** that contains all other entities
2. **Batch is optional for cattle** - cattle can exist without belonging to a batch
3. **Pen assignment is optional** - cattle can be moved between pens or exist without a pen
4. **Cattle can exist independently** - cattle only requires a feedlot association; batch and pen are both optional
5. **Multi-tenant architecture** - each feedlot has its own database for data isolation
6. **Audit trails** - cattle movements and changes are tracked in audit logs
7. **Capacity management** - pens track capacity and current cattle count
8. **Unique constraints** - pen numbers, batch numbers, and cattle IDs are unique within a feedlot

---

## Best Practices

1. **Always check pen capacity** before assigning cattle to a pen
2. **Batch association is optional** - cattle can be created with or without a batch
3. **Track cattle movements** using the `move_cattle()` method to maintain audit logs
4. **Query using feedlot_code** when accessing feedlot-specific databases
5. **Respect uniqueness constraints** - ensure pen numbers, batch numbers, and cattle IDs are unique within a feedlot
6. **Handle optional relationships** - always check for `None` values when querying by `batch_id` or `pen_id`
7. **Use indexes** - the system has indexes on `feedlot_id`, `batch_id`, and `pen_id` for efficient queries
8. **Support independent cattle** - design queries and UI to handle cattle that exist without batch or pen associations

---

## Related Documentation

- `OFFICE_DATABASE_STRUCTURE.md`: Database structure for the Office application
- `API_DOCUMENTATION.md`: API endpoints and usage
- Model files: `app/models/feedlot.py`, `app/models/pen.py`, `app/models/batch.py`, `app/models/cattle.py`

