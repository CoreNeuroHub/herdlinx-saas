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

### 1. Sync Batches

**Endpoint**: `POST /api/v1/feedlot/batches`

**Description**: Syncs batch data from the office app to the SaaS system.

**Request Body**:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "name": "Batch A - Oct 30",
      "funder": "Funding Source",
      "lot": "LOT123",
      "pen": "PEN01",
      "lot_group": "GROUP1",
      "pen_location": "North Section",
      "sex": "Mixed",
      "tag_color": "Red",
      "visual_id": "VIS001",
      "notes": "Additional notes",
      "created_at": "2024-10-30T10:00:00Z",
      "active": 1
    }
  ]
}
```

**Field Mapping**:
- `name` → `batch_number` (required)
- `funder` → `source`
- `notes` → `notes`
- `created_at` → `induction_date`
- `pen` → Creates/updates pen with `pen_number` (optional)
- `pen_location` → Pen `description` (optional)

**Pen Mapping**:
When `pen` is provided in the batch data:
- If a pen with the same `pen_number` exists for the feedlot, it will be updated (description updated if `pen_location` is provided)
- If no pen exists, a new pen will be created with:
  - `pen_number`: Value from `pen` field
  - `description`: Value from `pen_location` field (or default "Pen {pen_number}" if not provided)
  - `capacity`: Default capacity of 100 (can be updated later via web UI)
- The batch will be linked to the pen via `pen_id`

**Response**:
```json
{
  "success": true,
  "message": "Processed 1 batch records",
  "records_processed": 1,
  "records_created": 1,
  "records_updated": 0,
  "records_skipped": 0,
  "errors": []
}
```

**Notes**:
- Batches are matched by name within the same feedlot
- If a batch with the same name exists, it will be updated
- `created_at` is parsed as ISO format or `YYYY-MM-DD` format
- Pens are automatically created or updated when `pen` field is provided in batch data
- If `pen` is provided, the batch will be linked to the pen (created if it doesn't exist)
- Pen capacity defaults to 100 and can be updated later via the web UI

---

### 2. Sync Livestock (Current State)

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

### 3. Sync Induction Events

**Endpoint**: `POST /api/v1/feedlot/induction-events`

**Description**: Creates cattle records when animals are inducted into the system.

**Request Body**:
```json
{
  "feedlot_code": "FEEDLOT001",
  "data": [
    {
      "id": 1,
      "livestock_id": 123,
      "batch_id": 5,
      "batch_name": "Batch A - Oct 30",
      "timestamp": "2024-10-30T10:00:00Z"
    }
  ]
}
```

**Field Mapping**:
- `livestock_id` → Used to create cattle record (stored as `cattle_id`)
- `batch_name` → Used to find SaaS batch (required for mapping)
- `timestamp` → `induction_date`

**Response**:
```json
{
  "success": true,
  "message": "Processed 1 induction event records",
  "records_processed": 1,
  "records_created": 1,
  "records_updated": 0,
  "records_skipped": 0,
  "errors": []
}
```

**Notes**:
- `batch_name` is required to map office app batches to SaaS batches
- Cattle records are created with default values:
  - `sex`: "Unknown"
  - `weight`: 0.0
  - `health_status`: "Healthy"
- **Pen Assignment**: Cattle are automatically assigned to the pen associated with the batch (if the batch has a `pen_id`). This happens when:
  - A new cattle record is created via induction events
  - An existing cattle record is updated and doesn't already have a pen assignment
- If cattle already exists, the record is marked as updated
- Default values should be updated via other endpoints as data becomes available

---

### 4. Sync Pairing Events

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

### 5. Sync Check-in Events

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

### 6. Sync Repair Events

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

1. **Batches**: Sync batches first to establish batch references
2. **Induction Events**: Create cattle records when animals are inducted
3. **Pairing Events**: Pair tags and set initial weights
4. **Livestock**: Update current state (optional, for reconciliation)
5. **Check-in Events**: Add weight measurements over time
6. **Repair Events**: Handle tag replacements as needed

### Idempotency

All endpoints are designed to be idempotent:
- **Batches**: Matched by name, updates existing if found
- **Induction Events**: Checks if cattle exists before creating
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

# Sync batches
batches_data = {
    "feedlot_code": FEEDLOT_CODE,
    "data": [
        {
            "name": "Batch A - Oct 30",
            "funder": "Funding Source",
            "notes": "Initial batch",
            "created_at": "2024-10-30T10:00:00Z"
        }
    ]
}

response = requests.post(
    f"{API_BASE_URL}/batches",
    headers=headers,
    json=batches_data
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Created: {result['records_created']}")
print(f"Errors: {result['errors']}")
```

### cURL Example

```bash
curl -X POST https://your-domain.com/api/v1/feedlot/batches \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "feedlot_code": "FEEDLOT001",
    "data": [
      {
        "name": "Batch A - Oct 30",
        "funder": "Funding Source",
        "notes": "Initial batch",
        "created_at": "2024-10-30T10:00:00Z"
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

3. **"Batch not found"**: Ensure batches are synced before syncing `induction-events` that reference them.

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

