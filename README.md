# HerdLinx Office App

A standalone Flask-based cattle herd management system with LoRa device integration for real-time batch tracking from barns and export facilities.

## Features

- **Admin Dashboard** - Real-time cattle herd management
- **Batch Management** - Create and manage cattle batches with source tracking (barn/export)
- **Pen Management** - Track cattle pen assignments and capacity
- **Cattle Tracking** - Individual animal records with weight tracking, health status, and tag management
- **LoRa Integration** - Automatic batch creation from LoRa device payloads with deduplication
- **Payload Buffering** - Async processing of incoming LoRa payloads with background worker
- **Admin Controls** - User authentication and authorization

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd herdlinx-saas
```

2. **Create a virtual environment**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python -m office_app.run
```

The application will start at `http://localhost:5001`

**Default credentials:**
- Username: `admin`
- Password: `admin`

## Project Structure

```
herdlinx-saas/
├── office_app/                    # Main Flask application
│   ├── __init__.py               # App factory and initialization
│   ├── config.py                 # Configuration settings
│   ├── run.py                    # Entry point
│   ├── office_app.db             # SQLite database (auto-created)
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py              # Admin user model
│   │   ├── batch.py             # Batch model with payload parsing
│   │   ├── pen.py               # Pen model
│   │   ├── cattle.py            # Cattle model with tag history
│   │   └── lora_payload_buffer.py # LoRa payload buffer model
│   ├── routes/                   # Flask blueprints
│   │   ├── auth_routes.py       # Authentication and login
│   │   └── office_routes.py     # Office app and API routes
│   ├── utils/                    # Utility modules
│   │   ├── payload_processor.py # LoRa payload processing
│   │   └── background_worker.py # Background worker thread
│   ├── templates/                # Jinja2 HTML templates
│   ├── static/                   # CSS, JavaScript, images
│   ├── requirements.txt          # Dependencies
│   ├── README.md                 # Office app README
│   └── LORA_PAYLOAD_SYSTEM.md   # LoRa system documentation
├── requirements.txt              # Root dependencies
└── README.md                     # This file
```

## Usage

### Web Interface

1. **Login** - Visit `http://localhost:5001` and login with default credentials
2. **Dashboard** - View herd statistics and recent batches
3. **Batch Management** - Create and manage batches at `/office/batches`
4. **Pen Management** - Manage pens and capacity at `/office/pens`
5. **Cattle Management** - Track individual animals at `/office/cattle`
6. **LoRa Dashboard** - Monitor payload processing at `/lora-dashboard`

### API Endpoints

#### LoRa Payload Reception
```bash
POST /api/lora/receive
Content-Type: application/json

{
    "payload": "hxb:BATCH001:LF123:UHF456"
}
```

**Payload Format:**
- `hxb` - Barn source
- `hxe` - Export source
- `BATCH001` - Batch identifier
- `LF123` - Low-Frequency tag
- `UHF456` - Ultra-High-Frequency tag

#### Buffer Status
```bash
GET /api/lora/buffer-status
Authorization: Bearer <token>
```

#### List Payloads
```bash
GET /api/lora/payloads?status=processed&limit=50&offset=0
Authorization: Bearer <token>
```

#### Manual Processing
```bash
POST /api/lora/process
Authorization: Bearer <token>
```

See [LORA_PAYLOAD_SYSTEM.md](office_app/LORA_PAYLOAD_SYSTEM.md) for complete API documentation.

## Configuration

### Processing Interval

Edit `office_app/__init__.py` to change LoRa payload processing interval:

```python
init_background_worker(app, interval=5)  # 5 seconds (default)
```

Recommended values:
- **1-2 seconds**: High-frequency devices, low latency
- **5-10 seconds**: Standard operation
- **30+ seconds**: Low-frequency devices

### Database

SQLite database is automatically created at `office_app/office_app.db` on first run.

To reset database:
```bash
rm office_app/office_app.db
python -m office_app.run
```

### Environment Variables

Create a `.env` file in the project root:
```
OFFICE_DATABASE_URL=sqlite:///office_app/office_app.db
FLASK_ENV=development
```

## LoRa Payload Processing

The system automatically processes incoming LoRa payloads:

1. **Reception** - Payload buffered to database
2. **Deduplication** - SHA256 hash prevents duplicates
3. **Parsing** - Format validated and extracted
4. **Batch Creation** - Auto-creates batch if needed
5. **Status Tracking** - Records success/failure

Background worker runs every 5 seconds and processes pending payloads asynchronously.

## Database Schema

### Main Tables

**users** - Admin users
```sql
id, username, email, password_hash, is_admin, is_active, created_at
```

**batches** - Cattle batches
```sql
id, batch_number, induction_date, source, source_type, notes, created_at, updated_at
```

**pens** - Physical pen locations
```sql
id, pen_number, capacity, description, created_at, updated_at
```

**cattle** - Individual animals
```sql
id, batch_id, cattle_id, pen_id, sex, weight, health_status, lf_tag, uhf_tag, created_at, updated_at
```

**lora_payload_buffer** - Payload tracking
```sql
id, raw_payload, payload_hash, source_type, batch_number, lf_tag, uhf_tag, status, batch_id, error_message, received_at, processed_at, created_at, updated_at
```

## Performance

- **Payload Throughput**: 1-2 payloads/second per device
- **Processing Latency**: <5 seconds (default 5s interval)
- **Storage**: ~500 bytes per payload
- **Memory**: ~20 MB overhead

## Troubleshooting

### Database errors
```bash
# Recreate database
rm office_app/office_app.db
python -m office_app.run
```

### Port already in use
```bash
# Change port in office_app/run.py or use environment variable
# Or kill the process using port 5001
```

### Payload processing errors
Check `/api/lora/payloads?status=error` for failed payloads and error messages.

## Development

### Running in Debug Mode
```bash
python -m office_app.run
```

The app runs with `debug=True` by default, enabling hot reloading and detailed error pages.

### Testing

```bash
# Send test payload
curl -X POST http://localhost:5001/api/lora/receive \
  -H "Content-Type: application/json" \
  -d '{"payload": "hxb:TEST001:LF999:UHF888"}'

# Check buffer status
curl http://localhost:5001/api/lora/buffer-status
```

## Documentation

- [LoRa Payload System](office_app/LORA_PAYLOAD_SYSTEM.md) - Complete API and architecture documentation
- [Office App README](office_app/README.md) - Additional office app documentation

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.

## Version History

### Current
- LoRa payload processing with background worker
- Batch creation from device payloads
- Admin dashboard and cattle management

### Future
- WebSocket for real-time updates
- Advanced filtering and reporting
- Export to CSV/Excel
- Multi-user support with role-based access
