# HerdLinx Startup Guide

Quick reference for starting HerdLinx Raspberry Pi Backend and Server UI.

## 🎯 Quick Start (Raspberry Pi)

### First Time Only

```bash
# Clone the repository
git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
cd herdlinx-saas

# Checkout Pi backend branch
git checkout aj/pi-backend

# Run one-time setup
./scripts/setup.sh
```

This will:
- Install dependencies
- Generate SSL certificates
- Create configuration
- Display your API key (save it!)

### Every Time (Start the Backend)

```bash
# Option 1: Using script (recommended)
./scripts/start.sh

# Option 2: Development mode
./scripts/start.sh --dev

# Option 3: Production mode
./scripts/start.sh --prod
```

### Or Run as System Service

```bash
# Install systemd service (one-time)
sudo cp scripts/herdlinx-pi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable herdlinx-pi

# Start/stop the service
sudo systemctl start herdlinx-pi
sudo systemctl stop herdlinx-pi
sudo systemctl restart herdlinx-pi

# Check status
sudo systemctl status herdlinx-pi

# View logs
sudo journalctl -u herdlinx-pi -f
```

---

## 🖥️ Quick Start (Remote Server)

### First Time Only

```bash
# Clone the repository
git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
cd herdlinx-saas

# Checkout Server UI branch
git checkout aj/server-ui

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
IS_SERVER_UI=True
REMOTE_PI_HOST=192.168.1.100
REMOTE_PI_PORT=5001
PI_API_KEY=hxb_xxxxxxxxxxxxxxxxxxxxxxxx
DB_SYNC_INTERVAL=10
USE_SSL_FOR_PI=True
USE_SELF_SIGNED_CERT=True
EOF
```

Replace:
- `192.168.1.100` with your Pi's IP address
- `hxb_xxxxxxxxxxxxxxxxxxxxxxxx` with the API key from Pi setup

### Every Time (Start the Server)

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python -m office_app.run
```

Access at: `http://localhost:5000`
- Username: `admin`
- Password: `admin`

---

## 📋 What the Scripts Do

### `scripts/setup.sh`

**One-time setup for Raspberry Pi**

```bash
./scripts/setup.sh
```

Handles:
- System updates
- Dependency installation
- Virtual environment creation
- Python package installation
- SSL certificate generation
- Configuration file setup

### `scripts/start.sh`

**Start the Pi backend application**

```bash
./scripts/start.sh              # Default mode
./scripts/start.sh --dev        # Development (debug on)
./scripts/start.sh --prod       # Production (debug off)
./scripts/start.sh --help       # Show help
```

Handles:
- Environment activation
- Dependency verification
- Certificate checking
- Application startup
- Port availability check

### `scripts/herdlinx-pi.service`

**Systemd service for auto-start**

Install:
```bash
sudo cp scripts/herdlinx-pi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable herdlinx-pi
```

Manage:
```bash
sudo systemctl start herdlinx-pi
sudo systemctl stop herdlinx-pi
sudo systemctl restart herdlinx-pi
sudo systemctl status herdlinx-pi
```

---

## 🔑 Important: Save Your API Key

After running `./scripts/setup.sh` on the Pi, you'll see:

```
Your API Key: hxb_6f8a9c2d1e5b4a3f7g8h9i0j
```

**Save this!** You need it for Server UI configuration.

---

## ✅ Verify Everything Works

### On Pi

```bash
# Check if running
curl https://localhost:5001/api/remote/health

# Should return:
# {"status": "healthy", "timestamp": "..."}
```

### On Server

```bash
# Start server
python -m office_app.run

# Open browser to: http://localhost:5000
# Login with: admin / admin

# Check sync status
curl http://localhost:5000/office/api/sync-status
```

---

## 📁 Directory Structure

```
herdlinx-saas/
├── scripts/
│   ├── start.sh               # Main startup script
│   ├── setup.sh               # One-time setup
│   ├── herdlinx-pi.service    # Systemd service
│   └── README.md              # Detailed guide
├── office_app/
│   ├── office_app.db          # Database (auto-created)
│   ├── certs/                 # SSL certificates
│   ├── models/                # Database models
│   ├── routes/                # API routes
│   ├── utils/                 # Utilities
│   └── templates/             # HTML templates
├── venv/                       # Virtual environment (auto-created)
├── logs/                       # Application logs (auto-created)
├── .env                        # Configuration (auto-created)
└── requirements.txt            # Dependencies
```

---

## 🚀 Common Commands

### Raspberry Pi

```bash
# Start application
./scripts/start.sh

# Check if running
curl https://localhost:5001/api/remote/health

# View logs
tail -f logs/app.log

# Check sync API
curl -X GET "https://localhost:5001/api/sync/changes" \
  -H "X-API-Key: hxb_xxxxx"

# Restart service
sudo systemctl restart herdlinx-pi

# Check service status
sudo systemctl status herdlinx-pi

# View service logs
sudo journalctl -u herdlinx-pi -f
```

### Remote Server

```bash
# Activate venv
source venv/bin/activate

# Start application
python -m office_app.run

# Check sync status
curl http://localhost:5000/office/api/sync-status

# View logs
tail -f logs/app.log

# Query database
sqlite3 office_app/office_app.db ".tables"
```

---

## 🔧 Troubleshooting

### "Port already in use"

```bash
# Find process on port 5001
lsof -i :5001

# Kill it
kill -9 <PID>

# Or use different port in .env
echo "PORT=5002" >> .env
```

### "SSL certificate error"

```bash
# Regenerate certificates
python -m office_app.generate_certs

# Check if files exist
ls -la office_app/certs/
```

### "Dependencies not found"

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Virtual environment not found"

```bash
# Recreate it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Database connection error"

```bash
# Check database file
ls -la office_app/office_app.db

# Reset database (stops app first!)
sudo systemctl stop herdlinx-pi
rm office_app/office_app.db

# Restart (auto-creates new database)
sudo systemctl start herdlinx-pi
```

---

## 📊 Monitoring

### Check Sync Status

```bash
curl http://server:5000/office/api/sync-status
```

### View Recent Logs

```bash
# Last 20 lines
tail -20 logs/app.log

# Last 100 lines of errors
grep ERROR logs/app.log | tail -100

# Real-time monitoring
tail -f logs/app.log
```

### Database Size

```bash
ls -lh office_app/office_app.db
du -sh .
```

---

## 🛡️ Security Notes

1. **API Key**: Keep your `PI_API_KEY` secret
2. **SSL Certificates**: Generate proper certificates for production
3. **Firewall**: Restrict access to port 5001 to Server IP only
4. **Backups**: Regular database backups recommended

---

## 📚 Detailed Documentation

For comprehensive information, see:

- **`scripts/README.md`** - Detailed startup script guide
- **`DATABASE_REPLICATION.md`** - Sync architecture
- **`DISTRIBUTED_ARCHITECTURE.md`** - System design
- **`IMPLEMENTATION_SUMMARY.md`** - Full overview

---

## ⚡ Quick Reference

| Task | Command |
|------|---------|
| First setup (Pi) | `./scripts/setup.sh` |
| Start Pi app | `./scripts/start.sh` |
| Start Pi (dev) | `./scripts/start.sh --dev` |
| Start Pi (prod) | `./scripts/start.sh --prod` |
| Start service | `sudo systemctl start herdlinx-pi` |
| Stop service | `sudo systemctl stop herdlinx-pi` |
| Check service | `sudo systemctl status herdlinx-pi` |
| View service logs | `sudo journalctl -u herdlinx-pi -f` |
| Start Server | `python -m office_app.run` |
| Check sync | `curl http://localhost:5000/office/api/sync-status` |
| Check Pi health | `curl https://localhost:5001/api/remote/health` |

---

## 🎯 Next Steps

1. Run `./scripts/setup.sh` on Pi (first time only)
2. Note the API key
3. Start Pi with `./scripts/start.sh`
4. Configure Server with Pi's IP and API key
5. Start Server with `python -m office_app.run`
6. Open `http://localhost:5000` in browser
7. Login with `admin` / `admin`

Enjoy! 🚀
