# LoRa Payload Processing System

## Overview

The LoRa Payload Processing System handles incoming LoRa payloads from barn and export devices, buffers them, deduplicates them, and automatically creates batches in the SQLite database. The system runs in the background and provides real-time monitoring capabilities through the office app UI.

## Architecture

### Components

1. **LoRaPayloadBuffer Model** (`office_app/models/lora_payload_buffer.py`)
   - Database table for buffering incoming payloads
   - Stores raw payloads and parsed data
   - Tracks processing status and errors
   - Linked to Batch table for easy reference

2. **PayloadProcessor Utility** (`office_app/utils/payload_processor.py`)
   - Core payload processing logic
   - Handles deduplication via SHA256 hashing
   - Parses payload format: `hxb:batchnumber:LF:UHF` or `hxe:batchnumber:LF:UHF`
   - Creates/updates batches automatically
   - Provides buffer statistics

3. **PayloadProcessingWorker** (`office_app/utils/background_worker.py`)
   - Background thread for async payload processing
   - Runs on configurable interval (default: 5 seconds)
   - Processes pending payloads in batches
   - Handles exceptions gracefully
   - Automatic startup on app initialization

4. **API Endpoints** (`office_app/routes/office_routes.py`)
   - `/api/lora/receive` - Receive incoming payloads from LoRa device
   - `/api/lora/buffer-status` - Get buffer statistics
   - `/api/lora/payloads` - List and filter buffered payloads
   - `/api/lora/process` - Manually trigger payload processing
   - `/lora-dashboard` - Web UI for monitoring

## Payload Format

### Input Format
```
hxb:BATCH001:LF123:UHF456
hxe:EXPORT001:LF789:UHF012
```

**Components:**
- `hxb` - Payload source: **h**erd**x**-**b**arn
- `hxe` - Payload source: **h**erd**x**-**e**xport
- `BATCH001` - Batch identifier
- `LF123` - Low-Frequency (LF) tag
- `UHF456` - Ultra-High-Frequency (UHF) tag

## Processing Flow

```
1. LoRa Device sends payload
   └─> POST /api/lora/receive

2. Payload received and buffered
   ├─> SHA256 hash generated
   ├─> Deduplication check
   └─> Stored in lora_payload_buffer table with status="received"

3. Background worker processes every 5 seconds
   ├─> Fetch pending payloads
   ├─> Parse payload format
   ├─> Check if batch exists
   ├─> Create/Update batch if needed
   └─> Update buffer entry status="processed"

4. UI displays results
   ├─> List buffered payloads
   ├─> Show statistics
   └─> Monitor processing status
```

## Payload Status States

| Status | Description |
|--------|-------------|
| `received` | Payload buffered, waiting for processing |
| `processing` | Currently being processed |
| `processed` | Successfully processed and batch created/updated |
| `duplicate` | Duplicate payload (same hash received before) |
| `error` | Processing failed with error message |

## Database Schema

### lora_payload_buffer Table
```sql
CREATE TABLE lora_payload_buffer (
    id INTEGER PRIMARY KEY,
    raw_payload VARCHAR(255) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL UNIQUE,
    source_type VARCHAR(10),  -- 'hxb' or 'hxe'
    batch_number VARCHAR(50),
    lf_tag VARCHAR(50),
    uhf_tag VARCHAR(50),
    status VARCHAR(20),  -- received, processing, processed, duplicate, error
    batch_id INTEGER,  -- Foreign key to batches
    error_message TEXT,
    received_at DATETIME,
    processed_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME
);
```

## API Documentation

### 1. Receive LoRa Payload

**Endpoint:** `POST /api/lora/receive`

**Authentication:** None (Device endpoint)

**Request:**
```json
{
    "payload": "hxb:BATCH001:LF123:UHF456"
}
```

**Response (Success - 201):**
```json
{
    "success": true,
    "message": "Payload buffered successfully",
    "status": "buffered",
    "payload_id": 1,
    "payload_hash": "abc123..."
}
```

**Response (Duplicate - 409):**
```json
{
    "success": false,
    "message": "Duplicate payload. Originally received at 2024-01-15T10:30:00",
    "status": "duplicate",
    "payload_id": 1,
    "original_received_at": "2024-01-15T10:30:00"
}
```

### 2. Get Buffer Status

**Endpoint:** `GET /api/lora/buffer-status`

**Authentication:** Required (Admin only)

**Response:**
```json
{
    "success": true,
    "data": {
        "total": 100,
        "received": 10,
        "processing": 0,
        "processed": 85,
        "duplicates": 5,
        "errors": 0
    }
}
```

### 3. List Payloads

**Endpoint:** `GET /api/lora/payloads?status=processed&limit=50&offset=0`

**Authentication:** Required (Admin only)

**Query Parameters:**
- `status` (optional): Filter by status
- `limit` (optional): Results per page (default: 50, max: 500)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "raw_payload": "hxb:BATCH001:LF123:UHF456",
            "payload_hash": "abc123...",
            "source_type": "hxb",
            "batch_number": "BATCH001",
            "lf_tag": "LF123",
            "uhf_tag": "UHF456",
            "status": "processed",
            "batch_id": 5,
            "error_message": null,
            "received_at": "2024-01-15T10:30:00",
            "processed_at": "2024-01-15T10:30:05",
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:05"
        }
    ],
    "total": 85,
    "count": 50
}
```

### 4. Manually Process Payloads

**Endpoint:** `POST /api/lora/process`

**Authentication:** Required (Admin only)

**Response:**
```json
{
    "success": true,
    "stats": {
        "total": 10,
        "processed": 9,
        "duplicates": 0,
        "errors": 1,
        "failed_payloads": [
            {
                "id": 2,
                "payload": "invalid:data",
                "reason": "Invalid payload format"
            }
        ]
    }
}
```

### 5. LoRa Dashboard UI

**Endpoint:** `GET /lora-dashboard`

**Authentication:** Required (Admin only)

Displays:
- Buffer status statistics (pie/bar charts)
- Recent payloads table with filtering
- Processing history
- Error log

## Configuration

### Processing Interval

Edit `office_app/__init__.py` to change payload processing interval:

```python
init_background_worker(app, interval=5)  # 5 seconds (default)
```

Recommended values:
- **1-2 seconds**: High-frequency devices, low latency requirement
- **5-10 seconds**: Standard operation
- **30+ seconds**: Low-frequency devices, bandwidth-limited

## Deduplication

### How It Works

1. Each incoming payload is hashed using SHA256
2. Hash is checked against existing records in database
3. If duplicate found:
   - Payload not processed
   - Status marked as "duplicate"
   - Original reception time returned to device
4. Hash stored in database as unique index for fast lookups

### Example

```
Device sends: "hxb:BATCH001:LF123:UHF456"
  ├─> Hash: abc123def456...
  ├─> Check database
  └─> If not found, buffer it
     └─> If found, reject as duplicate
```

## Error Handling

### Invalid Payload Format
```json
{
    "success": false,
    "message": "Invalid payload format. Expected: source_type:batch_number:lf_tag:uhf_tag (e.g., hxb:BATCH001:LF123:UHF456)",
    "status": "error"
}
```

### Database Errors
- Errors logged to application logger
- Payload marked with error status
- Error message stored for debugging
- Processing continues with next payload

## Monitoring

### Log Messages

The system logs:
- Payload reception: `"Payload buffered: hxb:BATCH001:LF123:UHF456 (ID: 1)"`
- Processing cycles: `"Payload processing cycle - Total: 10, Processed: 9, Errors: 1"`
- Duplicates: `"Duplicate payload received: hxb:BATCH001:LF123:UHF456"`
- Errors: `"Error processing payload 1: {error details}"`

### Real-time Stats

Use `/api/lora/buffer-status` endpoint to monitor:
- Total payloads
- Pending processing
- Successfully processed
- Duplicate count
- Error count

## Performance Considerations

### Throughput
- **Single device**: 1-2 payloads/second sustained
- **Multiple devices**: Scales linearly with processing interval
- **Database**: Indexed on `payload_hash` and `batch_number` for fast lookups

### Storage
- **Per payload**: ~500 bytes average
- **100 payloads/day**: ~50 KB
- **30 days retention**: ~1.5 MB

### Resource Usage
- **CPU**: Minimal (JSON parsing + hash calculation)
- **Memory**: Single thread, ~20 MB overhead
- **I/O**: 1 database write per payload received, 1 per processed payload

## Usage Examples

### Python Client
```python
import requests

# Send payload
response = requests.post(
    'http://localhost:5001/api/lora/receive',
    json={'payload': 'hxb:BATCH001:LF123:UHF456'}
)
print(response.json())

# Check status
response = requests.get(
    'http://localhost:5001/api/lora/buffer-status',
    headers={'Authorization': 'Bearer token'}
)
print(response.json())
```

### cURL
```bash
# Send payload
curl -X POST http://localhost:5001/api/lora/receive \
  -H "Content-Type: application/json" \
  -d '{"payload": "hxb:BATCH001:LF123:UHF456"}'

# Get buffer status
curl -X GET http://localhost:5001/api/lora/buffer-status \
  -H "Authorization: Bearer token"
```

## Troubleshooting

### High Error Rate
1. Check `/api/lora/payloads?status=error`
2. Review error messages
3. Verify payload format matches `source_type:batch_number:lf_tag:uhf_tag`

### Processing Delay
1. Check `/api/lora/buffer-status` for pending count
2. Reduce processing interval in `__init__.py`
3. Check database for slow queries

### Duplicates
1. Normal behavior - same payload hashed to same value
2. Check device for sending duplicate batches
3. Review reception time in buffer

## Future Enhancements

1. **Persistence**: Archive old payloads to separate table
2. **Compression**: Gzip payloads for storage optimization
3. **Notifications**: Alert on processing errors
4. **Retry Logic**: Auto-retry failed payloads
5. **Rate Limiting**: Per-device rate limiting
6. **Webhook**: Push events to external systems
