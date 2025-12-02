# Office API Payload Comparison

This document compares the payloads sent from the Office application with what the SaaS API endpoints expect.

## Summary of Issues

| Endpoint | Issue | Severity | Status |
|----------|-------|----------|--------|
| `/api/v1/feedlot/induction-events` | API requires `batch_id` but office only sends `batch_name` | **CRITICAL** | Needs Fix |
| `/api/v1/feedlot/checkin-events` | Office defaults `weight_kg` to 0, but API requires `weight_kg > 0` | **HIGH** | Known Issue |
| `/api/v1/feedlot/batches` | Office sends `id` field (not used by API) | Low | Expected |
| `/api/v1/feedlot/pairing-events` | No issues found | - | OK |
| `/api/v1/feedlot/repair-events` | No issues found | - | OK |

---

## Detailed Comparison

### 1. Sync Batches

**Endpoint**: `POST /api/v1/feedlot/batches`

#### Office Payload
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "name": "Batch A - Oct 30",
      "funder": "Funding Source",
      "notes": "Additional notes",
      "created_at": "2024-10-30T10:00:00"
    }
  ]
}
```

#### API Expectations
- **Required**: `name` (mapped to `batch_number`)
- **Optional**: `funder`, `notes`, `created_at` (mapped to `induction_date`)
- **Optional**: `pen`, `pen_location` (for pen creation/linking)
- **Not Used**: `id` (sent by office but ignored by API)

#### Status: ✅ COMPATIBLE
- All required fields are present
- Optional fields are handled correctly
- The `id` field is ignored (as documented)

---

### 2. Sync Induction Events

**Endpoint**: `POST /api/v1/feedlot/induction-events`

#### Office Payload
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "event_id": "hxbind000001",
      "livestock_id": 123,
      "batch_name": "Batch A - Oct 30",
      "timestamp": "2024-10-30T10:00:00"
    }
  ]
}
```

#### API Expectations (from code analysis)
Looking at `app/routes/api_routes.py` lines 375-398:

1. **Line 375**: Checks for `livestock_id` ✅ (office sends this)
2. **Line 376**: Gets `batch_id` from payload (office does NOT send this)
3. **Line 383-386**: **REQUIRES `batch_id`** - This will cause the request to fail!
4. **Line 392**: Checks for `batch_name` ✅ (office sends this)
5. **Line 393-398**: Uses `batch_name` to find SaaS batch ✅

#### The Problem
The API code has a logic error:
- It requires `batch_id` at line 383-386, but office doesn't send it
- It then uses `batch_name` at line 392-398, which office does send
- The code will fail before it reaches the `batch_name` check

#### Code Reference
```375:398:app/routes/api_routes.py
                livestock_id = event_item.get('livestock_id')
                batch_id_office = event_item.get('batch_id')  # Office app batch ID
                
                if not livestock_id:
                    errors.append(f'Record {records_processed}: livestock_id is required')
                    records_skipped += 1
                    continue
                
                if not batch_id_office:
                    errors.append(f'Record {records_processed}: batch_id is required')
                    records_skipped += 1
                    continue
                
                # Find batch in SaaS system
                # We need to map office batch_id to SaaS batch
                # For now, we'll need the office app to send batch name or we'll need a mapping
                # Let's assume the office app sends batch_name or we look it up
                batch_name = event_item.get('batch_name')
                if not batch_name:
                    # Try to find batch by office batch_id if we have a mapping
                    # For now, skip if no batch_name
                    errors.append(f'Record {records_processed}: batch_name is required to map to SaaS batch')
                    records_skipped += 1
                    continue
```

#### Status: ❌ **INCOMPATIBLE - CRITICAL ISSUE**
- Office sends: `batch_name` ✅
- Office does NOT send: `batch_id` ❌
- API requires: `batch_id` (line 383-386) ❌
- API then uses: `batch_name` (line 392-398) ✅

**Fix Required**: Remove the `batch_id` requirement check (lines 383-386) since the API actually uses `batch_name` to find the batch.

---

### 3. Sync Pairing Events

**Endpoint**: `POST /api/v1/feedlot/pairing-events`

#### Office Payload
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "event_id": "hxbind000002",
      "livestock_id": 123,
      "lf_id": "LF123456",
      "epc": "EPC789012",
      "weight_kg": 250.5,
      "timestamp": "2024-10-30T10:00:00"
    }
  ]
}
```

#### API Expectations (from code analysis)
Looking at `app/routes/api_routes.py` lines 547-580:

- **Required**: `livestock_id` ✅
- **Optional**: `lf_id`, `epc`, `weight_kg` ✅
- All fields are handled correctly

#### Status: ✅ COMPATIBLE
- All required fields are present
- Optional fields are handled correctly
- Weight is only added if `weight_kg > 0` (line 575)

---

### 4. Sync Checkin Events

**Endpoint**: `POST /api/v1/feedlot/checkin-events`

#### Office Payload
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "event_id": "hxbind000003",
      "livestock_id": 123,
      "weight_kg": 275.3,
      "timestamp": "2024-10-30T10:00:00"
    }
  ]
}
```

#### API Expectations (from code analysis)
Looking at `app/routes/api_routes.py` lines 655-692:

- **Required**: `livestock_id` ✅
- **Required**: `weight_kg` (must be > 0) ⚠️
- **Line 663-666**: Checks if `weight_kg` is None
- **Line 668-677**: Validates `weight_kg > 0`

#### The Problem
According to the office documentation:
- Office defaults `weight_kg` to `0` if not present in `parsed_data`
- API requires `weight_kg > 0` (line 670-673)
- Records with `weight_kg = 0` will be skipped with error: "weight_kg must be greater than 0"

#### Code Reference
```663:677:app/routes/api_routes.py
                if weight_kg is None:
                    errors.append(f'Record {records_processed}: weight_kg is required')
                    records_skipped += 1
                    continue
                
                try:
                    weight_float = float(weight_kg)
                    if weight_float <= 0:
                        errors.append(f'Record {records_processed}: weight_kg must be greater than 0')
                        records_skipped += 1
                        continue
                except (ValueError, TypeError):
                    errors.append(f'Record {records_processed}: Invalid weight_kg value')
                    records_skipped += 1
                    continue
```

#### Status: ⚠️ **PARTIALLY COMPATIBLE - KNOWN ISSUE**
- Office sends `weight_kg` ✅
- Office defaults to `0` if missing ⚠️
- API requires `weight_kg > 0` ⚠️
- Records with `weight_kg = 0` will be skipped (expected behavior per documentation)

**Note**: This is documented as expected behavior - invalid data should be skipped.

---

### 5. Sync Repair Events

**Endpoint**: `POST /api/v1/feedlot/repair-events`

#### Office Payload
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "event_id": "hxbind000004",
      "livestock_id": 123,
      "old_lf_id": "LF123456",
      "new_lf_id": "LF654321",
      "old_epc": "EPC789012",
      "new_epc": "EPC210987",
      "reason": "LF tag lost, UHF tag damaged",
      "timestamp": "2024-10-30T09:00:00"
    }
  ]
}
```

#### API Expectations (from code analysis)
Looking at `app/routes/api_routes.py` lines 767-803:

- **Required**: `livestock_id` ✅
- **Required**: At least one of `new_lf_id` or `new_epc` ✅
- **Optional**: `old_lf_id`, `old_epc`, `reason` ✅

#### Status: ✅ COMPATIBLE
- All required fields are present
- Validation logic matches office payload structure
- At least one new tag is required (line 780-783), which office should provide

---

## Recommended Fixes

### Fix 1: Remove `batch_id` Requirement from Induction Events (CRITICAL)

**File**: `app/routes/api_routes.py`

**Current Code** (lines 383-386):
```python
if not batch_id_office:
    errors.append(f'Record {records_processed}: batch_id is required')
    records_skipped += 1
    continue
```

**Recommended Fix**:
Remove this check entirely since:
1. Office doesn't send `batch_id`
2. The API uses `batch_name` to find the batch anyway
3. The `batch_name` check at line 392-398 is sufficient

**Updated Code**:
```python
# Remove lines 376, 383-386
# Keep only the batch_name check (lines 392-398)
batch_name = event_item.get('batch_name')
if not batch_name:
    errors.append(f'Record {records_processed}: batch_name is required to map to SaaS batch')
    records_skipped += 1
    continue
```

---

## Testing Recommendations

After applying the fix, test the following scenarios:

1. **Induction Events**:
   - ✅ Send payload with `batch_name` only (no `batch_id`)
   - ✅ Verify cattle records are created successfully
   - ✅ Verify batch lookup works by name

2. **Checkin Events**:
   - ✅ Send payload with `weight_kg = 0` (should be skipped)
   - ✅ Send payload with `weight_kg > 0` (should succeed)
   - ✅ Send payload with missing `weight_kg` (should error)

3. **All Endpoints**:
   - ✅ Verify `feedlot_code` validation works
   - ✅ Verify API key authentication works
   - ✅ Verify error messages are clear and helpful

---

## Conclusion

The main issue is in the **Induction Events** endpoint where the API incorrectly requires `batch_id` which the office application doesn't send. The API should only require `batch_name`, which it already uses to find the batch. This is a critical bug that will cause all induction event syncs to fail.

The checkin events issue with `weight_kg = 0` is expected behavior (invalid data should be skipped) and is already documented.

