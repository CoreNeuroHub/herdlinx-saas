# Office and SAAS Integration Guide

## Architecture Overview

HerdLinx has two deployment models that work together:

### Multi-Feedlot SAAS Model (Primary)
- **SAAS Application:** Cloud-based web dashboard (one instance for all feedlots)
- **Admin Users:** Each feedlot has business owner/admin users who see only their feedlot
- **Super Admin:** Super owners and super admins (SFT team) can see all feedlots
- **MongoDB:** Shared MongoDB instance (same database name but different collections or namespaced)

### Office Raspberry Pi Model (Per-Feedlot)
- **One Office Pi per Feedlot:** Each feedlot location has its own office Raspberry Pi
- **Purpose:** Receives LoRa packets from barn Pi, stores in local SQLite, syncs to MongoDB
- **Sync Target:** Syncs to the shared MongoDB that SAAS reads from
- **feedlot_code:** Each office Pi identifies by a unique feedlot_code (e.g., "FEEDLOT001", "FEEDLOT002")

---

## Data Flow

```
Feedlot 1:
  Barn Raspberry Pi (RFID detection)
    ↓ LoRa TX (radio)
  Office Raspberry Pi #1 (office_receiver.db SQLite)
    ↓ MongoDB Sync
  MongoDB (herdlinx_saas.events, herdlinx_saas.livestock, herdlinx_saas.batches)
    ↓ SAAS Queries (filtered by feedlot_code)
  SAAS Dashboard (admin user sees only this feedlot)

Feedlot 2:
  Barn Raspberry Pi (RFID detection)
    ↓ LoRa TX (radio)
  Office Raspberry Pi #2 (office_receiver.db SQLite)
    ↓ MongoDB Sync
  MongoDB (herdlinx_saas.events, herdlinx_saas.livestock, herdlinx_saas.batches)
    ↓ SAAS Queries (filtered by feedlot_code)
  SAAS Dashboard (different admin user sees only this feedlot)

SAAS Super Admin:
  Can see all feedlots from all office Raspberry Pis
  Uses aggregated queries across all data
```

---

## SAAS Model Structure

### Users & Permissions

#### Super Owner / Super Admin (SFT Team)
- Login route: `/auth/login` (all users)
- Access: Dashboard shows ALL feedlots and their data
- Can manage all feedlots, users, API keys
- See in navigation: "Dashboard", "Feedlot Hub", "Manage Users", "Settings"

#### Business Owner / Business Admin (Feedlot Owners)
- Login route: `/auth/login` (same)
- Access: Dashboard shows ONLY their assigned feedlot
- Can manage their feedlot's users and view their office data
- See in navigation: "Dashboard", "Settings" (for their feedlot only)

### Feedlot Association

Each feedlot in SAAS has:
- `_id`: MongoDB ObjectId (unique identifier in SAAS)
- `feedlot_code`: String (matches office Raspberry Pi's feedlot_code)
- `name`: Human-readable name
- `owner_id`: ObjectId reference to business owner user
- `location`: Physical location

### Database Integration

**SAAS Collections in MongoDB:**
- `feedlots` - Feedlot definitions with feedlot_code
- `users` - User accounts and permissions
- `api_keys` - API keys for office Raspberry Pi authentication
- `batches` - SAAS-created batches (or synced from office)
- `cattle` - SAAS-created cattle (or synced from office)
- `pens` - Pen definitions

**Office Collections in MongoDB (per-feedlot):**
- `events` - Raw LoRa event packets from barn
- `livestock` - Animal records with RFID tags (office schema)
- `batches` - Induction batches (office schema)
- `event_audit` - Complete audit trail per animal

---

## Integration Implementation

### Office Data Adapter (`saas/app/adapters/office_adapter.py`)

Transparently maps office data to SAAS format:

1. **Field Mapping:**
   - Office `lf_id` → SAAS `lf_tag`
   - Office `epc` → SAAS `uhf_tag`
   - Office `livestock_id` → SAAS `cattle_id`
   - Office `batch_id` (integer) → SAAS `batch_id` (kept as reference)

2. **Feedlot Association:**
   - Office data has no feedlot_id
   - Adapter looks up `feedlot_code` from SAAS feedlot
   - Filters office data by feedlot_code to ensure users only see their data

3. **Transformation:**
   - Converts office SQLite schema to SAAS MongoDB expected fields
   - Adds default values for missing fields (weight, health_status, etc.)
   - Preserves ObjectId references for MongoDB compatibility

### Updated SAAS Models

**`saas/app/models/batch.py`**
- `find_by_id()` - Supports both ObjectId (SAAS) and integer (office)
- `find_by_feedlot()` - Returns both native SAAS and office synced batches
- `get_cattle_count()` - Counts office livestock in batch

**`saas/app/models/cattle.py`**
- `find_by_id()` - Supports both ObjectId (SAAS) and integer (office)
- `find_by_batch()` - Returns office livestock for batch
- Other methods work with both data sources

**`saas/app/models/feedlot.py`**
- Unchanged - provides feedlot lookup including feedlot_code
- Feedlot model connects SAAS metadata to office data

### Querying Office Data

**From a route handler:**
```python
from app.adapters import get_office_adapter
from app import db

# In a feedlot-scoped route
feedlot_id = request.args.get('feedlot_id')  # From URL
adapter = get_office_adapter(db)
adapter.set_feedlot_context(feedlot_id)

# Query office livestock for this feedlot's batch
livestock = adapter.get_office_livestock_by_batch(batch_id)
```

---

## Configuration

### Environment Variables

**SAAS (`saas/.env`):**
```
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB=herdlinx_saas
SECRET_KEY=your-secret-key
```

**Office Raspberry Pi (`office/config.env.mongodb`):**
```
MONGO_HOST=mongodb-cloud-url.mongodb.net
MONGO_PORT=27017
MONGO_USERNAME=office_pi_1
MONGO_PASSWORD=secure_password
MONGO_DB=herdlinx_saas

LORA_PORT=/dev/ttyUSB0
LORA_BAUD_RATE=115200

OFFICE_FEEDLOT_CODE=FEEDLOT001
```

### MongoDB Setup

Single MongoDB instance shared by both office Pi and SAAS:

1. **Collections by prefix:**
   - `events` - Office data
   - `livestock` - Office data
   - `batches` - Office data
   - `event_audit` - Office audit
   - `users` - SAAS users
   - `feedlots` - SAAS feedlots (with feedlot_code)
   - `api_keys` - SAAS API keys
   - `cattle` - SAAS cattle (if manual entry)
   - `pens` - SAAS pens

2. **Or use separate databases:**
   - `herdlinx_saas` - Main SAAS data (users, feedlots, api_keys)
   - `herdlinx_office_feedlot001` - Office Pi 1 data
   - `herdlinx_office_feedlot002` - Office Pi 2 data
   - etc.

   Then adapter would connect to appropriate database per feedlot.

---

## Dashboard Display

### Super Admin Dashboard
Shows data from ALL office Raspberry Pis:
- List of all feedlots
- Aggregated statistics (total cattle, total batches, etc.)
- View/manage any feedlot
- View/manage any user

### Feedlot Admin Dashboard
Shows data from ONLY their assigned office Raspberry Pi:
- Their feedlot's batches
- Their feedlot's cattle
- Their feedlot's pens
- Their feedlot's users (office staff)
- Cannot see other feedlots

### Implementation in Routes

**`saas/app/routes/top_level_routes.py`** (Super Admin)
```python
@top_level_bp.route('/dashboard')
def dashboard():
    feedlots = Feedlot.find_all()  # ALL feedlots
    # Aggregate data from all office Pis
    return render_template('top_level/dashboard.html', feedlots=feedlots)
```

**`saas/app/routes/feedlot_routes.py`** (Feedlot Admin)
```python
@feedlot_bp.route('/feedlot/<feedlot_id>/dashboard')
def feedlot_dashboard(feedlot_id):
    feedlot = Feedlot.find_by_id(feedlot_id)
    adapter = get_office_adapter(db)
    adapter.set_feedlot_context(feedlot_id)

    batches = Batch.find_by_feedlot(feedlot_id)  # Uses adapter for office data
    return render_template('feedlot/dashboard.html', feedlot=feedlot, batches=batches)
```

---

## Access Control

### Middleware / Route Protection

**Super Admin:**
- Checks `session['user_type']` == 'super_owner' or 'super_admin'
- Can access `/` (root dashboard)
- Can access `/feedlot/<any_feedlot_id>/`
- Can access `/admin/*`

**Feedlot Admin:**
- Checks `session['user_type']` == 'business_owner' or 'business_admin'
- Can only access `/feedlot/<their_feedlot_id>/`
- Cannot access other feedlots
- Cannot access `/admin/*`

### Implementation in Routes
```python
@feedlot_bp.route('/feedlot/<feedlot_id>/view')
def view_feedlot(feedlot_id):
    # Check if user can access this feedlot
    user_id = session.get('user_id')
    user_type = session.get('user_type')

    if user_type in ['super_owner', 'super_admin']:
        # Super admin can see any feedlot
        pass
    elif user_type in ['business_owner', 'business_admin']:
        # Check if user is assigned to this feedlot
        feedlot = Feedlot.find_by_id(feedlot_id)
        if str(feedlot.get('owner_id')) != user_id:
            abort(403)  # Forbidden
    else:
        abort(403)

    # Now safe to query office data
    adapter = get_office_adapter(db)
    adapter.set_feedlot_context(feedlot_id)
    batches = Batch.find_by_feedlot(feedlot_id)
    return render_template(...)
```

---

## API Integration

### Office Raspberry Pi → SAAS API

Office Pi can push data to SAAS API endpoints (`saas/app/routes/api_routes.py`):

```
POST /api/v1/feedlot/batches
POST /api/v1/feedlot/livestock
POST /api/v1/feedlot/events
```

Requires API key (generated in SAAS Settings).

Currently, office data flows:
1. SQLite (office) → MongoDB (sync daemon)
2. SAAS reads from MongoDB directly (via adapter)

Could also implement:
1. SQLite (office) → SAAS API
2. SAAS creates records in MongoDB
3. Office pulls from SAAS to show local dashboard (optional)

---

## Testing

### Development Setup

**Terminal 1: MongoDB**
```bash
mongod --dbpath ./data
```

**Terminal 2: Office Simulator**
```bash
cd office
python -c "
import sqlite3
import mongodb_client
# Insert test events into MongoDB
# Simulate office sync
"
```

**Terminal 3: SAAS**
```bash
cd saas
python run.py
```

### Test Cases

1. **Super Admin Views All Data:**
   - Login as super_admin
   - Dashboard shows all feedlots
   - Click feedlot → shows office data from that office Pi

2. **Feedlot Admin Views Own Data:**
   - Login as business_owner for FEEDLOT001
   - Dashboard shows only FEEDLOT001 data
   - Cannot access FEEDLOT002
   - Shows office Raspberry Pi #1 data

3. **Data Sync:**
   - Office Pi syncs new event to MongoDB
   - SAAS dashboard updates without reload (or with F5 refresh)
   - Data visible to correct user (super admin or feedlot admin)

---

## Troubleshooting

### Office Data Not Showing in SAAS

1. **Check MongoDB connectivity:**
   ```bash
   # From SAAS machine
   python -c "from pymongo import MongoClient; MongoClient('mongodb://...').admin.command('ping')"
   ```

2. **Check office collections exist:**
   ```bash
   # In MongoDB shell
   db.getCollectionNames()  # Should show events, livestock, batches, event_audit
   ```

3. **Check adapter transform:**
   - Add logging to `office_adapter.py` transform methods
   - Verify field names are mapped correctly
   - Check for missing fields with defaults

4. **Check feedlot_code:**
   - Verify office Pi has correct `OFFICE_FEEDLOT_CODE` in config
   - Verify SAAS feedlot has matching `feedlot_code`
   - Check if adapter is filtering correctly

### User Sees Wrong Feedlot Data

1. **Check user assignment:**
   - Verify user `owner_id` matches feedlot `owner_id`
   - Check session user_type

2. **Check adapter context:**
   - Ensure `adapter.set_feedlot_context()` is called
   - Verify feedlot_id is correct in URL/params

3. **Check MongoDB data:**
   - Verify office data includes `feedlot_code` or is in correct collection
   - Run query to see what's actually in MongoDB

---

## Future Enhancements

1. **Separate MongoDB Databases:** Use different databases for each office (herdlinx_office_feedlot001, etc.)
2. **Real-time Sync:** WebSocket updates when office Pi sends new data
3. **Offline Office:** Local SAAS dashboard on office Pi (read-only mirror)
4. **Data Validation:** Validate office data before syncing
5. **Conflict Resolution:** Handle conflicts if office data changed while syncing

---

**Last Updated:** 2025-11-07
**Status:** Implementation in progress
