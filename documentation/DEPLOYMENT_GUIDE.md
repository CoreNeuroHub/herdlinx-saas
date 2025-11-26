# HerdLinx - Complete Deployment Guide

Comprehensive guide to deploying the HerdLinx distributed system with Raspberry Pi backend and remote Server UI.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Network                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐       ┌──────────────────────┐   │
│  │  Raspberry Pi        │       │  Linux/Windows       │   │
│  │  Backend             │       │  Server UI           │   │
│  │                      │       │                      │   │
│  │ • LoRa Receiver      │◄─────►│ • Web Interface      │   │
│  │ • Data Processing    │ REST  │ • Sync Service       │   │
│  │ • Local Database     │ API   │ • Replica Database   │   │
│  │ • API Server         │ WSS   │ • Monitoring         │   │
│  │                      │       │                      │   │
│  └──────────────────────┘       └──────────────────────┘   │
│      branch:                        branch:                 │
│    aj/pi-backend              deployment/linux-server       │
│                                deployment/windows-server    │
└─────────────────────────────────────────────────────────────┘
```

## Available Branches

### 1. **aj/pi-backend** - Raspberry Pi Backend
   - **Purpose**: Data collection and processing from LoRa devices
   - **Platform**: Raspberry Pi (Linux)
   - **Startup**: `./scripts/setup.sh` + `./scripts/start.sh`
   - **Database**: SQLite (master/source of truth)
   - **Endpoints**:
     - REST API: `:5001`
     - WebSocket: `:5001`
   - **Documentation**: `STARTUP_GUIDE.md`

### 2. **aj/server-ui** - Server UI Base
   - **Purpose**: Base branch for Server UI with cross-platform startup scripts
   - **Platforms**: Linux, Windows
   - **Contents**: Setup, startup scripts, configuration templates
   - **Documentation**: `SERVER-STARTUP-GUIDE.md`

### 3. **deployment/linux-server** - Linux Deployment
   - **Purpose**: Optimized for Linux servers (Ubuntu, Debian, CentOS, Rocky Linux)
   - **Features**:
     - Systemd service setup
     - Reverse proxy (nginx/Apache)
     - SSL/TLS with Let's Encrypt
     - Firewall configuration
     - Automated backups
   - **Database**: SQLite (replica of Pi)
   - **Endpoints**: `:5000` (configurable)
   - **Documentation**: `scripts/LINUX-DEPLOYMENT.md`

### 4. **deployment/windows-server** - Windows Deployment
   - **Purpose**: Optimized for Windows servers/desktops
   - **Features**:
     - Task Scheduler auto-start
     - NSSM service installation
     - Windows Firewall setup
     - Easy CLI startup
   - **Database**: SQLite (replica of Pi)
   - **Endpoints**: `:5000` (configurable)
   - **Documentation**: `scripts/WINDOWS-DEPLOYMENT.md`

## Quick Start

### For Raspberry Pi Backend

```bash
git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
cd herdlinx-saas
git checkout aj/pi-backend

# One-time setup
./scripts/setup.sh --skip-update    # Skip slow system updates if desired

# Start the backend
./scripts/start.sh

# Or start in dev/prod mode
./scripts/start.sh --dev
./scripts/start.sh --prod
```

**Output:**
```
API Server: https://192.168.1.100:5001
API Key:    hxb_xxxxxxxxxxxxx  (SAVE THIS!)
Database:   office_app/office_app.db
```

### For Linux Server UI

```bash
git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
cd herdlinx-saas
git checkout deployment/linux-server

# One-time setup
./scripts/setup-server.sh

# Configure Pi connection
nano .env
# Set REMOTE_PI_HOST and PI_API_KEY

# Start the server
./scripts/start-server.sh

# Or start in dev/prod mode
./scripts/start-server.sh --dev
./scripts/start-server.sh --prod
```

**Output:**
```
Web Server: http://localhost:5000
Username:   admin
Password:   admin
Database:   office_app/office_app.db
```

### For Windows Server UI

```bash
git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
cd herdlinx-saas
git checkout deployment/windows-server

# Run startup script (handles all setup)
scripts\start-server.bat

# Configure Pi connection when prompted
# Edit .env and set REMOTE_PI_HOST and PI_API_KEY

# Run again to start
scripts\start-server.bat

# Or use modes
scripts\start-server.bat dev
scripts\start-server.bat prod
```

**Output:**
```
Web Server: http://localhost:5000
Username:   admin
Password:   admin
Database:   office_app\office_app.db
```

## Step-by-Step Deployment

### Step 1: Deploy Raspberry Pi Backend (First)

1. **Get a Raspberry Pi**
   - Raspberry Pi 3B+ or higher recommended
   - With microSD card (32GB+) and power supply

2. **Install Raspberry Pi OS**
   - Download from: https://www.raspberrypi.com/software/
   - Flash to microSD card
   - Boot and initial setup

3. **Clone and Setup**
   ```bash
   git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
   cd herdlinx-saas
   git checkout aj/pi-backend
   ./scripts/setup.sh --skip-update
   ```

4. **Start Backend**
   ```bash
   ./scripts/start.sh
   ```

5. **Save API Key**
   - Copy the displayed API key: `hxb_xxxxxxxxxxxxx`
   - You'll need this for Server UI

6. **Optional: Run as Service**
   ```bash
   sudo cp scripts/herdlinx-pi.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable herdlinx-pi
   sudo systemctl start herdlinx-pi
   ```

### Step 2: Deploy Server UI (After Pi Backend is Running)

#### Option A: Linux Server

1. **Get a Linux Server**
   - Ubuntu 18.04+, Debian 10+, CentOS 8+, Rocky Linux 8+
   - 2GB RAM, 1GB disk
   - Network access to Pi

2. **Clone and Setup**
   ```bash
   git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
   cd herdlinx-saas
   git checkout deployment/linux-server
   ./scripts/setup-server.sh
   ```

3. **Configure Connection**
   ```bash
   nano .env
   # Set: REMOTE_PI_HOST=<pi-ip>
   # Set: PI_API_KEY=<from-step-1>
   ```

4. **Start Server**
   ```bash
   ./scripts/start-server.sh
   ```

5. **Access Web UI**
   - Open: `http://<server-ip>:5000`
   - Login: `admin` / `admin`
   - Change password immediately!

6. **Optional: Production Setup**
   - Setup systemd service
   - Setup reverse proxy (nginx)
   - Setup SSL/TLS
   - See: `scripts/LINUX-DEPLOYMENT.md`

#### Option B: Windows Server

1. **Get a Windows Server**
   - Windows Server 2016+ or Windows 10/11 Pro
   - 2GB RAM, 1GB disk
   - Network access to Pi
   - Python 3.8+ installed (from python.org)

2. **Clone Repository**
   ```bash
   git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
   cd herdlinx-saas
   git checkout deployment/windows-server
   ```

3. **Start Server**
   ```batch
   scripts\start-server.bat
   ```

4. **Configure Connection**
   - Script creates `.env`
   - Edit `.env`:
     ```ini
     REMOTE_PI_HOST=<pi-ip>
     PI_API_KEY=<from-step-1>
     ```

5. **Start Again**
   ```batch
   scripts\start-server.bat
   ```

6. **Access Web UI**
   - Open: `http://localhost:5000`
   - Login: `admin` / `admin`
   - Change password immediately!

7. **Optional: Auto-Start**
   - Setup Task Scheduler
   - Or use NSSM for Windows Service
   - See: `scripts/WINDOWS-DEPLOYMENT.md`

## Data Flow

### LoRa Data Collection

```
LoRa Device
    │
    ├─ Sends payload: hxb:12345:LF:UHF
    │
    ▼
Pi Backend (/api/lora/receive)
    │
    ├─ Buffer (dedup check)
    ├─ Validate (format check)
    ├─ Process (parse payload)
    │
    ▼
Local Database (Pi)
    │
    ├─ Insert into batches
    ├─ Insert into cattle
    ├─ Update pens
    │
    ▼
Sync to Server (every 10 seconds)
    │
    ├─ /api/sync/changes (incremental)
    ├─ WebSocket (real-time notification)
    │
    ▼
Server Database (Replica)
    │
    ▼
Web UI (Real-time updates)
```

### Real-Time Updates

```
Pi Backend receives data
    │
    ├─ Write to local database
    ├─ Broadcast via WebSocket
    │
    ▼
Server UI WebSocket Client
    │
    ├─ Receive update notification
    ├─ Update local database immediately
    ├─ Refresh web UI in real-time
    │
    ▼
Periodic Sync (every 10 seconds)
    │
    ├─ Pull changes from Pi
    ├─ Verify consistency
    ├─ Update any missed records
```

## Configuration Reference

### Pi Backend (.env)

```ini
# Application
IS_PI_BACKEND=True
FLASK_ENV=development

# Database
SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db

# Security
PI_API_KEY=hxb_xxxxxxxxxxxxx    # Generated by setup.sh
JWT_SECRET=xxxxxxxxxxxxx        # Generated by setup.sh

# Server
PORT=5001
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR

# Development
DEBUG=False
```

### Server UI (.env)

```ini
# Application
IS_SERVER_UI=True
FLASK_ENV=development

# Database (Replica)
SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db

# Pi Backend Connection (REQUIRED)
REMOTE_PI_HOST=192.168.1.100
REMOTE_PI_PORT=5001
PI_API_KEY=hxb_xxxxxxxxxxxxx    # From Pi backend setup
USE_SSL_FOR_PI=True
USE_SELF_SIGNED_CERT=True

# Sync Configuration
DB_SYNC_INTERVAL=10             # Seconds between syncs

# Server
PORT=5000
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO

# Development
DEBUG=False
```

## Monitoring and Health Checks

### Pi Backend Health

```bash
# Health endpoint
curl -k https://192.168.1.100:5001/api/remote/health

# Response
{
  "status": "healthy",
  "timestamp": "2024-11-03T12:34:56"
}
```

### Server UI Sync Status

```bash
# Sync status endpoint
curl http://localhost:5000/office/api/sync-status

# Response
{
  "status": "healthy",
  "last_sync": "2024-11-03T12:34:56",
  "records_synced": 1234,
  "sync_interval": 10
}
```

## Troubleshooting

### Connection Issues

**Test network connectivity:**
```bash
ping <pi-ip>                    # Ping Pi from Server
ping <server-ip>                # Ping Server from Pi
```

**Test API endpoint:**
```bash
curl -k https://<pi-ip>:5001/api/remote/health
```

**Check .env configuration:**
```bash
grep REMOTE_PI .env             # Verify IP and API key
grep PI_API_KEY .env
```

### Database Issues

**Reset database on Server:**
```bash
rm office_app/office_app.db     # Delete replica
# Server will auto-sync from Pi on next sync cycle
```

**Reset database on Pi:**
```bash
sudo systemctl stop herdlinx-pi  # Stop service
rm office_app/office_app.db     # Delete database
sudo systemctl start herdlinx-pi # Restart (creates empty DB)
```

### Performance Issues

**Reduce sync frequency:**
```ini
# In .env
DB_SYNC_INTERVAL=30
```

**Check resource usage:**
```bash
# On Pi
top -b -n 1 | head -20

# On Server
top -b -n 1 | head -20
```

**Optimize database:**
```bash
sqlite3 office_app/office_app.db "VACUUM;"
```

## Production Checklist

### Raspberry Pi Backend

- [ ] Install on Raspberry Pi 3B+ or higher
- [ ] Configure static IP address
- [ ] Run systemd service auto-start
- [ ] Setup firewall (port 5001 only from Server IP)
- [ ] Configure automated backups
- [ ] Monitor disk space and memory
- [ ] Setup alerting for errors
- [ ] Document API key securely
- [ ] Test LoRa device reception
- [ ] Verify data is being processed

### Linux Server UI

- [ ] Install on Ubuntu 18.04+ or equivalent
- [ ] Configure static IP address
- [ ] Setup systemd service auto-start
- [ ] Setup reverse proxy (nginx/Apache)
- [ ] Setup SSL/TLS (Let's Encrypt recommended)
- [ ] Configure firewall (port 80/443)
- [ ] Setup log rotation
- [ ] Setup automated backups
- [ ] Monitor disk space and memory
- [ ] Setup alerting for sync failures
- [ ] Change default admin password
- [ ] Setup user accounts

### Windows Server UI

- [ ] Install Python 3.8+
- [ ] Configure static IP address
- [ ] Setup Task Scheduler or NSSM auto-start
- [ ] Setup Windows Firewall exceptions
- [ ] Configure automated backups
- [ ] Monitor disk space and memory
- [ ] Change default admin password
- [ ] Setup user accounts
- [ ] Test web access from other machines
- [ ] Configure reverse proxy (optional)

## Support and Documentation

### Documentation Files

**Pi Backend:**
- `STARTUP_GUIDE.md` - Quick start guide
- `scripts/README.md` - Detailed script documentation
- `DATABASE_REPLICATION.md` - Sync architecture
- `DISTRIBUTED_ARCHITECTURE.md` - System design

**Server UI:**
- `SERVER-STARTUP-GUIDE.md` - Cross-platform quick start
- `scripts/LINUX-DEPLOYMENT.md` - Linux-specific guide
- `scripts/WINDOWS-DEPLOYMENT.md` - Windows-specific guide
- `IMPLEMENTATION_SUMMARY.md` - Full system overview

### Getting Help

1. **Check logs:**
   ```bash
   tail -f logs/app.log          # Real-time
   grep ERROR logs/app.log       # Errors only
   ```

2. **Enable debug mode:**
   ```ini
   # In .env
   DEBUG=True
   LOG_LEVEL=DEBUG
   ```

3. **Test endpoints:**
   ```bash
   curl http://localhost:5000/office/api/sync-status
   curl -k https://192.168.1.100:5001/api/remote/health
   ```

4. **Check GitHub Issues:**
   - https://github.com/CoreNeuroHub/herdlinx-saas/issues

## Next Steps

1. **Deploy Pi Backend** (if not already done)
   - Clone `aj/pi-backend` branch
   - Run `./scripts/setup.sh`
   - Run `./scripts/start.sh`

2. **Deploy Server UI** (Linux or Windows)
   - Clone appropriate deployment branch
   - Configure Pi connection in `.env`
   - Run startup script

3. **Configure Web UI**
   - Login with admin/admin
   - Change default password
   - Create user accounts
   - Configure sync settings

4. **Monitor System**
   - Watch sync status
   - Monitor database size
   - Check error logs
   - Verify LoRa data reception

5. **Production Setup**
   - Enable auto-start services
   - Setup automated backups
   - Configure monitoring/alerting
   - Document deployment

## Summary

HerdLinx provides a distributed architecture with:

- **Raspberry Pi Backend**: Collects LoRa data, buffers, deduplicates, processes, and stores locally
- **Server UI**: Provides web interface, replicates database, syncs every 10 seconds, real-time WebSocket updates
- **Multiple Deployment Options**: Linux or Windows servers
- **Complete Automation**: Setup and startup scripts handle all configuration

The system is resilient, scalable, and production-ready. Happy deploying!
