# Database Schema Documentation

## Overview

The HerdLinx SaaS application uses a **multi-tenant MongoDB architecture** with the following structure:

- **Main Database**: Contains feedlot records, user accounts, API keys, and manifest templates/manifests
- **Feedlot-Specific Databases**: Each feedlot has its own database (`feedlot_{feedlot_code}`) containing pens, batches, cattle records, and feedlot-specific manifests/templates

This design provides:
- **Data Isolation**: Each feedlot's operational data is completely separated
- **Scalability**: Feedlot databases can be scaled independently
- **Security**: Multi-tenant data isolation at the database level
- **Performance**: Optimized queries within each feedlot's context

---

## Database Architecture

### Main Database

**Database Name**: Configured via `MONGODB_DB` environment variable

**Collections**:
- `users` - User accounts (top-level and feedlot-level)
- `feedlots` - Feedlot instances (tenants)
- `api_keys` - API authentication keys
- `manifests` - Manifest records (shared across feedlots)
- `manifest_templates` - Manifest templates (shared across feedlots)

### Feedlot-Specific Databases

**Database Naming Pattern**: `feedlot_{feedlot_code}` (lowercase, trimmed)

**Collections**:
- `pens` - Physical pen locations within the feedlot
- `batches` - Batch groups for cattle induction/events
- `cattle` - Individual cattle records
- `manifest_templates` - Feedlot-specific manifest templates
- `manifests` - Feedlot-specific manifest records

**Note**: Pens are stored in the main database, not in feedlot-specific databases, but are logically associated with feedlots via `feedlot_id`.

---

## Main Database Collections

### 1. `users` Collection

**Purpose**: Manages user accounts for both top-level and feedlot-level access.

**Schema**:
```javascript
{
  _id: ObjectId,
  username: String,              // Unique username
  email: String,                 // Email address
  password_hash: Binary,          // bcrypt hashed password
  user_type: String,              // 'super_owner', 'super_admin', 'business_owner', 'business_admin', 'user'
  feedlot_id: ObjectId,           // Single feedlot ID (for 'user' type)
  feedlot_ids: [ObjectId],        // Array of feedlot IDs (for 'business_admin' or 'business_owner')
  is_active: Boolean,             // Account active status
  created_at: DateTime,
  dashboard_preferences: Object   // Optional user dashboard widget preferences
}
```

**Field Descriptions**:
- `_id`: Unique user identifier (ObjectId)
- `username`: Unique login identifier (required, unique)
- `email`: User email address (required, unique)
- `password_hash`: bcrypt hashed password (required)
- `user_type`: User role type (required)
  - `super_owner`: Top-level owner with system-wide access
  - `super_admin`: Top-level administrator with system-wide access
  - `business_owner`: Feedlot owner with access to multiple feedlots
  - `business_admin`: Feedlot administrator with access to multiple feedlots
  - `user`: Regular user with access to a single feedlot
- `feedlot_id`: Single feedlot assignment (for `user` type only)
- `feedlot_ids`: Array of feedlot assignments (for `business_admin` or `business_owner` types)
- `is_active`: Whether the account is active (default: `true`)
- `created_at`: Account creation timestamp
- `dashboard_preferences`: Optional JSON object storing user's dashboard widget preferences

**Indexes**:
- `username` (unique)
- `email` (unique)
- `user_type`
- `feedlot_id`
- `feedlot_ids`

**Constraints**:
- `username` must be unique
- `email` must be unique
- `user_type` must be one of the valid types
- `feedlot_id` is only set for `user` type
- `feedlot_ids` is only set for `business_admin` or `business_owner` types

---

### 2. `feedlots` Collection

**Purpose**: Represents feedlot instances (tenants) in the multi-tenant SaaS system.

**Schema**:
```javascript
{
  _id: ObjectId,
  name: String,                   // Feedlot name
  location: String,               // Physical location
  feedlot_code: String,           // Unique code for database identification (case-insensitive, unique)
  contact_info: Object,           // Contact information dictionary
  owner_id: ObjectId,             // Reference to business owner user
  land_description: String,       // Land description
  premises_id: String,             // Premises Identification (PID) number
  pen_map: Object,                // Pen map configuration
  branding: Object,                // Branding configuration
  deleted_at: DateTime,            // Soft delete timestamp (null if not deleted)
  created_at: DateTime,
  updated_at: DateTime
}
```

**Field Descriptions**:
- `_id`: Unique feedlot identifier (ObjectId)
- `name`: Feedlot name (required)
- `location`: Physical location of the feedlot
- `feedlot_code`: Unique code used to identify the feedlot-specific database (required, unique, case-insensitive)
- `contact_info`: Dictionary containing contact information (phone, email, address, etc.)
- `owner_id`: Reference to the business owner user (ObjectId, optional)
- `land_description`: Description of the land/premises
- `premises_id`: Premises Identification (PID) number
- `pen_map`: Pen map configuration object containing:
  - `grid_width`: Integer
  - `grid_height`: Integer
  - `pen_placements`: Array of `{row, col, pen_id}` objects
  - `updated_at`: DateTime
- `branding`: Branding configuration object containing:
  - `logo_path`: String (path to logo file)
  - `favicon_path`: String (path to favicon file)
  - `primary_color`: String (hex color code)
  - `secondary_color`: String (hex color code)
  - `company_name`: String (custom company name)
- `deleted_at`: Soft delete timestamp (null if active, DateTime if deleted)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_code` (unique, case-insensitive)
- `owner_id`
- `deleted_at` (for filtering active feedlots)

**Constraints**:
- `feedlot_code` must be unique (case-insensitive comparison)
- `feedlot_code` is used to generate database name: `feedlot_{feedlot_code.toLowerCase().trim()}`

**Soft Delete**: Feedlots use soft delete (`deleted_at` field) rather than hard delete.

---

### 3. `pens` Collection

**Purpose**: Represents physical pen locations within feedlots where cattle can be housed.

**Note**: Pens are stored in the main database, not in feedlot-specific databases.

**Schema**:
```javascript
{
  _id: ObjectId,
  feedlot_id: ObjectId,           // Reference to parent feedlot (required)
  pen_number: String,              // Unique pen identifier within feedlot
  capacity: Integer,               // Maximum number of cattle the pen can hold
  description: String,             // Optional description
  deleted_at: DateTime,            // Soft delete timestamp (null if not deleted)
  created_at: DateTime,
  updated_at: DateTime
}
```

**Field Descriptions**:
- `_id`: Unique pen identifier (ObjectId)
- `feedlot_id`: Reference to the parent feedlot (ObjectId, required)
- `pen_number`: Unique pen identifier within the feedlot (required, unique per feedlot)
- `capacity`: Maximum number of cattle the pen can hold (integer, required)
- `description`: Optional description of the pen
- `deleted_at`: Soft delete timestamp (null if active, DateTime if deleted)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_id`
- `(feedlot_id, pen_number)` (unique compound index)

**Constraints**:
- `pen_number` must be unique within a feedlot
- `feedlot_id` is required
- `capacity` must be a positive integer

**Soft Delete**: Pens use soft delete (`deleted_at` field) rather than hard delete.

---

### 4. `api_keys` Collection

**Purpose**: Manages API authentication keys for feedlot API access.

**Schema**:
```javascript
{
  _id: ObjectId,
  feedlot_id: ObjectId,           // Reference to feedlot
  api_key_hash: String,            // SHA-256 hash of the API key
  description: String,             // Optional description
  created_at: DateTime,
  last_used_at: DateTime,          // Last time the key was used (null if never used)
  is_active: Boolean               // Whether the key is active
}
```

**Field Descriptions**:
- `_id`: Unique API key identifier (ObjectId)
- `feedlot_id`: Reference to the feedlot this key belongs to (ObjectId, required)
- `api_key_hash`: SHA-256 hash of the API key (required)
- `description`: Optional description for the key
- `created_at`: Creation timestamp
- `last_used_at`: Last time the key was used for authentication (null if never used)
- `is_active`: Whether the key is active and can be used (default: `true`)

**Indexes**:
- `feedlot_id`
- `api_key_hash` (unique)
- `is_active`

**Security Notes**:
- API keys are never stored in plain text
- Only the SHA-256 hash is stored
- The plain text key is only returned once during creation
- Keys can be deactivated without deletion

---

### 5. `manifests` Collection (Main Database)

**Purpose**: Stores manifest records in the main database (shared across feedlots).

**Schema**:
```javascript
{
  _id: ObjectId,
  feedlot_id: ObjectId,            // Reference to feedlot
  manifest_data: Object,            // Full manifest data structure
  cattle_ids: [ObjectId],           // List of cattle IDs included in manifest
  template_id: ObjectId,             // Reference to manifest template (optional)
  created_by: String,                // User who created the manifest
  total_head: Integer,               // Total number of cattle
  destination_name: String,          // Destination name
  date: String,                      // Manifest date (YYYY-MM-DD)
  created_at: DateTime,
  updated_at: DateTime
}
```

**Field Descriptions**:
- `_id`: Unique manifest identifier (ObjectId)
- `feedlot_id`: Reference to the feedlot (ObjectId, required)
- `manifest_data`: Complete manifest data structure (object)
- `cattle_ids`: Array of cattle record IDs included in the manifest (ObjectId array)
- `template_id`: Reference to the manifest template used (ObjectId, optional)
- `created_by`: Username or identifier of the user who created the manifest
- `total_head`: Total number of cattle in the manifest (integer)
- `destination_name`: Name of the destination
- `date`: Manifest date in YYYY-MM-DD format
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_id`
- `created_at` (descending, for recent manifests)
- `(feedlot_id, created_at)` (compound index)

---

### 6. `manifest_templates` Collection (Main Database)

**Purpose**: Stores manifest templates in the main database (shared across feedlots).

**Schema**:
```javascript
{
  _id: ObjectId,
  feedlot_id: ObjectId,                    // Reference to feedlot
  name: String,                             // Template name
  owner_name: String,                       // Default owner name
  owner_phone: String,                      // Default owner phone
  owner_address: String,                    // Default owner address
  dealer_name: String,                      // Default dealer name
  dealer_phone: String,                     // Default dealer phone
  dealer_address: String,                   // Default dealer address
  default_destination_name: String,         // Default destination name
  default_destination_address: String,       // Default destination address
  default_transporter_name: String,         // Default transporter name
  default_transporter_phone: String,        // Default transporter phone
  default_transporter_trailer: String,      // Default transporter trailer
  default_purpose: String,                  // Default purpose (e.g., 'transport_only')
  default_premises_id_before: String,        // Default premises ID before
  default_premises_id_destination: String,  // Default premises ID destination
  is_default: Boolean,                      // Whether this is the default template
  created_at: DateTime,
  updated_at: DateTime
}
```

**Field Descriptions**:
- `_id`: Unique template identifier (ObjectId)
- `feedlot_id`: Reference to the feedlot (ObjectId, required)
- `name`: Template name (required)
- `owner_name`, `owner_phone`, `owner_address`: Default owner information
- `dealer_name`, `dealer_phone`, `dealer_address`: Default dealer information
- `default_destination_name`, `default_destination_address`: Default destination information
- `default_transporter_name`, `default_transporter_phone`, `default_transporter_trailer`: Default transporter information
- `default_purpose`: Default purpose (e.g., 'transport_only')
- `default_premises_id_before`, `default_premises_id_destination`: Default premises IDs
- `is_default`: Whether this is the default template for the feedlot (only one default per feedlot)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_id`
- `(feedlot_id, is_default)` (compound index)

**Constraints**:
- Only one template per feedlot can have `is_default: true`
- Setting a template as default automatically unsets other defaults for that feedlot

---

## Feedlot-Specific Database Collections

Each feedlot has its own database named `feedlot_{feedlot_code}` containing the following collections:

### 1. `pens` Collection (Feedlot Database)

**Note**: This collection may not exist in feedlot databases as pens are stored in the main database. This section is included for completeness.

**Schema**: Same as main database `pens` collection (see above).

---

### 2. `batches` Collection

**Purpose**: Represents groups of cattle that were inducted together or processed as a unit.

**Schema**:
```javascript
{
  _id: ObjectId,
  feedlot_id: ObjectId,           // Reference to parent feedlot (required)
  batch_number: String,            // Unique batch identifier within feedlot
  event_date: DateTime,           // Date when the batch event occurred
  funder: String,                  // Information about who funded the batch
  event_type: String,              // Type of event: 'induction', 'pairing', 'checkin', 'repair', 'export'
  notes: String,                   // Optional notes about the batch
  cattle_ids: [ObjectId],          // Historical record of all cattle ever associated with this batch
  deleted_at: DateTime,             // Soft delete timestamp (null if not deleted)
  created_at: DateTime,
  updated_at: DateTime
}
```

**Field Descriptions**:
- `_id`: Unique batch identifier (ObjectId)
- `feedlot_id`: Reference to the parent feedlot (ObjectId, required)
- `batch_number`: Unique batch identifier within the feedlot (required, unique per feedlot)
- `event_date`: Date when the batch event occurred (DateTime, required)
- `funder`: Information about who funded the batch (string)
- `event_type`: Type of event (string, required)
  - `induction`: Initial cattle induction into the feedlot
  - `pairing`: Tag pairing event
  - `checkin`: Check-in event
  - `repair`: Tag repair event
  - `export`: Export event
- `notes`: Optional notes about the batch
- `cattle_ids`: Historical array of all cattle record IDs that have ever been associated with this batch (ObjectId array)
- `deleted_at`: Soft delete timestamp (null if active, DateTime if deleted)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_id`
- `(feedlot_id, batch_number)` (unique compound index)
- `event_type`
- `event_date`

**Constraints**:
- `batch_number` must be unique within a feedlot
- `feedlot_id` is required
- `event_type` must be one of the valid types
- `cattle_ids` is a historical record - cattle can be removed from batches but their IDs remain in this array

**Soft Delete**: Batches use soft delete (`deleted_at` field) rather than hard delete.

---

### 3. `cattle` Collection

**Purpose**: Represents individual cattle records with complete tracking information.

**Schema**:
```javascript
{
  _id: ObjectId,
  feedlot_id: ObjectId,            // Reference to parent feedlot (required)
  batch_id: ObjectId,              // Reference to batch (optional)
  pen_id: ObjectId,                 // Reference to current pen (optional)
  cattle_id: String,                // Unique cattle identifier within feedlot
  sex: String,                      // Sex of the cattle
  weight: Number,                   // Current weight
  cattle_status: String,            // Cattle status
  lf_tag: String,                   // Low Frequency tag identifier
  uhf_tag: String,                  // Ultra High Frequency tag identifier (EPC)
  color: String,                    // Color description
  breed: String,                    // Breed information
  visual_id: String,                // Visual identification
  lot: String,                      // Lot identifier
  lot_group: String,                // Lot group identifier
  brand_drawings: String,           // Brand drawings information
  brand_locations: String,          // Brand locations
  other_marks: String,              // Other identifying marks
  notes: String,                    // General notes
  status: String,                   // Current status: 'active' or 'removed'
  induction_date: DateTime,         // Date when cattle was inducted
  weight_history: [Object],         // Array of weight records
  notes_history: [Object],          // Array of notes with timestamps
  tag_pair_history: [Object],       // Array of previous LF/UHF tag pairs
  audit_log: [Object],              // Complete audit trail of all activities
  deleted_at: DateTime,             // Soft delete timestamp (null if not deleted)
  created_at: DateTime,
  updated_at: DateTime
}
```

**Field Descriptions**:
- `_id`: Unique cattle record identifier (ObjectId)
- `feedlot_id`: Reference to the parent feedlot (ObjectId, required)
- `batch_id`: Reference to the batch this cattle belongs to (ObjectId, optional)
- `pen_id`: Reference to the pen where this cattle is currently located (ObjectId, optional)
- `cattle_id`: Unique cattle identifier within the feedlot (string, required, unique per feedlot)
- `sex`: Sex of the cattle (string, e.g., 'male', 'female', 'steer', 'heifer')
- `weight`: Current weight in kilograms (number)
- `cattle_status`: Cattle status (string, e.g., 'Healthy', 'Sick', 'Quarantine')
- `lf_tag`: Low Frequency tag identifier (string, optional)
- `uhf_tag`: Ultra High Frequency tag identifier/EPC (string, optional)
- `color`: Color description (string, optional)
- `breed`: Breed information (string, optional)
- `visual_id`: Visual identification (string, optional)
- `lot`: Lot identifier (string, optional)
- `lot_group`: Lot group identifier (string, optional)
- `brand_drawings`: Brand drawings information (string, optional)
- `brand_locations`: Brand locations (string, optional)
- `other_marks`: Other identifying marks (string, optional)
- `notes`: General notes (string, optional)
- `status`: Current status (string, required)
  - `active`: Cattle is active in the system
  - `removed`: Cattle has been removed
- `induction_date`: Date when cattle was inducted (DateTime)
- `weight_history`: Array of weight records, each containing:
  - `weight`: Number
  - `recorded_at`: DateTime
  - `recorded_by`: String (username)
- `notes_history`: Array of notes, each containing:
  - `note`: String
  - `recorded_at`: DateTime
  - `recorded_by`: String (username)
- `tag_pair_history`: Array of previous tag pairs, each containing:
  - `lf_tag`: String
  - `uhf_tag`: String
  - `paired_at`: DateTime
  - `unpaired_at`: DateTime
  - `updated_by`: String (username)
- `audit_log`: Array of audit log entries, each containing:
  - `activity_type`: String (e.g., 'created', 'pen_moved', 'weight_recorded', 'tag_repair')
  - `description`: String
  - `performed_by`: String (username)
  - `timestamp`: DateTime
  - `details`: Object (optional additional details)
- `deleted_at`: Soft delete timestamp (null if active, DateTime if deleted)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Indexes**:
- `feedlot_id`
- `batch_id`
- `pen_id`
- `(feedlot_id, cattle_id)` (unique compound index)
- `uhf_tag` (for tag lookups)
- `status`
- `cattle_status`

**Constraints**:
- `cattle_id` must be unique within a feedlot
- `feedlot_id` is required
- `batch_id` is optional (cattle can exist without a batch)
- `pen_id` is optional (cattle can be moved between pens or have no pen assignment)
- `status` must be 'active' or 'removed'
- Only active cattle (`status: 'active'`) are counted toward pen capacity

**Soft Delete**: Cattle use soft delete (`deleted_at` field) rather than hard delete.

**Historical Data**:
- `weight_history`: Tracks all weight measurements over time
- `notes_history`: Tracks all notes added to the cattle record
- `tag_pair_history`: Tracks previous LF/UHF tag pairs when tags are re-paired
- `audit_log`: Complete audit trail of all activities (creation, movements, updates, etc.)

---

### 4. `manifest_templates` Collection (Feedlot Database)

**Purpose**: Stores feedlot-specific manifest templates.

**Schema**: Same as main database `manifest_templates` collection (see above).

**Note**: Feedlots can have templates in both the main database and their feedlot-specific database. The feedlot-specific templates take precedence.

---

### 5. `manifests` Collection (Feedlot Database)

**Purpose**: Stores feedlot-specific manifest records.

**Schema**: Same as main database `manifests` collection (see above).

**Note**: Feedlots can have manifests in both the main database and their feedlot-specific database. The feedlot-specific manifests take precedence.

---

## Indexes Summary

### Main Database Indexes

**users**:
- `username` (unique)
- `email` (unique)
- `user_type`
- `feedlot_id`
- `feedlot_ids`

**feedlots**:
- `feedlot_code` (unique, case-insensitive)
- `owner_id`
- `deleted_at`

**pens**:
- `feedlot_id`
- `(feedlot_id, pen_number)` (unique compound)

**api_keys**:
- `feedlot_id`
- `api_key_hash` (unique)
- `is_active`

**manifests**:
- `feedlot_id`
- `created_at` (descending)
- `(feedlot_id, created_at)` (compound)

**manifest_templates**:
- `feedlot_id`
- `(feedlot_id, is_default)` (compound)

### Feedlot-Specific Database Indexes

**batches**:
- `feedlot_id`
- `(feedlot_id, batch_number)` (unique compound)
- `event_type`
- `event_date`

**cattle**:
- `feedlot_id`
- `batch_id`
- `pen_id`
- `(feedlot_id, cattle_id)` (unique compound)
- `uhf_tag`
- `status`
- `cattle_status`

**manifest_templates**:
- `feedlot_id`
- `(feedlot_id, is_default)` (compound)

**manifests**:
- `feedlot_id`
- `created_at` (descending)
- `(feedlot_id, created_at)` (compound)

---

## Data Types

### MongoDB Data Types Used

- **ObjectId**: MongoDB's unique identifier type (12-byte identifier)
- **String**: UTF-8 string
- **Number**: 64-bit floating point or integer
- **Boolean**: true/false
- **DateTime**: MongoDB Date type (stored as UTC)
- **Binary**: Binary data (used for password hashes)
- **Object**: Embedded document (nested object)
- **Array**: Array of values or documents

### Field Type Guidelines

- **IDs**: Always use ObjectId for references to other documents
- **Timestamps**: Always use DateTime (UTC)
- **Unique Identifiers**: Use String for human-readable identifiers (cattle_id, pen_number, batch_number)
- **Status Fields**: Use String with predefined values
- **Historical Arrays**: Use Array of Objects with timestamp fields

---

## Constraints and Validation

### Uniqueness Constraints

1. **Feedlot Code**: Must be unique across all feedlots (case-insensitive)
2. **Username**: Must be unique across all users
3. **Email**: Must be unique across all users
4. **Pen Number**: Must be unique within a feedlot
5. **Batch Number**: Must be unique within a feedlot
6. **Cattle ID**: Must be unique within a feedlot
7. **API Key Hash**: Must be unique (enforced by application logic)

### Required Fields

**Users**:
- `username` (required, unique)
- `email` (required, unique)
- `password_hash` (required)
- `user_type` (required)

**Feedlots**:
- `name` (required)
- `feedlot_code` (required, unique)

**Pens**:
- `feedlot_id` (required)
- `pen_number` (required, unique per feedlot)
- `capacity` (required, positive integer)

**Batches**:
- `feedlot_id` (required)
- `batch_number` (required, unique per feedlot)
- `event_date` (required)
- `event_type` (required)

**Cattle**:
- `feedlot_id` (required)
- `cattle_id` (required, unique per feedlot)
- `status` (required, must be 'active' or 'removed')

### Optional Relationships

1. **Cattle → Batch**: `batch_id` can be `None` (cattle can exist without a batch)
2. **Cattle → Pen**: `pen_id` can be `None` (cattle can be moved between pens or have no pen assignment)
3. **Feedlot → Owner**: `owner_id` can be `None` (feedlot can exist without an owner)

---

## Soft Delete Pattern

Several collections use soft delete instead of hard delete:

- **feedlots**: `deleted_at` field (null if active, DateTime if deleted)
- **pens**: `deleted_at` field (null if active, DateTime if deleted)
- **batches**: `deleted_at` field (null if active, DateTime if deleted)
- **cattle**: `deleted_at` field (null if active, DateTime if deleted)

**Benefits**:
- Preserves data for audit trails
- Allows data recovery if needed
- Maintains referential integrity
- Enables historical reporting

**Query Pattern**:
```python
# Query active records only
query = {'feedlot_id': ObjectId(feedlot_id), 'deleted_at': None}

# Query including deleted records
query = {'feedlot_id': ObjectId(feedlot_id)}
```

---

## Relationships Summary

### Entity Relationships

| Parent Entity | Relationship | Child Entity | Type | Required |
|---------------|--------------|-------------|------|----------|
| Feedlot | One-to-Many | Pens | Parent-Child | Yes |
| Feedlot | One-to-Many | Batches | Parent-Child | Yes |
| Feedlot | One-to-Many | Cattle | Parent-Child | Yes |
| Feedlot | One-to-Many | API Keys | Parent-Child | Yes |
| Feedlot | One-to-Many | Manifests | Parent-Child | Yes |
| Feedlot | One-to-Many | Manifest Templates | Parent-Child | Yes |
| Batch | One-to-Many | Cattle | Parent-Child | No |
| Pen | One-to-Many | Cattle | Parent-Child | No |
| User (business_owner) | One-to-Many | Feedlots | Owner | No |

### Relationship Details

1. **Feedlot → Pens**: Required relationship. Each pen must belong to a feedlot.
2. **Feedlot → Batches**: Required relationship. Each batch must belong to a feedlot.
3. **Feedlot → Cattle**: Required relationship. Each cattle record must belong to a feedlot.
4. **Batch → Cattle**: Optional relationship. Cattle can exist without a batch.
5. **Pen → Cattle**: Optional relationship. Cattle can be moved between pens or have no pen assignment.

---

## Database Initialization

### Main Database Initialization

The main database is initialized when the application starts. Collections are created automatically on first use.

### Feedlot Database Initialization

When a feedlot is created, its feedlot-specific database is initialized with:

1. **Collections**: `batches`, `cattle`, `manifest_templates`, `manifests`
2. **Indexes**: All required indexes are created automatically
3. **Validation**: Database name is generated as `feedlot_{feedlot_code.toLowerCase().trim()}`

**Initialization Code** (from `Feedlot.initialize_feedlot_database()`):
```python
# Pens collection (in main database)
db.pens.create_index('feedlot_id')
db.pens.create_index([('feedlot_id', 1), ('pen_number', 1)], unique=True)

# Batches collection
feedlot_db.batches.create_index('feedlot_id')
feedlot_db.batches.create_index([('feedlot_id', 1), ('batch_number', 1)], unique=True)

# Cattle collection
feedlot_db.cattle.create_index('feedlot_id')
feedlot_db.cattle.create_index('batch_id')
feedlot_db.cattle.create_index('pen_id')
feedlot_db.cattle.create_index([('feedlot_id', 1), ('cattle_id', 1)], unique=True)

# Manifest templates collection
feedlot_db.manifest_templates.create_index('feedlot_id')
feedlot_db.manifest_templates.create_index([('feedlot_id', 1), ('is_default', 1)])

# Manifests collection
feedlot_db.manifests.create_index('feedlot_id')
feedlot_db.manifests.create_index([('feedlot_id', 1), ('created_at', -1)])
feedlot_db.manifests.create_index('created_at')
```

---

## Security Considerations

### Password Storage

- Passwords are hashed using **bcrypt** with automatic salt generation
- Never store plain text passwords
- Password hashes are stored as Binary type in MongoDB

### API Key Storage

- API keys are hashed using **SHA-256** before storage
- Plain text keys are only returned once during creation
- Keys can be deactivated without deletion
- `api_key_hash` is indexed for fast lookups

### Data Isolation

- Feedlot-specific databases provide complete data isolation
- Users can only access feedlots they are assigned to
- API keys are scoped to specific feedlots
- Queries automatically filter by `feedlot_id` or `feedlot_code`

---

## Best Practices

### Querying

1. **Always filter by feedlot**: Include `feedlot_id` or use `feedlot_code` to access the correct database
2. **Respect soft deletes**: Filter by `deleted_at: None` unless explicitly querying deleted records
3. **Use indexes**: Query on indexed fields for optimal performance
4. **Limit results**: Use pagination for large datasets

### Data Integrity

1. **Validate uniqueness**: Check for existing records before creating new ones
2. **Check relationships**: Verify parent entities exist before creating child entities
3. **Handle optional fields**: Always check for `None` values when querying by optional relationships
4. **Maintain audit trails**: Use audit logs for important operations

### Performance

1. **Use compound indexes**: Create compound indexes for common query patterns
2. **Avoid full collection scans**: Always use indexed fields in queries
3. **Cache feedlot databases**: Feedlot database connections are cached for performance
4. **Batch operations**: Use bulk operations when inserting/updating multiple documents

---

## Related Documentation

- `ENTITY_RELATIONSHIPS.md`: Detailed relationship documentation
- `API_DOCUMENTATION.md`: API endpoints and usage
- `OFFICE_DATABASE_STRUCTURE.md`: Office application database structure
- Model files: `app/models/*.py` - Implementation details

---

## Version History

- **Initial Version**: Multi-tenant MongoDB architecture with feedlot-specific databases
- **Soft Delete**: Implemented soft delete pattern for feedlots, pens, batches, and cattle
- **Audit Logging**: Added comprehensive audit logging for cattle records
- **Historical Tracking**: Added weight_history, notes_history, and tag_pair_history for cattle
