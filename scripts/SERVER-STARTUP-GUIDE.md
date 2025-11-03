# HerdLinx Server UI - Startup Guide

Quick reference for starting HerdLinx Server UI on Windows or Linux.

## Quick Start

### Linux Server

```bash
# One-time setup (first time only)
./scripts/setup-server.sh

# Start the Server UI
./scripts/start-server.sh
```

### Windows Server

```bash
# One-time setup (first time only)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Start the Server UI
scripts\start-server.bat
```

Or with development/production modes:

```bash
scripts\start-server.bat dev       # Development mode
scripts\start-server.bat prod      # Production mode
```

## Before Starting

### Get Pi Backend API Key

Before running the Server UI, you need:
1. The Raspberry Pi's IP address
2. The API key from Pi backend setup (shown after `./scripts/setup.sh`)

### Configure .env File

Edit `.env` and set:

```bash
REMOTE_PI_HOST=192.168.1.100          # Your Pi's IP address
PI_API_KEY=hxb_xxxxxxxxxxxxx          # From Pi backend setup
```

## Startup Scripts

### Linux: `setup-server.sh`

One-time setup for Linux servers.

**What it does:**
- Updates system packages
- Installs Python 3, pip, venv
- Creates virtual environment
- Installs Python dependencies
- Creates `.env` configuration file

**Usage:**
```bash
./scripts/setup-server.sh              # Default (updates system)
./scripts/setup-server.sh --skip-update # Skip system package update
./scripts/setup-server.sh --help        # Show help
```

**Requirements:**
- Linux (Debian-based: Ubuntu, Debian, Raspberry Pi OS)
- Internet connection
- sudo access for system installations

### Linux: `start-server.sh`

Main startup script for Linux servers.

**What it does:**
- Activates virtual environment
- Checks Python dependencies
- Creates .env if missing
- Starts Flask application on port 5000

**Usage:**
```bash
./scripts/start-server.sh              # Start with defaults
./scripts/start-server.sh --dev        # Development mode (debug on)
./scripts/start-server.sh --prod       # Production mode (debug off)
./scripts/start-server.sh --help       # Show help
```

**Output:**
```
═══════════════════════════════════════════════════════════
  HerdLinx Server UI Startup
═══════════════════════════════════════════════════════════

✓ Python 3 found: Python 3.9.2
✓ pip3 found
✓ Virtual environment activated
✓ Dependencies installed
✓ .env file exists
✓ Logs directory ready: /home/user/herdlinx-saas/logs

═══════════════════════════════════════════════════════════
HerdLinx Server UI is starting...
═══════════════════════════════════════════════════════════

📍 Server:       http://localhost:5000
👤 Default User: admin
🔑 Default Pass: admin
📦 Database:     /home/user/herdlinx-saas/office_app/office_app.db
📋 Logs:         /home/user/herdlinx-saas/logs
🔧 Mode:         development

Press Ctrl+C to stop
```

### Windows: `start-server.bat`

Startup script for Windows servers.

**Usage:**
```batch
start-server.bat              # Start with defaults
start-server.bat dev          # Development mode
start-server.bat prod         # Production mode
start-server.bat help         # Show help
```

**Features:**
- Auto-creates virtual environment
- Auto-installs dependencies
- Auto-creates .env if missing
- Shows startup information
- Works in Command Prompt or PowerShell

## First Time Setup

### Linux

1. **Clone and setup:**
   ```bash
   git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
   cd herdlinx-saas
   git checkout aj/server-ui
   ```

2. **Run setup:**
   ```bash
   ./scripts/setup-server.sh
   ```

3. **Configure Pi connection:**
   ```bash
   nano .env
   # Edit REMOTE_PI_HOST and PI_API_KEY
   ```

4. **Start the server:**
   ```bash
   ./scripts/start-server.sh
   ```

5. **Access in browser:**
   ```
   http://localhost:5000
   Username: admin
   Password: admin
   ```

### Windows

1. **Clone and setup:**
   ```bash
   git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
   cd herdlinx-saas
   git checkout aj/server-ui
   ```

2. **Run startup script:**
   ```bash
   scripts\start-server.bat
   ```

3. **Configure Pi connection:**
   - Open `.env` in text editor
   - Edit `REMOTE_PI_HOST` and `PI_API_KEY`
   - Save

4. **Run again:**
   ```bash
   scripts\start-server.bat
   ```

5. **Access in browser:**
   ```
   http://localhost:5000
   Username: admin
   Password: admin
   ```

## Configuration

### Environment Variables (.env)

**Required:**
- `REMOTE_PI_HOST` - Pi backend IP address (e.g., 192.168.1.100)
- `PI_API_KEY` - API key from Pi backend setup

**Optional:**
- `REMOTE_PI_PORT` - Pi port (default: 5001)
- `DB_SYNC_INTERVAL` - Sync interval in seconds (default: 10)
- `PORT` - Server UI port (default: 5000)
- `FLASK_ENV` - Flask environment (development/production)

### Default Credentials

```
Username: admin
Password: admin
```

Change these in the database after first login!

## Common Tasks

### Start in Development Mode

```bash
# Linux
./scripts/start-server.sh --dev

# Windows
scripts\start-server.bat dev
```

Features:
- Debug logging enabled
- Hot reload on code changes
- More verbose output

### Start in Production Mode

```bash
# Linux
./scripts/start-server.sh --prod

# Windows
scripts\start-server.bat prod
```

Features:
- Debug logging disabled
- Optimized performance
- Minimal output

### Access Web Server

1. Open browser to `http://localhost:5000`
2. Login with `admin` / `admin`
3. Configure/monitor data from Pi backend

### View Logs

**Linux:**
```bash
# Last 50 lines
tail -50 logs/app.log

# Real-time monitoring
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

**Windows:**
```cmd
# View log file
type logs\app.log

# Real-time (using PowerShell)
Get-Content logs\app.log -Wait
```

### Check Database Sync

In web browser:
```
http://localhost:5000/office/api/sync-status
```

Shows:
- Last sync time
- Number of records synced
- Sync status (healthy/error)

### Reset Database

**Stop server first!**

```bash
# Linux
rm office_app/office_app.db

# Windows
del office_app\office_app.db
```

Then restart the server - database will auto-create.

## Troubleshooting

### "Port 5000 already in use"

**Linux:**
```bash
# Find process
lsof -i :5000

# Kill it
kill -9 <PID>
```

**Windows:**
```cmd
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

Or change port in `.env`:
```
PORT=5001
```

### "Cannot connect to Pi backend"

Check:
1. Pi is running: `ping <pi-ip>`
2. `.env` has correct IP and API key
3. Network connection between server and Pi
4. Firewall allows port 5001

### "Virtual environment not found"

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### "Dependencies not found"

**Linux:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```batch
venv\Scripts\activate
pip install -r requirements.txt
```

### "Database connection error"

```bash
# Check database file exists
ls -la office_app/office_app.db

# Or remove and recreate
rm office_app/office_app.db
```

## Directory Structure

```
herdlinx-saas/
├── scripts/
│   ├── start-server.sh         # Linux startup script
│   ├── start-server.bat        # Windows startup script
│   ├── setup-server.sh         # Linux setup script
│   └── SERVER-STARTUP-GUIDE.md # This file
├── office_app/
│   ├── office_app.db           # SQLite database (auto-created)
│   ├── models/                 # Database models
│   ├── routes/                 # Web routes
│   ├── templates/              # HTML templates
│   ├── static/                 # CSS, JavaScript, images
│   └── sync_service.py         # Database sync worker
├── venv/                        # Virtual environment (auto-created)
├── logs/                        # Application logs (auto-created)
├── .env                         # Configuration (auto-created)
└── requirements.txt             # Python dependencies
```

## Performance Notes

### Sync Settings

`DB_SYNC_INTERVAL=10` (seconds)
- Slower = less network traffic, more latency
- Faster = more responsive, more network traffic

For production, consider:
- `DB_SYNC_INTERVAL=30` for large datasets
- `DB_SYNC_INTERVAL=5` for real-time requirements

### Resource Usage

Memory: ~150-200MB (Flask + SQLite)
CPU: Minimal when idle, ~5-10% during sync

To reduce memory usage:
- Close unused browser tabs
- Reduce `DB_SYNC_INTERVAL`

## Getting Help

Check logs for errors:
```bash
# Last 100 lines
tail -100 logs/app.log

# Search for errors
grep -i error logs/app.log

# Real-time monitoring
tail -f logs/app.log
```

## Next Steps

1. ✅ Run setup.sh (first time only)
2. ✅ Configure .env with Pi details
3. ✅ Start Server UI with start.sh
4. ✅ Access web UI at http://localhost:5000
5. ✅ Login with admin / admin
6. ✅ Change default password
7. ✅ Monitor data sync from Pi backend

Enjoy! 🚀
