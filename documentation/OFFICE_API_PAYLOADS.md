# Office API Payloads Documentation

This document describes the exact payload structures that the Office application sends to the SaaS API.

## Overview

The Office application syncs data to the SaaS system via HTTP POST requests with JSON payloads. All requests are authenticated using an API key in the `X-API-Key` header.

**Base URL**: Configured via `API_URL` in `config.env` (e.g., `https://api.herdlinx.com`)

**Authentication**: API key provided in `X-API-Key` header

**Content-Type**: `application/json`

---

## Common Request Structure

All API requests follow this structure:

```json
{
  "feedlot_code": "FEEDLOT_CODE",
  "data": [
    // Array of records (endpoint-specific)
  ]
}
```

**Common Fields**:
- `feedlot_code` (string, required): The feedlot code configured in `OFFICE_FEEDLOT_CODE`
- `data` (array, required): Array of records to sync

**Request Headers**:
```
X-API-Key: <api_key_from_config>
Content-Type: application/json
```

---

## Endpoints and Payloads

### 1. ~~Sync Batches~~ (REMOVED)

**Endpoint**: ~~`POST /api/v1/feedlot/batches`~~ **REMOVED**

**Status**: ✅ **ENDPOINT REMOVED**

**Note**: Batches are now automatically created from the `induction-events` endpoint. The batch information (name, funder, notes, pen, pen_location) is included in each induction event payload, and batches are created/updated automatically when processing induction events.

**Code Reference**: Batch creation logic is now in `app/routes/api_routes.py` in the `sync_induction_events()` function.

---

### 2. Sync Induction Events

**Endpoint**: `POST /api/v1/feedlot/induction-events`

**Description**: Syncs induction events that create cattle records in SaaS. **Now also creates/updates batches automatically from event data.**

**Payload Structure**:

```json
{
  "feedlot_code": "jfmurray",
  "data": [
    {
      "id": 7,
      "event_id": "hxbind000001",
      "livestock_id": 3,
      "funder": "None",
      "lot": "6",
      "pen": "6",
      "lot_group": "6",
      "pen_location": "6",
      "sex": "Steer",
      "tag_color": "",
      "visual_id": "",
      "notes": "",
      "batch_name": "BATCH_2025-12-04_7325",
      "lf_id": "124000224161433",
      "epc": "0900000000000003",
      "weight": 0,
      "timestamp": "2025-12-04 14:18:11.265273"
    }
  ]
}
```

**Field Descriptions**:

| Field | Type | Required | Processed | Description | Source |
|-------|------|----------|-----------|-------------|--------|
| `livestock_id` | integer | Yes | Yes | Office livestock ID (used as cattle_id) | `events.livestock_id` |
| `batch_name` | string | Yes | Yes | Batch name (creates/finds batch) | `events.parsed_data.batch` |
| `id` | integer | No | No | Office database event ID (accepted but not used) | `events.id` |
| `event_id` | string | No | Yes | Unique event identifier (used in audit logs) | `events.event_id` |
| `timestamp` | string | No | Yes | Event timestamp (or use `created_at`) | `events.received_at` |
| `created_at` | string | No | Yes | Alternative timestamp field | `events.created_at` |
| `funder` | string | No | Yes | Batch funder (empty if "None") | `events.parsed_data.funder` |
| `pen` | string | No | Yes | Pen number (creates/updates pen) | `events.parsed_data.pen` |
| `pen_location` | string | No | Yes | Pen location/description | `events.parsed_data.pen_location` |
| `sex` | string | No | Yes | Cattle sex (defaults to "Unknown") | `events.parsed_data.sex` |
| `lf_id` | string | No | Yes | Low frequency tag ID | `events.parsed_data.lf_id` |
| `epc` | string | No | Yes | UHF/EPC tag ID | `events.parsed_data.epc` |
| `weight` | float | No | Yes | Initial weight (must be >= 0) | `events.parsed_data.weight` |
| `notes` | string | No | Yes | Notes (for batch or cattle) | `events.parsed_data.notes` |
| `lot` | string | No | Yes | Lot identifier (stored on cattle record) | `events.parsed_data.lot` |
| `lot_group` | string | No | Yes | Lot group identifier (stored on cattle record) | `events.parsed_data.lot_group` |
| `tag_color` | string | No | Yes | Tag color (mapped to `color` field on cattle record) | `events.parsed_data.tag_color` |
| `visual_id` | string | No | Yes | Visual ID (stored on cattle record) | `events.parsed_data.visual_id` |

**Notes**:
- **API Required Fields**: `livestock_id`, `batch_name` (these will cause errors if missing)
- **Timestamp Handling**: Accepts `timestamp` or `created_at` in formats: `"YYYY-MM-DD HH:MM:SS"`, ISO format with `T`, or `"YYYY-MM-DD"`. Defaults to current UTC time if missing or invalid.
- **Batch Creation**: Batches are automatically created from `batch_name` if they don't exist. Batch fields (`funder`, `notes`, `pen`, `pen_location`) are used to create/update batches.
- **Pen Creation**: Pens are automatically created/updated when `pen` field is provided. Default capacity is 100.
- **Cattle Creation**: Cattle records are created with all provided fields (`sex`, `weight`, `lf_id`, `epc`, `notes`, `tag_color`, `visual_id`, `lot`, `lot_group`). Existing cattle are matched by `livestock_id` and updated if fields differ.
- **Field Mappings**: 
  - `tag_color` → stored as `color` field on cattle record
  - `visual_id` → stored as `visual_id` field on cattle record
  - `lot` → stored as `lot` field on cattle record
  - `lot_group` → stored as `lot_group` field on cattle record
- **Unused Fields**: `id` is accepted in the payload but not processed by the API (used for office app tracking only).
- The `funder` field value "None" (case-insensitive) is treated as empty string.

**Code Reference**: `office/scripts/api_sync.py` lines 172-184, 252-286

---

### 3. Sync Pairing Events

**Endpoint**: `POST /api/v1/feedlot/pairing-events`

**Description**: Syncs pairing events that associate LF and UHF tags with livestock.

**Payload Structure**:

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

**Field Descriptions**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `id` | integer | Yes | Office database event ID | `events.id` |
| `event_id` | string | Yes | Unique event identifier | `events.event_id` |
| `livestock_id` | integer | Yes | Office livestock ID | `events.livestock_id` |
| `lf_id` | string | No | Low frequency tag ID | `events.parsed_data.lf_id` |
| `epc` | string | No | UHF/EPC tag ID | `events.parsed_data.epc` |
| `weight_kg` | float | No | Weight in kilograms | `events.parsed_data.weight_kg` |
| `timestamp` | string | Yes | Event timestamp | `events.received_at` |

**Notes**:
- Only events with `event_type = 'pairing'` and `synced_at IS NULL` are synced
- Tag and weight data extracted from `parsed_data` JSON field
- Default values: `lf_id = ''`, `epc = ''`, `weight_kg = 0` if not present in parsed_data
- Events are ordered by `received_at ASC` (oldest first)

**Code Reference**: `office/scripts/api_sync.py` lines 186-197, 288-324

---

### 4. Sync Checkin Events

**Endpoint**: `POST /api/v1/feedlot/checkin-events`

**Description**: Syncs checkin events that record weight measurements.

**Payload Structure**:

```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "event_id": "hxbind000003",
      "livestock_id": 123,
      "weight_kg": 275.3,
      "timestamp": "2024-11-15T14:30:00"
    }
  ]
}
```

**Field Descriptions**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `id` | integer | Yes | Office database event ID | `events.id` |
| `event_id` | string | Yes | Unique event identifier | `events.event_id` |
| `livestock_id` | integer | Yes | Office livestock ID | `events.livestock_id` |
| `weight_kg` | float | No | Weight in kilograms | `events.parsed_data.weight_kg` |
| `timestamp` | string | Yes | Event timestamp | `events.received_at` |

**Notes**:
- Only events with `event_type = 'checkin'` and `synced_at IS NULL` are synced
- Weight data extracted from `parsed_data` JSON field
- Default value: `weight_kg = 0` if not present in parsed_data
- Events are ordered by `received_at ASC` (oldest first)
- SaaS API requires `weight_kg > 0`, so default value of 0 may cause records to be skipped

**Code Reference**: `office/scripts/api_sync.py` lines 199-210, 326-360

---

### 5. Sync Repair Events

**Endpoint**: `POST /api/v1/feedlot/repair-events`

**Description**: Syncs repair events that record tag replacements.

**Payload Structure**:

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
      "timestamp": "2024-11-20T09:00:00"
    }
  ]
}
```

**Field Descriptions**:

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `id` | integer | Yes | Office database event ID | `events.id` |
| `event_id` | string | Yes | Unique event identifier | `events.event_id` |
| `livestock_id` | integer | Yes | Office livestock ID | `events.livestock_id` |
| `old_lf_id` | string | No | Previous LF tag ID | `events.parsed_data.old_lf_id` |
| `new_lf_id` | string | No | New LF tag ID | `events.parsed_data.new_lf_id` |
| `old_epc` | string | No | Previous UHF/EPC tag ID | `events.parsed_data.old_epc` |
| `new_epc` | string | No | New UHF/EPC tag ID | `events.parsed_data.new_epc` |
| `reason` | string | No | Repair reason/notes | `events.parsed_data.reason` |
| `timestamp` | string | Yes | Event timestamp | `events.received_at` |

**Notes**:
- Only events with `event_type = 'repair'` and `synced_at IS NULL` are synced
- Tag and reason data extracted from `parsed_data` JSON field
- Default values: empty strings for all optional fields if not present
- Events are ordered by `received_at ASC` (oldest first)
- SaaS API requires at least one new tag (`new_lf_id` or `new_epc`)

**Code Reference**: `office/scripts/api_sync.py` lines 212-223, 362-400

---

## Sync Process

### Sync Loop

The API sync engine runs in a background thread that executes every 5 seconds:

1. **Batches**: All batches are synced (no filtering by sync status)
2. **Induction Events**: Only unsynced events (`synced_at IS NULL`)
3. **Pairing Events**: Only unsynced events (`synced_at IS NULL`)
4. **Checkin Events**: Only unsynced events (`synced_at IS NULL`)
5. **Repair Events**: Only unsynced events (`synced_at IS NULL`)

### Sync Status Tracking

- **Batches**: No sync status tracking (all batches sent on each sync)
- **Events**: Marked as synced by updating `events.synced_at` timestamp after successful API response

### Batch Size

- Default limit: 100 records per endpoint per sync cycle
- Can be adjusted in code (limit parameter in `_get_unsynced_*` methods)

---

## Data Source Mapping

### Database Tables

All data is sourced from the office SQLite database (`office_receiver.db`):

- **Batches**: `batches` table
- **Events**: `events` table (filtered by `event_type`)

### Parsed Data Extraction

Event payloads extract additional fields from the `parsed_data` JSON column:

- **Induction Events**: `batch` → `batch_name`
- **Pairing Events**: `lf_id`, `epc`, `weight_kg`
- **Checkin Events**: `weight_kg`
- **Repair Events**: `old_lf_id`, `new_lf_id`, `old_epc`, `new_epc`, `reason`

---

## Known Issues and Limitations

### 1. Induction Events Missing `batch_id`

**Issue**: SaaS API requires `batch_id` field (line 328-331 in `api_routes.py`), but office only sends `batch_name`.

**Impact**: Induction events will fail with error: "batch_id is required"

**Workaround**: None currently. SaaS code should be updated to make `batch_id` optional when `batch_name` is provided.

**Status**: Needs SaaS code fix

### 2. Batches Not Filtered by Sync Status

**Issue**: All batches are sent on every sync, not just new/unsynced ones.

**Impact**: Unnecessary API calls and potential for duplicate processing.

**Status**: Design decision (batches table doesn't have `synced_at` column)

### 3. Default Weight Values

**Issue**: Checkin events default `weight_kg` to 0 if not in parsed_data, but SaaS requires `weight_kg > 0`.

**Impact**: Records with missing weight data will be skipped by SaaS.

**Status**: Expected behavior (invalid data should be skipped)

### 4. Empty String vs NULL

**Issue**: Office sends empty strings (`''`) for optional fields when database value is NULL.

**Impact**: SaaS may treat empty strings differently than NULL values.

**Status**: Expected behavior (consistent with code implementation)

---

## Example Complete Payloads

### Example 1: Full Sync Cycle

```json
// 1. Batches
POST /api/v1/feedlot/batches
{
  "feedlot_code": "JF_MURRAY",
  "data": [
    {
      "id": 1,
      "name": "LOT2024-11-07",
      "funder": "ABC Funding",
      "notes": "Initial batch",
      "created_at": "2024-11-07T08:00:00"
    }
  ]
}

// 2. Induction Events
POST /api/v1/feedlot/induction-events
{
  "feedlot_code": "JF_MURRAY",
  "data": [
    {
      "id": 1,
      "event_id": "hxbind000001",
      "livestock_id": 1,
      "batch_name": "LOT2024-11-07",
      "timestamp": "2024-11-07T08:15:00"
    }
  ]
}

// 3. Pairing Events
POST /api/v1/feedlot/pairing-events
{
  "feedlot_code": "JF_MURRAY",
  "data": [
    {
      "id": 1,
      "event_id": "hxbind000002",
      "livestock_id": 1,
      "lf_id": "LF123456789",
      "epc": "E2801160600002044310B2E2",
      "weight_kg": 250.5,
      "timestamp": "2024-11-07T08:20:00"
    }
  ]
}
```

---

## Configuration

The API sync engine is configured via `config.env`:

```bash
USE_API_SYNC=true
API_URL=https://api.herdlinx.com
API_KEY=your_api_key_here
OFFICE_FEEDLOT_CODE=JF_MURRAY
```

---

## Error Handling

### API Request Failures

- Network errors: Logged and sync continues on next cycle
- HTTP errors: Logged and sync continues on next cycle
- Timeout: 30 seconds per request

### Response Validation

- Checks for `success: true` in response before marking as synced
- Errors are logged but don't stop the sync process
- Failed records remain unsynced and will be retried on next cycle

---

## Related Documentation

- **SaaS API Documentation**: `saas/docs/documentation/API_DOCUMENTATION.md`
- **API Sync Migration Guide**: `office/docs/API_SYNC_MIGRATION_GUIDE.md`
- **Office Database Structure**: See receiver database schema

---

## Code References

- **Main Sync Engine**: `office/scripts/api_sync.py`
- **Database Access**: `office/receiver_db.py`
- **Configuration**: `office/config.env`

---

*Last Updated: Based on code analysis of `office/scripts/api_sync.py`*

