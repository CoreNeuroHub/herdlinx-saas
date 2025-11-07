# SAAS Routes and User Flow Documentation

## Two Main Routes

The SAAS application has two main route systems based on user type:

### 1. **Top-Level Routes** (`saas/app/routes/top_level_routes.py`)
- **For:** Super Owner, Super Admin, Business Owner, Business Admin
- **URL:** `/dashboard`, `/feedlot-hub`, `/manage-users`, `/settings`, `/api-keys`
- **Decorator:** `@admin_access_required`
- **Access Control:**
  - **Super Owner / Super Admin:** See ALL feedlots and their data
  - **Business Owner / Business Admin:** See ONLY their assigned feedlots (stored in `session['feedlot_ids']`)
- **Data Shown:**
  - Dashboard: Aggregated statistics across all accessible feedlots
  - Feedlot Hub: List of all accessible feedlots with search/filter
  - Manage Users: All users across all feedlots
  - Settings: API keys, system settings

### 2. **Feedlot Routes** (`saas/app/routes/feedlot_routes.py`)
- **For:** All authenticated users (when navigating to specific feedlot)
- **URL:** `/feedlot/<feedlot_id>/dashboard`, `/feedlot/<feedlot_id>/batches`, etc.
- **Decorator:** `@feedlot_access_required()`
- **Access Control:**
  - **Super Owner / Super Admin:** Can access ANY feedlot_id in URL
  - **Business Owner / Business Admin:** Can ONLY access feedlot_ids in their `session['feedlot_ids']`
  - **Regular User:** Can ONLY access their single assigned feedlot
- **Data Shown:**
  - Dashboard: Batches, cattle, pens for that specific feedlot
  - Batch Management: View/create/edit batches
  - Cattle Management: View/add cattle, manage tags, track weight
  - Pen Management: View/create pens, view cattle in pen

---

## User Types & Permissions

### Super Owner
- **Can:** View all feedlots, manage all users, manage API keys, system settings
- **Route:** Top-level (`@admin_access_required`)
- **Session:** No `feedlot_ids` restriction
- **Data Access:** ALL feedlots

### Super Admin
- **Can:** Same as Super Owner (manage all feedlots, users, API keys)
- **Route:** Top-level (`@admin_access_required`)
- **Session:** No `feedlot_ids` restriction
- **Data Access:** ALL feedlots

### Business Owner
- **Can:** Manage their assigned feedlot(s), manage feedlot users, view office data
- **Route:** Top-level (shows only assigned feedlots) + Feedlot (their feedlots only)
- **Session:** `session['feedlot_ids']` = list of their feedlot ObjectIds
- **Data Access:** ONLY their assigned feedlot(s)

### Business Admin
- **Can:** Same as Business Owner
- **Route:** Top-level (shows only assigned feedlots) + Feedlot (their feedlots only)
- **Session:** `session['feedlot_ids']` = list of their feedlot ObjectIds
- **Data Access:** ONLY their assigned feedlot(s)

### Regular User
- **Can:** View/manage cattle and batches for their assigned feedlot only
- **Route:** Feedlot only (their single feedlot)
- **Session:** `session['feedlot_id']` = single ObjectId
- **Data Access:** ONLY their assigned feedlot

---

## Login Flow

**Auth Route:** `/auth/login` (same for all user types)

```python
# After authentication:
if user_type in ['super_owner', 'super_admin']:
    session['user_id'] = user._id
    session['user_type'] = user_type
    # NO feedlot restriction
    redirect → /dashboard (top_level.dashboard)

elif user_type in ['business_owner', 'business_admin']:
    session['user_id'] = user._id
    session['user_type'] = user_type
    session['feedlot_ids'] = user.feedlot_ids  # List of ObjectIds
    redirect → /dashboard (top_level.dashboard)

elif user_type == 'user':
    session['user_id'] = user._id
    session['user_type'] = user_type
    session['feedlot_id'] = user.feedlot_id  # Single ObjectId
    redirect → /feedlot/<feedlot_id>/dashboard
```

---

## Route Protection

### Top-Level Routes
```python
@top_level_bp.route('/dashboard')
@login_required
@admin_access_required  # Only: super_owner, super_admin, business_owner, business_admin
def dashboard():
    user_type = session.get('user_type')

    if user_type in ['business_owner', 'business_admin']:
        # Show only assigned feedlots
        feedlot_ids = session.get('feedlot_ids', [])
        feedlots = Feedlot.find_by_ids(feedlot_ids)
    else:
        # Show ALL feedlots
        feedlots = Feedlot.find_all()
```

### Feedlot Routes
```python
@feedlot_bp.route('/feedlot/<feedlot_id>/dashboard')
@login_required
@feedlot_access_required()  # Checks if user can access this feedlot_id
def dashboard(feedlot_id):
    # feedlot_access_required() verifies:
    # - Super users: can access ANY feedlot_id
    # - Business users: feedlot_id in session['feedlot_ids']
    # - Regular users: feedlot_id == session['feedlot_id']
```

---

## Office Data Integration Points

### Where Office Data Is Displayed

The adapter should be integrated at these points:

#### 1. **Feedlot Dashboard** (`feedlot_routes.py` line 23-41)
```python
@feedlot_bp.route('/feedlot/<feedlot_id>/dashboard')
def dashboard(feedlot_id):
    feedlot = Feedlot.find_by_id(feedlot_id)
    statistics = Feedlot.get_statistics(feedlot_id)
    recent_batches = Batch.find_by_feedlot(feedlot_id)  # ← Uses adapter
    return render_template('feedlot/dashboard.html', ...)
```

**Action:** `Batch.find_by_feedlot()` already updated to use adapter ✓

#### 2. **Batch List** (`feedlot_routes.py`)
```python
@feedlot_bp.route('/feedlot/<feedlot_id>/batches')
def list_batches(feedlot_id):
    batches = Batch.find_by_feedlot(feedlot_id)  # ← Uses adapter
    return render_template('feedlot/batches/list.html', ...)
```

**Action:** Already supported ✓

#### 3. **Batch Details** (`feedlot_routes.py`)
```python
@feedlot_bp.route('/feedlot/<feedlot_id>/batches/<batch_id>/view')
def view_batch(feedlot_id, batch_id):
    batch = Batch.find_by_id(batch_id)  # ← Uses adapter
    cattle = Cattle.find_by_batch(batch_id)  # ← Uses adapter
    return render_template('feedlot/batches/view.html', ...)
```

**Action:** Already supported ✓

#### 4. **Cattle List** (`feedlot_routes.py`)
```python
@feedlot_bp.route('/feedlot/<feedlot_id>/cattle')
def list_cattle(feedlot_id):
    cattle = Cattle.find_by_feedlot(feedlot_id)  # ← Need to check
    return render_template('feedlot/cattle/list.html', ...)
```

**Action:** Need to verify/update `Cattle.find_by_feedlot()` for office support

#### 5. **Top-Level Dashboard** (`top_level_routes.py` line 13-78)
```python
def dashboard():
    user_type = session.get('user_type')

    if user_type in ['business_owner', 'business_admin']:
        feedlots = Feedlot.find_by_ids(user_feedlot_ids)
    else:
        feedlots = Feedlot.find_all()

    # Statistics across all feedlots
    total_cattle = db.cattle.count_documents({'feedlot_id': {'$in': feedlot_ids}})
    # ← Should include office livestock counts
```

**Action:** Need to update statistics calculation to include office livestock

---

## Implementation Checklist

### Phase 1: Model Updates (In Progress)
- [x] Create office adapter
- [x] Update `Batch.find_by_feedlot()`
- [x] Update `Batch.find_by_id()`
- [x] Update `Cattle.find_by_batch()`
- [x] Update `Cattle.find_by_id()`
- [ ] Update `Cattle.find_by_feedlot()` - office support
- [ ] Update statistics calculations - include office data

### Phase 2: Route Integration
- [ ] Verify feedlot dashboard shows office batches
- [ ] Verify batch view shows office cattle
- [ ] Verify top-level dashboard aggregates office data
- [ ] Test access control (business owner sees only their feedlot)
- [ ] Test access control (super admin sees all feedlots)

### Phase 3: Testing
- [ ] Create test office data in MongoDB
- [ ] Login as business owner → see only their feedlot's office data
- [ ] Login as super admin → see all feedlots' office data
- [ ] Verify dashboard statistics include office livestock
- [ ] Test feedlot/batch/cattle views display office data

### Phase 4: Documentation
- [ ] Update .claude.md with office integration info
- [ ] Document how office data flows to SAAS dashboard
- [ ] Document feedlot_code mapping
- [ ] Create troubleshooting guide

---

## Code Examples

### Example 1: Business Owner Viewing Their Feedlot
```
User: Alice (business_owner)
session['feedlot_ids'] = ['507f1f77bcf86cd799439011']  # Feedlot001 ObjectId

GET /feedlot/507f1f77bcf86cd799439011/dashboard
  ↓ @feedlot_access_required() checks:
    - session['user_type'] = 'business_owner'
    - session['feedlot_ids'] contains '507f1f77bcf86cd799439011'
    - ✓ Access granted

  ↓ Get feedlot
    feedlot = Feedlot.find_by_id('507f1f77bcf86cd799439011')
    feedlot.feedlot_code = 'FEEDLOT001'

  ↓ Get batches (using adapter)
    batches = Batch.find_by_feedlot('507f1f77bcf86cd799439011')
    ↓ adapter.get_office_batches_all()
      → MongoDB query on 'batches' collection
      → Filters to match FEEDLOT001 feedlot_code
      → Returns office batches transformed to SAAS format

  ↓ Render dashboard with office batches
    {{ batch.batch_number }}  (mapped from batch_name)
    {{ batch.funder }}
    {{ batch.lot }}
```

### Example 2: Super Admin Viewing All Feedlots
```
User: Admin (super_admin)
session['feedlot_ids'] = undefined  # No restriction

GET /dashboard
  ↓ @admin_access_required checks:
    - session['user_type'] = 'super_admin'
    - ✓ Access granted

  ↓ Get all feedlots
    feedlots = Feedlot.find_all()
    → Returns: [feedlot001, feedlot002, feedlot003, ...]

  ↓ Calculate statistics
    for each feedlot:
      - get its feedlot_code
      - query office batches for that code
      - count office livestock
      → Aggregates across all office Pis

  ↓ Display dashboard with totals:
    total_feedlots: 3
    total_batches: 15 (includes office synced batches)
    total_cattle: 342 (includes office synced livestock)
```

---

## Testing Scenarios

### Scenario 1: Business Owner Access Control
```
Setup:
  - Create feedlot001 (code: FEEDLOT001)
  - Create feedlot002 (code: FEEDLOT002)
  - Create business_owner Alice, assign to feedlot001
  - Sync office data to MongoDB for both feedlots

Test:
  1. Login as Alice (business_owner)
  2. Should see only feedlot001 in dashboard
  3. Click feedlot001/dashboard
     - Should show batches from office FEEDLOT001
     - Should NOT show batches from office FEEDLOT002
  4. Try to access /feedlot/<feedlot002_id>/dashboard
     - Should be denied (403 or redirected)
```

### Scenario 2: Super Admin Access Control
```
Setup:
  - Same as scenario 1

Test:
  1. Login as Super Admin
  2. Should see feedlot001 AND feedlot002 in dashboard
  3. Click feedlot001/dashboard
     - Should show batches from office FEEDLOT001
  4. Go back, click feedlot002/dashboard
     - Should show batches from office FEEDLOT002
  5. Dashboard statistics should aggregate:
     - All batches from both feedlots
     - All cattle from both feedlots
```

---

## Files to Update Next

1. **`saas/app/models/cattle.py`**
   - Update `find_by_feedlot()` to support office data
   - Update statistics methods

2. **`saas/app/models/feedlot.py`**
   - Update `get_statistics()` to include office livestock counts

3. **`saas/app/routes/feedlot_routes.py`**
   - May need to verify cattle list queries work with adapter

4. **`saas/app/routes/top_level_routes.py`**
   - Update dashboard statistics to aggregate office data

5. **`.claude.md`**
   - Add office integration information
   - Document the two routes and user flows

---

**Current Status:** Route analysis complete, ready for model updates
**Last Updated:** 2025-11-07
