# Office App API Documentation

## Overview

The HerdLinx SaaS Office App API allows office applications (using SQLite database structure) to sync their data to the SaaS MongoDB system. Each office app is identified by a unique `feedlot_code` that maps to a feedlot in the SaaS system.

### Key Features

- **API Key Authentication**: Secure authentication using API keys
- **Bulk Operations**: Process multiple records in a single request
- **Idempotency**: Safe to retry requests without creating duplicates
- **Comprehensive Error Reporting**: Detailed error messages for troubleshooting
- **Data Mapping**: Automatic mapping from office app structure to SaaS structure

---

## Authentication

All API endpoints require authentication using an API key.

### Obtaining an API Key

API keys can only be generated through the web UI. This ensures secure key management and proper access control.

#### Generating an API Key

Top-level administrators (Super Owner, Super Admin) can generate API keys through the Settings page:

1. Navigate to **Settings** → **API Keys** from the hamburger menu
2. Select the feedlot for which you want to generate an API key
3. Click **Generate New Key**
4. Optionally add a description to help identify the key later
5. **Important**: Copy and save the generated API key immediately - it will only be shown once

The web UI provides:
- Visual management of all API keys per feedlot
- Key status (Active/Inactive) indicators
- Creation date and last used timestamp
- Ability to activate, deactivate, or delete keys
- One-time key display with copy-to-clipboard functionality
- Secure key generation with proper access control

**Important**: The API key is only shown once during generation. Save it securely.

### Using API Keys

API keys can be provided in two ways:

1. **HTTP Header** (Recommended):
   ```
   X-API-Key: your_api_key_here
   ```

2. **Query Parameter**:
   ```
   ?api_key=your_api_key_here
   ```

### Security Notes

- API keys are hashed using SHA-256 before storage
- Keys are associated with a specific feedlot (identified by `feedlot_code`)
- Keys can be activated, deactivated, or deleted through the Settings UI
- Each API key usage is logged with timestamp (`last_used_at`)
- Keys can only be viewed once during generation - they are never stored in plain text
- Only top-level administrators (Super Owner, Super Admin) can manage API keys

---

## Base URL

All API endpoints are prefixed with `/api/v1/feedlot`:

```
https://your-domain.com/api/v1/feedlot
```

---

## Common Request Format

All endpoints accept JSON request bodies with the following structure:

```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      // Endpoint-specific data structure
    }
  ]
}
```

### Request Parameters

- **feedlot_code** (required): The feedlot code assigned to your office app. Must match the feedlot associated with your API key.
- **data** (required): Array of records to process. Each record follows the endpoint-specific schema.

---

## Common Response Format

All endpoints return JSON responses with the following structure:

```json
{
  "success": true,
  "message": "Descriptive message",
  "records_processed": 10,
  "records_created": 8,
  "records_updated": 2,
  "records_skipped": 0,
  "errors": []
}
```

### Response Fields

- **success**: Boolean indicating if the request was successful
- **message**: Human-readable message describing the result
- **records_processed**: Total number of records processed
- **records_created**: Number of new records created
- **records_updated**: Number of existing records updated
- **records_skipped**: Number of records skipped due to errors
- **errors**: Array of error messages for failed records

---

## Endpoints

### 1. Sync Livestock (Current State)

**Endpoint**: `POST /api/v1/feedlot/livestock`

**Description**: Syncs current livestock state, primarily updating tag information.

**Request Body**:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 123,
      "induction_event_id": 45,
      "current_lf_id": "LF123456",
      "current_epc": "EPC789012",
      "metadata": "Additional metadata",
      "created_at": "2024-10-30T10:00:00Z",
      "updated_at": "2024-10-30T10:00:00Z"
    }
  ]
}
```

**Field Mapping**:
- `id` → Used to find existing cattle (stored as `cattle_id`)
- `current_lf_id` → `lf_tag`
- `current_epc` → `uhf_tag`

**Response**:
```json
{
  "success": true,
  "message": "Processed 1 livestock records",
  "records_processed": 1,
  "records_created": 0,
  "records_updated": 1,
  "records_skipped": 0,
  "errors": []
}
```

**Notes**:
- Livestock records must be created via `induction-events` endpoint first
- This endpoint only updates existing cattle records
- Tags are updated if they differ from current values
- If livestock ID is not found, the record is skipped with an error message

---

### 2. Sync Induction Events

**Endpoint**: `POST /api/v1/feedlot/induction-events`

**Description**: Creates cattle records when animals are inducted into the system. **Now also creates/updates batches automatically from the event data.**

**Request Body**:
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

**Field Mapping**:

**Batch Fields** (used to create/update batches):
- `batch_name` → `batch_number` (required) - Creates or finds existing batch
- `funder` → `funder` (optional) - Batch funder information
- `notes` → `notes` (optional) - Batch notes
- `timestamp` → `induction_date` - Used for batch induction date
- `pen` → Creates/updates pen with `pen_number` (optional)
- `pen_location` → Pen `description` (optional)

**Cattle Fields**:
- `livestock_id` → Used to create cattle record (stored as `cattle_id`) (required)
- `sex` → `sex` (optional, defaults to "Unknown")
- `weight` → `weight` (optional, defaults to 0.0)
- `lf_id` → `lf_tag` (optional)
- `epc` → `uhf_tag` (optional)
- `notes` → `notes` (optional)
- `timestamp` → `induction_date` (optional, defaults to current time)

**Response**:
```json
{
  "success": true,
  "message": "Processed 1 induction event records",
  "records_processed": 1,
  "records_created": 1,
  "records_updated": 0,
  "records_skipped": 0,
  "batches_created": 1,
  "batches_updated": 0,
  "errors": []
}
```

**Notes**:
- **Batch Creation**: Batches are automatically created from the `batch_name` field if they don't exist. If a batch with the same name exists, it may be updated with new information (funder, notes, pen).
- **Pen Creation**: Pens are automatically created or updated when `pen` field is provided:
  - If a pen with the same `pen_number` exists, it will be updated (description updated if `pen_location` is provided)
  - If no pen exists, a new pen will be created with:
    - `pen_number`: Value from `pen` field
    - `description`: Value from `pen_location` field (or default "Pen {pen_number}" if not provided)
    - `capacity`: Default capacity of 100 (can be updated later via web UI)
  - The batch will be linked to the pen via `pen_id`
- **Cattle Creation**: Cattle records are created with values from the event:
  - If `sex` is provided, it's used; otherwise defaults to "Unknown"
  - If `weight` is provided and valid (> 0), it's used; otherwise defaults to 0.0
  - If `lf_id` or `epc` are provided, tags are set
  - `health_status` defaults to "Healthy"
- **Pen Assignment**: Cattle are automatically assigned to the pen from the event (if `pen` is provided) or from the batch's pen (if batch has a `pen_id`).
- **Timestamp Format**: Supports formats like "2025-12-04 14:18:11.265273", ISO format with 'T', or "YYYY-MM-DD" format.
- If cattle already exists, the record is updated with new information (sex, weight, tags, pen, notes) if provided.
- The `funder` field value "None" (case-insensitive) is treated as empty string.

---

### 3. Sync Pairing Events

**Endpoint**: `POST /api/v1/feedlot/pairing-events`

**Description**: Records when LF and UHF tags are paired together.

**Request Body**:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "livestock_id": 123,
      "lf_id": "LF123456",
      "epc": "EPC789012",
      "weight_kg": 250.5,
      "timestamp": "2024-10-30T10:00:00Z"
    }
  ]
}
```

**Field Mapping**:
- `livestock_id` → Used to find cattle record
- `lf_id` → `lf_tag`
- `epc` → `uhf_tag`
- `weight_kg` → Added to weight history (if provided and > 0)

**Response**:
```json
{
  "success": true,
  "message": "Processed 1 pairing event records",
  "records_processed": 1,
  "records_created": 0,
  "records_updated": 1,
  "records_skipped": 0,
  "errors": []
}
```

**Notes**:
- Updates the tag pair for the cattle record
- If `weight_kg` is provided and valid, it's added to the weight history
- Previous tag pairs are preserved in `tag_pair_history`

---

### 4. Sync Check-in Events

**Endpoint**: `POST /api/v1/feedlot/checkin-events`

**Description**: Records weight measurements during check-in operations.

**Request Body**:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "livestock_id": 123,
      "lf_id": "LF123456",
      "epc": "EPC789012",
      "weight_kg": 275.3,
      "timestamp": "2024-11-15T14:30:00Z"
    }
  ]
}
```

**Field Mapping**:
- `livestock_id` → Used to find cattle record
- `weight_kg` → Added to weight history and updates current weight

**Response**:
```json
{
  "success": true,
  "message": "Processed 1 check-in event records",
  "records_processed": 1,
  "records_created": 1,
  "records_updated": 0,
  "records_skipped": 0,
  "errors": []
}
```

**Notes**:
- `weight_kg` is required and must be greater than 0
- Each check-in event creates a new entry in the weight history
- The current weight field is updated with the latest measurement
- Multiple check-ins per animal are supported

---

### 5. Sync Repair Events

**Endpoint**: `POST /api/v1/feedlot/repair-events`

**Description**: Records when tags are replaced due to damage or loss.

**Request Body**:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "livestock_id": 123,
      "old_lf_id": "LF123456",
      "new_lf_id": "LF654321",
      "old_epc": "EPC789012",
      "new_epc": "EPC210987",
      "reason": "LF tag lost, UHF tag damaged",
      "timestamp": "2024-11-20T09:00:00Z"
    }
  ]
}
```

**Field Mapping**:
- `livestock_id` → Used to find cattle record
- `old_lf_id` / `new_lf_id` → LF tag replacement
- `old_epc` / `new_epc` → UHF tag replacement
- `reason` → Added to cattle notes

**Response**:
```json
{
  "success": true,
  "message": "Processed 1 repair event records",
  "records_processed": 1,
  "records_created": 0,
  "records_updated": 1,
  "records_skipped": 0,
  "errors": []
}
```

**Notes**:
- At least one new tag (`new_lf_id` or `new_epc`) is required
- If only one tag type is being repaired, the other tag remains unchanged
- Repair reason is appended to the cattle notes
- Previous tag pairs are preserved in `tag_pair_history`

---

## Error Handling

### HTTP Status Codes

- **200 OK**: Request processed successfully (may include errors for individual records)
- **400 Bad Request**: Invalid request format or missing required fields
- **401 Unauthorized**: Missing or invalid API key
- **403 Forbidden**: `feedlot_code` does not match API key's feedlot
- **404 Not Found**: Resource not found (e.g., feedlot, batch)
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "success": false,
  "message": "Error description"
}
```

### Common Errors

1. **Missing API Key**:
   ```json
   {
     "success": false,
     "message": "API key is required. Provide it in X-API-Key header or api_key query parameter."
   }
   ```

2. **Invalid API Key**:
   ```json
   {
     "success": false,
     "message": "Invalid or inactive API key."
   }
   ```

3. **Feedlot Code Mismatch**:
   ```json
   {
     "success": false,
     "message": "feedlot_code does not match the API key's feedlot"
   }
   ```

4. **Missing Required Fields**:
   ```json
   {
     "success": false,
     "message": "feedlot_code is required in request body"
   }
   ```

### Record-Level Errors

Individual record errors are included in the `errors` array:

```json
{
  "success": true,
  "records_processed": 5,
  "records_created": 3,
  "records_updated": 1,
  "records_skipped": 1,
  "errors": [
    "Record 3: Batch name is required"
  ]
}
```

---

## Data Flow Recommendations

### Recommended Sync Order

1. **Induction Events**: Create cattle records when animals are inducted (batches are automatically created from induction events)
2. **Pairing Events**: Pair tags and set initial weights
3. **Livestock**: Update current state (optional, for reconciliation)
4. **Check-in Events**: Add weight measurements over time
5. **Repair Events**: Handle tag replacements as needed

### Idempotency

All endpoints are designed to be idempotent:
- **Induction Events**: Creates/updates batches automatically from event data; checks if cattle exists before creating
- **Pairing/Repair Events**: Updates existing cattle records
- **Check-in Events**: Always creates new weight history entries (multiple entries are expected)

### Bulk Operations

- Process multiple records in a single request for efficiency
- Maximum recommended batch size: 100-500 records per request
- For larger datasets, split into multiple requests

---

## Example Integration

### Python Example

```python
import requests
import json

API_BASE_URL = "https://your-domain.com/api/v1/feedlot"
API_KEY = "your_api_key_here"
FEEDLOT_CODE = "FEEDLOT001"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Sync induction events (batches are automatically created)
induction_data = {
    "feedlot_code": FEEDLOT_CODE,
    "data": [
        {
            "id": 1,
            "event_id": "hxbind000001",
            "livestock_id": 3,
            "funder": "Funding Source",
            "pen": "6",
            "pen_location": "North Section",
            "sex": "Steer",
            "batch_name": "BATCH_2025-12-04_7325",
            "lf_id": "124000224161433",
            "epc": "0900000000000003",
            "weight": 250.5,
            "timestamp": "2025-12-04 14:18:11.265273"
        }
    ]
}

response = requests.post(
    f"{API_BASE_URL}/induction-events",
    headers=headers,
    json=induction_data
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Cattle Created: {result['records_created']}")
print(f"Batches Created: {result['batches_created']}")
print(f"Errors: {result['errors']}")
```

### cURL Example

```bash
curl -X POST https://your-domain.com/api/v1/feedlot/induction-events \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "feedlot_code": "jfmurray",
    "data": [
      {
        "id": 7,
        "event_id": "hxbind000001",
        "livestock_id": 3,
        "funder": "Funding Source",
        "pen": "6",
        "pen_location": "North Section",
        "sex": "Steer",
        "batch_name": "BATCH_2025-12-04_7325",
        "lf_id": "124000224161433",
        "epc": "0900000000000003",
        "weight": 250.5,
        "timestamp": "2025-12-04 14:18:11.265273"
      }
    ]
  }'
```

---

## Date/Time Format

All timestamps should be provided in ISO 8601 format:

- **Full format**: `2024-10-30T10:00:00Z` or `2024-10-30T10:00:00+00:00`
- **Date only**: `2024-10-30` (will be parsed as midnight UTC)

The API accepts both formats and will parse them accordingly.

---

## Rate Limiting

Currently, there are no rate limits enforced. However, for optimal performance:

- Batch requests to 100-500 records per request
- Add delays between requests if processing large datasets
- Monitor response times and adjust accordingly

---

## Support and Troubleshooting

### Common Issues

1. **"feedlot_code does not match"**: Ensure the `feedlot_code` in your request matches the feedlot associated with your API key.

2. **"Livestock ID not found"**: Make sure to sync `induction-events` before syncing other livestock-related endpoints.

3. **"Batch not found"**: This should no longer occur as batches are automatically created from `induction-events`. If you see this error, check that `batch_name` is provided in the induction event data.

4. **"Invalid weight_kg value"**: Weight must be a positive number greater than 0.

### Debugging Tips

- Check the `errors` array in responses for detailed error messages
- Verify API key is active and associated with the correct feedlot
- Ensure `feedlot_code` matches exactly (case-insensitive, but stored as lowercase)
- Validate data types match expected formats (numbers, strings, dates)

---

## Related Documentation

- **Office Database Structure**: See `OFFICE_DATABASE_STRUCTURE.md` for detailed information about the office app database schema
- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md` for deployment instructions
- **SaaS System**: Refer to main application documentation for SaaS system structure

---

## Changelog

### Version 1.1 (Current)
- Added web UI for API key management (Settings → API Keys)
- Enhanced API key management with visual interface
- Added key status tracking (Active/Inactive)
- Added last used timestamp tracking
- Improved key generation workflow with one-time display

### Version 1.0 (Initial Release)
- All 6 sync endpoints implemented
- API key authentication
- Bulk operation support
- Comprehensive error handling
- Idempotent operations

