# HerdLinx Server UI - Linux Deployment Guide

Complete guide for deploying HerdLinx Server UI on Linux servers.

## Prerequisites

### System Requirements

- Linux (Ubuntu 18.04+, Debian 10+, CentOS 8+, Rocky Linux 8+)
- 2GB RAM minimum (4GB recommended)
- 1GB disk space
- Network access to Raspberry Pi backend
- sudo access for installation

### Required Packages

Most Linux distributions include these, but verify:

```bash
# Check Python 3
python3 --version

# Check pip
pip3 --version
```

## Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
cd herdlinx-saas
git checkout deployment/linux-server
```

Or download:

```bash
wget https://github.com/CoreNeuroHub/herdlinx-saas/archive/deployment/linux-server.zip
unzip deployment/linux-server.zip
cd herdlinx-saas-deployment-linux-server
```

### Step 2: Get Pi Backend Details

Collect from your Raspberry Pi:

```
Pi IP Address:    192.168.1.100 (example)
Pi API Key:       hxb_xxxxxxxxxxxxx (from ./scripts/setup.sh output)
```

### Step 3: Run Setup

```bash
chmod +x scripts/setup-server.sh
./scripts/setup-server.sh
```

**What it does:**
- Updates system packages
- Installs Python 3, pip, venv
- Creates virtual environment
- Installs dependencies
- Creates `.env` file

**To skip slow package updates:**

```bash
./scripts/setup-server.sh --skip-update
```

### Step 4: Configure Pi Connection

Edit the `.env` file:

```bash
nano .env
```

Update these values:

```ini
REMOTE_PI_HOST=192.168.1.100         # Your Pi's IP
PI_API_KEY=hxb_your_api_key_here     # From Pi backend
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 5: Start the Server

```bash
./scripts/start-server.sh
```

Wait for output showing:
```
📍 Server:       http://localhost:5000
👤 Default User: admin
🔑 Default Pass: admin
```

### Step 6: Access the Web UI

1. Open browser on another machine
2. Go to: `http://<server-ip>:5000`
3. Login with `admin` / `admin`

## Startup Modes

### Development Mode

```bash
./scripts/start-server.sh --dev
```

Features:
- Debug logging enabled
- Hot reload on code changes
- Verbose output
- Good for testing

### Production Mode

```bash
./scripts/start-server.sh --prod
```

Features:
- Debug logging disabled
- Optimized performance
- Minimal output
- Good for production

## Configuration

### Environment Variables

Edit `.env`:

```bash
nano .env
```

**Required Settings:**

```ini
# Pi Backend Connection (MUST SET)
REMOTE_PI_HOST=192.168.1.100
PI_API_KEY=hxb_your_api_key_here

# Sync Settings
DB_SYNC_INTERVAL=10              # Sync every 10 seconds

# Server Settings
PORT=5000                         # Web server port
HOST=0.0.0.0                      # Listen on all interfaces

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR

# Development
DEBUG=False
FLASK_ENV=development
```

**SSL/TLS Settings:**

```ini
# For Pi with self-signed certs
USE_SSL_FOR_PI=True
USE_SELF_SIGNED_CERT=True
```

### Change Default Password

After first login:

1. Click "Settings" (top right menu)
2. Click "Change Password"
3. Enter current: `admin`
4. Enter new password
5. Click "Update"

**Important:** Change password immediately for production!

## Running as System Service

For production deployments, run as systemd service:

### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/herdlinx-server.service
```

Paste:

```ini
[Unit]
Description=HerdLinx Server UI Service
Documentation=https://github.com/CoreNeuroHub/herdlinx-saas
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/herdlinx/herdlinx-saas
Environment="PATH=/home/herdlinx/herdlinx-saas/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/herdlinx/herdlinx-saas/venv/bin/python -m office_app.run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=herdlinx-server

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/home/herdlinx/herdlinx-saas

# Resource limits
MemoryLimit=512M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
```

**Important:** Change paths to match your installation:
- `/home/herdlinx/herdlinx-saas` → your actual path
- `User=www-data` → appropriate user

### Step 2: Enable Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable herdlinx-server

# Start the service
sudo systemctl start herdlinx-server

# Check status
sudo systemctl status herdlinx-server
```

### Step 3: Manage Service

```bash
# Start
sudo systemctl start herdlinx-server

# Stop
sudo systemctl stop herdlinx-server

# Restart
sudo systemctl restart herdlinx-server

# View logs
sudo journalctl -u herdlinx-server -f

# Check status
sudo systemctl status herdlinx-server
```

## Common Tasks

### View Logs

**Terminal output (when running directly):**

```bash
# Last 50 lines
tail -50 logs/app.log

# Real-time monitoring
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

**Service logs (when running as systemd service):**

```bash
# Last 50 lines
sudo journalctl -u herdlinx-server -n 50

# Real-time monitoring
sudo journalctl -u herdlinx-server -f

# Search for errors
sudo journalctl -u herdlinx-server | grep ERROR
```

### Stop/Restart Server

**Running directly:**

```bash
# Press Ctrl+C in the terminal
# Or in another terminal:
pkill -f "python -m office_app.run"
```

**Running as service:**

```bash
# Stop
sudo systemctl stop herdlinx-server

# Restart
sudo systemctl restart herdlinx-server
```

### Change Server Port

Edit `.env`:

```bash
nano .env
```

Change:

```ini
PORT=5001
```

Restart:

```bash
./scripts/start-server.sh
```

Or if service:

```bash
sudo systemctl restart herdlinx-server
```

### Check Sync Status

```bash
curl http://localhost:5000/office/api/sync-status
```

Response:

```json
{
  "status": "healthy",
  "last_sync": "2024-11-03T12:34:56",
  "records_synced": 1234,
  "sync_interval": 10
}
```

### Reset Database

```bash
# Stop server
./scripts/start-server.sh
# Press Ctrl+C

# Delete database
rm office_app/office_app.db

# Restart
./scripts/start-server.sh
```

Or if service:

```bash
sudo systemctl stop herdlinx-server
rm office_app/office_app.db
sudo systemctl start herdlinx-server
```

## Reverse Proxy Setup

For production, use nginx or Apache as reverse proxy:

### Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/herdlinx
```

Paste:

```nginx
upstream herdlinx {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Proxy settings
    location / {
        proxy_pass http://herdlinx;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/herdlinx /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## SSL/TLS Certificates

### Use Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Self-Signed Certificate

For testing only:

```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 \
  -keyout /etc/ssl/private/herdlinx.key \
  -out /etc/ssl/certs/herdlinx.crt \
  -days 365 -nodes
```

## Firewall Configuration

### UFW (Ubuntu/Debian)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Firewalld (CentOS/Rocky)

```bash
# Allow HTTP
sudo firewall-cmd --add-service=http --permanent

# Allow HTTPS
sudo firewall-cmd --add-service=https --permanent

# Allow custom port
sudo firewall-cmd --add-port=5000/tcp --permanent

# Reload
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

## Monitoring and Logging

### Monitor System Resources

```bash
# CPU and memory usage
top

# Or use htop (more user-friendly)
sudo apt-get install htop
htop
```

Look for `python` process:
- Memory: Should be < 300MB
- CPU: Should be < 5% when idle

### Rotate Logs

Create logrotate config:

```bash
sudo nano /etc/logrotate.d/herdlinx
```

Paste:

```
/home/herdlinx/herdlinx-saas/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
}
```

## Backup and Recovery

### Automated Backup

Create backup script:

```bash
nano ~/backup-herdlinx.sh
```

Paste:

```bash
#!/bin/bash
BACKUP_DIR="/home/herdlinx/backups"
DB_FILE="/home/herdlinx/herdlinx-saas/office_app/office_app.db"

mkdir -p "$BACKUP_DIR"
cp "$DB_FILE" "$BACKUP_DIR/office_app.db.$(date +%Y%m%d_%H%M%S).backup"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.backup" -mtime +7 -delete
```

Make executable:

```bash
chmod +x ~/backup-herdlinx.sh
```

Schedule with cron:

```bash
crontab -e
```

Add:

```cron
0 2 * * * /home/herdlinx/backup-herdlinx.sh
```

This runs backup at 2 AM daily.

### Restore from Backup

```bash
# Stop service
sudo systemctl stop herdlinx-server

# Restore database
cp office_app/office_app.db.backup office_app/office_app.db

# Restart
sudo systemctl start herdlinx-server
```

## Troubleshooting

### "Port 5000 already in use"

```bash
# Find process
lsof -i :5000

# Kill it
kill -9 <PID>
```

Or use different port in `.env`.

### "Cannot connect to Pi backend"

Check connection:

```bash
# Ping Pi
ping 192.168.1.100

# Or use curl (get cert error is normal)
curl -k https://192.168.1.100:5001/api/remote/health
```

Verify `.env`:

```bash
grep REMOTE_PI .env
```

### "Permission denied" errors

```bash
# Check ownership
ls -la office_app/office_app.db

# Fix if needed
sudo chown www-data:www-data office_app/office_app.db
```

### "Virtual environment not found"

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Dependencies not found"

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database corruption

```bash
# Backup old database
cp office_app/office_app.db office_app/office_app.db.corrupted

# Delete and recreate
rm office_app/office_app.db

# Restart - will recreate
./scripts/start-server.sh
```

## Performance Optimization

### Sync Interval

Edit `.env`:

```ini
# Less frequently for large datasets
DB_SYNC_INTERVAL=30

# More frequently for real-time
DB_SYNC_INTERVAL=5
```

### Database Optimization

```bash
# Vacuum database to free space
sqlite3 office_app/office_app.db "VACUUM;"

# Check database size
du -sh office_app/office_app.db
```

### Memory Management

```bash
# Check memory usage
ps aux | grep python

# Adjust limits in service file
MemoryLimit=1G
```

## Directory Structure

```
/home/herdlinx/herdlinx-saas/
├── scripts/
│   ├── start-server.sh              # Main startup script
│   ├── setup-server.sh              # Setup script
│   └── LINUX-DEPLOYMENT.md          # This file
├── office_app/
│   ├── office_app.db                # SQLite database
│   ├── models/                      # Database models
│   ├── routes/                      # Web routes
│   ├── templates/                   # HTML templates
│   ├── static/                      # CSS, JS, images
│   └── sync_service.py              # Sync worker
├── venv/                            # Virtual environment
├── logs/                            # Application logs
├── .env                             # Configuration
└── requirements.txt                 # Dependencies
```

## Next Steps

1. ✅ Clone repository
2. ✅ Run `./scripts/setup-server.sh`
3. ✅ Edit `.env` with Pi details
4. ✅ Run `./scripts/start-server.sh`
5. ✅ Access at `http://localhost:5000`
6. ✅ Login with admin/admin
7. ✅ Change default password
8. ✅ (Production) Setup systemd service
9. ✅ (Production) Setup reverse proxy
10. ✅ (Production) Configure SSL/TLS

## Production Checklist

- [ ] Change default password
- [ ] Configure firewall
- [ ] Setup SSL/TLS
- [ ] Setup reverse proxy (nginx/apache)
- [ ] Configure systemd service
- [ ] Setup log rotation
- [ ] Setup automated backups
- [ ] Monitor disk space
- [ ] Monitor memory usage
- [ ] Setup monitoring/alerting (optional)

Enjoy! 🚀
