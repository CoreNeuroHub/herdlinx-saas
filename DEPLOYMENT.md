# HerdLinx SAAS Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└───────────────┬─────────────────────────┬───────────────────────┘
                │                         │
        ┌───────▼───────┐         ┌───────▼────────┐
        │ herdlinx.com  │         │ Office Pi API  │
        │ (SAAS Web UI) │         │ (Port 5021)    │
        │ Port 5001     │         │                │
        └───────┬───────┘         └───────┬────────┘
                │                         │
                └────────────┬────────────┘
                             │
                    ┌────────▼─────────┐
                    │ MongoDB Database  │
                    │ herdlinx_saas     │
                    └───────────────────┘
```

## Two Server Setup

### 1. SAAS Web Application (Port 5001)

**Purpose**: Web interface for users to view and manage cattle data

**Domains**:
- `herdlinx.com` → Super admin access (all feedlots)
- `uleth.herdlinx.com` → ULeth owner access (ULETH_LRS, ULETH_PBF)
- `lpoly.herdlinx.com` → LPoly owner access (LPOLY_CCF, LPOLY_TTC)

**Start Command**:
```bash
cd /Users/arnoldjosephaguila/Documents/GitHub/herdlinx-system/saas
source venv/bin/activate
python run.py
```

**Features**:
- User authentication (session-based)
- Multi-tenant feedlot management
- Dashboard with statistics
- Cattle, batch, and pen management
- Real-time data from MongoDB

---

### 2. Office API Server (Port 5021)

**Purpose**: Receive and process data from office Raspberry Pi systems

**Domain**:
- `api.herdlinx.com:5021` → Office Pi data ingestion

**Start Command**:
```bash
cd /Users/arnoldjosephaguila/Documents/GitHub/herdlinx-system/saas
source venv/bin/activate
python run_api.py
```

**Features**:
- API key authentication
- Endpoints for each event type
- Data validation and error handling
- Automatic MongoDB sync

---

## Office Raspberry Pi Configuration

Each feedlot has its own Raspberry Pi that syncs data to the SAAS:

### Example: University of Lethbridge - Research Station

**Pi Configuration** (`office/config.env`):
```bash
# MongoDB Connection
MONGO_HOST=api.herdlinx.com
MONGO_PORT=27017
MONGO_DB=herdlinx_saas
MONGO_USERNAME=office_user
MONGO_PASSWORD=secure_password_here

# Feedlot Identification
OFFICE_FEEDLOT_CODE=ULETH_LRS

# API Configuration
SAAS_API_URL=http://api.herdlinx.com:5021
SAAS_API_KEY=your_api_key_here

# Sync Settings
SYNC_INTERVAL=5  # seconds
SYNC_MODE=api    # Use API endpoint instead of direct MongoDB
```

**How it works**:
1. Office Pi receives LoRa packets from barn RFID readers
2. Stores events in local SQLite (`office_receiver.db`)
3. Every 5 seconds, syncs to SAAS via API:
   - Batches → POST to `/v1/feedlot/batches`
   - Livestock → POST to `/v1/feedlot/livestock`
   - Events → POST to `/v1/feedlot/*-events`
4. SAAS API validates data and stores in MongoDB
5. SAAS web UI displays data filtered by feedlot_code

---

## API Authentication

### Generating API Keys

1. Login to SAAS web UI as super admin
2. Go to Settings → API Keys
3. Click "Generate New API Key"
4. Select the feedlot (e.g., ULETH_LRS)
5. Copy the generated key
6. Configure it in the office Pi's `config.env`

### API Key Format

```json
{
  "api_key": "herdlinx_uleth_lrs_1234567890abcdef",
  "feedlot_code": "ULETH_LRS",
  "feedlot_id": "69122b44521cf7fffcb8fd36",
  "created_at": "2025-11-10T18:13:24.416Z",
  "is_active": true
}
```

---

## API Endpoints

### Base URL
```
http://api.herdlinx.com:5021
```

### Authentication
All endpoints require API key in header:
```
X-API-Key: your_api_key_here
```

### 1. Sync Batches
```http
POST /v1/feedlot/batches
Content-Type: application/json

{
  "feedlot_code": "ULETH_LRS",
  "data": [
    {
      "name": "HXBIND000001",
      "funder": "ULeth Research Grant",
      "created_at": "2024-10-15T06:00:00Z",
      "notes": "Fall 2024 batch"
    }
  ]
}
```

### 2. Sync Livestock Current State
```http
POST /v1/feedlot/livestock
Content-Type: application/json

{
  "feedlot_code": "ULETH_LRS",
  "data": [
    {
      "id": 101,
      "current_lf_id": "LF_ULETH_LRS_0101",
      "current_epc": "EPC:000000000000000000000101",
      "induction_event_id": "hxbind000101"
    }
  ]
}
```

### 3. Sync Induction Events
```http
POST /v1/feedlot/induction-events
Content-Type: application/json

{
  "feedlot_code": "ULETH_LRS",
  "data": [
    {
      "livestock_id": 101,
      "batch_id": 1,
      "batch_name": "HXBIND000001",
      "timestamp": "2024-10-15T06:00:00Z"
    }
  ]
}
```

### 4. Sync Pairing Events (Tags + Weight)
```http
POST /v1/feedlot/pairing-events
Content-Type: application/json

{
  "feedlot_code": "ULETH_LRS",
  "data": [
    {
      "livestock_id": 101,
      "lf_id": "LF_ULETH_LRS_0101",
      "epc": "EPC:000000000000000000000101",
      "weight_kg": 245.5,
      "timestamp": "2024-10-15T06:30:00Z"
    }
  ]
}
```

### 5. Sync Checkin Events (Weight Measurements)
```http
POST /v1/feedlot/checkin-events
Content-Type: application/json

{
  "feedlot_code": "ULETH_LRS",
  "data": [
    {
      "livestock_id": 101,
      "weight_kg": 267.3,
      "timestamp": "2024-10-30T10:00:00Z"
    }
  ]
}
```

### 6. Sync Repair Events (Tag Replacements)
```http
POST /v1/feedlot/repair-events
Content-Type: application/json

{
  "feedlot_code": "ULETH_LRS",
  "data": [
    {
      "livestock_id": 101,
      "old_lf_id": "LF_ULETH_LRS_0101",
      "new_lf_id": "LF_ULETH_LRS_0199",
      "reason": "Tag damaged"
    }
  ]
}
```

---

## Domain Configuration (Nginx)

### For herdlinx.com (SAAS Web UI)

```nginx
server {
    listen 80;
    server_name herdlinx.com www.herdlinx.com;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name herdlinx.com www.herdlinx.com;

    ssl_certificate /etc/ssl/certs/herdlinx.com.crt;
    ssl_certificate_key /etc/ssl/private/herdlinx.com.key;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### For uleth.herdlinx.com (ULeth Owner)

```nginx
server {
    listen 80;
    server_name uleth.herdlinx.com;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name uleth.herdlinx.com;

    ssl_certificate /etc/ssl/certs/uleth.herdlinx.com.crt;
    ssl_certificate_key /etc/ssl/private/uleth.herdlinx.com.key;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### For api.herdlinx.com (Office API)

```nginx
server {
    listen 80;
    server_name api.herdlinx.com;

    location / {
        proxy_pass http://localhost:5021;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # API endpoints don't need HTTPS (office Pi is trusted)
        # But you can add SSL if needed
    }
}
```

---

## Production Deployment

### Using systemd (Recommended)

**SAAS Web UI Service** (`/etc/systemd/system/herdlinx-web.service`):
```ini
[Unit]
Description=HerdLinx SAAS Web Application
After=network.target mongodb.service

[Service]
Type=simple
User=herdlinx
WorkingDirectory=/opt/herdlinx-system/saas
Environment="PATH=/opt/herdlinx-system/saas/venv/bin"
ExecStart=/opt/herdlinx-system/saas/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Office API Service** (`/etc/systemd/system/herdlinx-api.service`):
```ini
[Unit]
Description=HerdLinx Office API Server
After=network.target mongodb.service

[Service]
Type=simple
User=herdlinx
WorkingDirectory=/opt/herdlinx-system/saas
Environment="PATH=/opt/herdlinx-system/saas/venv/bin"
ExecStart=/opt/herdlinx-system/saas/venv/bin/python run_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start**:
```bash
sudo systemctl enable herdlinx-web
sudo systemctl enable herdlinx-api
sudo systemctl start herdlinx-web
sudo systemctl start herdlinx-api

# Check status
sudo systemctl status herdlinx-web
sudo systemctl status herdlinx-api
```

---

## Monitoring and Logs

### View Logs
```bash
# SAAS Web UI logs
sudo journalctl -u herdlinx-web -f

# Office API logs
sudo journalctl -u herdlinx-api -f

# MongoDB logs
sudo journalctl -u mongod -f
```

### Health Checks
```bash
# Check SAAS Web UI
curl http://localhost:5001/

# Check Office API
curl -H "X-API-Key: test_key" http://localhost:5021/v1/feedlot/batches
```

---

## Security Considerations

1. **API Keys**: Generate unique keys for each feedlot
2. **HTTPS**: Use SSL certificates for public domains
3. **Firewall**: Restrict port 5021 to office Pi IPs only
4. **MongoDB**: Enable authentication and use strong passwords
5. **Nginx**: Configure rate limiting to prevent abuse
6. **Backups**: Regular MongoDB backups to prevent data loss

---

## Troubleshooting

### Issue: Office Pi cannot connect to API
**Solution**: Check firewall rules, verify API key, check network connectivity

### Issue: Data not showing in SAAS
**Solution**: Verify feedlot_code matches, check MongoDB data, restart services

### Issue: API returns 401 Unauthorized
**Solution**: Verify API key is valid and active in database

### Issue: Duplicate cattle records
**Solution**: Office Pi should use OFFICE_{livestock_id} format for cattle_id

---

## Summary

✅ **SAAS Web UI**: http://localhost:5001 (Port 5001)
✅ **Office API**: http://localhost:5021 (Port 5021)
✅ **MongoDB**: localhost:27017
✅ **Multi-tenant**: Filtered by feedlot_code
✅ **Authentication**: Sessions (web) + API keys (API)
✅ **Production**: systemd services + Nginx reverse proxy

Ready for deployment! 🚀
