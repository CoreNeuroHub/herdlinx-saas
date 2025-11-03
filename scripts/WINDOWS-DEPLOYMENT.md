# HerdLinx Server UI - Windows Deployment Guide

Complete guide for deploying HerdLinx Server UI on Windows servers.

## Prerequisites

### System Requirements

- Windows Server 2016+ or Windows 10/11 Pro/Enterprise
- 2GB RAM minimum (4GB recommended)
- 1GB disk space
- Network access to Raspberry Pi backend
- Administrator access for installation

### Required Software

1. **Python 3.8+**
   - Download from: https://www.python.org/downloads/
   - **IMPORTANT**: Check "Add Python to PATH" during installation
   - Verify: `python --version`

2. **Git** (optional, for cloning repo)
   - Download from: https://git-scm.com/download/win
   - Or use GitHub Desktop

## Installation Steps

### Step 1: Clone Repository

**Using Git:**
```bash
git clone https://github.com/CoreNeuroHub/herdlinx-saas.git
cd herdlinx-saas
git checkout deployment/windows-server
```

**Using GitHub Desktop:**
1. Open GitHub Desktop
2. File > Clone Repository
3. Enter: `https://github.com/CoreNeuroHub/herdlinx-saas.git`
4. Choose local path
5. Click "Clone"
6. Switch to `deployment/windows-server` branch

**Manual Download:**
1. Visit: https://github.com/CoreNeuroHub/herdlinx-saas/tree/deployment/windows-server
2. Click "Code" > "Download ZIP"
3. Extract to desired location

### Step 2: Get Pi Backend Details

Before starting, collect from your Raspberry Pi:

```
Pi IP Address:    192.168.1.100 (example)
Pi API Key:       hxb_xxxxxxxxxxxxx (from ./scripts/setup.sh output)
```

### Step 3: Start the Server

Open **Command Prompt** or **PowerShell** in the project directory:

```batch
cd C:\path\to\herdlinx-saas
scripts\start-server.bat
```

**First Time:**
- Script creates virtual environment
- Installs dependencies
- Creates `.env` file

**When prompted:**
1. Edit `.env` file with your Pi details:
   - `REMOTE_PI_HOST=192.168.1.100`
   - `PI_API_KEY=hxb_xxxxxxxxxxxxx`

2. Run script again:
   ```batch
   scripts\start-server.bat
   ```

### Step 4: Access the Web UI

1. Open browser
2. Go to: `http://localhost:5000`
3. Login with:
   - Username: `admin`
   - Password: `admin`

## Startup Modes

### Development Mode (Default)

```batch
scripts\start-server.bat dev
```

- Debug logging enabled
- Hot reload (code changes restart app)
- Verbose output
- Good for testing and troubleshooting

### Production Mode

```batch
scripts\start-server.bat prod
```

- Debug logging disabled
- Optimized performance
- Minimal output
- Good for production deployments

## Configuration

### Edit Settings

All configuration in `.env` file:

```batch
notepad .env
```

Or right-click > Edit with Notepad

**Key Settings:**

```ini
# Pi Backend Connection (REQUIRED)
REMOTE_PI_HOST=192.168.1.100
PI_API_KEY=hxb_your_api_key_here

# Sync Settings
DB_SYNC_INTERVAL=10              # Sync every 10 seconds

# Server Settings
PORT=5000                         # Web server port
HOST=0.0.0.0                      # Listen on all interfaces

# Development
DEBUG=False                        # Set to True for debugging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
```

### Change Default Password

After first login:
1. Click "Settings" (top right)
2. Click "Change Password"
3. Enter current password: `admin`
4. Enter new password
5. Click "Update"

## Common Tasks

### View Logs

```batch
# Open log file
notepad logs\app.log

# Or in Command Prompt
type logs\app.log
```

For real-time logs, use PowerShell:
```powershell
Get-Content logs\app.log -Wait
```

### Stop the Server

- In Terminal: Press `Ctrl+C`
- Task Manager: Find "python.exe", right-click > End task

### Restart the Server

1. Press `Ctrl+C` (stop)
2. Run `scripts\start-server.bat` (start)

### Change Server Port

Edit `.env`:
```ini
PORT=5001
```

Save and restart.

### Reset Database

1. Stop the server (Ctrl+C)
2. Delete database file:
   ```batch
   del office_app\office_app.db
   ```
3. Restart server - database auto-creates

### Clear Python Cache

```batch
# Clear pycache directories
for /d /r . %d in (__pycache__) do @if exist "%d" rmdir /s /q "%d"

# Or delete venv and recreate
rmdir /s venv
scripts\start-server.bat
```

## Troubleshooting

### "Python is not recognized"

Python not in PATH.

**Fix:**
1. Uninstall Python
2. Reinstall from: https://www.python.org/
3. **IMPORTANT**: Check "Add Python to PATH"
4. Restart Command Prompt
5. Verify: `python --version`

### "Port 5000 already in use"

Another program using port 5000.

**Find process:**
```batch
netstat -ano | findstr :5000
```

**Kill process:**
```batch
taskkill /PID <PID_NUMBER> /F
```

**Or use different port:**
```ini
# In .env
PORT=5001
```

### "Cannot connect to Pi backend"

Check connection:

```batch
# Ping Pi
ping 192.168.1.100

# Or use Python
python -c "import requests; print(requests.get('https://192.168.1.100:5001/api/remote/health'))"
```

**Verify .env:**
```ini
REMOTE_PI_HOST=192.168.1.100      # Correct IP?
PI_API_KEY=hxb_xxxxxxxxxxxxx      # Correct key?
USE_SSL_FOR_PI=True
USE_SELF_SIGNED_CERT=True
```

Check Pi is running:
```bash
# On Pi
sudo systemctl status herdlinx-pi
```

### "ModuleNotFoundError"

Dependencies not installed.

**Fix:**
```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### "Cannot create virtual environment"

Python venv issues.

**Fix:**
```batch
# Install venv module
python -m pip install venv

# Recreate venv
rmdir /s venv
python -m venv venv
```

### "SSL Certificate Error"

Self-signed certificate issue.

**Already handled** - script sets:
```ini
USE_SSL_FOR_PI=True
USE_SELF_SIGNED_CERT=True
```

If still issues, disable SSL (dev only):
```ini
USE_SSL_FOR_PI=False
```

## Auto-Start on Boot

### Option 1: Task Scheduler

1. Open **Task Scheduler**
   - Press `Win+R`
   - Type: `taskschd.msc`
   - Press Enter

2. Click "Create Basic Task"

3. General Tab:
   - Name: `HerdLinx Server UI`
   - Check: "Run with highest privileges"

4. Triggers Tab:
   - New > At Startup
   - Click OK

5. Actions Tab:
   - Program: `C:\path\to\herdlinx-saas\scripts\start-server.bat`
   - Start in: `C:\path\to\herdlinx-saas`
   - Click OK

6. Click OK to save

### Option 2: Startup Folder

1. Create batch file: `run-herdlinx.bat`
   ```batch
   @echo off
   cd C:\path\to\herdlinx-saas
   scripts\start-server.bat
   pause
   ```

2. Save to:
   ```
   C:\Users\<username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
   ```

3. Restart Windows - app auto-starts

### Option 3: NSSM (Non-Sucking Service Manager)

For production, use NSSM to run as Windows Service:

1. Download NSSM: https://nssm.cc/download
2. Extract nssm.exe
3. Open Command Prompt as Administrator:
   ```batch
   nssm install HerdLinxServer C:\path\to\herdlinx-saas\scripts\start-server.bat
   nssm start HerdLinxServer
   ```

4. Manage in Services:
   ```batch
   services.msc
   ```

## Windows Firewall

Allow Server UI through firewall:

1. Open **Windows Defender Firewall**
2. Click "Allow an app through firewall"
3. Click "Change settings"
4. Click "Allow another app"
5. Click "Browse" and select `python.exe`
6. Click "Add"
7. Check boxes for "Private" and "Public"
8. Click OK

## Performance Tips

### Reduce Memory Usage

1. Close unused browser tabs
2. Edit `.env`:
   ```ini
   DB_SYNC_INTERVAL=30     # Sync less frequently
   ```

### Improve Responsiveness

1. Edit `.env`:
   ```ini
   DB_SYNC_INTERVAL=5      # Sync more frequently
   ```

### Optimize for Remote Access

1. Edit `.env`:
   ```ini
   LOG_LEVEL=WARNING       # Less logging overhead
   DEBUG=False
   ```

2. Use production mode:
   ```batch
   scripts\start-server.bat prod
   ```

## Monitoring

### Check Sync Status

Open in browser:
```
http://localhost:5000/office/api/sync-status
```

Response shows:
- Last sync time
- Number of records
- Sync status

### Monitor System Performance

Open Task Manager: `Ctrl+Shift+Esc`

Look for `python.exe`:
- Memory: Should be < 300MB
- CPU: Should be < 5% when idle

## Backup and Recovery

### Backup Database

```batch
# Copy database
copy office_app\office_app.db office_app\office_app.db.backup

# Or use scheduled backup
REM Add to Task Scheduler to run daily
```

### Restore Database

```batch
# Stop server first (Ctrl+C)
copy office_app\office_app.db.backup office_app\office_app.db
# Restart server
```

## Upgrading

### Get Latest Updates

```batch
git pull origin deployment/windows-server
```

### Reinstall Dependencies

```batch
pip install --upgrade -r requirements.txt
```

## Uninstall

```batch
# Delete entire directory
rmdir /s herdlinx-saas

# Or keep database and reinstall
rmdir /s /q venv office_app\templates office_app\static
```

## Support

### View Logs

```batch
type logs\app.log
```

### Enable Debug Logging

Edit `.env`:
```ini
DEBUG=True
LOG_LEVEL=DEBUG
```

Restart and check logs for errors.

## Directory Structure

```
C:\herdlinx-saas\
├── scripts\
│   ├── start-server.bat           # Main startup script
│   └── WINDOWS-DEPLOYMENT.md      # This file
├── office_app\
│   ├── office_app.db              # SQLite database
│   ├── models\                    # Database models
│   ├── routes\                    # Web routes
│   ├── templates\                 # HTML templates
│   ├── static\                    # CSS, JS, images
│   └── sync_service.py            # Sync worker
├── venv\                          # Virtual environment
├── logs\                          # Log files
├── .env                           # Configuration
└── requirements.txt               # Dependencies
```

## Next Steps

1. ✅ Install Python 3
2. ✅ Clone repository
3. ✅ Run `scripts\start-server.bat`
4. ✅ Edit `.env` with Pi details
5. ✅ Run `scripts\start-server.bat` again
6. ✅ Open browser to `http://localhost:5000`
7. ✅ Login with admin/admin
8. ✅ Change default password
9. ✅ Configure sync settings
10. ✅ Monitor data sync

Enjoy! 🚀
