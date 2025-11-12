# Cloudflare Tunnel Setup for HerdLinx SAAS

## Overview

Using Cloudflare Tunnel eliminates the need for Nginx and provides:
- ✅ Automatic HTTPS/SSL
- ✅ DDoS protection
- ✅ No port forwarding needed
- ✅ Easy subdomain routing
- ✅ Zero Trust security

## Architecture

```
Cloudflare Edge
    │
    ├── herdlinx.com ──────────────► Tunnel ──► localhost:5001 (Web UI)
    │
    ├── uleth.herdlinx.com ────────► Tunnel ──► localhost:5001 (Web UI)
    │
    ├── lpoly.herdlinx.com ────────► Tunnel ──► localhost:5001 (Web UI)
    │
    └── api.herdlinx.com ──────────► Tunnel ──► localhost:5021 (Office API)
```

## Step 1: Start Both Flask Servers

### Terminal 1 - Web UI (Port 5001)
```bash
cd /Users/arnoldjosephaguila/Documents/GitHub/herdlinx-system/saas
source venv/bin/activate
python run.py
```

### Terminal 2 - Office API (Port 5021)
```bash
cd /Users/arnoldjosephaguila/Documents/GitHub/herdlinx-system/saas
source venv/bin/activate
python run_api.py
```

## Step 2: Cloudflare Tunnel Configuration

Your existing tunnel config should route these domains to local ports.

### Config File (`~/.cloudflared/config.yml` or Cloudflare Dashboard)

```yaml
tunnel: your-tunnel-id
credentials-file: /path/to/your-tunnel-credentials.json

ingress:
  # Main SAAS Web UI
  - hostname: herdlinx.com
    service: http://localhost:5001

  # ULeth Owner Portal
  - hostname: uleth.herdlinx.com
    service: http://localhost:5001

  # LPoly Owner Portal
  - hostname: lpoly.herdlinx.com
    service: http://localhost:5001

  # Office API for Raspberry Pi
  - hostname: api.herdlinx.com
    service: http://localhost:5021

  # Catch-all
  - service: http_status:404
```

## Step 3: DNS Configuration in Cloudflare

In your Cloudflare DNS settings, add CNAME records:

```
Type    Name                Value                       Proxied
CNAME   herdlinx.com        your-tunnel-id.cfargotunnel.com   Yes
CNAME   uleth               your-tunnel-id.cfargotunnel.com   Yes
CNAME   lpoly               your-tunnel-id.cfargotunnel.com   Yes
CNAME   api                 your-tunnel-id.cfargotunnel.com   Yes
```

## Step 4: Test the Setup

### Test Web UI
```bash
curl -I https://herdlinx.com
# Should return 200 or 302 (redirect to login)

curl -I https://uleth.herdlinx.com
# Should return 200 or 302
```

### Test Office API
```bash
curl -X POST https://api.herdlinx.com/v1/feedlot/batches \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "feedlot_code": "ULETH_LRS",
    "data": []
  }'
# Should return 401 (no API key) or 200 (with valid key)
```

## Office Raspberry Pi Configuration

Each office Pi connects to the Cloudflare-protected API endpoint:

### Example: ULeth Research Station Pi

**File**: `office/config.env`
```bash
# MongoDB Connection (via Cloudflare Tunnel)
MONGO_HOST=api.herdlinx.com
MONGO_PORT=27017
MONGO_DB=herdlinx_saas

# SAAS API Configuration
SAAS_API_URL=https://api.herdlinx.com
SAAS_API_KEY=herdlinx_uleth_lrs_1234567890abcdef

# Feedlot Identification
OFFICE_FEEDLOT_CODE=ULETH_LRS

# Sync Settings
SYNC_INTERVAL=5
SYNC_MODE=api
```

### Office Pi Sync Script

The office Pi will POST to:
```
https://api.herdlinx.com/v1/feedlot/batches
https://api.herdlinx.com/v1/feedlot/livestock
https://api.herdlinx.com/v1/feedlot/induction-events
https://api.herdlinx.com/v1/feedlot/pairing-events
https://api.herdlinx.com/v1/feedlot/checkin-events
https://api.herdlinx.com/v1/feedlot/repair-events
```

All requests authenticated with `X-API-Key` header.

## Production Deployment with systemd

### Web UI Service (`/etc/systemd/system/herdlinx-web.service`)
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

### Office API Service (`/etc/systemd/system/herdlinx-api.service`)
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

### Enable Services
```bash
sudo systemctl enable herdlinx-web herdlinx-api
sudo systemctl start herdlinx-web herdlinx-api
sudo systemctl status herdlinx-web herdlinx-api
```

## Firewall Configuration

Since Cloudflare Tunnel handles external access, you only need to allow:

```bash
# Allow MongoDB (if remote)
sudo ufw allow 27017/tcp

# No need to expose 5001 or 5021 to the internet
# Cloudflare Tunnel connects from inside the server
```

## Monitoring

### Check Tunnel Status
```bash
cloudflared tunnel info your-tunnel-name
```

### Check Services
```bash
# Web UI
sudo journalctl -u herdlinx-web -f

# Office API
sudo journalctl -u herdlinx-api -f

# Test locally
curl http://localhost:5001
curl http://localhost:5021/v1/feedlot/batches
```

## Advantages of Cloudflare Tunnel

1. **Security**
   - No open ports on your server
   - DDoS protection included
   - Zero Trust access control

2. **SSL/HTTPS**
   - Automatic certificate management
   - Always encrypted

3. **Performance**
   - Cloudflare CDN caching
   - Global edge network
   - Fast DNS resolution

4. **Management**
   - Easy subdomain routing
   - No Nginx configuration needed
   - Dashboard control

## Troubleshooting

### Issue: Tunnel not connecting
```bash
# Restart tunnel
sudo systemctl restart cloudflared

# Check logs
sudo journalctl -u cloudflared -f
```

### Issue: 502 Bad Gateway
**Cause**: Flask servers not running

**Solution**:
```bash
sudo systemctl start herdlinx-web
sudo systemctl start herdlinx-api
```

### Issue: Office Pi can't connect
**Cause**: Wrong API URL or API key

**Solution**:
- Verify: `https://api.herdlinx.com` (must be HTTPS with Cloudflare)
- Check API key is valid in SAAS settings

## Summary

✅ **No Nginx needed** - Cloudflare handles everything
✅ **Port 5001** - Web UI (herdlinx.com, uleth.herdlinx.com, etc.)
✅ **Port 5021** - Office API (api.herdlinx.com)
✅ **Automatic HTTPS** - Cloudflare managed
✅ **DDoS Protection** - Built-in
✅ **Zero configuration** - Just point DNS to tunnel

Your setup is production-ready! 🚀
