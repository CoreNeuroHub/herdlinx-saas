# HerdLinx Distributed Architecture

This document describes the distributed architecture with separate Raspberry Pi backend and remote Server UI.

## Overview

```
┌──────────────────┐         Secure Connection          ┌──────────────────┐
│                  │         (REST + WebSocket)         │                  │
│  Raspberry Pi    │◄────────────────────────────────►│  Remote Server   │
│  Backend         │                                    │  Web UI          │
│                  │                                    │                  │
├──────────────────┤                                    ├──────────────────┤
│ SQLite Database  │                                    │ Web Interface    │
│ LoRa Receiver    │                                    │ Authentication   │
│ Payload Buffer   │                                    │ Admin Dashboard  │
│ Background       │                                    │                  │
│ Worker           │                                    │ Remote Client    │
│ WebSocket Server │                                    │ - REST API       │
│ REST API Server  │                                    │ - WebSocket      │
└──────────────────┘                                    └──────────────────┘
       Port 5001                                              Port 5000
       (With TLS)                                        (Connects to Pi)
```

## Architecture Components

### Raspberry Pi Backend (`aj/pi-backend` branch)

**Responsibilities:**
- Receive LoRa sensor data
- Buffer and deduplicate payloads
- Process payloads asynchronously
- Create batches in SQLite
- Serve REST API for remote access
- Broadcast real-time updates via WebSocket

**Key Modules:**
- `utils/background_worker.py` - Async payload processor
- `utils/payload_processor.py` - Payload parsing and deduplication
- `models/` - SQLAlchemy database models
- `security.py` - API authentication (API key, JWT)
- `remote_api.py` - REST API and WebSocket endpoints
- `generate_certs.py` - Self-signed certificate generation

**Configuration:**
```python
# Set in environment or config
IS_PI_BACKEND = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///office_app/office_app.db'
PI_API_KEY = 'your-secure-api-key'
```

**Running on Raspberry Pi:**
```bash
# Generate SSL certificates (one-time)
python -m office_app.generate_certs

# Run the backend
python -m office_app.run
# Accessible at: https://raspberry-pi-ip:5001
```

### Remote Server UI (`aj/server-ui` branch)

**Responsibilities:**
- Display admin web interface
- Authenticate users
- Fetch batch and payload data from Pi backend
- Display real-time updates
- User session management

**Key Modules:**
- `remote_db_client.py` - REST API client for Pi backend
- `websocket_client.py` - WebSocket client for real-time updates
- `routes/office_routes.py` - UI routes (modified for remote queries)
- `routes/auth_routes.py` - User authentication

**Configuration:**
```python
# Set in environment or config
IS_SERVER_UI = True
REMOTE_PI_HOST = 'raspberry-pi.local'  # or IP address
REMOTE_PI_PORT = 5001
PI_API_KEY = 'your-secure-api-key'  # Must match Pi
USE_SSL_FOR_PI = True
```

**Running on Server:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m office_app.run
# Accessible at: http://localhost:5000
```

## Setup Instructions

### 1. Generate SSL Certificates (Raspberry Pi)

```bash
# On the Raspberry Pi
cd /path/to/herdlinx-saas
git checkout aj/pi-backend

python -m office_app.generate_certs
```

This creates:
- `office_app/certs/server.crt` - Self-signed certificate
- `office_app/certs/server.key` - Private key

**Note:** If OpenSSL is not available, the script will use the cryptography library as fallback.

### 2. Configure Raspberry Pi Backend

Create `.env` file:
```bash
# Raspberry Pi .env
FLASK_ENV=development
PI_API_KEY=hxb_your_secure_api_key_here
IS_PI_BACKEND=True
```

Or set environment variables:
```bash
export PI_API_KEY='hxb_your_secure_api_key_here'
export IS_PI_BACKEND=True
```

### 3. Start Raspberry Pi Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run the backend server
python -m office_app.run

# Expected output:
# Starting Office Herd Management on https://0.0.0.0:5001
# WebSocket server running
```

### 4. Configure Remote Server

Create `.env` file:
```bash
# Remote Server .env
FLASK_ENV=development
REMOTE_PI_HOST=192.168.1.100  # Raspberry Pi IP or hostname
REMOTE_PI_PORT=5001
PI_API_KEY=hxb_your_secure_api_key_here  # Must match Pi
USE_SSL_FOR_PI=true
USE_SELF_SIGNED_CERT=true
IS_SERVER_UI=True
```

### 5. Start Remote Server

```bash
# Switch to server UI branch
git checkout aj/server-ui

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m office_app.run

# Expected output:
# Starting Office Herd Management on http://0.0.0.0:5000
# Remote client initialized successfully
# WebSocket connection successful
```

### 6. Access the Web Interface

1. Open browser to `http://localhost:5000` (or server IP)
2. Login with default credentials: `admin` / `admin`
3. View dashboard - should show real-time updates from Pi

## Communication Protocols

### REST API (Request/Response)

**Used for:**
- Fetching batches and payloads
- System status queries
- One-time data retrieval

**Endpoints:**
```
GET /api/remote/batches
GET /api/remote/batches/{id}
GET /api/remote/payloads
GET /api/remote/payloads/{id}
GET /api/remote/status
POST /api/remote/auth/token
```

**Authentication:**
- API Key: `X-API-Key: <your-api-key>` header
- JWT Token: `Authorization: Bearer <token>` header

### WebSocket (Pub/Sub)

**Used for:**
- Real-time payload received notifications
- Real-time payload processing updates
- Real-time batch creation events

**Events:**
```
payload:received       - New payload buffered
payload:processed      - Payload successfully processed
batch:created          - New batch created
```

**Subscribe/Unsubscribe:**
```javascript
// Client subscribes to updates
socket.emit('subscribe:payloads');
socket.emit('subscribe:batches');

// Server broadcasts
socket.emit('payload:received', {
  payload_id: 1,
  raw_payload: 'hxb:BATCH001:LF123:UHF456',
  timestamp: '2024-01-15T10:30:00'
});
```

## Security Configuration

### SSL/TLS Certificates

The system uses **self-signed certificates** for the Raspberry Pi backend.

**Generate certificates (one-time):**
```bash
python -m office_app.generate_certs
```

**For production:**
1. Replace with properly signed certificates from a CA
2. Update `office_app/certs/server.crt` and `server.key`
3. Set `USE_SELF_SIGNED_CERT=false` in environment

### API Key Authentication

**For Raspberry Pi:**
```bash
# Generate a secure API key
export PI_API_KEY='hxb_'$(openssl rand -hex 20)

# Or use python
python -c "from office_app.security import APIKeyManager; print(APIKeyManager.generate_api_key())"
```

**Configure on both Pi and Server:**
- Pi: `.env` with `PI_API_KEY=...`
- Server: `.env` with `PI_API_KEY=...` (must match)

### JWT Token Management

The system automatically:
1. Uses API key to get JWT token on first request
2. Caches token for 24 hours
3. Automatically refreshes when expired
4. Falls back to API key if token invalid

### Network Security

**Recommended firewall rules:**

```bash
# On Raspberry Pi - only allow server to connect
iptables -A INPUT -p tcp --dport 5001 -s <SERVER_IP> -j ACCEPT
iptables -A INPUT -p tcp --dport 5001 -j DROP
```

**Or use SSH tunnel for added security:**
```bash
# On Server, create SSH tunnel to Pi
ssh -L 5001:localhost:5001 pi@raspberry-pi.local

# Then connect through tunnel
# REMOTE_PI_HOST=localhost
# REMOTE_PI_PORT=5001
```

## Data Flow Example

### Payload Reception
```
1. LoRa Sensor → Raspberry Pi (UDP/Serial)
2. Pi buffers payload → SQLite
3. Pi broadcasts via WebSocket:
   socket.emit('payload:received', {...})
4. Server receives event → UI updates in real-time
5. Latency: <100ms
```

### Payload Processing
```
1. Background worker processes payload every 5 seconds
2. Worker parses format: hxb:BATCH001:LF123:UHF456
3. Worker creates batch in SQLite
4. Worker broadcasts:
   socket.emit('payload:processed', {...})
5. Server receives event → UI updates status
6. User sees batch immediately created
```

## Troubleshooting

### "Connection refused" error
```
Check:
1. Raspberry Pi backend is running
   ps aux | grep office_app
2. Firewall allows port 5001
   sudo ufw allow 5001
3. Pi IP address is correct
   hostname -I
4. No port conflicts
   sudo lsof -i :5001
```

### "SSL certificate verification failed"
```
Solutions:
1. Ensure USE_SELF_SIGNED_CERT=true in server config
2. Regenerate certificates on Pi:
   rm -rf office_app/certs/
   python -m office_app.generate_certs
3. For production, use proper CA certificates
```

### "API key authentication failed"
```
Check:
1. API key matches on both Pi and Server
   echo $PI_API_KEY
2. Header format is correct:
   X-API-Key: <key>
3. Token hasn't expired (auto-refresh should handle)
```

### "Real-time updates not working"
```
Check:
1. WebSocket client connected:
   Server log should show "Connected to remote WebSocket"
2. Subscribed to events:
   Check websocket_client.py subscribe_payloads()
3. Firewall allows WebSocket:
   curl wss://pi-ip:5001/socket.io/
4. Browser console for JS errors (if applicable)
```

## Performance Considerations

### Latency
- **API Request**: 50-200ms (network dependent)
- **WebSocket Update**: <100ms (real-time)
- **Payload Processing**: <5 seconds (interval-based)

### Scalability
- **Single Server**: Handles 100+ concurrent UI users
- **Payload Throughput**: 1-2/second per device
- **Storage**: ~500 bytes per payload

### Network Requirements
- **Bandwidth**: Minimal (<1 Mbps average)
- **Latency**: <500ms acceptable
- **Reliability**: TCP/WebSocket handles retries

## Monitoring

### Health Checks

**From Server:**
```bash
# Check Pi backend health
curl -k https://pi-ip:5001/api/remote/health

# Check system status
curl -k https://pi-ip:5001/api/remote/status \
  -H "X-API-Key: your-api-key"
```

**From Pi:**
```bash
# Check local database
sqlite3 office_app/office_app.db "SELECT COUNT(*) FROM lora_payload_buffer;"

# Check background worker
tail -f logs/app.log
```

### Logging

Enable debug logging:
```python
# In config.py
LOGGING_LEVEL = 'DEBUG'
```

Or via environment:
```bash
export LOG_LEVEL=DEBUG
python -m office_app.run
```

## Migration Path

If you need to separate into true separate repositories:

1. **Create Pi Repository:**
   ```bash
   git checkout aj/pi-backend
   git checkout --orphan root-pi
   git commit -m "Initial Pi backend"
   git push -u origin root-pi
   ```

2. **Create Server Repository:**
   ```bash
   git checkout aj/server-ui
   git checkout --orphan root-server
   git commit -m "Initial Server UI"
   git push -u origin root-server
   ```

3. **Configure Both:**
   - Pi: `IS_PI_BACKEND=True`
   - Server: `IS_SERVER_UI=True`

## Future Enhancements

- [ ] Database replication for failover
- [ ] Multiple Pi backends with load balancing
- [ ] WebUI for managing remote connection
- [ ] Real-time charts/graphs
- [ ] Mobile app with notifications
- [ ] Advanced filtering and reporting
- [ ] Data export (CSV/Excel)
- [ ] Webhook integrations

## Additional Resources

- [LORA_PAYLOAD_SYSTEM.md](office_app/LORA_PAYLOAD_SYSTEM.md) - Detailed payload documentation
- [README.md](README.md) - Quick start guide
- `.env.example` - Configuration template
