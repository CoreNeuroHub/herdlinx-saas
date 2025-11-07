# HerdLinx Sample Feedlot Data

This directory contains sample data and tools for testing the HerdLinx SaaS API with realistic Alberta cattle industry data.

## Overview

The sample data system consists of:
1. **SQLite Database** - Office app database structure as specified in the documentation
2. **Sample Data** - Realistic Alberta cattle industry data (batches, cattle, events)
3. **API Sync Application** - Python script to sync data from SQLite to the SaaS API

## Files

- `db_init.py` - Initializes the SQLite database with all tables, indexes, views, and default data
- `populate_sample_data.py` - Populates the database with realistic sample data
- `sync_to_api.py` - Syncs data from SQLite database to the SaaS API
- `requirements.txt` - Python dependencies
- `herdlinx.db` - SQLite database (created after running initialization)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python db_init.py
```

This creates the `herdlinx.db` SQLite database with:
- All required tables (users, settings, batches, livestock, events)
- Database indexes for performance
- The `lora_package` view
- Default users (owner/admin/user)
- Default system settings

### 3. Populate Sample Data

```bash
python populate_sample_data.py
```

This populates the database with:
- **5 batches** spanning several months
- **250 cattle records** (50 per batch)
- **Induction events** for each animal
- **Pairing events** with initial tag assignments and weights
- **Check-in events** (2-5 per animal) showing weight progression over time
- **Repair events** (about 5% of animals) for tag replacements

The data includes realistic:
- Alberta feedlot names and locations
- Common cattle breeds (Angus, Hereford, Charolais, Simmental, etc.)
- Realistic weights (200-700 kg range)
- Tag IDs (LF tags and EPC tags)
- Timestamps spanning several months

## Syncing to API

### Prerequisites

Before syncing, you need:
1. An API key from the HerdLinx SaaS system (generated via Settings → API Keys)
2. The feedlot code that matches your API key
3. The API base URL

### Configuration

You can configure the sync application in three ways:

#### Option 1: Environment Variables (Recommended)

```bash
export API_BASE_URL="https://your-domain.com/api/v1/feedlot"
export API_KEY="your_api_key_here"
export FEEDLOT_CODE="FEEDLOT001"
export DB_PATH="herdlinx.db"  # Optional, defaults to herdlinx.db

python sync_to_api.py
```

#### Option 2: Command Line Arguments

```bash
python sync_to_api.py "https://your-domain.com/api/v1/feedlot" "your_api_key_here" "FEEDLOT001" "herdlinx.db"
```

#### Option 3: Edit the Script

Edit the `main()` function in `sync_to_api.py` to set default values.

### Running the Sync

```bash
python sync_to_api.py
```

The sync process follows the recommended order from the API documentation:
1. **Batches** - Syncs all batch records
2. **Induction Events** - Creates cattle records
3. **Pairing Events** - Assigns tags and initial weights
4. **Livestock** - Updates current state (optional reconciliation)
5. **Check-in Events** - Adds weight measurements
6. **Repair Events** - Handles tag replacements

### Sync Output

The sync application provides detailed output:

```
============================================================
Starting full sync to API
============================================================
API Base URL: https://your-domain.com/api/v1/feedlot
Feedlot Code: FEEDLOT001
Database: herdlinx.db
============================================================

Syncing batches...
  Processed 5 batches

Syncing induction events...
  Processed 250 induction events

Syncing pairing events...
  Processed 250 pairing events

Syncing livestock (current state)...
  Processed 250 livestock records

Syncing check-in events...
  Processed 750 check-in events

Syncing repair events...
  Processed 12 repair events

============================================================
Sync Summary
============================================================
batches            | Processed:    5 | Created:    5 | Updated:    0 | Skipped:    0
induction_events   | Processed:  250 | Created:  250 | Updated:    0 | Skipped:    0
pairing_events     | Processed:  250 | Created:    0 | Updated:  250 | Skipped:    0
livestock          | Processed:  250 | Created:    0 | Updated:  250 | Skipped:    0
checkin_events     | Processed:  750 | Created:  750 | Updated:    0 | Skipped:    0
repair_events      | Processed:   12 | Created:    0 | Updated:   12 | Skipped:    0
============================================================
Total Processed: 1517
Total Created:   1005
Total Updated:   512
Total Skipped:     0
============================================================

Sync completed successfully!
```

## Sample Data Details

### Batches

The sample data includes 5 batches:
- Batch A - Sep 01
- Batch B - Sep 15
- Batch C - Sep 29
- Batch D - Oct 13
- Batch E - Oct 27 (active)

Each batch includes:
- Funder information
- Lot and pen assignments
- Lot groups and pen locations
- Sex designation (M/F/Mixed)
- Tag colors
- Visual IDs
- Notes

### Cattle Records

Each batch contains 50 cattle records with:
- Unique livestock IDs
- Breed information (stored in metadata)
- Tag pairs (LF and UHF/EPC tags)
- Weight history (2-5 check-ins per animal)
- Induction timestamps
- Some animals have repair events

### Events Timeline

The events are spread over several months:
- **Induction Events**: When animals enter the system
- **Pairing Events**: Initial tag pairing with starting weights (200-350 kg)
- **Check-in Events**: Regular weight measurements every 2-4 weeks
- **Repair Events**: Tag replacements (about 5% of animals)

## Database Structure

The database follows the structure documented in `OFFICE_DATABASE_STRUCTURE.md`:

- **Core Tables**: users, settings, batches, livestock
- **Event Tables**: induction_events, pairing_events, checkin_events, repair_events
- **Indexes**: Optimized for common queries
- **Views**: lora_package view for data aggregation

## Troubleshooting

### Database Not Found

If you get "Database not found" error:
```bash
python db_init.py
python populate_sample_data.py
```

### API Authentication Errors

- Verify your API key is correct and active
- Ensure the feedlot code matches the API key's feedlot
- Check that the API base URL is correct

### Sync Errors

- Check the error messages in the sync output
- Verify that batches are synced before induction events
- Ensure the API server is accessible
- Check network connectivity

### Re-populating Data

To start fresh:
```bash
rm herdlinx.db
python db_init.py
python populate_sample_data.py
```

## Customization

### Changing Sample Data Volume

Edit `populate_sample_data.py`:
- Change `count=5` in `populate_batches()` to adjust batch count
- Change `animals_per_batch=50` to adjust animals per batch

### Adding More Realistic Data

You can modify the constants in `populate_sample_data.py`:
- `ALBERTA_FEEDLOTS` - Add more feedlot names
- `BREEDS` - Add more cattle breeds
- `FUNDERS` - Add more funding sources
- `PEN_LOCATIONS` - Add more pen locations

## API Documentation

For detailed API documentation, see:
- `../documentation/API_DOCUMENTATION.md` - Complete API reference
- `../documentation/OFFICE_DATABASE_STRUCTURE.md` - Database structure details

## Support

For issues or questions:
1. Check the error messages in the sync output
2. Review the API documentation
3. Verify your API key and feedlot code
4. Ensure the database is properly initialized and populated

