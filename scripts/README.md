# HerdLinx Raspberry Pi Backend - Startup Scripts

This directory contains scripts to simplify starting and managing the HerdLinx Raspberry Pi backend.

## Quick Start

```bash
# One-time setup (first time only)
./scripts/setup.sh

# Start the application
./scripts/start.sh

# Or with options
./scripts/start.sh --dev      # Development mode
./scripts/start.sh --prod     # Production mode
./scripts/start.sh --help     # Show help
```

## Scripts

### 1. `setup.sh` - One-Time Setup

Run this once to prepare your Raspberry Pi.

**What it does:**
- Updates system packages
- Installs Python 3, pip, venv
- Installs system dependencies (git, openssl, build tools)
- Creates virtual environment
- Installs Python dependencies
- Generates SSL certificates
- Creates `.env` configuration file

**Usage:**
```bash
./scripts/setup.sh
```

**Requirements:**
- Raspberry Pi OS (Debian-based Linux)
- Internet connection
- sudo access for system installations

**Output:**
- Creates `venv/` directory
- Generates `office_app/certs/` directory with SSL certificates
- Creates `.env` file with API key

### 2. `start.sh` - Application Startup

Run this to start the HerdLinx backend application.

**What it does:**
- Activates virtual environment
- Checks system dependencies
- Verifies SSL certificates
- Loads environment configuration
- Starts Flask application on port 5001

**Usage:**
```bash
# Default mode (development)
./scripts/start.sh

# Development mode (debug logging, hot reload)
./scripts/start.sh --dev

# Production mode (minimal logging)
./scripts/start.sh --prod

# Show help
./scripts/start.sh --help
```

**Options:**

| Option | Mode | Description |
|--------|------|-------------|
| (none) | Auto | Uses FLASK_ENV from .env |
| `--dev` | Development | DEBUG=True, LOG_LEVEL=DEBUG |
| `--prod` | Production | DEBUG=False, LOG_LEVEL=WARNING |
| `--help` | Help | Show help message |

**Output:**
```
═══════════════════════════════════════════════════════════
  HerdLinx Raspberry Pi Backend Startup
═══════════════════════════════════════════════════════════

✓ Python 3 found: Python 3.9.2
✓ pip3 found
✓ Virtual environment activated
✓ Dependencies installed
✓ SSL certificates already exist
✓ .env file created
✓ Logs directory ready: /home/pi/herdlinx-saas/logs
✓ Port 5001 is available

════════════════════════════════════════════════════════════
HerdLinx Raspberry Pi Backend is starting...
════════════════════════════════════════════════════════════

📍 API Server:      https://192.168.1.100:5001
🔐 API Key:         hxb_6f8a...9i0j
📦 Database:        /home/pi/herdlinx-saas/office_app/office_app.db
📋 Logs:            /home/pi/herdlinx-saas/logs
🔧 Mode:            development

Press Ctrl+C to stop
```

### 3. `herdlinx-pi.service` - Systemd Service

Install this to run HerdLinx as a system service (auto-start on boot).

**Installation:**

```bash
# Copy to systemd directory
sudo cp scripts/herdlinx-pi.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable herdlinx-pi

# Start the service
sudo systemctl start herdlinx-pi

# Check status
sudo systemctl status herdlinx-pi
```

**Management:**

```bash
# Start service
sudo systemctl start herdlinx-pi

# Stop service
sudo systemctl stop herdlinx-pi

# Restart service
sudo systemctl restart herdlinx-pi

# View logs
sudo journalctl -u herdlinx-pi -f

# Check if running
sudo systemctl status herdlinx-pi

# Disable auto-start
sudo systemctl disable herdlinx-pi
```

**Configuration:**

Edit `/etc/systemd/system/herdlinx-pi.service` to customize:
- `User=pi` - Which user runs the service
- `WorkingDirectory=/home/pi/herdlinx-saas` - Project path
- `MemoryLimit=512M` - Memory limit
- `CPUQuota=80%` - CPU quota

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart herdlinx-pi
```

## Environment Setup

Both scripts use a `.env` file for configuration. This is created automatically by `setup.sh`.

**Location:** `/home/pi/herdlinx-saas/.env`

**Contents:**
```bash
IS_PI_BACKEND=True
FLASK_ENV=development
SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db
PI_API_KEY=hxb_6f8a9c2d1e5b4a3f7g8h9i0j  # Your unique key
JWT_SECRET=...
PORT=5001
HOST=0.0.0.0
LOG_LEVEL=INFO
DEBUG=False
```

**Important:** Save your `PI_API_KEY` - you'll need it to configure the Server UI!

## SSL Certificates

Self-signed SSL certificates are automatically generated in `office_app/certs/`:
- `server.crt` - Certificate
- `server.key` - Private key

Valid for 365 days. After expiration, regenerate:
```bash
python -m office_app.generate_certs
```

## First Time Setup

1. **Initial Setup (one time)**
   ```bash
   ./scripts/setup.sh
   ```
   This will:
   - Install all dependencies
   - Generate certificates
   - Create configuration
   - Display your API key

2. **Save Your API Key**
   The script will show something like:
   ```
   Your API Key: hxb_6f8a9c2d1e5b4a3f7g8h9i0j
   ```
   Copy this - you need it for Server UI!

3. **Start the Application**
   ```bash
   ./scripts/start.sh
   ```

4. **Verify It's Running**
   ```bash
   curl https://localhost:5001/api/remote/health
   ```
   You should see:
   ```json
   {"status": "healthy", "timestamp": "..."}
   ```

## Common Tasks

### Check Status
```bash
# If running with systemd
sudo systemctl status herdlinx-pi

# If running in terminal
# Press Ctrl+C to see statistics
```

### View Logs

**With systemd:**
```bash
sudo journalctl -u herdlinx-pi -f
```

**With script:**
```bash
tail -f logs/app.log
```

**With output:**
```bash
grep ERROR logs/app.log
grep sync logs/app.log
```

### Restart Application

**With systemd:**
```bash
sudo systemctl restart herdlinx-pi
```

**With script:**
```bash
# Press Ctrl+C to stop
# Run again to restart
./scripts/start.sh
```

### Regenerate Configuration

```bash
# Backup current
cp .env .env.backup

# Remove to regenerate
rm .env

# Start script will create new one
./scripts/start.sh
```

### Reset Database

```bash
# Stop the application
sudo systemctl stop herdlinx-pi
# Or Ctrl+C if running in terminal

# Remove database
rm office_app/office_app.db

# Start again
sudo systemctl start herdlinx-pi
# Or ./scripts/start.sh
```

### Change Port

Edit `.env`:
```bash
PORT=5002  # Change from 5001
```

Restart:
```bash
sudo systemctl restart herdlinx-pi
```

## Troubleshooting

### "Port 5001 already in use"

```bash
# Find process using port
lsof -i :5001

# Kill the process
kill -9 <PID>

# Or use different port
echo "PORT=5002" >> .env
```

### "Certificate generation failed"

```bash
# Install openssl
sudo apt-get install openssl

# Or regenerate
python -m office_app.generate_certs
```

### "Virtual environment not found"

```bash
# Recreate it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied"

```bash
# Make scripts executable
chmod +x scripts/start.sh scripts/setup.sh

# Or run with bash
bash scripts/start.sh
```

### Check if database initialized

```bash
sqlite3 office_app/office_app.db ".tables"

# Should show: batches cattle lora_payload_buffer pens users
```

## Production Deployment

For production use with systemd service:

1. **Run setup**
   ```bash
   ./scripts/setup.sh
   ```

2. **Update .env for production**
   ```bash
   FLASK_ENV=production
   LOG_LEVEL=WARNING
   DEBUG=False
   ```

3. **Install systemd service**
   ```bash
   sudo cp scripts/herdlinx-pi.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable herdlinx-pi
   sudo systemctl start herdlinx-pi
   ```

4. **Monitor logs**
   ```bash
   sudo journalctl -u herdlinx-pi -f
   ```

5. **Setup backup**
   ```bash
   # Add to crontab for daily backup
   0 2 * * * /home/pi/herdlinx-saas/scripts/backup.sh
   ```

## Performance Optimization

### Memory Usage
Edit `.env`:
```bash
# Reduce flask debug overhead
DEBUG=False
```

Edit `herdlinx-pi.service`:
```ini
MemoryLimit=1G  # Increase if needed
```

### CPU Usage
```ini
CPUQuota=90%  # Increase CPU quota
```

### Database Performance
```bash
# Vacuum database (cleanup)
sqlite3 office_app/office_app.db "VACUUM;"

# Check for large tables
sqlite3 office_app/office_app.db ".stat"
```

## Getting Help

Check logs for errors:
```bash
# Last 50 lines
tail -50 logs/app.log

# Search for errors
grep -i error logs/app.log

# Real-time monitoring
tail -f logs/app.log
```

View help:
```bash
./scripts/start.sh --help
```

## Files and Directories

```
herdlinx-saas/
├── scripts/                    # This directory
│   ├── start.sh               # Main startup script
│   ├── setup.sh               # One-time setup
│   ├── herdlinx-pi.service    # Systemd service file
│   └── README.md              # This file
├── office_app/
│   ├── office_app.db          # SQLite database (created at runtime)
│   ├── certs/                 # SSL certificates
│   │   ├── server.crt
│   │   └── server.key
│   └── ...
├── venv/                       # Virtual environment (created by setup)
├── logs/                       # Application logs (created at runtime)
├── .env                        # Configuration file (created by setup)
└── requirements.txt            # Python dependencies
```

## Next Steps

1. After startup, configure Server UI with your API key
2. Monitor logs for any errors
3. Test API endpoints
4. Setup automatic backups

Enjoy! 🚀
