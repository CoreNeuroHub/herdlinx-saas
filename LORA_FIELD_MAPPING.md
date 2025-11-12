# LoRa Packet to MongoDB Field Mapping

## Overview

This document maps LoRa packet fields to MongoDB data structure and shows what data is available from the office system.

---

## Data Flow Architecture

```
[Barn RFID Readers] → [LoRa Packet] → [Office Pi SQLite] → [MongoDB Sync] → [SAAS Adapter] → [SAAS GUI]
```

---

## Event Types and Fields

### 1. Induction Event (`hxbind000001`)

**Purpose**: Create batch and livestock record when animal enters feedlot

**LoRa Packet Format**:
```
event:hxbind000001|funder:Southwest Cattle Co|lot:LOT2024-001|pen:P1|lid:1|sex:M|tag_color:Red
```

**Parsed Fields**:
| LoRa Field | Type | Required | Description |
|------------|------|----------|-------------|
| `event` | string | ✅ | Event ID (hxbind000001) |
| `funder` | string | ✅ | Funding organization |
| `lot` | string | ✅ | Lot number (batch identifier) |
| `pen` | string | ✅ | Pen identifier (e.g., P1, A-1) |
| `lid` | integer | ✅ | Livestock ID (1, 2, 3...) |
| `lot_group` | string | ❌ | Optional lot grouping |
| `pen_location` | string | ❌ | Optional pen location |
| `sex` | string | ❌ | Sex (M/F) |
| `tag_color` | string | ❌ | Visual tag color |
| `visual_id` | string | ❌ | Visual ID number |
| `notes` | string | ❌ | Additional notes |

**MongoDB Batch Document** (created in `batches` collection):
```javascript
{
  _id: ObjectId('...'),
  id: 1,                                    // Auto-increment SQLite ID
  batch_name: "LOT2024-001",                // From 'lot' field
  funder: "Southwest Cattle Co",
  lot: "LOT2024-001",
  pen: "P1",                                // ⚠️ Important: pen is here!
  lot_group: null,
  pen_location: null,
  sex: "M",
  tag_color: "Red",
  visual_id: null,
  notes: "",
  barn_prefix: "hxb",
  first_event_id: "hxbind000001",
  first_induction_at: ISODate("2024-10-15T06:00:00Z"),
  created_at: ISODate("..."),
  feedlot_code: "ULETH_LRS"
}
```

**MongoDB Livestock Document** (created in `livestock` collection):
```javascript
{
  _id: ObjectId('...'),
  id: 101,                                  // Auto-increment SQLite ID
  livestock_id: 1,                          // From 'lid' field
  lf_id: null,                              // Set by pairing event
  epc: null,                                // Set by pairing event
  batch_id: 1,                              // Link to batch
  induction_event_id: "hxbind000001",
  first_induction_at: ISODate("2024-10-15T06:00:00Z"),
  created_at: ISODate("..."),
  feedlot_code: "ULETH_LRS"
}
```

---

### 2. Pairing Event (`hxbpai000001`)

**Purpose**: Assign RFID tags to livestock and record initial weight

**LoRa Packet Format**:
```
event:hxbpai000001|lf:LF_EAR_0001|epc:EPC:30143B7C84D500000000000|lid:1|weight:245.5
```

**Parsed Fields**:
| LoRa Field | Type | Required | Description |
|------------|------|----------|-------------|
| `event` | string | ✅ | Event ID |
| `lf` | string | ✅ | Low Frequency tag ID |
| `epc` | string | ✅ | UHF/EPC tag ID |
| `lid` | integer | ✅ | Livestock ID |
| `weight` | float | ❌ | Weight in kg |

**MongoDB Update** (updates `livestock` collection):
```javascript
{
  livestock_id: 1,
  lf_id: "LF_EAR_0001",                    // Updated from null
  epc: "EPC:30143B7C84D500000000000",     // Updated from null
  // ... other fields unchanged
}
```

**MongoDB Event** (stored in `events` collection):
```javascript
{
  _id: ObjectId('...'),
  event_id: "hxbpai000001",
  event_type: "pairing",
  livestock_id: 1,
  parsed_data: {
    lf: "LF_EAR_0001",
    epc: "EPC:30143B7C84D500000000000",
    weight: 245.5                          // ⚠️ Weight stored in events!
  },
  received_at: ISODate("..."),
  feedlot_code: "ULETH_LRS"
}
```

---

### 3. Check-in Event (`hxbchi000001`)

**Purpose**: Record weight measurement

**LoRa Packet Format**:
```
event:hxbchi000001|weight:267.3|lid:1
```

**Parsed Fields**:
| LoRa Field | Type | Required | Description |
|------------|------|----------|-------------|
| `event` | string | ✅ | Event ID |
| `weight` | float | ✅ | Weight in kg |
| `lid` | integer | ✅ | Livestock ID |

**MongoDB Event** (stored in `events` collection):
```javascript
{
  _id: ObjectId('...'),
  event_id: "hxbchi000001",
  event_type: "checkin",
  livestock_id: 1,
  parsed_data: {
    weight: 267.3                          // ⚠️ Weight history in events!
  },
  received_at: ISODate("..."),
  feedlot_code: "ULETH_LRS"
}
```

**Note**: Livestock record is NOT updated. Weight history comes from querying events collection.

---

### 4. Repair Event (`hxbrep000001`)

**Purpose**: Replace damaged RFID tag

**LoRa Packet Format**:
```
event:hxbrep000001|old_lf:LF_EAR_0001|new_lf:LF_EAR_0099|lid:1|reason:Tag damaged
```

**Parsed Fields**:
| LoRa Field | Type | Required | Description |
|------------|------|----------|-------------|
| `event` | string | ✅ | Event ID |
| `lid` | integer | ✅ | Livestock ID |
| `old_lf` | string | ❌ | Old LF tag |
| `new_lf` | string | ❌ | New LF tag |
| `old_epc` | string | ❌ | Old EPC tag |
| `new_epc` | string | ❌ | New EPC tag |
| `reason` | string | ❌ | Repair reason |

**MongoDB Update** (updates `livestock` collection):
```javascript
{
  livestock_id: 1,
  lf_id: "LF_EAR_0099",                    // Updated to new tag
  // ... other fields unchanged
}
```

**MongoDB Event** (audit trail in `events` collection):
```javascript
{
  _id: ObjectId('...'),
  event_id: "hxbrep000001",
  event_type: "repair",
  livestock_id: 1,
  parsed_data: {
    old_lf: "LF_EAR_0001",
    new_lf: "LF_EAR_0099",
    reason: "Tag damaged"                  // ⚠️ Tag history in events!
  },
  received_at: ISODate("..."),
  feedlot_code: "ULETH_LRS"
}
```

---

## SAAS Adapter Field Mapping

The `OfficeAdapter` transforms office schema to SAAS schema on-the-fly:

### Livestock Field Mapping

| Office Field | SAAS Field | Type | Notes |
|--------------|------------|------|-------|
| `lf_id` | `lf_tag` | string | Low Frequency tag |
| `epc` | `uhf_tag` | string | UHF/EPC tag |
| `livestock_id` | `cattle_id` | integer | Livestock ID |
| `batch_id` | `batch_id` | integer | Same field name |
| `first_induction_at` | `induction_date` | datetime | Induction timestamp |
| (none) | `weight` | float | Default: 0 (get from events) |
| (none) | `health_status` | string | Default: 'unknown' |
| (none) | `status` | string | Default: 'active' |
| (none) | `pen_id` | ObjectId | Default: null |
| (none) | `weight_history` | array | Default: [] (get from events) |
| (none) | `tag_pair_history` | array | Default: [] (get from events) |

### Batch Field Mapping

| Office Field | SAAS Field | Type | Notes |
|--------------|------------|------|-------|
| `batch_name` | `batch_number` | string | Batch identifier |
| `first_induction_at` | `induction_date` | datetime | Induction timestamp |
| `funder` | `funder` | string | Same field name |
| `lot` | `lot` | string | Same field name |
| `pen` | `pen` | string | ⚠️ Pen info here! |
| `lot_group` | `lot_group` | string | Same field name |
| `pen_location` | `pen_location` | string | Same field name |
| `sex` | `sex` | string | Same field name |
| `tag_color` | `tag_color` | string | Same field name |
| `visual_id` | `visual_id` | string | Same field name |
| `notes` | `notes` | string | Same field name |

---

## Important Distinctions

### ❌ Office System Does NOT Have:

1. **Separate Pens Table**: Pens are just text fields in batches (e.g., "P1", "A-1")
2. **Weight in Livestock**: Weights are stored in `events` collection
3. **Health Status**: Not tracked by office system
4. **Pen Capacity**: No capacity management in office
5. **Pen Maps/Layouts**: No visual pen arrangement

### ✅ Office System HAS:

1. **Pen Label**: Simple text identifier in batch (e.g., "P1", "Pen A")
2. **Pen Location**: Optional location within pen
3. **Weight History**: All weights in `events` collection by livestock_id
4. **Tag History**: Old/new tags in `repair` events
5. **Complete Audit Trail**: Every event stored in `events` collection

---

## Querying Office Data in SAAS

### Get Livestock with Pen Information

```python
# Get livestock
livestock = Cattle.find_by_feedlot(feedlot_id)

# Get batch to find pen
batch = Batch.find_by_id(livestock['batch_id'])

# Access pen label
pen_label = batch.get('pen')  # e.g., "P1"
pen_location = batch.get('pen_location')  # e.g., "North Section"
```

### Get Weight History

```python
# Query events collection for livestock
events = db.events.find({
    'livestock_id': livestock_id,
    'event_type': {'$in': ['pairing', 'checkin']}
}).sort('received_at', 1)

# Extract weights
weight_history = []
for event in events:
    parsed_data = event.get('parsed_data', {})
    weight = parsed_data.get('weight')
    if weight:
        weight_history.append({
            'weight': weight,
            'recorded_at': event['received_at']
        })
```

### Get Tag History

```python
# Query repair events
repairs = db.events.find({
    'livestock_id': livestock_id,
    'event_type': 'repair'
}).sort('received_at', 1)

# Extract tag changes
tag_history = []
for repair in repairs:
    parsed_data = repair.get('parsed_data', {})
    tag_history.append({
        'old_lf': parsed_data.get('old_lf'),
        'new_lf': parsed_data.get('new_lf'),
        'old_epc': parsed_data.get('old_epc'),
        'new_epc': parsed_data.get('new_epc'),
        'reason': parsed_data.get('reason'),
        'changed_at': repair['received_at']
    })
```

---

## Display Recommendations

### Dashboard Statistics

```python
# Total Pens: Show count of unique pen labels from batches
unique_pens = db.batches.distinct('pen', {'feedlot_code': feedlot_code})
total_pens = len(unique_pens)
```

### Cattle List View

Show these office fields:
- `cattle_id` (from livestock_id)
- `lf_tag` (from lf_id)
- `uhf_tag` (from epc)
- `batch_number` (from batch.lot or batch.batch_name)
- `pen` (from batch.pen) - ⚠️ Get from batch!
- `induction_date` (from first_induction_at)
- `latest_weight` (query latest event)

### Batch List View

Show these office fields:
- `batch_number` (from lot or batch_name)
- `funder`
- `pen` - ⚠️ This is the pen identifier!
- `pen_location` (if available)
- `induction_date` (from first_induction_at)
- `cattle_count` (count livestock by batch_id)

### Pen List View (Virtual)

Since office doesn't have a pens table, create virtual pen list from batches:

```python
# Group batches by pen
pens = {}
for batch in batches:
    pen_label = batch.get('pen', 'Unknown')
    if pen_label not in pens:
        pens[pen_label] = {
            'pen_number': pen_label,
            'batches': [],
            'total_cattle': 0
        }
    pens[pen_label]['batches'].append(batch)
    pens[pen_label]['total_cattle'] += batch['cattle_count']
```

---

## Summary

### Key Takeaways

1. **Pens are labels, not entities**: The `pen` field in batches is just text (e.g., "P1")
2. **Weights are in events**: Query events collection for weight history
3. **Tags can change**: Repair events track old → new tag replacements
4. **Complete audit trail**: All events preserved in events collection
5. **Feedlot code isolation**: All data tagged with `feedlot_code` for multi-tenancy

### Next Steps for SAAS Display

1. ✅ Show pen label from batch.pen in cattle list
2. ✅ Create virtual pens view from unique batch.pen values
3. ⚠️ Add weight history query from events collection
4. ⚠️ Add tag history query from repair events
5. ⚠️ Show pen location (batch.pen_location) if available
